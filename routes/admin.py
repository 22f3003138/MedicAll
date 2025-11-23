from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, DoctorProfile, PatientProfile, Appointment, Department, Role
from werkzeug.security import generate_password_hash
from utils import validate_email, validate_password, validate_required_fields, ValidationError, sanitize_input

admin = Blueprint('admin', __name__, url_prefix='/admin')

@admin.before_request
@login_required
def require_admin():
    if current_user.role != Role.ADMIN:
        return "Access Denied", 403

@admin.route('/dashboard')
def dashboard():
    # Stats
    total_doctors = User.query.filter_by(role=Role.DOCTOR).count()
    total_patients = User.query.filter_by(role=Role.PATIENT).count()
    total_appointments = Appointment.query.count()
    
    # Chart Data: Appointments per Department
    dept_stats = db.session.query(Department.name, db.func.count(Appointment.id))\
        .join(DoctorProfile, DoctorProfile.department_id == Department.id)\
        .join(Appointment, Appointment.doctor_id == DoctorProfile.id)\
        .group_by(Department.name).all()
        
    dept_labels = [stat[0] for stat in dept_stats]
    dept_data = [stat[1] for stat in dept_stats]
    
    return render_template('dashboards/admin.html', 
                         total_doctors=total_doctors,
                         total_patients=total_patients,
                         total_appointments=total_appointments,
                         dept_labels=dept_labels,
                         dept_data=dept_data)

@admin.route('/doctors')
def doctors():
    search = request.args.get('search', '')
    query = User.query.filter_by(role=Role.DOCTOR)
    if search:
        query = query.filter(User.name.ilike(f'%{search}%'))
    doctors = query.all()
    return render_template('admin/doctors.html', doctors=doctors, search=search)

@admin.route('/doctors/add', methods=['GET', 'POST'])
def add_doctor():
    if request.method == 'POST':
        email = sanitize_input(request.form.get('email'))
        name = sanitize_input(request.form.get('name'))
        password = request.form.get('password')
        dept_id = request.form.get('department_id')
        qualification = sanitize_input(request.form.get('qualification', ''))
        
        # Validate all fields
        try:
            validate_required_fields(request.form, ['email', 'name', 'password', 'department_id'])
            validate_email(email)
            validate_password(password)
            
            # Check department exists
            dept = db.session.get(Department, dept_id)
            if not dept:
                raise ValidationError("Invalid department selected")
                
        except ValidationError as e:
            flash(str(e), 'danger')
            departments = Department.query.all()
            return render_template('admin/doctor_form.html', departments=departments)
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            departments = Department.query.all()
            return render_template('admin/doctor_form.html', departments=departments)
            
        user = User(email=email, name=name, role=Role.DOCTOR)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        profile = DoctorProfile(user_id=user.id, department_id=dept_id, qualification=qualification)
        db.session.add(profile)
        db.session.commit()
        
        flash('Doctor added successfully', 'success')
        return redirect(url_for('admin.doctors'))
        
    departments = Department.query.all()
    return render_template('admin/doctor_form.html', departments=departments)

@admin.route('/doctors/<int:id>/edit', methods=['GET', 'POST'])
def edit_doctor(id):
    doctor = db.session.get(User, id)
    if not doctor or doctor.role != Role.DOCTOR:
        return "Not Found", 404
        
    if request.method == 'POST':
        name = sanitize_input(request.form.get('name'))
        email = sanitize_input(request.form.get('email'))
        dept_id = request.form.get('department_id')
        qualification = sanitize_input(request.form.get('qualification', ''))
        password = request.form.get('password')
        
        # Validate fields
        try:
            validate_required_fields(request.form, ['name', 'email', 'department_id'])
            validate_email(email)
            
            # Check department exists
            dept = db.session.get(Department, dept_id)
            if not dept:
                raise ValidationError("Invalid department selected")
            
            # Validate password if provided
            if password:
                validate_password(password)
                
        except ValidationError as e:
            flash(str(e), 'danger')
            departments = Department.query.all()
            return render_template('admin/doctor_form.html', doctor=doctor, departments=departments)
        
        # Check email uniqueness (excluding current doctor)
        existing = User.query.filter_by(email=email).first()
        if existing and existing.id != doctor.id:
            flash('Email already exists', 'danger')
            departments = Department.query.all()
            return render_template('admin/doctor_form.html', doctor=doctor, departments=departments)
        
        doctor.name = name
        doctor.email = email
        doctor.doctor_profile.department_id = dept_id
        doctor.doctor_profile.qualification = qualification
        
        if password:
            doctor.set_password(password)
            
        db.session.commit()
        flash('Doctor updated successfully', 'success')
        return redirect(url_for('admin.doctors'))
        
    departments = Department.query.all()
    return render_template('admin/doctor_form.html', doctor=doctor, departments=departments)

@admin.route('/doctors/<int:id>/delete', methods=['POST'])
def delete_doctor(id):
    doctor = db.session.get(User, id)
    if doctor and doctor.role == Role.DOCTOR:
        db.session.delete(doctor)
        db.session.commit()
        flash('Doctor deleted successfully', 'success')
    return redirect(url_for('admin.doctors'))

@admin.route('/patients')
def patients():
    search = request.args.get('search', '')
    query = User.query.filter_by(role=Role.PATIENT)
    if search:
        query = query.filter(User.name.ilike(f'%{search}%'))
    patients = query.all()
    return render_template('admin/patients.html', patients=patients, search=search)

@admin.route('/patients/<int:id>/toggle_status', methods=['POST'])
def toggle_patient_status(id):
    patient = db.session.get(User, id)
    if patient and patient.role == Role.PATIENT:
        patient.patient_profile.is_blacklisted = not patient.patient_profile.is_blacklisted
        db.session.commit()
        status = "blacklisted" if patient.patient_profile.is_blacklisted else "activated"
        flash(f'Patient {status} successfully', 'success')
    return redirect(url_for('admin.patients'))

@admin.route('/appointments')
def appointments():
    appointments = Appointment.query.order_by(Appointment.appointment_start.desc()).all()
    return render_template('admin/appointments.html', appointments=appointments)
