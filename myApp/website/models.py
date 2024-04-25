from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    gender = db.Column(db.String(1))
    appointments = db.relationship('Appointment', backref='patient', lazy='dynamic')
    def serialize(self):
        # Get the latest appointment
        latest_appointment = self.appointments.order_by(Appointment.id.desc()).first()
        # Get the age from the latest image of the latest appointment
        age = latest_appointment.images.order_by(Image.id.desc()).first().patient_age if latest_appointment and latest_appointment.images.count() > 0 else None
        return {
            'gender': self.gender,
            'age': age,
            'id': self.id,
            'appointments': [appointment.serialize() for appointment in self.appointments]
        }


class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'))
    follow_up_number = db.Column(db.Integer)
    group = db.Column(db.String(255))
    images = db.relationship('Image', backref='appointment', lazy='dynamic')

    def serialize(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'follow_up_number': self.follow_up_number,
            'group': self.group,
            'images': [image.serialize() for image in self.images]
        }


class Image(db.Model):
    __tablename__ = 'images'
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    image_index = db.Column(db.String(255))
    patient_age = db.Column(db.Integer)
    view_position = db.Column(db.String(255))
    original_image_width_height = db.Column(db.String(255))
    original_image_pixel_spacing = db.Column(db.String(255))
    findings = db.relationship('Finding', backref='image', lazy='dynamic')

    def serialize(self):
        return {
            'id': self.id,
            'appointment_id': self.appointment_id,
            'image_index': self.image_index,
            'patient_age': self.patient_age,
            'view_position': self.view_position,
            'original_image_width_height': self.original_image_width_height,
            'original_image_pixel_spacing': self.original_image_pixel_spacing,
            'findings': [finding.serialize() for finding in self.findings]
        }

class Finding(db.Model):
    __tablename__ = 'findings'
    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey('images.id'))
    finding_label = db.Column(db.String(255))

    def serialize(self):
        return {
            'id': self.id,
            'image_id': self.image_id,
            'finding_label': self.finding_label
        }

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    last_name = db.Column(db.String(150))
    