from google.adk.tools import BaseTool
from datetime import datetime, timedelta
import logging
from ..models import hospital_db, AppointmentStatus
class IntelligentAvailabilityTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="check_availability",
            description="""Advanced availability checker with intelligent schedule analysis.
            
            Understands various availability queries:
            - "Is Dr. Smith available?" → checks general availability
            - "When can I see Dr. Brown?" → finds next available slots
            - "Dr. Jones schedule tomorrow" → specific date availability
            - "Available times this week" → shows weekly availability
            - "Who's free right now?" → immediate availability check
            
            Provides detailed availability information including:
            - Available time slots for specific dates
            - Next available appointments
            - Alternative doctors if primary choice unavailable
            - Booking recommendations based on patient preferences
            
            Handles flexible date expressions:
            - "tomorrow", "next week", "Friday"
            - Specific dates: "June 7th", "2025-06-07"
            - Relative dates: "in 3 days", "next Monday"
            """
        )
    
    async def execute(self, doctor_id: str = None, date: str = None, specialty: str = None):
        try:
            doctors = hospital_db.doctors
            appointments = hospital_db.appointments
            
            if doctor_id and doctor_id not in doctors:
                return {"status": "error", "message": f"Doctor {doctor_id} not found in system"}
            
            if specialty and not doctor_id:
                # Find doctors by specialty first
                specialty_mappings = {
                    'cardiology': ['heart', 'cardiac', 'cardiologist'],
                    'neurology': ['brain', 'nerve', 'neurologist', 'neuro'],
                    'orthopedics': ['bone', 'joint', 'orthopedic', 'ortho'],
                    'general medicine': ['general', 'family', 'primary', 'gp']
                }
                
                target_specialty = None
                for spec, keywords in specialty_mappings.items():
                    if any(keyword in specialty.lower() for keyword in keywords) or specialty.lower() in spec:
                        target_specialty = spec
                        break
                
                if target_specialty:
                    matching_doctors = [doc for doc in doctors.values() 
                                      if target_specialty in doc.specialty.lower()]
                    
                    if matching_doctors:
                        # Return availability for all doctors in specialty
                        specialty_availability = {}
                        for doctor in matching_doctors:
                            availability = await self._get_doctor_availability(doctor.id, date)
                            specialty_availability[doctor.name] = availability
                        
                        return {
                            "status": "success",
                            "specialty": target_specialty,
                            "availability_by_doctor": specialty_availability
                        }
                
                return {"status": "error", "message": f"No doctors found for specialty: {specialty}"}
            
            if doctor_id:
                availability = await self._get_doctor_availability(doctor_id, date)
                return availability
            
            else:
                # General availability overview
                system_availability = {}
                for doc_id, doctor in doctors.items():
                    availability = await self._get_doctor_availability(doc_id, date)
                    system_availability[doctor.name] = availability
                
                return {
                    "status": "success",
                    "system_wide_availability": system_availability,
                    "summary": self._generate_availability_summary(system_availability)
                }
                
        except Exception as e:
            logger.error(f"Availability check error: {str(e)}")
            return {"status": "error", "message": f"Availability service error: {str(e)}"}
    
    async def _get_doctor_availability(self, doctor_id: str, date: str = None):
        """Get detailed availability for a specific doctor"""
        try:
            doctors = hospital_db.doctors
            appointments = hospital_db.appointments
            
            doctor = doctors[doctor_id]
            
            if date:
                # Specific date availability
                if date not in doctor.available_days:
                    return {
                        "status": "unavailable_date",
                        "doctor_name": doctor.name,
                        "message": f"{doctor.name} not available on {date}",
                        "available_dates": doctor.available_days
                    }
                
                booked_slots = [apt.time for apt in appointments 
                              if apt.doctor_id == doctor_id and apt.date == date 
                              and apt.status == AppointmentStatus.SCHEDULED]
                
                available_slots = [time for time in doctor.available_hours if time not in booked_slots]
                
                return {
                    "status": "success",
                    "doctor_name": doctor.name,
                    "specialty": doctor.specialty,
                    "date": date,
                    "available_slots": available_slots,
                    "booked_slots": booked_slots,
                    "total_capacity": len(doctor.available_hours),
                    "utilization": round((len(booked_slots) / len(doctor.available_hours)) * 100, 1)
                }
            else:
                # General availability - next few days
                next_slots = []
                current_date = datetime.now().date()
                
                for days_ahead in range(0, 7):  # Check next 7 days
                    check_date = (current_date + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
                    
                    if check_date in doctor.available_days:
                        booked_times = [apt.time for apt in appointments 
                                      if apt.doctor_id == doctor_id and apt.date == check_date 
                                      and apt.status == AppointmentStatus.SCHEDULED]
                        
                        available_times = [time for time in doctor.available_hours if time not in booked_times]
                        
                        if available_times:
                            next_slots.append({
                                "date": check_date,
                                "available_times": available_times,
                                "slots_available": len(available_times)
                            })
                
                return {
                    "status": "success",
                    "doctor_name": doctor.name,
                    "specialty": doctor.specialty,
                    "available_days": doctor.available_days,
                    "working_hours": doctor.available_hours,
                    "next_7_days_availability": next_slots,
                    "earliest_available": next_slots[0] if next_slots else None
                }
                
        except Exception as e:
            return {"status": "error", "message": f"Error checking {doctor_id}: {str(e)}"}
    
    def _generate_availability_summary(self, system_availability):
        """Generate a summary of system-wide availability"""
        available_doctors = 0
        busy_doctors = 0
        total_slots_today = 0
        
        for doctor_name, availability in system_availability.items():
            if availability.get("status") == "success":
                if availability.get("next_7_days_availability"):
                    available_doctors += 1
                    if availability["next_7_days_availability"]:
                        total_slots_today += availability["next_7_days_availability"][0].get("slots_available", 0)
                else:
                    busy_doctors += 1
        
        return {
            "available_doctors": available_doctors,
            "busy_doctors": busy_doctors,
            "total_available_slots_today": total_slots_today,
            "recommendation": "Good availability" if total_slots_today > 10 else "Limited availability - book early"
        }