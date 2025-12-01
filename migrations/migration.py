import sys
import os
import random

# Add parent dir for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, User, Role, Department, DoctorProfile, PatientProfile, DoctorAvailability, Appointment, AppointmentStatus, Treatment
from datetime import datetime, timedelta, time, date

def seed_database():
    with app.app_context():
        print("Initializing database...")
        db.create_all()

        print("Checking Admin...")
        admin = User.query.filter_by(email='admin@hospital.com').first()
        if not admin:
            admin = User(
                email='admin@hospital.com',
                name='System Admin',
                role=Role.ADMIN,
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print(" + Admin created")
        else:
            print(" - Admin exists")

        print("Checking Departments...")
        depts_data = [
            {'name': 'Cardiology', 'desc': 'Heart and cardiovascular care'},
            {'name': 'Oncology', 'desc': 'Cancer diagnosis and treatment'},
            {'name': 'General Medicine', 'desc': 'Primary healthcare'},
            {'name': 'Neurology', 'desc': 'Brain and nervous system'},
            {'name': 'Orthopedics', 'desc': 'Bone and joint specialist'},
            {'name': 'Pediatrics', 'desc': 'Child healthcare'},
            {'name': 'Dermatology', 'desc': 'Skin care specialists'}
        ]
        
        dept_map = {}
        for d in depts_data:
            dept = Department.query.filter_by(name=d['name']).first()
            if not dept:
                dept = Department(name=d['name'], description=d['desc'])
                db.session.add(dept)
                print(f" + Department {d['name']} created")
            dept_map[d['name']] = dept
        
        db.session.commit()
        
        for name in dept_map:
            if not dept_map[name].id:
                dept_map[name] = Department.query.filter_by(name=name).first()


        print("Checking Doctors...")
        doctors_info = [
            ('Cardiology', 'Dr. Rajesh Kumar', 'rajesh.k@hospital.com', 'MD, DM Cardiology'),
            ('Oncology', 'Dr. Priya Sharma', 'priya.s@hospital.com', 'MD Oncology'),
            ('General Medicine', 'Dr. Amit Patel', 'amit.p@hospital.com', 'MBBS, MD'),
            ('Neurology', 'Dr. Sneha Gupta', 'sneha.g@hospital.com', 'DM Neurology'),
            ('Orthopedics', 'Dr. Vikram Singh', 'vikram.s@hospital.com', 'MS Orthopedics'),
            ('Pediatrics', 'Dr. Anjali Desai', 'anjali.d@hospital.com', 'MD Pediatrics'),
            ('Dermatology', 'Dr. Rahul Verma', 'rahul.v@hospital.com', 'MD Dermatology')
        ]

        active_doctors = []
        for dept_name, name, email, qual in doctors_info:
            doc = User.query.filter_by(email=email).first()
            if not doc:
                doc = User(email=email, name=name, role=Role.DOCTOR)
                doc.set_password('doctor123')
                db.session.add(doc)
                db.session.flush()
                
                profile = DoctorProfile(
                    user_id=doc.id,
                    department_id=dept_map[dept_name].id,
                    phone=f"98765{random.randint(10000, 99999)}",
                    qualification=qual,
                    bio=f"Senior specialist in {dept_name} with over 10 years of experience."
                )
                db.session.add(profile)
                print(f" + Doctor {name} created")
                active_doctors.append(profile)
            else:
                if doc.doctor_profile:
                    active_doctors.append(doc.doctor_profile)


        print("Checking Patients...")
        patient_names = [
            ('Rohan Mehta', 'rohan.m@example.com'),
            ('Karthik Iyer', 'karthik.i@example.com'),
            ('Lakshmi Nair', 'lakshmi.n@example.com'),
            ('Arjun Reddy', 'arjun.r@example.com'),
            ('Meera Krishnan', 'meera.k@example.com'),
            ('Sanya Malhotra', 'sanya.m@example.com')
        ]

        active_patients = []
        for name, email in patient_names:
            pat = User.query.filter_by(email=email).first()
            if not pat:
                pat = User(email=email, name=name, role=Role.PATIENT)
                pat.set_password('patient123')
                db.session.add(pat)
                db.session.flush()
                
                profile = PatientProfile(
                    user_id=pat.id,
                    phone=f"99887{random.randint(10000, 99999)}",
                    dob=date(1990 + random.randint(-10, 10), random.randint(1, 12), random.randint(1, 28)),
                    gender='Male' if any(x in name for x in ['Rohan', 'Karthik', 'Arjun']) else 'Female',
                    address=f"{random.randint(1, 100)}, Park Street, Mumbai"
                )
                db.session.add(profile)
                print(f" + Patient {name} created")
                active_patients.append(profile)
            else:
                if pat.patient_profile:
                    active_patients.append(pat.patient_profile)

        db.session.commit()

        print("Generating Data...")
        today = date.today()
        
        for doc in active_doctors:
            for i in range(14):
                day = today + timedelta(days=i)
                
                exists = DoctorAvailability.query.filter_by(doctor_id=doc.id, date=day).first()
                if not exists:
                    slot1 = DoctorAvailability(
                        doctor_id=doc.id,
                        date=day,
                        start_time=time(10, 0),
                        end_time=time(13, 0)
                    )
                    slot2 = DoctorAvailability(
                        doctor_id=doc.id,
                        date=day,
                        start_time=time(17, 0),
                        end_time=time(20, 0)
                    )
                    db.session.add(slot1)
                    db.session.add(slot2)
        
        db.session.commit()

        if Appointment.query.count() < 10 and active_doctors and active_patients:
            
            for _ in range(5):
                doc = random.choice(active_doctors)
                pat = random.choice(active_patients)
                past_date = today - timedelta(days=random.randint(1, 30))
                start_time = time(random.randint(10, 19), 0)
                
                appt = Appointment(
                    patient_id=pat.id,
                    doctor_id=doc.id,
                    appointment_start=datetime.combine(past_date, start_time),
                    appointment_end=datetime.combine(past_date, start_time) + timedelta(minutes=30),
                    status=AppointmentStatus.COMPLETED,
                    reason="Regular checkup"
                )
                db.session.add(appt)
                db.session.flush()
                
                treat = Treatment(
                    appointment_id=appt.id,
                    diagnosis="Viral fever" if random.random() > 0.5 else "General Infection",
                    prescription="Paracetamol 500mg\nRest for 2 days",
                    notes="Patient recovering well",
                    doctor_notes="Follow up in 1 week"
                )
                db.session.add(treat)

            for _ in range(3):
                doc = random.choice(active_doctors)
                pat = random.choice(active_patients)
                d = today + timedelta(days=random.randint(-5, 5))
                t = time(random.randint(10, 18), 30)
                
                appt = Appointment(
                    patient_id=pat.id,
                    doctor_id=doc.id,
                    appointment_start=datetime.combine(d, t),
                    appointment_end=datetime.combine(d, t) + timedelta(minutes=30),
                    status=AppointmentStatus.CANCELLED,
                    canceled_by="PATIENT",
                    reason="Personal emergency"
                )
                db.session.add(appt)

            for _ in range(5):
                doc = random.choice(active_doctors)
                pat = random.choice(active_patients)
                fut_date = today + timedelta(days=random.randint(1, 7))
                t = time(random.randint(10, 12), 0)
                
                appt = Appointment(
                    patient_id=pat.id,
                    doctor_id=doc.id,
                    appointment_start=datetime.combine(fut_date, t),
                    appointment_end=datetime.combine(fut_date, t) + timedelta(minutes=30),
                    status=AppointmentStatus.BOOKED,
                    reason="Follow up consultation"
                )
                db.session.add(appt)

            print(" + Created sample appointments")
            db.session.commit()
        else:
            print(" - Appointments already populated")

        print("Database seeding completed!")

if __name__ == "__main__":
    seed_database()
