from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, Appointment, DoctorAvailability, Role, AppointmentStatus, Department, DoctorProfile
from datetime import datetime
from sqlalchemy import func
from utils import validate_phone, validate_date, validate_gender, validate_required_fields, ValidationError, sanitize_input

patient = Blueprint('patient', __name__, url_prefix='/patient')

@patient.before_request
@login_required
def require_patient():
    if current_user.role != Role.PATIENT:
        return "Access Denied", 403

@patient.route('/dashboard')
def dashboard():
    appts = Appointment.query.filter_by(patient_id=current_user.patient_profile.id)\
        .order_by(Appointment.appointment_start.desc()).all()
    
    # get depts
    departments = Department.query.all()
    
    hist_stats = db.session.query(func.strftime('%Y-%m', Appointment.appointment_start), func.count(Appointment.id))\
        .filter(Appointment.patient_id == current_user.patient_profile.id)\
        .group_by(func.strftime('%Y-%m', Appointment.appointment_start))\
        .order_by(func.strftime('%Y-%m', Appointment.appointment_start)).all()
        
    h_labels = [s[0] for s in hist_stats]
    h_data = [s[1] for s in hist_stats]
    
    status_stats = db.session.query(Appointment.status, db.func.count(Appointment.id))\
        .filter(Appointment.patient_id == current_user.patient_profile.id)\
        .group_by(Appointment.status).all()
        
    s_map = {s[0]: s[1] for s in status_stats}
    s_labels = ['Booked', 'Completed', 'Cancelled']
    s_data = [
        s_map.get(AppointmentStatus.BOOKED, 0),
        s_map.get(AppointmentStatus.COMPLETED, 0),
        s_map.get(AppointmentStatus.CANCELLED, 0)
    ]
    
    return render_template('dashboards/patient.html', 
                         appointments=appts,
                         departments=departments,
                         history_labels=h_labels,
                         history_data=h_data,
                         status_labels=s_labels,
                         status_data=s_data)

@patient.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        name = sanitize_input(request.form.get('name'))
        phone = sanitize_input(request.form.get('phone'))
        addr = sanitize_input(request.form.get('address'))
        gender = request.form.get('gender')
        dob_str = request.form.get('dob')
        
        # validate inputs
        try:
            validate_required_fields(request.form, ['name', 'phone'])
            validate_phone(phone)
            validate_gender(gender)
            
            # validate dob
            if dob_str:
                dob = validate_date(dob_str, allow_future=False)
                # sanity check for age
                if dob.year < 1900:
                    raise ValidationError("Date of birth too far in the past")
                current_user.patient_profile.dob = dob
            
            # check address length
            if addr and len(addr) > 200:
                raise ValidationError("Address must be at most 200 characters")
                
        except ValidationError as e:
            flash(str(e), 'danger')
            return render_template('patient/profile.html')
        
        current_user.name = name
        current_user.patient_profile.phone = phone
        current_user.patient_profile.address = addr
        current_user.patient_profile.gender = gender
        
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('patient.dashboard'))
        
    return render_template('patient/profile.html')

@patient.route('/doctors')
def doctors():
    search = request.args.get('search', '')
    dept_id = request.args.get('department_id')
    avail_date = request.args.get('date')
    
    q = User.query.join(DoctorProfile).filter(User.role == Role.DOCTOR)
    
    if search:
        q = q.filter(User.name.ilike(f'%{search}%'))
    if dept_id:
        q = q.filter(DoctorProfile.department_id == dept_id)
    if avail_date:
        try:
            date_obj = datetime.strptime(avail_date, '%Y-%m-%d').date()
            q = q.join(DoctorAvailability).filter(DoctorAvailability.date == date_obj)
        except ValueError:
            pass
        
    doctors = q.all()
    departments = Department.query.all()
    today = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('patient/doctors.html', doctors=doctors, departments=departments, search=search, selected_dept=dept_id, selected_date=avail_date, today=today)

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
    
    # check blacklist
    if current_user.patient_profile.is_blacklisted:
        flash('Your account has been restricted. Please contact administrator.', 'danger')
        return redirect(url_for('patient.dashboard'))
    
    # validate reason
    reason = sanitize_input(request.form.get('reason'))
    try:
        validate_required_fields(request.form, ['reason'])
        if len(reason) < 5:
            raise ValidationError("Please provide a detailed reason (minimum 5 characters)")
    except ValidationError as e:
        flash(str(e), 'danger')
        return redirect(url_for('patient.book_doctor', doctor_id=slot.doctor.user_id))
        
    # check overlap
    start_dt = datetime.combine(slot.date, slot.start_time)
    end_dt = datetime.combine(slot.date, slot.end_time)
    
    existing = Appointment.query.filter_by(doctor_id=slot.doctor_id)\
        .filter(Appointment.status != AppointmentStatus.CANCELLED)\
        .filter(
            db.and_(
                Appointment.appointment_start < end_dt,
                Appointment.appointment_end > start_dt
            )
        ).first()
    
    if existing:
        flash('This slot overlaps with an existing appointment', 'warning')
        return redirect(url_for('patient.book_doctor', doctor_id=slot.doctor.user_id))
        
    appointment = Appointment(
        patient_id=current_user.patient_profile.id,
        doctor_id=slot.doctor_id,
        appointment_start=start_dt,
        appointment_end=end_dt,
        reason=reason,
        status=AppointmentStatus.BOOKED
    )
    
    try:
        db.session.add(appointment)
        db.session.commit()
        flash('Appointment booked successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('This slot was just booked by someone else. Please choose another.', 'warning')
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
            flash('Appointment cancelled', 'success')
        else:
            flash('Cannot cancel this appointment', 'warning')
    return redirect(url_for('patient.dashboard'))

@patient.route('/appointments/<int:id>/reschedule', methods=['POST'])
def reschedule_appointment(id):
    appointment = db.session.get(Appointment, id)
    if appointment and appointment.patient_id == current_user.patient_profile.id:
        if appointment.status == AppointmentStatus.BOOKED:
            # Store doctor ID to redirect
            doctor_id = appointment.doctor.user.id
            
            # Cancel current appointment
            appointment.status = AppointmentStatus.CANCELLED
            appointment.canceled_by = 'PATIENT_RESCHEDULE'
            db.session.commit()
            
            flash('Previous appointment cancelled. Please select a new time slot.', 'info')
            return redirect(url_for('patient.book_doctor', doctor_id=doctor_id))
        else:
            flash('Cannot reschedule this appointment', 'warning')
    return redirect(url_for('patient.dashboard'))

@patient.route('/history')
def history():
    appointments = Appointment.query.filter_by(patient_id=current_user.patient_profile.id)\
        .filter(Appointment.status == AppointmentStatus.COMPLETED)\
        .order_by(Appointment.appointment_start.desc()).all()
    return render_template('patient/history.html', appointments=appointments)
