# Tools/doctor_search_tool.py - Doctor Search Tool
from google.adk.tools import BaseTool
from datetime import datetime, timedelta
import logging

# Import shared models
from ..models import hospital_db, AppointmentStatus
class AdvancedAnalyticsTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="system_analytics",
            description="""Comprehensive hospital analytics system providing deep operational insights.
            
            Generates detailed reports on:
            - System-wide performance metrics and KPIs
            - Doctor utilization and efficiency analysis
            - Patient flow patterns and trends
            - Appointment booking success rates
            - Cancellation patterns and reasons
            - Peak hours and capacity optimization
            - Revenue and operational cost analysis
            - Patient satisfaction indicators
            - Resource allocation recommendations
            
            Analytics types available:
            - "overview" → comprehensive system dashboard
            - "utilization" → detailed doctor and resource usage
            - "trends" → temporal patterns and forecasting
            - "efficiency" → operational optimization metrics
            - "patient_insights" → patient behavior analysis
            
            Provides actionable insights for:
            - Capacity planning and resource optimization
            - Staff scheduling improvements
            - Patient experience enhancement
            - Operational cost reduction
            - Strategic decision making
            """
        )
    
    async def execute(self, report_type: str = "overview", time_period: str = "current"):
        try:
            doctors = hospital_db.doctors
            appointments = hospital_db.appointments
            
            if report_type == "overview":
                return await self._generate_overview_analytics(time_period)
            elif report_type == "utilization":
                return await self._generate_utilization_analytics(time_period)
            elif report_type == "trends":
                return await self._generate_trend_analytics(time_period)
            elif report_type == "efficiency":
                return await self._generate_efficiency_analytics(time_period)
            elif report_type == "patient_insights":
                return await self._generate_patient_insights_analytics(time_period)
            else:
                return await self._generate_overview_analytics(time_period)
                
        except Exception as e:
            logger.error(f"Analytics error: {str(e)}")
            return {"status": "error", "message": f"Analytics service error: {str(e)}"}
    
    async def _generate_overview_analytics(self, time_period):
        """Generate comprehensive system overview"""
        try:
            doctors = hospital_db.doctors
            appointments = hospital_db.appointments
            
            # Basic metrics
            total_appointments = len(appointments)
            scheduled_count = len([apt for apt in appointments if apt.status == AppointmentStatus.SCHEDULED])
            cancelled_count = len([apt for apt in appointments if apt.status == AppointmentStatus.CANCELLED])
            completed_count = len([apt for apt in appointments if apt.status == AppointmentStatus.COMPLETED])
            
            # Calculate rates
            cancellation_rate = (cancelled_count / total_appointments * 100) if total_appointments > 0 else 0
            completion_rate = (completed_count / total_appointments * 100) if total_appointments > 0 else 0
            
            # Doctor utilization analysis
            doctor_analytics = {}
            total_utilization = 0
            
            for doctor_id, doctor in doctors.items():
                doctor_appointments = [apt for apt in appointments 
                                     if apt.doctor_id == doctor_id and apt.status == AppointmentStatus.SCHEDULED]
                
                total_capacity = len(doctor.available_hours) * len(doctor.available_days)
                utilization_rate = (len(doctor_appointments) / total_capacity * 100) if total_capacity > 0 else 0
                total_utilization += utilization_rate
                
                # Status categorization
                status = "overbooked" if utilization_rate > 90 else \
                        "busy" if utilization_rate > 70 else \
                        "moderate" if utilization_rate > 40 else \
                        "underutilized"
                
                doctor_analytics[doctor.name] = {
                    "appointments": len(doctor_appointments),
                    "utilization_rate": round(utilization_rate, 1),
                    "specialty": doctor.specialty,
                    "capacity": total_capacity,
                    "status": status,
                    "revenue_potential": self._calculate_revenue_potential(doctor, len(doctor_appointments))
                }
            
            # System health assessment
            avg_utilization = total_utilization / len(doctors) if doctors else 0
            
            system_health = "excellent" if cancellation_rate < 10 and 40 <= avg_utilization <= 80 else \
                           "good" if cancellation_rate < 15 and 30 <= avg_utilization <= 85 else \
                           "warning" if cancellation_rate < 25 and 20 <= avg_utilization <= 90 else \
                           "critical"
            
            # Capacity analysis
            total_system_capacity = sum(len(doc.available_hours) * len(doc.available_days) for doc in doctors.values())
            current_bookings = scheduled_count
            available_capacity = total_system_capacity - current_bookings
            capacity_utilization = (current_bookings / total_system_capacity * 100) if total_system_capacity > 0 else 0
            
            # Generate recommendations
            recommendations = self._generate_system_recommendations(
                avg_utilization, cancellation_rate, doctor_analytics, capacity_utilization
            )
            
            return {
                "status": "success",
                "report_type": "system_overview",
                "timestamp": datetime.now().isoformat(),
                "time_period": time_period,
                "system_metrics": {
                    "total_doctors": len(doctors),
                    "total_appointments": total_appointments,
                    "scheduled_appointments": scheduled_count,
                    "cancelled_appointments": cancelled_count,
                    "completed_appointments": completed_count,
                    "cancellation_rate": round(cancellation_rate, 1),
                    "completion_rate": round(completion_rate, 1),
                    "average_utilization": round(avg_utilization, 1),
                    "system_health": system_health
                },
                "capacity_analysis": {
                    "total_system_capacity": total_system_capacity,
                    "current_bookings": current_bookings,
                    "available_capacity": available_capacity,
                    "capacity_utilization": round(capacity_utilization, 1),
                    "peak_capacity_days": self._identify_peak_days(),
                    "bottleneck_specialties": self._identify_bottlenecks(doctor_analytics)
                },
                "doctor_performance": doctor_analytics,
                "operational_insights": {
                    "busiest_doctors": self._get_top_doctors_by_utilization(doctor_analytics, 3),
                    "underutilized_resources": self._get_underutilized_doctors(doctor_analytics),
                    "specialty_distribution": self._analyze_specialty_distribution(),
                    "patient_flow_patterns": self._analyze_patient_flow()
                },
                "recommendations": recommendations,
                "financial_overview": {
                    "estimated_revenue": self._calculate_system_revenue(),
                    "cost_optimization_opportunities": self._identify_cost_optimizations(doctor_analytics),
                    "growth_potential": self._calculate_growth_potential(available_capacity)
                }
            }
            
        except Exception as e:
            logger.error(f"Overview analytics error: {str(e)}")
            return {"status": "error", "message": f"Failed to generate overview: {str(e)}"}
    
    def _calculate_revenue_potential(self, doctor, current_appointments):
        """Calculate revenue potential for a doctor"""
        # Simplified revenue calculation - in real system would use actual pricing
        base_rate_per_appointment = {
            "Cardiology": 200,
            "Neurology": 180,
            "Orthopedics": 150,
            "General Medicine": 100
        }
        
        rate = base_rate_per_appointment.get(doctor.specialty, 120)
        max_capacity = len(doctor.available_hours) * len(doctor.available_days)
        
        return {
            "current_revenue": current_appointments * rate,
            "max_potential": max_capacity * rate,
            "revenue_opportunity": (max_capacity - current_appointments) * rate
        }
    
    def _generate_system_recommendations(self, avg_utilization, cancellation_rate, doctor_analytics, capacity_utilization):
        """Generate actionable system recommendations"""
        recommendations = []
        
        # Utilization recommendations
        if avg_utilization > 85:
            recommendations.append({
                "category": "capacity_expansion",
                "priority": "high",
                "message": "System approaching maximum capacity",
                "action": "Consider hiring additional staff or extending hours",
                "impact": "Prevent patient access issues and staff burnout"
            })
        elif avg_utilization < 40:
            recommendations.append({
                "category": "efficiency_optimization",
                "priority": "medium",
                "message": "System significantly underutilized",
                "action": "Implement marketing campaigns or optimize schedules",
                "impact": "Improve resource efficiency and revenue"
            })
        
        # Cancellation recommendations
        if cancellation_rate > 15:
            recommendations.append({
                "category": "patient_retention",
                "priority": "high",
                "message": f"High cancellation rate ({cancellation_rate}%)",
                "action": "Implement automated reminder systems and flexible rescheduling",
                "impact": "Reduce revenue loss and improve patient satisfaction"
            })
        
        # Doctor-specific recommendations
        overbooked_doctors = [name for name, data in doctor_analytics.items() if data["utilization_rate"] > 90]
        underutilized_doctors = [name for name, data in doctor_analytics.items() if data["utilization_rate"] < 30]
        
        if overbooked_doctors:
            recommendations.append({
                "category": "workload_balancing",
                "priority": "medium",
                "message": f"Doctors overbooked: {', '.join(overbooked_doctors)}",
                "action": "Redistribute appointments or add capacity for these specialties",
                "impact": "Prevent staff burnout and maintain care quality"
            })
        
        if underutilized_doctors:
            recommendations.append({
                "category": "resource_optimization",
                "priority": "low",
                "message": f"Underutilized doctors: {', '.join(underutilized_doctors)}",
                "action": "Cross-training, marketing focus, or schedule optimization",
                "impact": "Maximize resource utilization and profitability"
            })
        
        return recommendations
    
    def _identify_peak_days(self):
        """Identify peak utilization days"""
        appointments = hospital_db.appointments
        day_counts = {}
        
        for apt in appointments:
            if apt.status == AppointmentStatus.SCHEDULED:
                day_counts[apt.date] = day_counts.get(apt.date, 0) + 1
        
        if not day_counts:
            return []
        
        # Return top 3 busiest days
        return sorted(day_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    
    def _identify_bottlenecks(self, doctor_analytics):
        """Identify specialty bottlenecks"""
        specialty_utilization = {}
        
        for doctor_name, data in doctor_analytics.items():
            specialty = data["specialty"]
            if specialty not in specialty_utilization:
                specialty_utilization[specialty] = []
            specialty_utilization[specialty].append(data["utilization_rate"])
        
        # Calculate average utilization by specialty
        bottlenecks = []
        for specialty, rates in specialty_utilization.items():
            avg_rate = sum(rates) / len(rates)
            if avg_rate > 80:
                bottlenecks.append({
                    "specialty": specialty,
                    "average_utilization": round(avg_rate, 1),
                    "doctors_count": len(rates)
                })
        
        return sorted(bottlenecks, key=lambda x: x["average_utilization"], reverse=True)
    
    def _get_top_doctors_by_utilization(self, doctor_analytics, count):
        """Get top doctors by utilization rate"""
        return sorted(doctor_analytics.items(), 
                     key=lambda x: x[1]["utilization_rate"], 
                     reverse=True)[:count]
    
    def _get_underutilized_doctors(self, doctor_analytics):
        """Get underutilized doctors"""
        return [name for name, data in doctor_analytics.items() 
                if data["utilization_rate"] < 40]
    
    def _analyze_specialty_distribution(self):
        """Analyze distribution of specialties"""
        doctors = hospital_db.doctors
        appointments = hospital_db.appointments
        
        specialty_stats = {}
        
        for doctor in doctors.values():
            specialty = doctor.specialty
            if specialty not in specialty_stats:
                specialty_stats[specialty] = {
                    "doctors_count": 0,
                    "total_appointments": 0,
                    "total_capacity": 0
                }
            
            specialty_stats[specialty]["doctors_count"] += 1
            specialty_stats[specialty]["total_capacity"] += len(doctor.available_hours) * len(doctor.available_days)
            
            # Count appointments for this doctor
            doctor_appointments = len([apt for apt in appointments 
                                     if apt.doctor_id == doctor.id and apt.status == AppointmentStatus.SCHEDULED])
            specialty_stats[specialty]["total_appointments"] += doctor_appointments
        
        # Calculate utilization rates
        for specialty_data in specialty_stats.values():
            if specialty_data["total_capacity"] > 0:
                specialty_data["utilization_rate"] = round(
                    (specialty_data["total_appointments"] / specialty_data["total_capacity"]) * 100, 1
                )
            else:
                specialty_data["utilization_rate"] = 0
        
        return specialty_stats
    
    def _analyze_patient_flow(self):
        """Analyze patient flow patterns"""
        appointments = hospital_db.appointments
        
        # Time-based analysis
        time_distribution = {}
        date_distribution = {}
        
        for apt in appointments:
            if apt.status == AppointmentStatus.SCHEDULED:
                # Time analysis
                hour = apt.time.split(':')[0]
                time_distribution[hour] = time_distribution.get(hour, 0) + 1
                
                # Date analysis
                date_distribution[apt.date] = date_distribution.get(apt.date, 0) + 1
        
        # Identify peak hours
        peak_hours = sorted(time_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            "time_distribution": time_distribution,
            "date_distribution": date_distribution,
            "peak_hours": peak_hours,
            "total_scheduled": len([apt for apt in appointments if apt.status == AppointmentStatus.SCHEDULED])
        }
    
    def _calculate_system_revenue(self):
        """Calculate estimated system revenue"""
        appointments = hospital_db.appointments
        doctors = hospital_db.doctors
        
        revenue_rates = {
            "Cardiology": 200,
            "Neurology": 180,
            "Orthopedics": 150,
            "General Medicine": 100
        }
        
        total_revenue = 0
        revenue_by_specialty = {}
        
        for apt in appointments:
            if apt.status in [AppointmentStatus.SCHEDULED, AppointmentStatus.COMPLETED]:
                doctor = doctors[apt.doctor_id]
                specialty = doctor.specialty
                rate = revenue_rates.get(specialty, 120)
                
                total_revenue += rate
                revenue_by_specialty[specialty] = revenue_by_specialty.get(specialty, 0) + rate
        
        return {
            "total_estimated_revenue": total_revenue,
            "revenue_by_specialty": revenue_by_specialty,
            "average_revenue_per_appointment": round(total_revenue / len(appointments), 2) if appointments else 0
        }
    
    def _identify_cost_optimizations(self, doctor_analytics):
        """Identify cost optimization opportunities"""
        optimizations = []
        
        # Identify underutilized high-cost specialties
        for doctor_name, data in doctor_analytics.items():
            if data["utilization_rate"] < 30 and data["specialty"] in ["Cardiology", "Neurology"]:
                optimizations.append({
                    "type": "schedule_optimization",
                    "doctor": doctor_name,
                    "current_utilization": data["utilization_rate"],
                    "opportunity": "Reduce available hours or cross-train in other specialties"
                })
        
        return optimizations
    
    def _calculate_growth_potential(self, available_capacity):
        """Calculate system growth potential"""
        if available_capacity <= 0:
            return {
                "growth_capacity": "At maximum capacity",
                "recommendation": "Expand resources before accepting more patients"
            }
        
        growth_percentage = (available_capacity / (available_capacity + len(hospital_db.appointments))) * 100
        
        return {
            "available_slots": available_capacity,
            "growth_capacity_percentage": round(growth_percentage, 1),
            "recommendation": "Good capacity for growth" if growth_percentage > 20 else "Limited growth capacity"
        }