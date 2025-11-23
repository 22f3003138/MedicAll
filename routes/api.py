from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import db, User, Appointment, Role, AppointmentStatus, DoctorAvailability
from datetime import datetime

api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/doctors', methods=['GET'])
def get_doctors():
    doctors = User.query.filter_by(role=Role.DOCTOR).all()
    return jsonify([doc.to_dict() for doc in doctors])

@api.route('/doctors/<int:id>', methods=['GET'])
def get_doctor(id):
    doctor = db.session.get(User, id)
    if not doctor or doctor.role != Role.DOCTOR:
        return jsonify({'error': 'Doctor not found'}), 404
    return jsonify(doctor.to_dict())

@api.route('/patients/<int:id>', methods=['GET'])
@login_required
def get_patient(id):
    # Access control: Only Admin, Doctor, or the Patient themselves
    if current_user.role == Role.PATIENT and current_user.id != id:
        return jsonify({'error': 'Access denied'}), 403
        
    patient = db.session.get(User, id)
    if not patient or patient.role != Role.PATIENT:
        return jsonify({'error': 'Patient not found'}), 404
    return jsonify(patient.to_dict())

@api.route('/appointments', methods=['GET'])
@login_required
def get_appointments():
    if current_user.role == Role.PATIENT:
        appointments = Appointment.query.filter_by(patient_id=current_user.patient_profile.id).all()
    elif current_user.role == Role.DOCTOR:
        appointments = Appointment.query.filter_by(doctor_id=current_user.doctor_profile.id).all()
    else:
        appointments = Appointment.query.all()
        
    return jsonify([appt.to_dict() for appt in appointments])

@api.route('/appointments', methods=['POST'])
@login_required
def create_appointment():
    if current_user.role != Role.PATIENT:
        return jsonify({'error': 'Only patients can book appointments'}), 403
        
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    slot_id = data.get('slot_id')
    reason = data.get('reason')
    
    if not slot_id or not reason:
        return jsonify({'error': 'Missing slot_id or reason'}), 400
        
    slot = db.session.get(DoctorAvailability, slot_id)
    if not slot:
        return jsonify({'error': 'Slot not found'}), 404
        
    # Check for existing booking
    existing = Appointment.query.filter_by(
        doctor_id=slot.doctor_id,
        appointment_start=datetime.combine(slot.date, slot.start_time)
    ).first()
    
    if existing and existing.status != AppointmentStatus.CANCELLED:
        return jsonify({'error': 'Slot already booked'}), 409
        
    try:
        appointment = Appointment(
            patient_id=current_user.patient_profile.id,
            doctor_id=slot.doctor_id,
            appointment_start=datetime.combine(slot.date, slot.start_time),
            appointment_end=datetime.combine(slot.date, slot.end_time),
            reason=reason,
            status=AppointmentStatus.BOOKED
        )
        db.session.add(appointment)
        db.session.commit()
        return jsonify(appointment.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
