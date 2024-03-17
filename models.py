import random
import string
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from validate_email import validate_email

db = SQLAlchemy()
bcrypt = Bcrypt()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)
    parcels = db.relationship('Parcel', backref='user', lazy=True)

    def __init__(self, username, email, password, role='user'):
        self.username = username
        self.email = email
        self.set_password(password)
        self.role = role

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    @staticmethod
    def is_valid_email(email):
        return validate_email(email)

    def serialize(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
        }

    @classmethod
    def register(cls, username, email, password, role='user'):
        new_user = cls(username=username, email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        return new_user


class Parcel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(64))
    description = db.Column(db.Text())
    tracking_number = db.Column(db.String(5), unique=True, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    pickup_location = db.Column(db.String(100), nullable=False)
    destination_location = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='pending')
    present_location = db.Column(db.String(100))
    notifications = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, user_id, name, description, weight, pickup_location, destination_location, status=None, present_location=None, notifications=None):
        self.user_id = user_id
        self.name = name
        self.description = description
        self.tracking_number = self.generate_tracking_number()
        self.weight = weight
        self.pickup_location = pickup_location
        self.destination_location = destination_location
        self.status = status if status is not None else 'pending'  
        self.present_location = present_location
        self.notifications = notifications

    def generate_tracking_number(self):
        length = 5
        characters = string.ascii_uppercase + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'tracking_number': self.tracking_number,
            'weight': self.weight,
            'pickup_location': self.pickup_location,
            'destination_location': self.destination_location,
            'status': self.status,
            'present_location': self.present_location,
            'notifications': self.notifications,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class TokenBlocklist(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    jti = db.Column(db.String(), nullable=True)
    created_at = db.Column(db.DateTime(), default=datetime.now)

    def __repr__(self):
        return f"<Token {self.jti}>"
    
    def save(self):
        db.session.add(self)
        db.session.commit()