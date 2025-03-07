# ZochovaEdu - Peer-to-Peer Tutoring Platform

ZochovaEdu is a web application that facilitates peer-to-peer tutoring. It allows students to find tutors and book tutoring sessions in various subjects.

## Features

- User registration and authentication (both students and tutors)
- Tutor profiles with subjects and hourly rates
- Session booking system
- Dashboard for tutors to manage booking requests
- Dashboard for students to view their bookings
- Real-time availability checking

## Installation

1. Make sure you have Python 3.8+ installed on your system.

2. Create and activate the virtual environment:
```bash
# Windows
.\π\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5000`.

## Project Structure

- `app.py` - Main application file with routes and configuration
- `models.py` - Database models
- `forms.py` - Form classes using Flask-WTF
- `templates/` - HTML templates
- `static/` - Static files (CSS, JavaScript)
- `π/` - Virtual environment

## Usage

1. Register as either a student or tutor
2. If registered as a tutor:
   - Create your tutor profile
   - Set your hourly rate and subjects
   - Manage booking requests
3. If registered as a student:
   - Browse available tutors
   - Book tutoring sessions
   - View your booking history

## Technologies Used

- Flask - Web framework
- SQLAlchemy - Database ORM
- Flask-Login - User authentication
- Flask-WTF - Form handling
- Bootstrap 5 - Frontend styling
- SQLite - Database
