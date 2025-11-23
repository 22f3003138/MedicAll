from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, PatientProfile, Role
from werkzeug.security import generate_password_hash
from utils import validate_email, validate_password, validate_phone, validate_required_fields, ValidationError, sanitize_input

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == Role.ADMIN:
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == Role.DOCTOR:
            return redirect(url_for('doctor.dashboard'))
        return redirect(url_for('patient.dashboard'))

    if request.method == 'POST':
        email = sanitize_input(request.form.get('email'))
        password = request.form.get('password')
        
        # Validate required fields
        try:
            validate_required_fields(request.form, ['email', 'password'])
            validate_email(email)
        except ValidationError as e:
            flash(str(e), 'danger')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            if user.role == Role.ADMIN:
                return redirect(url_for('admin.dashboard'))
            elif user.role == Role.DOCTOR:
                return redirect(url_for('doctor.dashboard'))
            return redirect(url_for('patient.dashboard'))
        
        flash('Invalid email or password', 'danger')
    
    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('patient.dashboard'))
        
    if request.method == 'POST':
        email = sanitize_input(request.form.get('email'))
        name = sanitize_input(request.form.get('name'))
        password = request.form.get('password')
        phone = sanitize_input(request.form.get('phone'))
        
        # Validate all fields
        try:
            validate_required_fields(request.form, ['email', 'name', 'password', 'phone'])
            validate_email(email)
            validate_password(password)
            validate_phone(phone)
        except ValidationError as e:
            flash(str(e), 'danger')
            return render_template('auth/register.html')
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists', 'danger')
            return redirect(url_for('auth.register'))
            
        new_user = User(
            email=email,
            name=name,
            role=Role.PATIENT
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        # Create patient profile
        profile = PatientProfile(user_id=new_user.id, phone=phone)
        db.session.add(profile)
        db.session.commit()
        
        login_user(new_user)
        flash('Registration successful!', 'success')
        return redirect(url_for('patient.dashboard'))
        
    return render_template('auth/register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
