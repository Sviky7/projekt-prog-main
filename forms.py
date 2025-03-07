from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, \
    SelectField, FloatField, DateTimeField, SelectMultipleField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from flask_wtf.file import FileField, FileAllowed
from models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', 
                            validators=[DataRequired(), EqualTo('password')])
    is_tutor = BooleanField('Register as Tutor')
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class TutorProfileForm(FlaskForm):
    hourly_rate = FloatField('Hourly Rate (€)', validators=[DataRequired()])
    bio = TextAreaField('Bio', validators=[DataRequired(), Length(min=10, max=500)])
    subjects = SelectMultipleField('Subjects', coerce=int)
    profile_photo = FileField('Profile Photo', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    submit = SubmitField('Update Profile')

class BookingForm(FlaskForm):
    subject = SelectField('Subject', coerce=int, validators=[DataRequired()])
    date_time = DateTimeField('Date and Time',
                            format='%Y-%m-%dT%H:%M',  
                            validators=[DataRequired()])
    duration = SelectField('Duration (minutes)', 
                         choices=[(30, '30'), (60, '60'), (90, '90'), (120, '120')],
                         coerce=int,
                         validators=[DataRequired()])
    submit = SubmitField('Book Session')

class RatingForm(FlaskForm):
    rating = SelectField('Rating', choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], 
                        coerce=int, validators=[DataRequired()])
    comment = TextAreaField('Comment', validators=[Length(max=500)])
    submit = SubmitField('Submit Rating')
