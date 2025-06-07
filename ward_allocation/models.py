from enum import Enum
from dataclasses import dataclass, field

# ------------ Bed class added ------------
@dataclass
class Bed:
    bed_id: str
    patient_id: str = None

    @property
    def is_occupied(self):
        return self.patient_id is not None

# ------------ Core hospital data models ------------

@dataclass
class Patient:
    id: str
    name: str
    condition: str
    assigned_ward: str = None

@dataclass
class Ward:
    name: str
    capacity: int
    beds: dict = field(default_factory=dict)  # bed_id -> Bed

    def available_beds(self):
        return [bed_id for bed_id, bed in self.beds.items() if not bed.is_occupied]

    def occupancy(self):
        return len([bed for bed in self.beds.values() if bed.is_occupied])

class AppointmentStatus(Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

@dataclass
class Doctor:
    id: str
    name: str
    specialty: str
    available_days: list
    available_hours: list

@dataclass
class Appointment:
    doctor_id: str
    date: str
    time: str
    patient_id: str
    status: AppointmentStatus

# ------------ In-memory mock database ------------

class HospitalDB:
    def __init__(self):
        self.patients = {
            "P001": Patient("P001", "Alice", "cardiac"),
            "P002": Patient("P002", "Bob", "orthopedic"),
            "P003": Patient("P003", "Charlie", "general"),
        }

        self.wards = {
            "WardA": Ward("WardA", capacity=2),
            "WardB": Ward("WardB", capacity=3),
        }

        # Initialize beds
        for ward in self.wards.values():
            for i in range(1, ward.capacity + 1):
                bed_id = f"{ward.name}_bed{i}"
                ward.beds[bed_id] = Bed(bed_id)

        self.doctors = {
            "D001": Doctor("D001", "Dr. Smith", "cardiology", ["2025-06-07", "2025-06-08"], ["10:00", "11:00", "14:00"]),
            "D002": Doctor("D002", "Dr. Brown", "orthopedics", ["2025-06-07", "2025-06-09"], ["09:00", "12:00"]),
        }

        self.appointments = [
            Appointment("D001", "2025-06-07", "10:00", "P001", AppointmentStatus.SCHEDULED),
            Appointment("D002", "2025-06-07", "09:00", "P002", AppointmentStatus.SCHEDULED),
        ]

# Global instance
hospital_db = HospitalDB()
