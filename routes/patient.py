from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, Appointment, DoctorAvailability, Role, AppointmentStatus, Department, DoctorProfile
from datetime import datetime

patient = Blueprint('patient', __name__, url_prefix='/patient')

@patient.before_request
@login_required
def require_patient():
    if current_user.role != Role.PATIENT:
        return "Access Denied", 403

@patient.route('/dashboard')
def dashboard():
    appointments = Appointment.query.filter_by(patient_id=current_user.patient_profile.id)\
        .order_by(Appointment.appointment_start.desc()).all()
    return render_template('dashboards/patient.html', appointments=appointments)

@patient.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        current_user.name = request.form.get('name')
        current_user.patient_profile.phone = request.form.get('phone')
        current_user.patient_profile.address = request.form.get('address')
        current_user.patient_profile.gender = request.form.get('gender')
        current_user.patient_profile.dob = datetime.strptime(request.form.get('dob'), '%Y-%m-%d').date() if request.form.get('dob') else None
        
        db.session.commit()
        flash('Profile updated successfully')
        return redirect(url_for('patient.dashboard'))
        
    return render_template('patient/profile.html')

@patient.route('/doctors')
def doctors():
    search = request.args.get('search', '')
    dept_id = request.args.get('department_id')
    
    query = User.query.join(DoctorProfile).filter(User.role == Role.DOCTOR)
    
    if search:
        query = query.filter(User.name.ilike(f'%{search}%'))
    if dept_id:
        query = query.filter(DoctorProfile.department_id == dept_id)
        
    doctors = query.all()
    departments = Department.query.all()
    
    return render_template('patient/doctors.html', doctors=doctors, departments=departments, search=search, selected_dept=dept_id)

@patient.route('/book/<int:doctor_id>')
def book_doctor(doctor_id):
    doctor = db.session.get(User, doctor_id)
    if not doctor or doctor.role != Role.DOCTOR:
        return "Not Found", 404
        
    today = datetime.now().date()
    availabilities = DoctorAvailability.query.filter_by(doctor_id=doctor.doctor_profile.id)\
        .filter(DoctorAvailability.date >= today)\
        .order_by(DoctorAvailability.date, DoctorAvailability.start_time).all()
        
    return render_template('patient/book.html', doctor=doctor, availabilities=availabilities)

@patient.route('/book/slot/<int:slot_id>', methods=['POST'])
def book_slot(slot_id):
    slot = db.session.get(DoctorAvailability, slot_id)
    if not slot:
        return "Slot not found", 404
        
    # Check if slot is already booked (basic check)
    existing = Appointment.query.filter_by(
        doctor_id=slot.doctor_id,
        appointment_start=datetime.combine(slot.date, slot.start_time)
    ).first()
    
    if existing and existing.status != AppointmentStatus.CANCELLED:
        flash('This slot is already booked')
        return redirect(url_for('patient.book_doctor', doctor_id=slot.doctor.user_id))
        
    appointment = Appointment(
        patient_id=current_user.patient_profile.id,
        doctor_id=slot.doctor_id,
        appointment_start=datetime.combine(slot.date, slot.start_time),
        appointment_end=datetime.combine(slot.date, slot.end_time),
        reason=request.form.get('reason'),
        status=AppointmentStatus.BOOKED
    )
    
    try:
        db.session.add(appointment)
        db.session.commit()
        flash('Appointment booked successfully')
    except Exception as e:
        db.session.rollback()
        flash('This slot was just booked by someone else. Please choose another.')
        return redirect(url_for('patient.book_doctor', doctor_id=slot.doctor.user_id))
    
    return redirect(url_for('patient.dashboard'))

@patient.route('/appointments/<int:id>/cancel', methods=['POST'])
def cancel_appointment(id):
    appointment = db.session.get(Appointment, id)
    if appointment and appointment.patient_id == current_user.patient_profile.id:
        if appointment.can_transition_to(AppointmentStatus.CANCELLED):
            appointment.status = AppointmentStatus.CANCELLED
            appointment.canceled_by = 'PATIENT'
            db.session.commit()
            flash('Appointment cancelled')
        else:
            flash('Cannot cancel this appointment')
    return redirect(url_for('patient.dashboard'))

@patient.route('/history')
def history():
    appointments = Appointment.query.filter_by(patient_id=current_user.patient_profile.id)\
        .filter(Appointment.status == AppointmentStatus.COMPLETED)\
        .order_by(Appointment.appointment_start.desc()).all()
    return render_template('patient/history.html', appointments=appointments)
