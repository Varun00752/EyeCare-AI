from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'patient', 'hospital', 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    patient = db.relationship("Patient", backref="user", uselist=False, cascade="all, delete-orphan")
    hospital = db.relationship("Hospital", backref="user", uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    phone = db.Column(db.String(30))
    diabetes_years = db.Column(db.Integer)

    # Relationships
    scans = db.relationship("Scan", backref="patient", lazy=True, cascade="all, delete-orphan")
    appointments = db.relationship("Appointment", backref="patient", lazy=True, cascade="all, delete-orphan")


class Hospital(db.Model):
    __tablename__ = "hospitals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    city = db.Column(db.String(100), nullable=False, index=True)
    address = db.Column(db.String(255))
    phone = db.Column(db.String(30))
    description = db.Column(db.Text)
    approved = db.Column(db.Integer, default=0)  # 0 pending, 1 approved, 2 rejected

    # Relationships
    hospital_procedures = db.relationship("HospitalProcedure", backref="hospital", lazy=True, cascade="all, delete-orphan")
    appointments = db.relationship("Appointment", backref="hospital", lazy=True, cascade="all, delete-orphan")


class Procedure(db.Model):
    __tablename__ = "procedures"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    category = db.Column(db.String(100))  # Surgery / Laser / Injection / Checkup
    description = db.Column(db.Text)

    # Relationships
    hospital_procedures = db.relationship("HospitalProcedure", backref="procedure", lazy=True, cascade="all, delete-orphan")
    appointments = db.relationship("Appointment", backref="procedure", lazy=True)


class HospitalProcedure(db.Model):
    __tablename__ = "hospital_procedures"

    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id"), nullable=False)
    procedure_id = db.Column(db.Integer, db.ForeignKey("procedures.id"), nullable=False)
    price_min = db.Column(db.Integer, nullable=False)  # in INR
    price_max = db.Column(db.Integer, nullable=False)  # in INR

    __table_args__ = (
        db.UniqueConstraint("hospital_id", "procedure_id", name="uq_hospital_procedure"),
    )


class Scan(db.Model):
    __tablename__ = "scans"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    scan_type = db.Column(db.String(20), nullable=False, default="dr")  # 'dr' or 'infection'
    image_path = db.Column(db.String(255), nullable=False)
    heatmap_path = db.Column(db.String(255))
    predicted_grade = db.Column(db.Integer)  # 0-4 for dr; 0/1 for infection
    predicted_label = db.Column(db.String(100))
    confidence = db.Column(db.Float)
    is_demo = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    appointments = db.relationship("Appointment", backref="scan", lazy=True)


class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id"), nullable=False)
    procedure_id = db.Column(db.Integer, db.ForeignKey("procedures.id"), nullable=False)
    scan_id = db.Column(db.Integer, db.ForeignKey("scans.id"), nullable=True)
    appt_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default="pending")  # pending / accepted / rejected / cancelled
