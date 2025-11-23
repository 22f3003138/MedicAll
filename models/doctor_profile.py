from models.base import db


class DoctorProfile(db.Model):
    __tablename__ = "doctor_profiles"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id", ondelete="SET NULL"))
    phone = db.Column(db.String(20))
    qualification = db.Column(db.String(255))
    bio = db.Column(db.Text)
    is_blacklisted = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', back_populates='doctor_profile')

    def to_dict(self):
        return {
            'department': self.department.name if self.department else None,
            'qualification': self.qualification,
            'bio': self.bio,
            'phone': self.phone
        }
    availabilities = db.relationship("DoctorAvailability", back_populates="doctor", cascade="all, delete-orphan")
    appointments = db.relationship("Appointment", back_populates="doctor")
    
    def __repr__(self):
        return f'<DoctorProfile User:{self.user_id}>'
