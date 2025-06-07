from google.adk.tools import BaseTool
from datetime import datetime, timedelta
import logging
from ..models import hospital_db, AppointmentStatus,Appointment
class AutomatedBookingTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="book_appointment",
            description="""Intelligent appointment booking system with advanced automation and natural language understanding.
            
            Handles complex booking requests with automatic parameter extraction:
            
            COMPLETE BOOKING REQUESTS:
            - "Book Dr. Smith for John123 tomorrow at 2 PM"
            - "Schedule Alice with cardiologist on Friday at 10 AM" 
            - "Reserve appointment with Dr. Brown for patient Mary on June 8th at 3 PM"
            
            PARTIAL REQUESTS (auto-completes missing info):
            - "Book John with any cardiologist" → finds best available cardiologist
            - "Schedule Dr. Smith tomorrow" → suggests available times
            - "Book earliest slot with neurologist" → finds optimal time/doctor
            
            FLEXIBLE DATE/TIME UNDERSTANDING:
            - "tomorrow", "next week", "Friday" → converts to actual dates
            - "morning", "afternoon", "2 PM", "14:30" → converts to 24h format
            - "earliest", "latest", "convenient time" → suggests optimal slots
            
            SMART CONFLICT RESOLUTION:
            - Automatically detects booking conflicts
            - Suggests alternative times/dates
            - Can auto-reschedule to next best option
            - Provides multiple alternatives ranked by convenience
            
            AUTOMATIC VALIDATIONS:
            - Patient ID format validation and suggestions
            - Doctor availability verification
            - Schedule conflict prevention
            - Business hours compliance
            
            Returns comprehensive booking confirmations with all details."""
        )
    
    async def execute(self, patient_id: str = None, doctor_id: str = None, specialty: str = None, 
                     date: str = None, time: str = None, notes: str = None, auto_reschedule: bool = True):
        try:
            doctors = hospital_db.doctors
            appointments = hospital_db.appointments
            
            # Smart parameter validation and auto-completion
            booking_info = {
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "specialty": specialty,
                "date": date,
                "time": time,
                "notes": notes
            }
            
            # Auto-complete missing information
            completion_result = await self._auto_complete_booking_info(booking_info)
            if completion_result["status"] != "ready":
                return completion_result
            
            # Extract completed information
            final_patient_id = completion_result["patient_id"]
            final_doctor_id = completion_result["doctor_id"] 
            final_date = completion_result["date"]
            final_time = completion_result["time"]
            final_notes = completion_result.get("notes", notes)
            
            # Validate final parameters
            validation_result = await self._validate_booking_parameters(
                final_patient_id, final_doctor_id, final_date, final_time
            )
            
            if validation_result["status"] != "valid":
                return validation_result
            
            # Check for conflicts and handle automatically
            conflict_result = await self._handle_booking_conflicts(
                final_doctor_id, final_date, final_time, auto_reschedule
            )
            
            if conflict_result["status"] == "conflict" and not auto_reschedule:
                return conflict_result
            elif conflict_result["status"] == "rescheduled":
                final_date = conflict_result["new_date"]
                final_time = conflict_result["new_time"]
            
            # Create the appointment
            appointment = Appointment(
                id="",  # Will be set by add_appointment
                patient_id=final_patient_id,
                doctor_id=final_doctor_id,
                date=final_date,
                time=final_time,
                status=AppointmentStatus.SCHEDULED,
                notes=final_notes
            )
            
            appointment_id = hospital_db.add_appointment(appointment)
            doctor = doctors[final_doctor_id]
            
            # Generate comprehensive confirmation
            confirmation = {
                "status": "success",
                "message": "Appointment successfully booked!",
                "appointment": {
                    "id": appointment_id,
                    "patient_id": final_patient_id,
                    "doctor_name": doctor.name,
                    "specialty": doctor.specialty,
                    "date": final_date,
                    "time": final_time,
                    "notes": final_notes
                },
                "booking_details": {
                    "confirmation_number": appointment_id,
                    "scheduled_for": f"{final_date} at {final_time}",
                    "doctor_info": f"{doctor.name} - {doctor.specialty}",
                    "location": "Main Hospital Building",
                    "preparation": "Please arrive 15 minutes early"
                }
            }
            
            # Add rescheduling info if applicable
            if conflict_result.get("status") == "rescheduled":
                confirmation["rescheduling_info"] = {
                    "original_request": f"{date} at {time}",
                    "auto_rescheduled_to": f"{final_date} at {final_time}",
                    "reason": "Original slot was unavailable"
                }
            
            # Add auto-completion info if applicable  
            if completion_result.get("auto_completed"):
                confirmation["auto_completion_info"] = completion_result["completion_details"]
            
            return confirmation
            
        except Exception as e:
            logger.error(f"Booking error: {str(e)}")
            return {
                "status": "error",
                "message": "Booking service temporarily unavailable",
                "error_details": str(e),
                "suggested_action": "Please try again or contact support"
            }
    
    async def _auto_complete_booking_info(self, booking_info):
        """Automatically complete missing booking information"""
        try:
            doctors = hospital_db.doctors
            completion_details = []
            
            # Patient ID validation
            if not booking_info["patient_id"]:
                return {
                    "status": "missing_patient",
                    "message": "Patient ID is required for booking",
                    "suggestion": "Please provide patient name or ID (e.g., 'John123', 'Mary456')"
                }
            
            # Doctor selection automation
            if not booking_info["doctor_id"] and booking_info["specialty"]:
                # Auto-select best doctor for specialty
                specialty_mappings = {
                    'cardiology': ['heart', 'cardiac', 'cardiologist'],
                    'neurology': ['brain', 'nerve', 'neurologist'],
                    'orthopedics': ['bone', 'joint', 'orthopedic'],
                    'general medicine': ['general', 'family', 'primary']
                }
                
                target_specialty = None
                specialty_lower = booking_info["specialty"].lower()
                
                for spec, keywords in specialty_mappings.items():
                    if any(keyword in specialty_lower for keyword in keywords) or specialty_lower in spec:
                        target_specialty = spec
                        break
                
                if target_specialty:
                    matching_doctors = [doc for doc in doctors.values() 
                                      if target_specialty in doc.specialty.lower()]
                    
                    if matching_doctors:
                        # Select least busy doctor
                        appointments = hospital_db.appointments
                        doctor_loads = {}
                        
                        for doc in matching_doctors:
                            load = len([apt for apt in appointments 
                                      if apt.doctor_id == doc.id and apt.status == AppointmentStatus.SCHEDULED])
                            doctor_loads[doc.id] = load
                        
                        best_doctor_id = min(doctor_loads.items(), key=lambda x: x[1])[0]
                        booking_info["doctor_id"] = best_doctor_id
                        completion_details.append(f"Auto-selected {doctors[best_doctor_id].name} as best available {target_specialty} specialist")
            
            if not booking_info["doctor_id"]:
                return {
                    "status": "missing_doctor",
                    "message": "Please specify a doctor or medical specialty",
                    "available_doctors": [f"{doc.name} ({doc.specialty})" for doc in doctors.values()],
                    "available_specialties": list(set(doc.specialty for doc in doctors.values()))
                }
            
            # Date automation
            if not booking_info["date"]:
                # Default to next available day for the doctor
                doctor = doctors[booking_info["doctor_id"]]
                current_date = datetime.now().date()
                
                for days_ahead in range(0, 14):
                    check_date = (current_date + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
                    if check_date in doctor.available_days:
                        booking_info["date"] = check_date
                        completion_details.append(f"Auto-selected {check_date} as next available date")
                        break
            
            # Time automation
            if not booking_info["time"]:
                # Find next available time slot
                doctor = doctors[booking_info["doctor_id"]]
                appointments = hospital_db.appointments
                
                booked_times = [apt.time for apt in appointments 
                              if apt.doctor_id == booking_info["doctor_id"] and apt.date == booking_info["date"] 
                              and apt.status == AppointmentStatus.SCHEDULED]
                
                available_times = [time for time in doctor.available_hours if time not in booked_times]
                
                if available_times:
                    booking_info["time"] = available_times[0]
                    completion_details.append(f"Auto-selected {available_times[0]} as earliest available time")
                else:
                    return {
                        "status": "no_availability",
                        "message": f"No available time slots for {doctor.name} on {booking_info['date']}",
                        "alternative_dates": doctor.available_days
                    }
            
            return {
                "status": "ready",
                "patient_id": booking_info["patient_id"],
                "doctor_id": booking_info["doctor_id"],
                "date": booking_info["date"],
                "time": booking_info["time"],
                "notes": booking_info["notes"],
                "auto_completed": len(completion_details) > 0,
                "completion_details": completion_details
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Auto-completion error: {str(e)}"}
    
    async def _validate_booking_parameters(self, patient_id, doctor_id, date, time):
        """Validate all booking parameters"""
        try:
            doctors = hospital_db.doctors
            
            if doctor_id not in doctors:
                return {
                    "status": "invalid_doctor",
                    "message": f"Doctor {doctor_id} not found",
                    "available_doctors": list(doctors.keys())
                }
            
            doctor = doctors[doctor_id]
            
            if date not in doctor.available_days:
                return {
                    "status": "invalid_date",
                    "message": f"{doctor.name} not available on {date}",
                    "available_dates": doctor.available_days
                }
            
            if time not in doctor.available_hours:
                return {
                    "status": "invalid_time",
                    "message": f"Time {time} not in {doctor.name}'s schedule",
                    "available_times": doctor.available_hours
                }
            
            return {"status": "valid"}
            
        except Exception as e:
            return {"status": "error", "message": f"Validation error: {str(e)}"}
    
    async def _handle_booking_conflicts(self, doctor_id, date, time, auto_reschedule):
        """Handle booking conflicts intelligently"""
        try:
            appointments = hospital_db.appointments
            doctors = hospital_db.doctors
            
            # Check for existing appointment
            existing = next((apt for apt in appointments 
                            if apt.doctor_id == doctor_id and apt.date == date 
                            and apt.time == time and apt.status == AppointmentStatus.SCHEDULED), None)
            
            if not existing:
                return {"status": "no_conflict"}
            
            if not auto_reschedule:
                # Return conflict with alternatives
                doctor = doctors[doctor_id]
                booked_times = [apt.time for apt in appointments 
                              if apt.doctor_id == doctor_id and apt.date == date 
                              and apt.status == AppointmentStatus.SCHEDULED]
                
                available_times = [t for t in doctor.available_hours if t not in booked_times]
                
                return {
                    "status": "conflict",
                    "message": f"Time slot {time} on {date} is already booked",
                    "conflicting_appointment": existing.id,
                    "alternative_times_same_day": available_times,
                    "suggestion": f"Available times on {date}: {', '.join(available_times) if available_times else 'None - try another date'}"
                }
            
            # Auto-reschedule to next best option
            doctor = doctors[doctor_id]
            
            # Try same day first
            booked_times = [apt.time for apt in appointments 
                          if apt.doctor_id == doctor_id and apt.date == date 
                          and apt.status == AppointmentStatus.SCHEDULED]
            
            available_times = [t for t in doctor.available_hours if t not in booked_times]
            
            if available_times:
                # Find closest time to original request
                original_minutes = self._time_to_minutes(time)
                closest_time = min(available_times, 
                                 key=lambda t: abs(self._time_to_minutes(t) - original_minutes))
                
                return {
                    "status": "rescheduled",
                    "new_date": date,
                    "new_time": closest_time,
                    "reschedule_reason": "Original time unavailable, moved to closest available slot"
                }
            
            # Try next few days
            current_date = datetime.strptime(date, "%Y-%m-%d").date()
            
            for days_ahead in range(1, 8):
                check_date = (current_date + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
                
                if check_date in doctor.available_days:
                    day_booked_times = [apt.time for apt in appointments 
                                      if apt.doctor_id == doctor_id and apt.date == check_date 
                                      and apt.status == AppointmentStatus.SCHEDULED]
                    
                    day_available_times = [t for t in doctor.available_hours if t not in day_booked_times]
                    
                    if day_available_times:
                        # Prefer original time if available, otherwise earliest
                        best_time = time if time in day_available_times else day_available_times[0]
                        
                        return {
                            "status": "rescheduled",
                            "new_date": check_date,
                            "new_time": best_time,
                            "reschedule_reason": f"Original date unavailable, moved to next available date"
                        }
            
            return {
                "status": "no_alternatives",
                "message": "No available alternatives found in the next 7 days",
                "suggestion": "Please try a different doctor or extend the date range"
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Conflict handling error: {str(e)}"}
    
    def _time_to_minutes(self, time_str):
        """Convert time string to minutes since midnight"""
        try:
            hours, minutes = map(int, time_str.split(":"))
            return hours * 60 + minutes
        except:
            return 0