# __init__.py - Hospital System Package
from .agent import root_agent, hospital_system, hospital_db_instance
from .models import hospital_db, AppointmentStatus, Doctor, Appointment

__version__ = "1.0.0"
__author__ = "Hospital AI Team"

__all__ = [
    'root_agent',
    'hospital_system', 
    'hospital_db_instance',
    'hospital_db',
    'AppointmentStatus',
    'Doctor',
    'Appointment'
]
