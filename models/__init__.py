from models.base import db, utc_now, Role, AppointmentStatus
from models.user import User
from models.department import Department
from models.doctor_profile import DoctorProfile
from models.patient_profile import PatientProfile
from models.doctor_availability import DoctorAvailability
from models.appointment import Appointment
from models.treatment import Treatment


def init_db():
    db.create_all()


__all__ = [
    'db',
    'utc_now',
    'Role',
    'AppointmentStatus',
    'User',
    'Department',
    'DoctorProfile',
    'PatientProfile',
    'DoctorAvailability',
    'Appointment',
    'Treatment',
    'init_db'
]
