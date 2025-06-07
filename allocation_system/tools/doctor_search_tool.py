# Tools/doctor_search_tool.py - Doctor Search Tool
from google.adk.tools import BaseTool
from datetime import datetime, timedelta
import logging

# Import shared models
from ..models import hospital_db, AppointmentStatus

logger = logging.getLogger(__name__)

class SmartDoctorSearchTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="find_doctors",
            description="""Advanced doctor search tool with intelligent natural language understanding. 
            
            This tool handles ALL doctor-related queries and understands various ways humans express their needs:
            
            SPECIALTY SEARCH:
            - "I need a cardiologist" → finds heart specialists
            - "Find me a brain doctor" → finds neurologists  
            - "Any bone doctors?" → finds orthopedic specialists
            - "Show me heart specialists" → finds cardiology doctors
            - "Do you have neurologists?" → searches neurology
            
            GENERAL DOCTOR SEARCH:
            - "Show all doctors" → lists all available doctors
            - "What doctors do you have?" → returns complete doctor list
            - "Who can I see?" → shows all available physicians
            
            SPECIFIC DOCTOR SEARCH:
            - "Find Dr. Smith" → gets specific doctor info
            - "Tell me about Dr. Jones" → shows doctor details
            - "Is Dr. Brown available?" → doctor-specific information
            
            SMART MAPPINGS:
            - heart/cardiac → cardiology
            - brain/nerve → neurology  
            - bone/joint → orthopedics
            - family/primary → general medicine
            
            Returns comprehensive doctor information including current workload and availability status."""
        )
    
    async def execute(self, specialty: str = None, doctor_name: str = None):
        try:
            doctors = hospital_db.doctors
            appointments = hospital_db.appointments
            
            if specialty:
                # Advanced specialty mapping with synonyms
                specialty_mappings = {
                    'heart': 'cardiology', 'cardiac': 'cardiology', 'cardiologist': 'cardiology',
                    'cardiovascular': 'cardiology', 'heart doctor': 'cardiology',
                    'brain': 'neurology', 'nerve': 'neurology', 'neurologist': 'neurology', 
                    'neuro': 'neurology', 'brain doctor': 'neurology', 'nervous system': 'neurology',
                    'bone': 'orthopedics', 'joint': 'orthopedics', 'orthopedic': 'orthopedics', 
                    'ortho': 'orthopedics', 'bone doctor': 'orthopedics', 'musculoskeletal': 'orthopedics',
                    'general': 'general medicine', 'family': 'general medicine', 'primary': 'general medicine',
                    'family doctor': 'general medicine', 'gp': 'general medicine'
                }
                
                # Smart specialty detection
                specialty_lower = specialty.lower()
                mapped_specialty = specialty_lower
                
                for keyword, mapped in specialty_mappings.items():
                    if keyword in specialty_lower:
                        mapped_specialty = mapped
                        break
                
                # Find matching doctors
                matching_doctors = [doc for doc in doctors.values() 
                                  if mapped_specialty in doc.specialty.lower()]
                
                if not matching_doctors:
                    available_specialties = list(set(doc.specialty for doc in doctors.values()))
                    return {
                        "status": "no_match", 
                        "message": f"No doctors found for '{specialty}'. We have specialists in:",
                        "available_specialties": available_specialties,
                        "suggestion": "Try: 'cardiologist', 'neurologist', 'orthopedic doctor', or 'general medicine doctor'"
                    }
                
                # Build detailed result
                result = {}
                for doctor in matching_doctors:
                    current_load = len([apt for apt in appointments 
                                      if apt.doctor_id == doctor.id and apt.status == AppointmentStatus.SCHEDULED])
                    
                    # Calculate availability score
                    total_capacity = len(doctor.available_hours) * len(doctor.available_days)
                    utilization = (current_load / total_capacity) * 100 if total_capacity > 0 else 0
                    
                    availability_status = "fully_booked" if utilization >= 90 else \
                                        "busy" if utilization >= 70 else \
                                        "moderate" if utilization >= 40 else "available"
                    
                    result[doctor.name] = {
                        "doctor_id": doctor.id,
                        "specialty": doctor.specialty,
                        "available_days": doctor.available_days,
                        "working_hours": doctor.available_hours,
                        "current_appointments": current_load,
                        "utilization_rate": round(utilization, 1),
                        "availability_status": availability_status,
                        "next_available": self._get_next_available_slot(doctor.id)
                    }
                
                return {
                    "status": "success", 
                    "specialty_searched": mapped_specialty,
                    "doctors_found": len(result),
                    "doctors": result
                }
            
            elif doctor_name:
                # Enhanced doctor name matching
                doctor = None
                search_name = doctor_name.lower().replace('dr. ', '').replace('dr ', '').replace('doctor ', '')
                
                for doc in doctors.values():
                    doc_name_clean = doc.name.lower().replace('dr. ', '').replace('dr ', '')
                    if search_name in doc_name_clean or doc_name_clean in search_name:
                        doctor = doc
                        break
                
                if not doctor:
                    available_doctors = [doc.name for doc in doctors.values()]
                    # Suggest similar names
                    suggestions = [name for name in available_doctors 
                                 if any(word in name.lower() for word in search_name.split())]
                    
                    return {
                        "status": "not_found", 
                        "message": f"Doctor '{doctor_name}' not found in our system",
                        "available_doctors": available_doctors,
                        "suggestions": suggestions if suggestions else ["Dr. Smith", "Dr. Jones", "Dr. Brown", "Dr. Wilson"]
                    }
                
                # Get detailed doctor information
                current_load = len([apt for apt in appointments 
                                  if apt.doctor_id == doctor.id and apt.status == AppointmentStatus.SCHEDULED])
                
                total_capacity = len(doctor.available_hours) * len(doctor.available_days)
                utilization = (current_load / total_capacity) * 100 if total_capacity > 0 else 0
                
                return {
                    "status": "success",
                    "doctor": {
                        "name": doctor.name,
                        "specialty": doctor.specialty,
                        "doctor_id": doctor.id,
                        "available_days": doctor.available_days,
                        "working_hours": doctor.available_hours,
                        "current_appointments": current_load,
                        "utilization_rate": round(utilization, 1),
                        "availability_status": "busy" if utilization > 70 else "available",
                        "next_available": self._get_next_available_slot(doctor.id)
                    }
                }
            
            else:
                # Return all doctors with comprehensive information
                all_doctors = {}
                total_appointments = len(appointments)
                
                for doc in doctors.values():
                    current_load = len([apt for apt in appointments 
                                      if apt.doctor_id == doc.id and apt.status == AppointmentStatus.SCHEDULED])
                    
                    total_capacity = len(doc.available_hours) * len(doc.available_days)
                    utilization = (current_load / total_capacity) * 100 if total_capacity > 0 else 0
                    
                    all_doctors[doc.name] = {
                        "doctor_id": doc.id,
                        "specialty": doc.specialty,
                        "available_days": doc.available_days,
                        "working_hours": doc.available_hours,
                        "current_appointments": current_load,
                        "utilization_rate": round(utilization, 1),
                        "availability_status": "busy" if utilization > 70 else "available",
                        "next_available": self._get_next_available_slot(doc.id)
                    }
                
                return {
                    "status": "success", 
                    "total_doctors": len(all_doctors),
                    "total_appointments_in_system": total_appointments,
                    "all_doctors": all_doctors
                }
                
        except Exception as e:
            logger.error(f"Doctor search error: {str(e)}")
            return {"status": "error", "message": f"Search service temporarily unavailable: {str(e)}"}
    
    def _get_next_available_slot(self, doctor_id: str):
        """Find next available appointment slot for a doctor"""
        try:
            doctors = hospital_db.doctors
            appointments = hospital_db.appointments
            
            if doctor_id not in doctors:
                return None
            
            doctor = doctors[doctor_id]
            current_date = datetime.now().date()
            
            # Check next 14 days
            for days_ahead in range(0, 14):
                check_date = (current_date + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
                
                if check_date in doctor.available_days:
                    booked_times = [apt.time for apt in appointments 
                                  if apt.doctor_id == doctor_id and apt.date == check_date 
                                  and apt.status == AppointmentStatus.SCHEDULED]
                    
                    available_times = [time for time in doctor.available_hours if time not in booked_times]
                    
                    if available_times:
                        return {"date": check_date, "time": available_times[0]}
            
            return None
        except Exception:
            return None
