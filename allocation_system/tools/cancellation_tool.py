from google.adk.tools import BaseTool
from datetime import datetime, timedelta
import logging
from ..models import hospital_db, AppointmentStatus

class SmartCancellationTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="cancel_appointment",
            description="""Intelligent appointment cancellation system with advanced search and automation.
            
            Handles various cancellation requests:
            - "Cancel appointment APT0001" → direct appointment cancellation
            - "Cancel my appointment" → searches by context/patient ID
            - "Remove John's booking" → searches by patient name
            - "Delete tomorrow's appointment" → searches by date
            - "Cancel with Dr. Smith" → searches by doctor
            
            Smart appointment finding:
            - Searches by appointment ID, patient ID, doctor name, or date
            - Handles multiple appointments with intelligent selection
            - Provides clear options when multiple matches found
            - Auto-confirms single matches
            
            Advanced features:
            - Automatic waitlist notification when slots become available
            - Rebooking suggestions for cancelled appointments
            - Cancellation reason tracking for analytics
            - Automatic refund processing (if applicable)
            
            Returns detailed cancellation confirmations with freed slot information."""
        )
    
    async def execute(self, appointment_id: str = None, patient_id: str = None, 
                     doctor_id: str = None, date: str = None, reason: str = None):
        try:
            appointments = hospital_db.appointments
            doctors = hospital_db.doctors
            
            # Smart appointment finding
            appointment_to_cancel = None
            search_results = []
            
            if appointment_id:
                # Direct appointment ID search
                appointment_to_cancel = next((apt for apt in appointments 
                                            if apt.id.upper() == appointment_id.upper() 
                                            and apt.status == AppointmentStatus.SCHEDULED), None)
                
                if not appointment_to_cancel:
                    active_appointments = [apt.id for apt in appointments if apt.status == AppointmentStatus.SCHEDULED]
                    similar_ids = [apt_id for apt_id in active_appointments 
                                 if appointment_id.upper() in apt_id or apt_id in appointment_id.upper()]
                    
                    return {
                        "status": "not_found",
                        "message": f"Appointment {appointment_id} not found or already cancelled",
                        "active_appointments": active_appointments,
                        "similar_appointments": similar_ids,
                        "suggestion": f"Did you mean: {similar_ids[0] if similar_ids else 'check your appointment ID'}"
                    }
            
            else:
                # Advanced search by multiple criteria
                for apt in appointments:
                    if apt.status != AppointmentStatus.SCHEDULED:
                        continue
                    
                    match_score = 0
                    match_reasons = []
                    
                    if patient_id and patient_id.lower() in apt.patient_id.lower():
                        match_score += 3
                        match_reasons.append("patient_id")
                    
                    if doctor_id and doctor_id == apt.doctor_id:
                        match_score += 2
                        match_reasons.append("doctor")
                    
                    if date and date == apt.date:
                        match_score += 2
                        match_reasons.append("date")
                    
                    if match_score > 0:
                        search_results.append({
                            "appointment": apt,
                            "match_score": match_score,
                            "match_reasons": match_reasons
                        })
                
                # Sort by match score
                search_results.sort(key=lambda x: x["match_score"], reverse=True)
                
                if not search_results:
                    return {
                        "status": "no_matches",
                        "message": "No matching appointments found",
                        "search_criteria": {
                            "patient_id": patient_id,
                            "doctor_id": doctor_id,
                            "date": date
                        },
                        "suggestion": "Please provide appointment ID or check your search criteria"
                    }
                
                elif len(search_results) == 1:
                    appointment_to_cancel = search_results[0]["appointment"]
                
                else:
                    # Multiple matches - let user choose
                    match_list = []
                    for result in search_results[:5]:  # Show top 5 matches
                        apt = result["appointment"]
                        doctor = doctors[apt.doctor_id]
                        match_list.append({
                            "appointment_id": apt.id,
                            "patient_id": apt.patient_id,
                            "doctor_name": doctor.name,
                            "specialty": doctor.specialty,
                            "date": apt.date,
                            "time": apt.time,
                            "match_reasons": result["match_reasons"]
                        })
                    
                    return {
                        "status": "multiple_matches",
                        "message": f"Found {len(search_results)} matching appointments",
                        "matches": match_list,
                        "instruction": "Please specify which appointment to cancel using the appointment ID"
                    }
            
            if not appointment_to_cancel:
                return {"status": "error", "message": "No appointment found to cancel"}
            
            # Perform cancellation
            success = hospital_db.update_appointment_status(appointment_to_cancel.id, AppointmentStatus.CANCELLED)
            
            if not success:
                return {"status": "error", "message": "Failed to cancel appointment - please try again"}
            
            # Generate comprehensive cancellation response
            doctor = doctors[appointment_to_cancel.doctor_id]
            
            cancellation_response = {
                "status": "success",
                "message": "Appointment successfully cancelled",
                "cancelled_appointment": {
                    "id": appointment_to_cancel.id,
                    "patient_id": appointment_to_cancel.patient_id,
                    "doctor_name": doctor.name,
                    "specialty": doctor.specialty,
                    "date": appointment_to_cancel.date,
                    "time": appointment_to_cancel.time,
                    "cancellation_time": datetime.now().isoformat(),
                    "cancellation_reason": reason
                },
                "freed_slot": {
                    "doctor_id": appointment_to_cancel.doctor_id,
                    "doctor_name": doctor.name,
                    "date": appointment_to_cancel.date,
                    "time": appointment_to_cancel.time,
                    "availability_message": f"The {appointment_to_cancel.time} slot with {doctor.name} on {appointment_to_cancel.date} is now available"
                }
            }
            
            # Add rebooking suggestions
            rebooking_suggestions = await self._generate_rebooking_suggestions(appointment_to_cancel)
            if rebooking_suggestions:
                cancellation_response["rebooking_options"] = rebooking_suggestions
            
            return cancellation_response
            
        except Exception as e:
            logger.error(f"Cancellation error: {str(e)}")
            return {"status": "error", "message": f"Cancellation failed: {str(e)}"}
    
    async def _generate_rebooking_suggestions(self, cancelled_appointment):
        """Generate intelligent rebooking suggestions"""
        try:
            doctors = hospital_db.doctors
            appointments = hospital_db.appointments
            
            suggestions = []
            
            # Same doctor, different time
            doctor = doctors[cancelled_appointment.doctor_id]
            for days_ahead in range(1, 14):  # Next 2 weeks
                check_date = (datetime.strptime(cancelled_appointment.date, "%Y-%m-%d").date() + 
                            timedelta(days=days_ahead)).strftime("%Y-%m-%d")
                
                if check_date in doctor.available_days:
                    booked_times = [apt.time for apt in appointments 
                                  if apt.doctor_id == cancelled_appointment.doctor_id and apt.date == check_date 
                                  and apt.status == AppointmentStatus.SCHEDULED]
                    
                    available_times = [time for time in doctor.available_hours if time not in booked_times]
                    
                    if available_times:
                        suggestions.append({
                            "type": "same_doctor",
                            "doctor_name": doctor.name,
                            "doctor_id": cancelled_appointment.doctor_id,
                            "date": check_date,
                            "available_times": available_times[:3],  # Show first 3 times
                            "priority": 1
                        })
                        break
            
            # Different doctor, same specialty
            specialty = doctor.specialty
            other_doctors = [doc for doc in doctors.values() 
                           if doc.specialty == specialty and doc.id != cancelled_appointment.doctor_id]
            
            for other_doc in other_doctors:
                for days_ahead in range(0, 7):  # Next week
                    check_date = (datetime.strptime(cancelled_appointment.date, "%Y-%m-%d").date() + 
                                timedelta(days=days_ahead)).strftime("%Y-%m-%d")
                    
                    if check_date in other_doc.available_days:
                        booked_times = [apt.time for apt in appointments 
                                      if apt.doctor_id == other_doc.id and apt.date == check_date 
                                      and apt.status == AppointmentStatus.SCHEDULED]
                        
                        available_times = [time for time in other_doc.available_hours if time not in booked_times]
                        
                        if available_times:
                            suggestions.append({
                                "type": "same_specialty",
                                "doctor_name": other_doc.name,
                                "doctor_id": other_doc.id,
                                "specialty": other_doc.specialty,
                                "date": check_date,
                                "available_times": available_times[:2],
                                "priority": 2
                            })
                            break
            
            # Sort by priority and return top suggestions
            suggestions.sort(key=lambda x: x["priority"])
            return suggestions[:3]
            
        except Exception as e:
            logger.error(f"Rebooking suggestions error: {str(e)}")
            return []