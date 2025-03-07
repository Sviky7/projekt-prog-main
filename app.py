from flask import Flask, render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os

from extensions import db, migrate, login_manager
from models import User, TutorProfile, Subject, Booking, Rating
from forms import LoginForm, RegistrationForm, TutorProfileForm, BookingForm, RatingForm

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///zochova_edu.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'profile_photos')

# Initialize extensions with app
db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)
login_manager.login_view = 'login'

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_profile_photo(form_photo):
    if form_photo:
        filename = secure_filename(form_photo.filename)
        unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        form_photo.save(filepath)
        return f'profile_photos/{unique_filename}'
    return None

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/')
def index():
    subject_id = request.args.get('subject', '')
    search_query = request.args.get('search', '').strip().lower()
    sort_by = request.args.get('sort', 'rating')  # Default sort by rating
    
    # Start with all tutors
    tutors_query = TutorProfile.query
    
    # Filter by subject if selected
    if subject_id and subject_id.isdigit():
        tutors_query = tutors_query.join(TutorProfile.subjects).filter(Subject.id == int(subject_id))
    
    # Filter by search query
    if search_query:
        tutors_query = tutors_query.join(TutorProfile.user).filter(
            db.or_(
                db.func.lower(User.username).contains(search_query),
                db.func.lower(TutorProfile.bio).contains(search_query)
            )
        )
    
    # Get all tutors before sorting
    tutors = tutors_query.all()
    
    # Sort tutors based on selected criteria
    if sort_by == 'price_asc':
        tutors.sort(key=lambda x: x.hourly_rate)
    elif sort_by == 'price_desc':
        tutors.sort(key=lambda x: x.hourly_rate, reverse=True)
    else:  # sort by rating (default)
        tutors.sort(key=lambda x: x.average_rating, reverse=True)
    
    subjects = Subject.query.all()
    
    # Pre-calculate tutor counts for each subject
    subject_data = []
    for subject in subjects:
        tutor_count = len(list(subject.tutor_profiles))
        subject_data.append({
            'id': subject.id,
            'name': subject.name,
            'tutor_count': tutor_count
        })
    
    return render_template('index.html', tutors=tutors, subject_data=subject_data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not check_password_hash(user.password_hash, form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data,
                   email=form.email.data,
                   is_tutor=form.is_tutor.data,
                   password_hash=generate_password_hash(form.password.data))
        db.session.add(user)
        db.session.commit()
        if user.is_tutor:
            return redirect(url_for('create_tutor_profile'))
        flash('Congratulations, you are now a registered user!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/create_tutor_profile', methods=['GET', 'POST'])
@login_required
def create_tutor_profile():
    if not current_user.is_tutor:
        return redirect(url_for('index'))
    form = TutorProfileForm()
    form.subjects.choices = [(s.id, s.name) for s in Subject.query.all()]
    
    if form.validate_on_submit():
        profile = TutorProfile(user=current_user,
                             hourly_rate=form.hourly_rate.data,
                             bio=form.bio.data)
        for subject_id in form.subjects.data:
            subject = Subject.query.get(subject_id)
            profile.subjects.append(subject)
        db.session.add(profile)
        db.session.commit()
        flash('Your tutor profile has been created!', 'success')
        return redirect(url_for('tutor_dashboard'))
    return render_template('create_tutor_profile.html', form=form)

@app.route('/tutor/<int:tutor_id>')
def tutor_profile(tutor_id):
    tutor = TutorProfile.query.get_or_404(tutor_id)
    form = BookingForm()
    form.subject.choices = [(s.id, s.name) for s in tutor.subjects]
    now = datetime.now()
    
    has_completed_session = False
    if current_user.is_authenticated and not current_user.is_tutor:
        has_completed_session = Booking.query.filter_by(
            student_id=current_user.id,
            tutor_id=tutor_id,
            status='completed'
        ).first() is not None
    
    return render_template('tutor_profile.html', 
                         tutor=tutor, 
                         form=form, 
                         now=now,
                         has_completed_session=has_completed_session)

@app.route('/book_session/<int:tutor_id>', methods=['POST'])
@login_required
def book_session(tutor_id):
    tutor = TutorProfile.query.get_or_404(tutor_id)
    form = BookingForm()
    form.subject.choices = [(s.id, s.name) for s in tutor.subjects]
    
    if not form.validate_on_submit():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error in {field}: {error}', 'danger')
        return redirect(url_for('tutor_profile', tutor_id=tutor_id))

    try:
        # Check if the time slot is available
        existing_booking = Booking.query.filter_by(
            tutor_id=tutor_id,
            date_time=form.date_time.data
        ).first()
        
        if existing_booking:
            flash('This time slot is already booked. Please choose another time.', 'warning')
            return redirect(url_for('tutor_profile', tutor_id=tutor_id))
        
        booking = Booking(
            student_id=current_user.id,
            tutor_id=tutor.id,
            subject_id=form.subject.data,
            date_time=form.date_time.data,
            duration=form.duration.data,
            status='pending'
        )
        db.session.add(booking)
        db.session.commit()
        flash('Booking request sent successfully!', 'success')
        return redirect(url_for('student_dashboard'))
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while booking: {str(e)}', 'danger')
        return redirect(url_for('tutor_profile', tutor_id=tutor_id))

@app.route('/tutor_dashboard')
@login_required
def tutor_dashboard():
    if not current_user.is_tutor:
        return redirect(url_for('index'))
    if not current_user.tutor_profile:
        flash('Please create your tutor profile first', 'warning')
        return redirect(url_for('create_tutor_profile'))
    bookings = current_user.tutor_profile.bookings.all()
    return render_template('tutor_dashboard.html', bookings=bookings)

@app.route('/student_dashboard')
@login_required
def student_dashboard():
    bookings = current_user.bookings_as_student
    return render_template('student_dashboard.html', bookings=bookings)

@app.route('/handle_booking/<int:booking_id>/<action>')
@login_required
def handle_booking(booking_id, action):
    booking = Booking.query.get_or_404(booking_id)
    if booking.tutor_profile.user != current_user:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('index'))
    
    if action == 'confirm':
        booking.status = 'confirmed'
        flash('Booking confirmed!', 'success')
    elif action == 'cancel':
        booking.status = 'cancelled'
        flash('Booking cancelled!', 'success')
    elif action == 'complete':
        booking.status = 'completed'
        flash('Session marked as completed! Student can now leave a review.', 'success')
    
    db.session.commit()
    return redirect(url_for('tutor_dashboard'))

@app.route('/edit_tutor_profile', methods=['GET', 'POST'])
@login_required
def edit_tutor_profile():
    if not current_user.is_tutor:
        flash('Only tutors can access this page.', 'danger')
        return redirect(url_for('index'))
    
    profile = current_user.tutor_profile
    if not profile:
        return redirect(url_for('create_tutor_profile'))
    
    form = TutorProfileForm()
    form.subjects.choices = [(s.id, s.name) for s in Subject.query.all()]
    
    if request.method == 'GET':
        form.hourly_rate.data = profile.hourly_rate
        form.bio.data = profile.bio
        form.subjects.data = [s.id for s in profile.subjects]
    
    if form.validate_on_submit():
        profile.hourly_rate = form.hourly_rate.data
        profile.bio = form.bio.data
        profile.subjects = []
        
        # Handle profile photo upload
        if form.profile_photo.data:
            photo_path = save_profile_photo(form.profile_photo.data)
            if photo_path:
                profile.profile_photo = photo_path
        
        for subject_id in form.subjects.data:
            subject = Subject.query.get(subject_id)
            if subject:
                profile.subjects.append(subject)
        
        db.session.commit()
        flash('Your tutor profile has been updated!', 'success')
        return redirect(url_for('tutor_dashboard'))
    
    return render_template('edit_tutor_profile.html', title='Edit Profile', form=form)

@app.route('/rate_tutor/<int:tutor_id>', methods=['GET', 'POST'])
@login_required
def rate_tutor(tutor_id):
    if current_user.is_tutor:
        flash('Tutors cannot rate other tutors.', 'danger')
        return redirect(url_for('index'))
    
    tutor_profile = TutorProfile.query.get_or_404(tutor_id)
    form = RatingForm()
    
    # Check if student has completed a session with this tutor
    has_completed_session = Booking.query.filter_by(
        student_id=current_user.id,
        tutor_id=tutor_id,
        status='completed'
    ).first() is not None
    
    if not has_completed_session:
        flash('You can only rate tutors after completing a session with them.', 'warning')
        return redirect(url_for('tutor_profile', tutor_id=tutor_id))
    
    if form.validate_on_submit():
        rating = Rating(
            rating=form.rating.data,
            comment=form.comment.data,
            student_id=current_user.id,
            tutor_profile_id=tutor_id
        )
        db.session.add(rating)
        db.session.commit()
        flash('Thank you for your rating!', 'success')
        return redirect(url_for('tutor_profile', tutor_id=tutor_id))
    
    return render_template('rate_tutor.html', form=form, tutor=tutor_profile.user)

@app.route('/how_it_works')
def how_it_works():
    return render_template('how_it_works.html')

@app.route('/for_schools')
def for_schools():
    return render_template('for_schools.html')

@app.route('/become_tutor')
def become_tutor():
    return render_template('become_tutor.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Add default subjects if they don't exist
        default_subjects = ['Mathematics', 'Physics', 'Chemistry', 'Biology', 'Computer Science', 'History', 'Geography', 'Economics', 'Business Studies', 'Accounting','Slovak']
        for subject_name in default_subjects:
            if not Subject.query.filter_by(name=subject_name).first():
                subject = Subject(name=subject_name)
                db.session.add(subject)
        db.session.commit()
        
    app.run(debug=True)
