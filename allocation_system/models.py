# models.py - Shared data models and database manager
import threading
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AppointmentStatus(Enum):
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

@dataclass
class Doctor:
    id: str
    name: str
    specialty: str
    available_days: List[str]
    available_hours: List[str]

@dataclass
class Appointment:
    id: str
    patient_id: str
    doctor_id: str
    date: str
    time: str
    status: AppointmentStatus
    notes: Optional[str] = None

# Thread-safe data management
class HospitalDataManager:
    def __init__(self):
        self._lock = threading.RLock()
        self._doctors = {
            "dr_smith": Doctor("dr_smith", "Dr. Smith", "Cardiology", 
                          ["2025-06-03", "2025-06-04", "2025-06-05", "2025-06-06", "2025-06-07", "2025-06-08"], 
                          ["09:00", "10:00", "11:00", "14:00", "15:00"]),
            "dr_jones": Doctor("dr_jones", "Dr. Jones", "Orthopedics", 
                          ["2025-06-03", "2025-06-04", "2025-06-05", "2025-06-06", "2025-06-07", "2025-06-08"], 
                          ["14:00", "15:00", "16:00", "17:00"]),
            "dr_wilson": Doctor("dr_wilson", "Dr. Wilson", "General Medicine", 
                           ["2025-06-03", "2025-06-04", "2025-06-05", "2025-06-06", "2025-06-07", "2025-06-08"], 
                           ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00"]),
            "dr_brown": Doctor("dr_brown", "Dr. Brown", "Neurology", 
                          ["2025-06-03", "2025-06-04", "2025-06-05", "2025-06-06", "2025-06-07", "2025-06-08"], 
                          ["09:00", "10:00", "11:00", "13:00", "14:00"])
        }
        self._appointments = []
        self._appointment_counter = 1
    
    @property
    def doctors(self):
        with self._lock:
            return self._doctors.copy()
    
    @property
    def appointments(self):
        with self._lock:
            return self._appointments.copy()
    
    def add_appointment(self, appointment):
        with self._lock:
            appointment.id = f"APT{self._appointment_counter:04d}"
            self._appointments.append(appointment)
            self._appointment_counter += 1
            return appointment.id
    
    def update_appointment_status(self, appointment_id: str, status: AppointmentStatus):
        with self._lock:
            for apt in self._appointments:
                if apt.id == appointment_id:
                    apt.status = status
                    return True
            return False

# Singleton instance
hospital_db = HospitalDataManager()
