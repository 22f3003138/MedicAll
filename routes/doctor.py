from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, Appointment, Treatment, DoctorAvailability, Role, AppointmentStatus, PatientProfile
from datetime import datetime, timedelta, date

doctor = Blueprint('doctor', __name__, url_prefix='/doctor')

@doctor.before_request
@login_required
def require_doctor():
    if current_user.role != Role.DOCTOR:
        return "Access Denied", 403

@doctor.route('/dashboard')
def dashboard():
    today = datetime.now().date()
    # Get upcoming appointments
    appointments = Appointment.query.join(User, Appointment.doctor_id == User.doctor_profile.property.mapper.class_.id)\
        .filter(Appointment.doctor_id == current_user.doctor_profile.id)\
        .filter(Appointment.appointment_start >= datetime.now())\
        .order_by(Appointment.appointment_start.asc()).all()
        
    return render_template('dashboards/doctor.html', appointments=appointments)

@doctor.route('/appointments/<int:id>/status', methods=['POST'])
def update_status(id):
    appointment = db.session.get(Appointment, id)
    if appointment and appointment.doctor_id == current_user.doctor_profile.id:
        new_status = request.form.get('status')
        if appointment.can_transition_to(new_status):
            appointment.status = new_status
            db.session.commit()
            flash(f'Appointment marked as {new_status}')
        else:
            flash('Invalid status transition')
    return redirect(url_for('doctor.dashboard'))

@doctor.route('/appointments/<int:id>/treatment', methods=['GET', 'POST'])
def treatment(id):
    appointment = db.session.get(Appointment, id)
    if not appointment or appointment.doctor_id != current_user.doctor_profile.id:
        return "Not Found", 404
        
    treatment = appointment.treatment
    
    if request.method == 'POST':
        if not treatment:
            treatment = Treatment(appointment_id=appointment.id)
            db.session.add(treatment)
            
        treatment.diagnosis = request.form.get('diagnosis')
        treatment.prescription = request.form.get('prescription')
        treatment.notes = request.form.get('notes')
        treatment.doctor_notes = request.form.get('doctor_notes')
        
        # Auto-complete appointment if adding treatment
        if appointment.can_transition_to(AppointmentStatus.COMPLETED):
            appointment.status = AppointmentStatus.COMPLETED
            
        db.session.commit()
        flash('Treatment record saved successfully')
        return redirect(url_for('doctor.dashboard'))
        
    return render_template('doctor/treatment.html', appointment=appointment, treatment=treatment)

@doctor.route('/patients/<int:id>/history')
def patient_history(id):
    patient = db.session.get(PatientProfile, id)
    if not patient:
        return "Not Found", 404
    
    appointments = Appointment.query.filter_by(patient_id=id)\
        .order_by(Appointment.appointment_start.desc()).all()
        
    return render_template('doctor/patient_history.html', patient=patient, appointments=appointments)

@doctor.route('/availability', methods=['GET', 'POST'])
def availability():
    if request.method == 'POST':
        date_str = request.form.get('date')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        
        avail_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()
        
        # Basic validation
        if avail_date < datetime.now().date():
            flash('Cannot set availability in the past')
        else:
            avail = DoctorAvailability(
                doctor_id=current_user.doctor_profile.id,
                date=avail_date,
                start_time=start_time,
                end_time=end_time
            )
            db.session.add(avail)
            db.session.commit()
            flash('Availability slot added')
            
        return redirect(url_for('doctor.availability'))
        
    # Show next 7 days
    today = datetime.now().date()
    availabilities = DoctorAvailability.query.filter_by(doctor_id=current_user.doctor_profile.id)\
        .filter(DoctorAvailability.date >= today)\
        .order_by(DoctorAvailability.date, DoctorAvailability.start_time).all()
        
    return render_template('doctor/availability.html', availabilities=availabilities, today=today)

@doctor.route('/availability/<int:id>/delete', methods=['POST'])
def delete_availability(id):
    avail = db.session.get(DoctorAvailability, id)
    if avail and avail.doctor_id == current_user.doctor_profile.id:
        db.session.delete(avail)
        db.session.commit()
        flash('Availability slot removed')
    return redirect(url_for('doctor.availability'))
