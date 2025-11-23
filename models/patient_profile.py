from models.base import db


class PatientProfile(db.Model):
    __tablename__ = "patient_profiles"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    dob = db.Column(db.Date)
    gender = db.Column(db.String(20))
    address = db.Column(db.Text)
    is_blacklisted = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', back_populates='patient_profile')

    def to_dict(self):
        return {
            'phone': self.phone,
            'dob': self.dob.isoformat() if self.dob else None,
            'gender': self.gender,
            'address': self.address
        }
    appointments = db.relationship("Appointment", back_populates="patient")
    
    def __repr__(self):
        return f'<PatientProfile User:{self.user_id}>'
