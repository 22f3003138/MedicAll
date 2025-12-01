from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, Appointment, Treatment, DoctorAvailability, Role, AppointmentStatus, PatientProfile
from datetime import datetime, timedelta, date
from utils import validate_required_fields, validate_date, validate_time_range, ValidationError, sanitize_input

doctor = Blueprint('doctor', __name__, url_prefix='/doctor')

@doctor.before_request
@login_required
def require_doctor():
    if current_user.role != Role.DOCTOR:
        return "Access Denied", 403

@doctor.route('/dashboard')
def dashboard():
    today = datetime.now().date()
    # fetch upcoming appointments
    appointments = Appointment.query.filter_by(
        doctor_id=current_user.doctor_profile.id,
        status=AppointmentStatus.BOOKED
    ).order_by(Appointment.appointment_start).all()
    
    # chart data: status
    stats = db.session.query(Appointment.status, db.func.count(Appointment.id))\
        .filter(Appointment.doctor_id == current_user.doctor_profile.id)\
        .group_by(Appointment.status).all()
        
    labels = [s[0] for s in stats]
    data = [s[1] for s in stats]
    
    return render_template('dashboards/doctor.html', 
                         appointments=appointments,
                         status_labels=labels,
                         status_data=data)

@doctor.route('/appointments/<int:id>/status', methods=['POST'])
def update_status(id):
    appointment = db.session.get(Appointment, id)
    if appointment and appointment.doctor_id == current_user.doctor_profile.id:
        new_status = request.form.get('status')
        
        if not new_status:
            flash('Status is required', 'danger')
            return redirect(url_for('doctor.dashboard'))
        
        if appointment.can_transition_to(new_status):
            appointment.status = new_status
            db.session.commit()
            flash(f'Appointment marked as {new_status}', 'success')
        else:
            flash('Invalid status transition', 'warning')
    return redirect(url_for('doctor.dashboard'))

@doctor.route('/appointments/<int:id>/treatment', methods=['GET', 'POST'])
def treatment(id):
    appointment = db.session.get(Appointment, id)
    if not appointment or appointment.doctor_id != current_user.doctor_profile.id:
        return "Not Found", 404
        
    treatment = appointment.treatment
    
    if request.method == 'POST':
        diagnosis = sanitize_input(request.form.get('diagnosis'))
        prescription = sanitize_input(request.form.get('prescription'))
        notes = sanitize_input(request.form.get('notes'))
        doc_notes = sanitize_input(request.form.get('doctor_notes'))
        
        # basic checks
        try:
            validate_required_fields(request.form, ['diagnosis', 'prescription'])
            
            # ensure enough detail
            if len(diagnosis) < 10:
                raise ValidationError("Diagnosis must be at least 10 characters")
            if len(prescription) < 10:
                raise ValidationError("Prescription must be at least 10 characters")
            
        except ValidationError as e:
            flash(str(e), 'danger')
            return render_template('doctor/treatment.html', appointment=appointment, treatment=treatment)
        
        if not treatment:
            treatment = Treatment(appointment_id=appointment.id)
            db.session.add(treatment)
            
        treatment.diagnosis = diagnosis
        treatment.prescription = prescription
        treatment.notes = notes
        treatment.doctor_notes = doc_notes
        
        # complete appointment automatically
        if appointment.can_transition_to(AppointmentStatus.COMPLETED):
            appointment.status = AppointmentStatus.COMPLETED
            
        db.session.commit()
        flash('Treatment record saved successfully', 'success')
        return redirect(url_for('doctor.dashboard'))
        
    return render_template('doctor/treatment.html', appointment=appointment, treatment=treatment)

@doctor.route('/patients/<int:id>/history')
def patient_history(id):
    patient = db.session.get(PatientProfile, id)
    if not patient:
        return "Not Found", 404
    
    # Verify doctor has access to this patient (has at least one appointment)
    has_access = Appointment.query.filter_by(
        doctor_id=current_user.doctor_profile.id,
        patient_id=id
    ).first()
    
    if not has_access:
        return "Access Denied", 403
    
    appointments = Appointment.query.filter_by(patient_id=id)\
        .order_by(Appointment.appointment_start.desc()).all()
        
    return render_template('doctor/patient_history.html', patient=patient, appointments=appointments)

@doctor.route('/patients')
def my_patients():
    patients = db.session.query(PatientProfile)\
        .join(Appointment, Appointment.patient_id == PatientProfile.id)\
        .filter(Appointment.doctor_id == current_user.doctor_profile.id)\
        .distinct().all()
        
    return render_template('doctor/my_patients.html', patients=patients)

@doctor.route('/availability', methods=['GET', 'POST'])
def availability():
    if request.method == 'POST':
        date_str = request.form.get('date')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        
        # Validate required fields and formats
        try:
            validate_required_fields(request.form, ['date', 'start_time', 'end_time'])
            
            # Parse and validate date
            avail_date = validate_date(date_str, allow_future=True, allow_past=False)
            
            # Parse time fields
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
            
            # Validate time range
            validate_time_range(start_time, end_time)
            
            # Check for overlapping slots
            existing = DoctorAvailability.query.filter_by(
                doctor_id=current_user.doctor_profile.id,
                date=avail_date
            ).filter(
                db.and_(
                    DoctorAvailability.start_time < end_time,
                    DoctorAvailability.end_time > start_time
                )
            ).first()
            
            if existing:
                raise ValidationError("This time slot overlaps with an existing availability")
            
        except ValueError as e:
            flash(f'Invalid time format: {str(e)}', 'danger')
            today = datetime.now().date()
            availabilities = DoctorAvailability.query.filter_by(doctor_id=current_user.doctor_profile.id)\
                .filter(DoctorAvailability.date >= today)\
                .order_by(DoctorAvailability.date, DoctorAvailability.start_time).all()
            return render_template('doctor/availability.html', availabilities=availabilities, today=today)
        except ValidationError as e:
            flash(str(e), 'danger')
            today = datetime.now().date()
            availabilities = DoctorAvailability.query.filter_by(doctor_id=current_user.doctor_profile.id)\
                .filter(DoctorAvailability.date >= today)\
                .order_by(DoctorAvailability.date, DoctorAvailability.start_time).all()
            return render_template('doctor/availability.html', availabilities=availabilities, today=today)
        
        avail = DoctorAvailability(
            doctor_id=current_user.doctor_profile.id,
            date=avail_date,
            start_time=start_time,
            end_time=end_time
        )
        db.session.add(avail)
        db.session.commit()
        flash('Availability slot added', 'success')
            
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
        flash('Availability slot removed', 'success')
    return redirect(url_for('doctor.availability'))
