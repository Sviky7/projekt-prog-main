from datetime import datetime
from flask_login import UserMixin
from extensions import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_tutor = db.Column(db.Boolean, default=False)
    
    # One-to-one relationship with TutorProfile
    tutor_profile = db.relationship('TutorProfile', backref='user', uselist=False)
    
    # One-to-many relationships
    bookings_as_student = db.relationship('Booking', backref='student', 
                                        foreign_keys='Booking.student_id')
    ratings_given = db.relationship('Rating', backref='student',
                                  foreign_keys='Rating.student_id')

class TutorProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    hourly_rate = db.Column(db.Float, nullable=False)
    bio = db.Column(db.Text)
    profile_photo = db.Column(db.String(255), nullable=True, default='default_profile.jpg')
    
    # Many-to-many relationship with subjects
    subjects = db.relationship('Subject', secondary='tutor_subjects',
                             backref=db.backref('tutor_profiles', lazy='select'))
    
    # One-to-many relationships
    bookings = db.relationship('Booking', backref='tutor_profile',
                             foreign_keys='Booking.tutor_id', lazy='dynamic')
    ratings = db.relationship('Rating', backref='tutor_profile',
                            foreign_keys='Rating.tutor_profile_id')
    
    @property
    def average_rating(self):
        ratings = [r.rating for r in self.ratings]
        return round(sum(ratings) / len(ratings), 1) if ratings else 0.0

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)

# Association table for many-to-many relationship between tutors and subjects
tutor_subjects = db.Table('tutor_subjects',
    db.Column('tutor_id', db.Integer, db.ForeignKey('tutor_profile.id')),
    db.Column('subject_id', db.Integer, db.ForeignKey('subject.id'))
)

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Float, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tutor_profile_id = db.Column(db.Integer, db.ForeignKey('tutor_profile.id'), nullable=False)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutor_profile.id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    date_time = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # in minutes
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    subject = db.relationship('Subject')
