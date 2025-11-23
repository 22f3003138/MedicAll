from models.base import db, utc_now, AppointmentStatus


class Appointment(db.Model):
    __tablename__ = "appointments"
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor_profiles.id", ondelete="CASCADE"), nullable=False)
    appointment_start = db.Column(db.DateTime, nullable=False, index=True)
    appointment_end = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False, default=AppointmentStatus.BOOKED)
    reason = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    canceled_by = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    
    patient = db.relationship("PatientProfile", back_populates="appointments")
    doctor = db.relationship("DoctorProfile", back_populates="appointments")
    treatment = db.relationship("Treatment", uselist=False, back_populates="appointment", cascade="all, delete-orphan")
    
    __table_args__ = (
        db.Index('ix_doctor_start', 'doctor_id', 'appointment_start'),
        db.UniqueConstraint('doctor_id', 'appointment_start', name='uq_doctor_appointment_slot'),
    )
    
    def can_transition_to(self, new_status):
        if self.status == new_status:
            return True
        
        # Cannot change from COMPLETED or CANCELLED
        if self.status in [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED]:
            return False
            
        # Can cancel BOOKED
        if new_status == AppointmentStatus.CANCELLED:
            return self.status == AppointmentStatus.BOOKED
            
        # Can complete BOOKED
        if new_status == AppointmentStatus.COMPLETED:
            return self.status == AppointmentStatus.BOOKED
            
        return False
    
    def __repr__(self):
        return f'<Appointment {self.id} - Patient:{self.patient_id} Doctor:{self.doctor_id}>'
