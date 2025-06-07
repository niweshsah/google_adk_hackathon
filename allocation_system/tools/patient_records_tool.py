# Tools/doctor_search_tool.py - Doctor Search Tool
from google.adk.tools import BaseTool
from datetime import datetime, timedelta
import logging

# Import shared models
from ..models import hospital_db, AppointmentStatus

class ComprehensivePatientTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="patient_records",
            description="""Advanced patient record management with comprehensive analytics and insights.
            
            Provides detailed patient information including:
            - Complete appointment history (scheduled, cancelled, completed)
            - Patient behavior analytics and patterns
            - Medical specialties visited and frequency
            - Cancellation rates and reliability scores
            - Preferred doctors and time slots
            - Health trend analysis
            - Upcoming appointment reminders
            
            Handles various record requests:
            - "Show John123's history" → complete patient record
            - "Patient records for Mary" → all appointments and analytics
            - "How often does John cancel?" → behavior analysis
            - "What specialists has Mary seen?" → specialty breakdown
            - "John's upcoming appointments" → future bookings only
            
            Provides actionable insights for:
            - Patient care coordination
            - Appointment scheduling optimization
            - Risk assessment for no-shows
            - Personalized healthcare recommendations
            """
        )
    
    async def execute(self, patient_id: str, include_analytics: bool = True, 
                     date_range: str = "all", appointment_status: str = "all"):
        try:
            if not patient_id:
                return {
                    "status": "missing_patient",
                    "message": "Patient ID is required",
                    "suggestion": "Please provide a patient ID (e.g., 'John123', 'Mary456')"
                }
            
            appointments = hospital_db.appointments
            doctors = hospital_db.doctors
            
            # Find all appointments for patient
            patient_appointments = [apt for apt in appointments if apt.patient_id.lower() == patient_id.lower()]
            
            if not patient_appointments:
                return {
                    "status": "no_records",
                    "patient_id": patient_id,
                    "message": f"No appointment records found for patient {patient_id}",
                    "suggestion": "Check patient ID spelling or create a new patient record"
                }
            
            # Filter by date range if specified
            if date_range != "all":
                patient_appointments = self._filter_by_date_range(patient_appointments, date_range)
            
            # Filter by status if specified
            if appointment_status != "all":
                patient_appointments = [apt for apt in patient_appointments 
                                      if apt.status.value == appointment_status]
            
            # Organize appointments by status
            scheduled = []
            cancelled = []
            completed = []
            
            for apt in patient_appointments:
                doctor = doctors[apt.doctor_id]
                apt_info = {
                    "appointment_id": apt.id,
                    "doctor_name": doctor.name,
                    "specialty": doctor.specialty,
                    "date": apt.date,
                    "time": apt.time,
                    "notes": apt.notes,
                    "status": apt.status.value,
                    "days_from_now": self._calculate_days_from_now(apt.date)
                }
                
                if apt.status == AppointmentStatus.SCHEDULED:
                    scheduled.append(apt_info)
                elif apt.status == AppointmentStatus.CANCELLED:
                    cancelled.append(apt_info)
                elif apt.status == AppointmentStatus.COMPLETED:
                    completed.append(apt_info)
            
            # Sort appointments chronologically
            all_appointments = scheduled + cancelled + completed
            all_appointments.sort(key=lambda x: (x['date'], x['time']))
            
            # Basic record structure
            patient_record = {
                "status": "success",
                "patient_id": patient_id,
                "record_summary": {
                    "total_appointments": len(patient_appointments),
                    "scheduled": len(scheduled),
                    "cancelled": len(cancelled),
                    "completed": len(completed),
                    "date_range_filtered": date_range,
                    "status_filtered": appointment_status
                },
                "appointments": {
                    "scheduled": sorted(scheduled, key=lambda x: (x['date'], x['time'])),
                    "cancelled": sorted(cancelled, key=lambda x: (x['date'], x['time'])),
                    "completed": sorted(completed, key=lambda x: (x['date'], x['time'])),
                    "chronological_all": all_appointments
                }
            }
            
            # Add comprehensive analytics if requested
            if include_analytics and patient_appointments:
                analytics = await self._generate_patient_analytics(patient_appointments, patient_id)
                patient_record["analytics"] = analytics
                patient_record["insights"] = await self._generate_patient_insights(analytics, patient_appointments)
            
            return patient_record
            
        except Exception as e:
            logger.error(f"Patient records error: {str(e)}")
            return {"status": "error", "message": f"Failed to retrieve patient records: {str(e)}"}
    
    def _filter_by_date_range(self, appointments, date_range):
        """Filter appointments by date range"""
        try:
            current_date = datetime.now().date()
            
            if date_range == "last_month":
                start_date = current_date - timedelta(days=30)
                return [apt for apt in appointments 
                       if datetime.strptime(apt.date, "%Y-%m-%d").date() >= start_date]
            
            elif date_range == "last_year":
                start_date = current_date - timedelta(days=365)
                return [apt for apt in appointments 
                       if datetime.strptime(apt.date, "%Y-%m-%d").date() >= start_date]
            
            elif date_range == "upcoming":
                return [apt for apt in appointments 
                       if datetime.strptime(apt.date, "%Y-%m-%d").date() >= current_date]
            
            else:
                return appointments
                
        except Exception:
            return appointments
    
    def _calculate_days_from_now(self, date_str):
        """Calculate days from current date"""
        try:
            appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            current_date = datetime.now().date()
            delta = (appointment_date - current_date).days
            
            if delta == 0:
                return "today"
            elif delta == 1:
                return "tomorrow"
            elif delta == -1:
                return "yesterday"
            elif delta > 0:
                return f"in {delta} days"
            else:
                return f"{abs(delta)} days ago"
        except:
            return "unknown"
    
    async def _generate_patient_analytics(self, appointments, patient_id):
        """Generate comprehensive patient analytics"""
        try:
            doctors = hospital_db.doctors
            
            # Specialty analysis
            specialty_visits = {}
            doctor_visits = {}
            monthly_pattern = {}
            time_preferences = {}
            
            for apt in appointments:
                doctor = doctors[apt.doctor_id]
                specialty = doctor.specialty
                doctor_name = doctor.name
                
                # Specialty tracking
                specialty_visits[specialty] = specialty_visits.get(specialty, 0) + 1
                
                # Doctor preference tracking
                doctor_visits[doctor_name] = doctor_visits.get(doctor_name, 0) + 1
                
                # Monthly pattern analysis
                try:
                    month_year = apt.date[:7]  # YYYY-MM
                    monthly_pattern[month_year] = monthly_pattern.get(month_year, 0) + 1
                except:
                    pass
                
                # Time preference analysis
                try:
                    hour = int(apt.time.split(':')[0])
                    time_period = "morning" if hour < 12 else "afternoon" if hour < 17 else "evening"
                    time_preferences[time_period] = time_preferences.get(time_period, 0) + 1
                except:
                    pass
            
            # Calculate rates
            total_appointments = len(appointments)
            cancelled_appointments = len([apt for apt in appointments if apt.status == AppointmentStatus.CANCELLED])
            completed_appointments = len([apt for apt in appointments if apt.status == AppointmentStatus.COMPLETED])
            
            cancellation_rate = (cancelled_appointments / total_appointments * 100) if total_appointments > 0 else 0
            completion_rate = (completed_appointments / total_appointments * 100) if total_appointments > 0 else 0
            
            # Most visited specialty and doctor
            most_visited_specialty = max(specialty_visits.items(), key=lambda x: x[1]) if specialty_visits else None
            most_visited_doctor = max(doctor_visits.items(), key=lambda x: x[1]) if doctor_visits else None
            preferred_time = max(time_preferences.items(), key=lambda x: x[1]) if time_preferences else None
            
            return {
                "specialty_breakdown": specialty_visits,
                "doctor_preferences": doctor_visits,
                "most_visited_specialty": most_visited_specialty[0] if most_visited_specialty else None,
                "most_visited_doctor": most_visited_doctor[0] if most_visited_doctor else None,
                "preferred_time_period": preferred_time[0] if preferred_time else None,
                "behavioral_metrics": {
                    "cancellation_rate": round(cancellation_rate, 1),
                    "completion_rate": round(completion_rate, 1),
                    "reliability_score": round(100 - cancellation_rate, 1),
                    "average_appointments_per_month": round(len(appointments) / max(1, len(monthly_pattern)), 1)
                },
                "visit_patterns": {
                    "monthly_frequency": monthly_pattern,
                    "time_preferences": time_preferences,
                    "total_unique_doctors": len(doctor_visits),
                    "total_specialties_visited": len(specialty_visits)
                }
            }
            
        except Exception as e:
            logger.error(f"Analytics generation error: {str(e)}")
            return {"error": "Analytics unavailable"}
    
    async def _generate_patient_insights(self, analytics, appointments):
        """Generate actionable patient insights"""
        try:
            insights = []
            
            # Behavioral insights
            if analytics.get("behavioral_metrics"):
                metrics = analytics["behavioral_metrics"]
                cancellation_rate = metrics.get("cancellation_rate", 0)
                
                if cancellation_rate > 25:
                    insights.append({
                        "type": "high_risk",
                        "message": f"High cancellation rate ({cancellation_rate}%) - consider flexible scheduling or reminder systems",
                        "recommendation": "Implement 24-hour and 2-hour appointment reminders"
                    })
                elif cancellation_rate < 10:
                    insights.append({
                        "type": "reliable_patient",
                        "message": f"Excellent reliability ({100-cancellation_rate}% completion rate)",
                        "recommendation": "Priority scheduling candidate"
                    })
                
                if metrics.get("average_appointments_per_month", 0) > 3:
                    insights.append({
                        "type": "frequent_patient",
                        "message": "High appointment frequency detected",
                        "recommendation": "Consider care coordination between specialists"
                    })
            
            # Specialty insights
            if analytics.get("specialty_breakdown"):
                specialties = analytics["specialty_breakdown"]
                if len(specialties) > 3:
                    insights.append({
                        "type": "multi_specialty",
                        "message": f"Patient visits {len(specialties)} different specialties",
                        "recommendation": "Coordinate care plan across departments"
                    })
            
            # Time preference insights
            if analytics.get("preferred_time_period"):
                preferred_time = analytics["preferred_time_period"]
                insights.append({
                    "type": "scheduling_optimization",
                    "message": f"Patient prefers {preferred_time} appointments",
                    "recommendation": f"Offer {preferred_time} slots when available"
                })
            
            # Recent activity insights
            recent_appointments = [apt for apt in appointments 
                                 if datetime.strptime(apt.date, "%Y-%m-%d").date() >= 
                                 datetime.now().date() - timedelta(days=30)]
            
            if len(recent_appointments) > 2:
                insights.append({
                    "type": "recent_activity",
                    "message": f"{len(recent_appointments)} appointments in the last 30 days",
                    "recommendation": "Monitor for ongoing health concerns"
                })
            
            return insights
            
        except Exception as e:
            logger.error(f"Insights generation error: {str(e)}")
            return []