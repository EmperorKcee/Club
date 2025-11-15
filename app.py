import logging
import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, Blueprint, make_response, g, current_app, send_file, session
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from wtforms import StringField, TextAreaField, DateTimeField, SelectField, validators, BooleanField, PasswordField, SubmitField
from flask_migrate import Migrate, upgrade
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta, date
import uuid
import traceback
from werkzeug.utils import secure_filename
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, Image as ReportLabImage, HRFlowable
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.colors import HexColor, Color, black, white, lightgrey, whitesmoke
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from extensions import db, login_manager, mail, migrate, csrf, socketio

# Import blueprints
from admin_routes import admin_bp
from admin_shop_routes import shop_admin
from filters import filters_bp, format_datetime
from fans_routes import fans_bp

# Import utils
from utils import get_country_code, calculate_age
from utils.email import send_player_credentials, send_password_reset

# Import configuration
from config import config
import os

def init_team_settings(app=None):
    """Initialize default team settings if they don't exist.
    
    Args:
        app: Optional Flask app instance. If provided, will use its app context.
    """
    def _init_settings():
        # Check if team settings exist, if not create default
        if not TeamSettings.query.first():
            default_settings = TeamSettings(
                team_name='Zambia FC',
                logo_url='img/logo.png',
                primary_color='#b11601',
                secondary_color='#f8f9fa',
                text_color='#ffffff',
                contact_email='info@fcms.com',
                contact_phone='+260 763 158 232',
                address='123 Soccer Way, Lusaka, Zambia',
                founded_year=2025,
                about='A professional football club based in Zambia'
            )
            db.session.add(default_settings)
            db.session.commit()
            print("Default team settings created.")
    
    # If app is provided, use its context
    if app is not None:
        with app.app_context():
            _init_settings()
    else:
        # Otherwise, assume we're already in an app context
        _init_settings()

# Import staff blueprint
from staff_routes import staff_bp

# Import models after db initialization to avoid circular imports
from models import User, Player, PlayerStats, Match, FinancialRecord, Staff, TeamSettings, PlayerUser
def delete_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    db.session.delete(staff)
    db.session.commit()
    flash('Staff member deleted successfully!', 'success')
    return redirect(url_for('staff.staff_list'))

# Initialize Flask app
# News Form
class NewsForm(FlaskForm):
    title = StringField('Title', [validators.DataRequired(), validators.Length(max=200)])
    content = TextAreaField('Content', [validators.DataRequired()])
    summary = TextAreaField('Summary', [validators.Length(max=500)])
    category = SelectField('Category', choices=[
        ('general', 'General'),
        ('match', 'Match Report'),
        ('team', 'Team News'),
        ('academy', 'Academy'),
        ('community', 'Community')
    ], default='general')
    is_published = BooleanField('Publish')
    is_featured = BooleanField('Feature')

app = Flask(__name__)

# Load configuration from config.py
app.config.from_object(config[os.getenv('FLASK_ENV', 'development')])

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'your-app-password'    # Replace with your app password
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'
app.config['BASE_URL'] = 'http://localhost:5000'
app.config['PLAYER_BASE_URL'] = 'http://localhost:5000'
app.config['SECRET_KEY'] = app.config.get('SECRET_KEY', 'your-secret-key-here')

# Initialize Flask-Mail
mail = Mail(app)

# Initialize CSRF protection
csrf = CSRFProtect()

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
mail.init_app(app)
migrate.init_app(app, db)
csrf.init_app(app)

# Add CSRF token to template context
@app.context_processor
def inject_csrf_token():
    from flask_wtf.csrf import generate_csrf
    return {'csrf_token': generate_csrf}

# Configure logging
if not app.debug and not app.testing:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = logging.FileHandler('logs/app.log')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Application startup')

# Configure Jinja2 filters
app.jinja_env.filters['country_code'] = get_country_code
app.jinja_env.filters['age'] = calculate_age

# Ensure upload directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join('static', 'uploads'), exist_ok=True)

# Import models after db initialization to avoid circular imports
from models import User, Player, Match, FinancialRecord, Staff, TeamSettings, PlayerUser, TrainingSession, PlayerAttendance, News
from wtforms import StringField, TextAreaField, DateTimeField, SelectField, SubmitField, validators
login_manager = LoginManager()
login_manager.login_view = 'unified_login'
login_manager.init_app(app)

# Initialize filters
from filters import init_app as init_filters
init_filters(app)

# Register blueprints
app.register_blueprint(admin_bp)
app.register_blueprint(shop_admin)
app.register_blueprint(fans_bp)
app.register_blueprint(staff_bp, url_prefix='')
app.register_blueprint(filters_bp)

# Initialize team settings
init_team_settings(app)

# Register datetime filter directly with Jinja2
app.jinja_env.filters['datetimeformat'] = format_datetime

@login_manager.user_loader
def load_user(user_id):
    # First try to load as PlayerUser
    player_user = PlayerUser.query.get(int(user_id))
    if player_user:
        return player_user
    
    # If not found, try to load as regular User
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        
        # Check if user is a PlayerUser (should not have admin access)
        if isinstance(current_user, PlayerUser):
            flash('You do not have permission to access this page. Please use staff login.', 'danger')
            return redirect(url_for('login'))
        
        # Check if user is a regular User with admin role
        if not hasattr(current_user, 'role') or current_user.role != 'admin':
            flash('You do not have permission to access this page. Admin access required.', 'danger')
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

def player_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in with your player account to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        
        # Check if the current user is a PlayerUser
        from models import PlayerUser
        if not isinstance(current_user, PlayerUser):
            flash('This area is restricted to player accounts only. Please log in with a player account.', 'danger')
            return redirect(url_for('dashboard'))
            
        # Check if the player account is active
        if not current_user.is_active:
            flash('Your player account is currently inactive. Please contact an administrator.', 'danger')
            return redirect(url_for('login'))
            
        # Update last login time
        current_user.last_login = datetime.utcnow()
        db.session.commit()
            
        return f(*args, **kwargs)
    return decorated_function

# Context processor to make team settings available in all templates
@app.context_processor
def inject_team_settings():
    team_settings = TeamSettings.query.first()
    # If no team settings exist, initialize default settings
    if not team_settings:
        init_team_settings(app)
        team_settings = TeamSettings.query.first()
    return {'team_settings': team_settings}

# Debug route to check team settings
@app.route('/debug/team-settings')
def debug_team_settings():
    team_settings = TeamSettings.query.first()
    if not team_settings:
        init_team_settings()
        team_settings = TeamSettings.query.first()
    return jsonify({
        'team_name': team_settings.team_name if team_settings else 'No team settings found',
        'logo_url': team_settings.logo_url if team_settings else None,
        'primary_color': team_settings.primary_color if team_settings else None,
        'secondary_color': team_settings.secondary_color if team_settings else None,
        'text_color': team_settings.text_color if team_settings else None
    })

# Test route to verify team settings in template
@app.route('/test-team-settings')
def test_team_settings():
    team_settings = TeamSettings.query.first()
    if not team_settings:
        init_team_settings()
        team_settings = TeamSettings.query.first()
    return render_template('test_team_settings.html', team_settings=team_settings)

# Routes
    
# Auth Routes

# Unified Login Route
@app.route('/auth', methods=['GET', 'POST'])
def unified_login():
    # Check if user is already authenticated
    if current_user.is_authenticated:
        if isinstance(current_user, PlayerUser):
            return redirect(url_for('player_dashboard'))
        return redirect(url_for('dashboard'))
    
    # Redirect to the single login page that handles both user types
    return redirect(url_for('login'))

def get_reset_token(user, expires_sec=1800):
    """Generate a password reset token for the user"""
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps({'user_id': user.id, 'user_type': 'user' if hasattr(user, 'is_admin') else 'player'}, salt='password-reset-salt')

def verify_reset_token(token):
    """Verify the password reset token and return the user if valid"""
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(token, salt='password-reset-salt', max_age=1800)  # 30 minutes expiration
        if data.get('user_type') == 'user':
            return User.query.get(data['user_id'])
        else:
            return PlayerUser.query.get(data['user_id'])
    except (SignatureExpired, BadSignature):
        return None

@app.route('/reset_password', methods=['GET', 'POST'])
def request_reset():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first() or \
               PlayerUser.query.filter_by(email=form.email.data).first()
        
        if user:
            token = get_reset_token(user)
            reset_url = url_for('reset_token', token=token, _external=True)
            
            # Send email with reset link
            from utils.email import send_password_reset
            send_password_reset(user, token)
            
            flash('An email has been sent with instructions to reset your password.', 'info')
            return redirect(url_for('login'))
        else:
            flash('There is no account with that email. Please register first.', 'warning')
            return redirect(url_for('register'))
    
    return render_template('reset_request.html', title='Reset Password', form=form, team_settings=TeamSettings.get_settings())

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    user = verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('request_reset'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user.password = hashed_password
        db.session.commit()
        
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_token.html', title='Reset Password', form=form, team_settings=TeamSettings.get_settings())

@app.route('/login', methods=['GET', 'POST'])
def login():
    from forms import LoginForm
    from models import PlayerUser, User, TeamSettings
    
    if current_user.is_authenticated:
        if hasattr(current_user, 'is_active') and not current_user.is_active:
            flash('Your account is inactive. Please contact an administrator.', 'danger')
            logout_user()
        elif isinstance(current_user, PlayerUser):
            return redirect(url_for('player_dashboard'))
        else:
            return redirect(url_for('dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        # First, try to authenticate as player user
        player_user = PlayerUser.query.filter_by(username=username).first()
        if player_user:
            if player_user.check_password(password):
                if player_user.is_active:
                    login_user(player_user, remember=form.remember_me.data)
                    player_user.last_login = datetime.utcnow()
                    db.session.commit()
                    next_page = request.args.get('next') or url_for('player_dashboard')
                    return redirect(next_page)
                else:
                    flash('Your account is inactive. Please contact an administrator.', 'danger')
            else:
                flash('Invalid username or password', 'danger')
            return render_template('login.html', form=form, team_settings=TeamSettings.get_settings())
        
        # If player login fails, try to authenticate as admin user
        admin_user = User.query.filter_by(username=username).first()
        if admin_user and admin_user.check_password(password):
            if getattr(admin_user, 'is_active', True):  # Default to True if is_active doesn't exist
                login_user(admin_user, remember=form.remember_me.data)
                next_page = request.args.get('next') or url_for('dashboard')
                return redirect(next_page)
            else:
                flash('Your account is inactive. Please contact an administrator.', 'danger')
        else:
            flash('Invalid username or password', 'danger')
    
    # If GET request or form validation failed, show login form
    return render_template('login.html', form=form, team_settings=TeamSettings.get_settings())

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        # Validate CSRF token
        from flask_wtf.csrf import validate_csrf
        try:
            validate_csrf(request.form.get('csrf_token'))
        except Exception as csrf_error:
            app.logger.error(f"CSRF validation failed: {csrf_error}")
            flash('Security token expired. Please try again.', 'error')
            return redirect(url_for('register'))
        
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'danger')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
            
        # Create new user
        user = User(username=username, email=email, role='user')
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Settings Routes
@app.route('/settings')
@login_required
def settings():
    team_settings = TeamSettings.get_settings()
    return render_template('settings.html', 
                         team_settings=team_settings,
                         now=datetime.utcnow())

@app.route('/settings/update', methods=['POST'])
@login_required
def update_settings():
    # Validate CSRF token
    from flask_wtf.csrf import validate_csrf
    try:
        validate_csrf(request.form.get('csrf_token'))
    except Exception as csrf_error:
        app.logger.error(f"CSRF validation failed: {csrf_error}")
        flash('Security token expired. Please try again.', 'error')
        return redirect(url_for('settings'))
    
    try:
        app.logger.info('Starting settings update...')
        team_settings = TeamSettings.get_settings()
        if not team_settings:
            app.logger.error('No team settings found')
            flash('Team settings not found. Please contact support.', 'danger')
            return redirect(url_for('settings'))
        
        app.logger.info(f'Current settings: {team_settings.__dict__}')
        
        # Update basic info
        try:
            team_settings.team_name = request.form.get('team_name', team_settings.team_name)
            team_settings.contact_email = request.form.get('contact_email', team_settings.contact_email)
            team_settings.contact_phone = request.form.get('contact_phone', team_settings.contact_phone)
            team_settings.address = request.form.get('address', team_settings.address)
            
            # Handle founded_year with validation
            founded_year = request.form.get('founded_year', team_settings.founded_year)
            if founded_year:
                try:
                    team_settings.founded_year = int(founded_year)
                except (ValueError, TypeError):
                    app.logger.warning(f'Invalid founded_year: {founded_year}')
                    team_settings.founded_year = 2020  # Default value
            
            team_settings.about = request.form.get('about', team_settings.about)
            
            # Update colors with validation
            primary_color = request.form.get('primary_color')
            if primary_color and primary_color.startswith('#'):
                team_settings.primary_color = primary_color
                
            secondary_color = request.form.get('secondary_color')
            if secondary_color and secondary_color.startswith('#'):
                team_settings.secondary_color = secondary_color
            
            app.logger.info('Processing logo upload...')
            # Handle logo upload
            if 'logo' in request.files:
                logo = request.files['logo']
                if logo and logo.filename != '':
                    if not allowed_file(logo.filename):
                        app.logger.warning(f'Invalid file type: {logo.filename}')
                        flash('Invalid file type. Please upload an image file (PNG, JPG, JPEG, GIF).', 'warning')
                    else:
                        # Create uploads directory if it doesn't exist
                        upload_dir = os.path.join(app.root_path, 'static', 'uploads')
                        os.makedirs(upload_dir, exist_ok=True)
                        app.logger.info(f'Upload directory: {upload_dir}')
                        
                        # Generate a unique filename
                        file_ext = os.path.splitext(logo.filename)[1].lower()
                        filename = f"logo_{uuid.uuid4().hex}{file_ext}"
                        logo_path = os.path.join('uploads', filename)
                        full_path = os.path.join(app.root_path, 'static', logo_path)
                        
                        app.logger.info(f'Saving logo to: {full_path}')
                        logo.save(full_path)
                        
                        # Verify file was saved
                        if not os.path.exists(full_path):
                            app.logger.error(f'Failed to save logo to {full_path}')
                            flash('Failed to save logo. Please try again.', 'danger')
                        else:
                            # Delete old logo if it's not the default one
                            if team_settings.logo_url and team_settings.logo_url != 'img/logo.png':
                                old_logo_path = os.path.join(app.root_path, 'static', team_settings.logo_url)
                                if os.path.exists(old_logo_path):
                                    try:
                                        os.remove(old_logo_path)
                                        app.logger.info(f'Removed old logo: {old_logo_path}')
                                    except Exception as e:
                                        app.logger.error(f'Error deleting old logo: {e}', exc_info=True)
                            
                            team_settings.logo_url = logo_path.replace('\\', '/')
                            app.logger.info(f'Logo updated to: {team_settings.logo_url}')
            
            app.logger.info('Committing changes to database...')
            db.session.commit()
            app.logger.info('Settings updated successfully')
            
            # Update the team settings in the context processor
            if hasattr(g, 'team_settings'):
                g.team_settings = team_settings
            
            flash('Settings updated successfully!', 'success')
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error updating settings: {str(e)}', exc_info=True)
            flash(f'Error updating settings: {str(e)}', 'danger')
            
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Unexpected error in update_settings: {str(e)}', exc_info=True)
        flash('An unexpected error occurred. Please try again.', 'danger')
    
    return redirect(url_for('settings'))

import os
from werkzeug.utils import secure_filename
from flask import jsonify, url_for
import uuid

# Allowed file extensions for uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
UPLOAD_FOLDER = os.path.join('static', 'uploads', 'ckeditor')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# CKEditor Image Upload
@app.route('/upload_image', methods=['POST'])
@login_required
def upload_image():
    """Handle image uploads from CKEditor"""
    # Check if the post request has the file part
    if 'upload' not in request.files:
        return jsonify({
            'error': {
                'message': 'No file part in the request.'
            }
        }), 400

    file = request.files['upload']
    
    # If user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return jsonify({
            'error': {
                'message': 'No selected file.'
            }
        }), 400

    if file and allowed_file(file.filename):
        # Create upload folder if it doesn't exist
        upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'ckeditor')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save the file
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        # Get the URL to the uploaded file
        file_url = url_for('static', filename=f'uploads/ckeditor/{filename}')
        
        # Return the URL to the uploaded file
        return jsonify({
            'url': file_url
        })
    
    return jsonify({
        'error': {
            'message': 'File type not allowed. Allowed types are: ' + ', '.join(ALLOWED_EXTENSIONS)
        }
    }), 400

# Legal Pages
@app.route('/privacy-policy')
def privacy_policy():
    team_settings = TeamSettings.get_settings()
    return render_template('privacy_policy.html', 
                         team_settings=team_settings,
                         now=datetime.utcnow())

@app.route('/terms-of-service')
def terms_of_service():
    team_settings = TeamSettings.query.first()
    return render_template('terms_of_service.html', 
                         team_settings=team_settings,
                         now=datetime.utcnow())

# Main Routes
@app.route('/')
def index():
    # Get player statistics
    total_players = Player.query.filter_by(is_active=True).count()
    
    # Get top scorers (limit to 5)
    top_scorers = db.session.query(
        Player, 
        PlayerStats.goals
    ).join(Player.stats).filter(
        Player.is_active == True
    ).order_by(
        PlayerStats.goals.desc()
    ).limit(5).all()
    
    # Calculate total goals
    total_goals = db.session.query(db.func.sum(PlayerStats.goals)).scalar() or 0
    
    # Get recent matches (last 5)
    recent_matches = Match.query.order_by(Match.match_date.desc()).limit(5).all()
    
    # Get upcoming matches (next 5)
    upcoming_matches = Match.query.filter(
        Match.match_date >= datetime.utcnow()
    ).order_by(Match.match_date.asc()).limit(5).all()
    
    # Get team settings for the site
    team_settings = TeamSettings.get_settings()
    
    # Calculate win/loss/draw stats
    total_matches = Match.query.filter(Match.status == 'completed').count()
    wins = 0
    if total_matches > 0:
        wins = Match.query.filter(
            ((Match.home_goals > Match.away_goals) & (Match.venue == 'home')) |
            ((Match.home_goals < Match.away_goals) & (Match.venue == 'away')),
            Match.status == 'completed'
        ).count()
    
    win_percentage = round((wins / total_matches * 100), 1) if total_matches > 0 else 0
    
    return render_template(
        'index.html',
        total_players=total_players,
        top_scorers=top_scorers,
        total_goals=total_goals,
        recent_matches=recent_matches,
        upcoming_matches=upcoming_matches,
        team_settings=team_settings,
        total_matches=total_matches,
        wins=wins,
        win_percentage=win_percentage
    )

@app.route('/about')
def about():
    team_settings = TeamSettings.query.first()
    return render_template('about.html', team_settings=team_settings)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    team_settings = TeamSettings.query.first()
    if request.method == 'POST':
        # Validate CSRF token
        from flask_wtf.csrf import validate_csrf
        try:
            validate_csrf(request.form.get('csrf_token'))
        except Exception as csrf_error:
            app.logger.error(f"CSRF validation failed: {csrf_error}")
            flash('Security token expired. Please try again.', 'error')
            return redirect(url_for('contact'))
        
        # Here you can add code to handle the contact form submission
        # For example, send an email or save to database
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # For now, just flash a success message
        flash('Your message has been sent! We will get back to you soon.', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html', team_settings=team_settings)

@app.route('/finances')
@login_required
def finances():
    # Get current month and year for monthly calculations
    team_settings = TeamSettings.query.first()
    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year
    now = datetime.utcnow()
    current_month = now.month
    current_year = now.year
    
    # Calculate monthly revenue, expenses, and profit
    monthly_revenue = db.session.query(db.func.sum(FinancialRecord.amount)).filter(
        FinancialRecord.transaction_type == 'income',
        db.extract('month', FinancialRecord.transaction_date) == current_month,
        db.extract('year', FinancialRecord.transaction_date) == current_year
    ).scalar() or 0
    
    monthly_expenses = db.session.query(db.func.sum(FinancialRecord.amount)).filter(
        FinancialRecord.transaction_type == 'expense',
        db.extract('month', FinancialRecord.transaction_date) == current_month,
        db.extract('year', FinancialRecord.transaction_date) == current_year
    ).scalar() or 0
    
    # Calculate annual figures (last 12 months)
    one_year_ago = now.replace(year=now.year-1) if now.month == 12 else now.replace(year=now.year-1, month=now.month+1)
    
    annual_revenue = db.session.query(db.func.sum(FinancialRecord.amount)).filter(
        FinancialRecord.transaction_type == 'income',
        FinancialRecord.transaction_date >= one_year_ago
    ).scalar() or 0
    
    annual_expenses = db.session.query(db.func.sum(FinancialRecord.amount)).filter(
        FinancialRecord.transaction_type == 'expense',
        FinancialRecord.transaction_date >= one_year_ago
    ).scalar() or 0
    
    # Calculate profit
    monthly_profit = monthly_revenue - monthly_expenses
    annual_profit = annual_revenue - annual_expenses
    
    # Get recent transactions
    recent_transactions = FinancialRecord.query.order_by(FinancialRecord.transaction_date.desc()).limit(10).all()
    
    # Format data for template
    financial_data = {
        'revenue': {
            'monthly': monthly_revenue,
            'annual': annual_revenue,
            'trend': 'up',  # This would be calculated based on previous period
            'change_percent': 12.5  # This would be calculated
        },
        'expenses': {
            'monthly': monthly_expenses,
            'annual': annual_expenses,
            'trend': 'down',  # This would be calculated
            'change_percent': 5.2  # This would be calculated
        },
        'profit': {
            'monthly': monthly_profit,
            'annual': annual_profit,
            'trend': 'up' if monthly_profit > 0 else 'down',
            'change_percent': 25.8  # This would be calculated
        },
        'transactions': [{
            'id': t.id,
            'date': t.transaction_date.strftime('%Y-%m-%d'),
            'description': t.description,
            'amount': t.amount if t.transaction_type == 'income' else -t.amount,
            'type': t.transaction_type,
            'category': t.category
        } for t in recent_transactions]
    }
    
    return render_template('finances.html', financial_data=financial_data)

@app.route('/transaction/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        # Validate CSRF token
        from flask_wtf.csrf import validate_csrf
        try:
            validate_csrf(request.form.get('csrf_token'))
        except Exception as csrf_error:
            app.logger.error(f"CSRF validation failed: {csrf_error}")
            flash('Security token expired. Please try again.', 'error')
            return redirect(url_for('add_transaction'))
        
        try:
            # Get form data
            description = request.form.get('description')
            amount = float(request.form.get('amount'))
            transaction_type = request.form.get('transaction_type')
            category = request.form.get('category')
            transaction_date = datetime.strptime(request.form.get('transaction_date'), '%Y-%m-%d')
            
            # Create new transaction
            transaction = FinancialRecord(
                description=description,
                amount=amount if transaction_type == 'income' else abs(amount),
                transaction_type=transaction_type,
                category=category,
                transaction_date=transaction_date
            )
            
            db.session.add(transaction)
            db.session.commit()
            flash('Transaction added successfully!', 'success')
            return redirect(url_for('finances'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding transaction: {str(e)}', 'danger')
    
    # Pass datetime and current time to the template context
    return render_template('add_transaction.html', 
                         datetime=datetime, 
                         now=datetime.utcnow())

@app.route('/transaction/<int:transaction_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    transaction = FinancialRecord.query.get_or_404(transaction_id)
    
    if request.method == 'POST':
        # Validate CSRF token
        from flask_wtf.csrf import validate_csrf
        try:
            validate_csrf(request.form.get('csrf_token'))
        except Exception as csrf_error:
            app.logger.error(f"CSRF validation failed: {csrf_error}")
            flash('Security token expired. Please try again.', 'error')
            return redirect(url_for('edit_transaction', transaction_id=transaction_id))
        
        try:
            # Update transaction data
            transaction.description = request.form.get('description')
            transaction.amount = float(request.form.get('amount'))
            transaction.transaction_type = request.form.get('transaction_type')
            transaction.category = request.form.get('category')
            transaction.transaction_date = datetime.strptime(request.form.get('transaction_date'), '%Y-%m-%d')
            
            db.session.commit()
            flash('Transaction updated successfully!', 'success')
            return redirect(url_for('finances'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating transaction: {str(e)}', 'danger')
    
    # Pass transaction, datetime, and current time to the template context
    return render_template('edit_transaction.html', 
                         transaction=transaction, 
                         datetime=datetime,
                         now=datetime.utcnow())

@app.route('/transaction/<int:transaction_id>/delete', methods=['POST'])
@login_required
def delete_transaction(transaction_id):
    # Validate CSRF token
    from flask_wtf.csrf import validate_csrf
    try:
        validate_csrf(request.form.get('csrf_token'))
    except Exception as csrf_error:
        app.logger.error(f"CSRF validation failed: {csrf_error}")
        flash('Security token expired. Please try again.', 'error')
        return redirect(url_for('finances'))
    
    transaction = FinancialRecord.query.get_or_404(transaction_id)
    
    try:
        db.session.delete(transaction)
        db.session.commit()
        flash('Transaction deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting transaction: {str(e)}', 'danger')
    
    return redirect(url_for('finances'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get upcoming matches (next 3 matches)
    current_date = datetime.utcnow().date()
    upcoming_matches = Match.query.filter(
        Match.match_date >= current_date
    ).order_by(Match.match_date.asc()).limit(3).all()
    
    # Player statistics
    total_players = Player.query.count()
    active_players = Player.query.filter_by(is_active=True).count()
    
    # Get players by position
    players_by_position = db.session.query(
        Player.position,
        db.func.count(Player.id).label('count')
    ).group_by(Player.position).all()
    
    # Get top scorers with their stats
    from models import PlayerStats
    top_scorers_data = db.session.query(
        Player,
        PlayerStats
    ).join(
        PlayerStats,
        Player.id == PlayerStats.player_id
    ).order_by(
        PlayerStats.goals.desc()
    ).limit(5).all()
    
    # Create a list of player objects with stats attached
    top_scorers = []
    for player, stats in top_scorers_data:
        player.stats = stats  # Attach stats to player object
        top_scorers.append(player)
    
    # Get recent players with their stats
    recent_players_data = db.session.query(
        Player,
        PlayerStats
    ).outerjoin(
        PlayerStats,
        Player.id == PlayerStats.player_id
    ).order_by(
        Player.join_date.desc()
    ).limit(5).all()
    
    # Create a list of player objects with stats attached
    recent_players = []
    for player, stats in recent_players_data:
        player.stats = stats or PlayerStats(goals=0, assists=0)  # Default stats if none exists
        recent_players.append(player)
    
    # Match statistics
    now = datetime.utcnow()
    
    # Upcoming matches (next 30 days)
    upcoming_matches = Match.query.filter(
        Match.match_date >= now,
        Match.match_date <= now + timedelta(days=30)
    ).order_by(Match.match_date.asc()).limit(5).all()
    
    # Recent matches (last 30 days)
    recent_matches = Match.query.filter(
        Match.match_date < now,
        Match.match_date >= now - timedelta(days=30)
    ).order_by(Match.match_date.desc()).limit(5).all()
    
    # Calculate win/loss/draw for recent matches
    match_results = {'wins': 0, 'losses': 0, 'draws': 0}
    for match in recent_matches:
        if match.home_goals > match.away_goals:
            match_results['wins'] += 1
        elif match.home_goals < match.away_goals:
            match_results['losses'] += 1
        else:
            match_results['draws'] += 1
            
    # Get team settings
    team_settings = TeamSettings.query.first()
    
    # If no team settings exist, initialize default settings
    if not team_settings:
        init_team_settings()
        team_settings = TeamSettings.query.first()
    
    # Calculate total goals
    total_goals = sum(player.stats.goals for player in Player.query.all() if player.stats)
    
    # Get upcoming training sessions
    from models import TrainingSession
    upcoming_trainings = TrainingSession.query.filter(
        TrainingSession.session_date >= now
    ).order_by(TrainingSession.session_date.asc()).limit(5).all()
    
    # Get current time for the template
    now = datetime.utcnow()
    
    return render_template(
        'dashboard.html',
        total_players=total_players,
        active_players=active_players,
        position_counts=dict(players_by_position),
        top_scorers=top_scorers,
        recent_players=recent_players,
        upcoming_matches=upcoming_matches,
        recent_matches=recent_matches,
        match_results=match_results,
        total_goals=total_goals,
        upcoming_trainings=upcoming_trainings,
        now=now,
        timedelta=timedelta,
        team_settings=team_settings
    )

# Match Routes
@app.route('/matches')
@login_required
def matches():
    # Get query parameters for filtering
    status = request.args.get('status', '')
    competition = request.args.get('competition', '')
    
    # Base query
    query = Match.query
    
    # Apply filters
    if status:
        query = query.filter(Match.status == status)
    if competition:
        query = query.filter(Match.competition.ilike(f'%{competition}%'))
    
    # Order by match date
    matches = query.order_by(Match.match_date.desc()).all()
    
    # Get unique competitions for filter dropdown
    competitions = db.session.query(Match.competition).distinct().all()
    competitions = [c[0] for c in competitions if c[0]]  # Flatten and remove None
    
    # Get team settings for displaying home team info
    team_settings = TeamSettings.get_settings()
    
    # Create form instance for CSRF protection
    form = DeleteMatchForm()
    
    return render_template(
        'matches.html',
        matches=matches,
        status=status,
        competition=competition,
        competitions=competitions,
        team_settings=team_settings,
        form=form  # Pass the form to the template
    )

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'webpm'}

@app.route('/uploads/teams/<path:filename>')
def uploaded_team_logo(filename):
    """Serve uploaded team logos"""
    try:
        # Sanitize the filename to prevent directory traversal
        safe_filename = secure_filename(os.path.basename(filename))
        if not safe_filename:
            return "Invalid filename", 400
            
        uploads_dir = os.path.join(app.root_path, 'static', 'uploads', 'teams')
        filepath = os.path.join(uploads_dir, safe_filename)
        
        # Check if file exists and is within the uploads directory
        if not os.path.isfile(filepath) or not filepath.startswith(os.path.abspath(uploads_dir)):
            current_app.logger.warning(f"Logo not found or invalid path: {safe_filename}")
            return "Logo not found", 404
            
        return send_from_directory(uploads_dir, safe_filename, as_attachment=False)
        
    except Exception as e:
        current_app.logger.error(f"Error serving team logo: {str(e)}", exc_info=True)
        return "Error serving logo", 500

def save_team_logo(file, opponent_name):
    if not file or file.filename == '':
        return None
        
    if not allowed_file(file.filename):
        current_app.logger.warning(f"Invalid file type: {file.filename}")
        return None
        
    try:
        # Create a secure filename
        timestamp = int(datetime.now().timestamp())
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        safe_opponent_name = secure_filename(opponent_name.replace(' ', '_'))
        filename = f"{safe_opponent_name}_{timestamp}.{file_ext}"
        
        # Define the upload directory and ensure it exists
        upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'teams')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save the file
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        current_app.logger.info(f"Saved team logo to: {filepath}")
        
        # Return the relative path to the static folder
        return f"uploads/teams/{filename}"
        
    except Exception as e:
        current_app.logger.error(f"Error saving team logo: {str(e)}", exc_info=True)
        return None

class MatchForm(FlaskForm):
    """Form for adding and editing matches with CSRF protection"""
    opponent = StringField('Opponent', [validators.DataRequired()])
    match_date = DateTimeField('Match Date', format='%Y-%m-%dT%H:%M', validators=[validators.DataRequired()])
    venue = StringField('Venue', [validators.DataRequired()])
    is_home = BooleanField('Home Match', default=True, 
                          description='Check if this is a home match, uncheck for away match')
    competition = StringField('Competition')
    status = SelectField('Status', 
                        choices=[
                            ('scheduled', 'Scheduled'),
                            ('ongoing', 'Ongoing'),
                            ('completed', 'Completed'),
                            ('postponed', 'Postponed')
                        ], 
                        default='scheduled')

@app.route('/matches/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_match():
    form = MatchForm()
    
    if form.validate_on_submit():
        try:
            # Handle file upload for opponent logo if provided
            opponent_logo = request.files.get('opponent_logo')
            logo_filename = None
            if opponent_logo and opponent_logo.filename != '' and allowed_file(opponent_logo.filename):
                logo_filename = save_team_logo(opponent_logo, form.opponent.data)
            
            # Create new match
            match = Match(
                opponent=form.opponent.data,
                match_date=form.match_date.data,
                venue=form.venue.data,
                is_home=form.is_home.data,
                competition=form.competition.data,
                status=form.status.data,
                opponent_logo=logo_filename
            )
            
            db.session.add(match)
            db.session.commit()
            flash('Match added successfully!', 'success')
            return redirect(url_for('matches'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding match: {str(e)}")
            flash('An error occurred while adding the match. Please try again.', 'danger')
    
    # Get unique competitions for datalist
    competitions = db.session.query(Match.competition).distinct().filter(Match.competition.isnot(None)).all()
    competitions = [comp[0] for comp in competitions]
    
    return render_template('add_match.html', form=form, competitions=competitions)

@app.route('/matches/<int:match_id>')
@login_required
def view_match(match_id):
    match = Match.query.get_or_404(match_id)
    team_settings = TeamSettings.query.first()
    return render_template('view_match.html', 
                         match=match, 
                         team_settings=team_settings)

@app.route('/matches/<int:match_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_match(match_id):
    match = Match.query.get_or_404(match_id)
    
    if request.method == 'POST':
        try:
            # Update match data
            match.opponent = request.form.get('opponent', match.opponent)
            match.match_date = datetime.strptime(request.form.get('match_date'), '%Y-%m-%dT%H:%M')
            match.venue = request.form.get('venue', match.venue)
            match.is_home = 'is_home' in request.form  # Check if the checkbox is checked
            match.competition = request.form.get('competition', match.competition)
            match.status = request.form.get('status', match.status)
            match.home_goals = int(request.form.get('home_goals', match.home_goals or 0))
            match.away_goals = int(request.form.get('away_goals', match.away_goals or 0))
            match.match_report = request.form.get('match_report', match.match_report)
            
            # Handle file upload
            if 'opponent_logo' in request.files:
                file = request.files['opponent_logo']
                if file.filename != '':
                    # Delete old logo if it exists
                    if match.opponent_logo:
                        try:
                            old_logo_path = os.path.join('static', match.opponent_logo)
                            if os.path.exists(old_logo_path):
                                os.remove(old_logo_path)
                        except Exception as e:
                            print(f"Error deleting old logo: {e}")
                    
                    # Save new logo
                    opponent_logo_path = save_team_logo(file, match.opponent)
                    if opponent_logo_path:
                        match.opponent_logo = opponent_logo_path
            
            db.session.commit()
            flash('Match updated successfully!', 'success')
            return redirect(url_for('view_match', match_id=match.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating match: {str(e)}', 'danger')
    
    # Get unique competitions for datalist
    competitions = db.session.query(Match.competition).distinct().filter(Match.competition.isnot(None)).all()
    competitions = [comp[0] for comp in competitions]
    
    return render_template('edit_match.html', match=match, competitions=competitions)

class DeleteMatchForm(FlaskForm):
    """Form for deleting matches with CSRF protection"""
    pass

@app.route('/match/<int:match_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_match(match_id):
    form = DeleteMatchForm()
    
    if form.validate_on_submit():
        try:
            # Get the match or return 404 if not found
            match = Match.query.get_or_404(match_id)
            
            # Delete the match
            db.session.delete(match)
            db.session.commit()
            
            flash('Match deleted successfully!', 'success')
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting match {match_id}: {str(e)}")
            flash('An error occurred while deleting the match.', 'error')
    else:
        current_app.logger.error(f"CSRF validation failed: {form.errors}")
        flash('Invalid request. Please try again.', 'error')
    
    return redirect(url_for('matches'))

@app.route('/match/<int:match_id>/flyer')
@login_required
def match_flyer(match_id):
    try:
        match = Match.query.get_or_404(match_id)
        team_settings = TeamSettings.query.first()
        now = datetime.utcnow()
        
        # Debug information
        print(f"Match ID: {match_id}")
        print(f"Match opponent: {match.opponent}")
        print(f"Match date: {match.match_date}")
        print(f"Team settings: {team_settings}")
        
        # Validate match data
        if not match.opponent:
            flash('Match opponent information is missing.', 'error')
            return redirect(url_for('view_match', match_id=match_id))
            
        if not match.match_date:
            flash('Match date information is missing.', 'error')
            return redirect(url_for('view_match', match_id=match_id))
        
        # Create a file-like buffer to receive PDF data
        buffer = BytesIO()
        
        # Create the PDF object
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=72)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        
        # Debug: Print available styles
        print("Available styles:", list(styles.byName.keys()))
        
        # Get team colors
        primary_color = '#1a237e'  # Default blue
        if team_settings and team_settings.primary_color:
            primary_color = team_settings.primary_color
            if not primary_color.startswith('#'):
                primary_color = '#' + primary_color
        
        # Create custom styles with unique names - check if they already exist first
        if 'FlyerTitle' not in styles.byName:
            styles.add(ParagraphStyle(
                name='FlyerTitle',
                fontSize=28,
                leading=34,
                alignment=1,  # Center
                spaceAfter=20,
                textColor=colors.HexColor(primary_color),
                fontName='Helvetica-Bold'
            ))
        
        if 'FlyerSubtitle' not in styles.byName:
            styles.add(ParagraphStyle(
                name='FlyerSubtitle',
                fontSize=18,
                leading=22,
                alignment=1,
                spaceAfter=15,
                fontName='Helvetica-Bold'
            ))
        
        if 'FlyerNormalCenter' not in styles.byName:
            styles.add(ParagraphStyle(
                name='FlyerNormalCenter',
                parent=styles['Normal'],
                alignment=1,
                fontSize=12,
                spaceAfter=8
            ))
        
        if 'FlyerLargeCenter' not in styles.byName:
            styles.add(ParagraphStyle(
                name='FlyerLargeCenter',
                parent=styles['Normal'],
                alignment=1,
                fontSize=14,
                fontName='Helvetica-Bold',
                spaceAfter=12
            ))
        
        # Debug: Print styles after adding custom ones
        print("Styles after adding custom ones:", list(styles.byName.keys()))
        
        # Add header with team logo (use default if team logo not available)
        logo_added = False
        
        # Try to load team logo first
        if team_settings and team_settings.logo_url:
            try:
                # Handle different logo path formats
                logo_url = team_settings.logo_url
                
                # Remove leading slash or 'static/' if present
                if logo_url.startswith('/static/'):
                    logo_url = logo_url[8:]  # Remove '/static/'
                elif logo_url.startswith('static/'):
                    logo_url = logo_url[7:]  # Remove 'static/'
                elif logo_url.startswith('/'):
                    logo_url = logo_url[1:]  # Remove leading '/'
                
                # Construct the full path
                logo_path = os.path.join(app.root_path, 'static', logo_url)
                
                # Check if file exists and is a valid image
                if os.path.exists(logo_path) and os.path.isfile(logo_path):
                    # Check file extension
                    valid_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
                    file_ext = os.path.splitext(logo_path)[1].lower()
                    
                    if file_ext in valid_extensions:
                        try:
                            logo = ReportLabImage(logo_path, width=1.2*inch, height=1.2*inch, kind='proportional')
                            logo.hAlign = 'CENTER'
                            elements.append(logo)
                            elements.append(Spacer(1, 20))
                            logo_added = True
                        except Exception as img_error:
                            current_app.logger.warning(f"Could not create ReportLab image from {logo_path}: {img_error}")
                    else:
                        current_app.logger.warning(f"Invalid image format: {file_ext}")
                else:
                    current_app.logger.warning(f"Logo file not found: {logo_path}")
                    
            except Exception as e:
                current_app.logger.warning(f"Error processing team logo: {e}")
        
        # Use default logo if team logo wasn't loaded
        if not logo_added:
            try:
                default_logo_path = os.path.join(app.root_path, 'static', 'img', 'default-team-logo.png')
                if os.path.exists(default_logo_path):
                    logo = ReportLabImage(default_logo_path, width=1.2*inch, height=1.2*inch, kind='proportional')
                    logo.hAlign = 'CENTER'
                    elements.append(logo)
                    elements.append(Spacer(1, 20))
            except Exception as e:
                current_app.logger.warning(f"Could not load default logo: {e}")
                # Continue without logo if all else fails
        
        # Add title
        elements.append(Paragraph("MATCH FLYER", styles['FlyerTitle']))
        elements.append(Spacer(1, 20))
        
        # Add match details in a more structured way
        home_team = team_settings.team_name if team_settings else 'Home Team'
        
        # Create match info table
        match_info = [
            [Paragraph(f"<b>{home_team}</b>", styles['FlyerLargeCenter']), 
             Paragraph("<b>VS</b>", styles['FlyerLargeCenter']), 
             Paragraph(f"<b>{match.opponent}</b>", styles['FlyerLargeCenter'])]
        ]
        
        match_table = Table(match_info, colWidths=[doc.width*0.4, doc.width*0.2, doc.width*0.4])
        match_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 16),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
        ]))
        elements.append(match_table)
        elements.append(Spacer(1, 30))
        
        # Add match date and time
        match_date = match.match_date.strftime('%A, %B %d, %Y')
        match_time = match.match_date.strftime('%H:%M')
        elements.append(Paragraph(f"<b>Date:</b> {match_date}", styles['FlyerLargeCenter']))
        elements.append(Paragraph(f"<b>Time:</b> {match_time}", styles['FlyerLargeCenter']))
        
        # Add venue
        venue_text = "Home" if match.venue == 'home' else "Away"
        elements.append(Paragraph(f"<b>Venue:</b> {venue_text}", styles['FlyerLargeCenter']))
        
        # Add competition if exists
        if match.competition:
            elements.append(Paragraph(f"<b>Competition:</b> {match.competition}", styles['FlyerLargeCenter']))
        
        elements.append(Spacer(1, 40))
        
        # Add status if not scheduled
        if match.status != 'scheduled':
            status_text = match.status.upper()
            if match.status == 'completed' and match.home_goals is not None and match.away_goals is not None:
                status_text = f"FINAL SCORE: {home_team} {match.home_goals} - {match.away_goals} {match.opponent}"
            elements.append(Paragraph(f"<b>{status_text}</b>", styles['FlyerLargeCenter']))
            elements.append(Spacer(1, 20))
        
        # Add decorative line
        line_table = Table([['']], colWidths=[doc.width], rowHeights=[0.1*inch])
        line_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, -1), 2, colors.HexColor(primary_color)),
            ('LINEBELOW', (0, 0), (-1, -1), 2, colors.HexColor(primary_color)),
        ]))
        elements.append(line_table)
        elements.append(Spacer(1, 20))
        
        # Add footer
        footer = f"{home_team} • {now.year}"
        elements.append(Paragraph(footer, styles['FlyerNormalCenter']))
        
        try:
            # Build the PDF
            doc.build(elements)
            
            # File response
            buffer.seek(0)
            
            # Create a safe filename
            safe_opponent_name = "".join(c for c in match.opponent if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_opponent_name = safe_opponent_name.replace(' ', '_')
            filename = f"{safe_opponent_name}_match_flyer.pdf"
            
            return send_file(
                buffer,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            current_app.logger.error(f"Error building PDF: {error_details}")
            print(f"PDF build error: {error_details}")  # Also print to console
            flash(f'Error generating PDF: {str(e)}', 'error')
            return redirect(url_for('view_match', match_id=match_id))
            
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        current_app.logger.error(f"Error in match_flyer: {error_details}")
        print(f"Match flyer error: {error_details}")  # Also print to console for debugging
        flash(f'Error generating match flyer: {str(e)}', 'error')
        return redirect(url_for('view_match', match_id=match_id))
# Player Routes
@app.route('/players')
@login_required
def players():
    # Get query parameters for filtering
    search = request.args.get('search', '')
    position = request.args.get('position', '')
    status = request.args.get('status', '')
    
    # Start with base query
    query = Player.query
    
    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Player.first_name.ilike(search_term)) | 
            (Player.last_name.ilike(search_term)) |
            (Player.jersey_number.cast(db.String).ilike(search_term))
        )
    
    if position:
        query = query.filter(Player.position == position)
        
    if status:
        query = query.filter(Player.status == status)
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    
    # Execute query with pagination
    players_paginated = query.order_by(Player.jersey_number).paginate(page=page, per_page=10, error_out=False)
    
    # Process player photo URLs
    for player in players_paginated.items:
        if player.photo_url:
            if not player.photo_url.startswith(('http://', 'https://')):
                # Convert to use the uploaded_player_photo route
                filename = os.path.basename(player.photo_url)
                player.photo_url = url_for('uploaded_player_photo', filename=filename, _external=True)
    
    # Get total players
    total_players = Player.query.count()
    
    # Get active players
    active_players = Player.query.filter_by(is_active=True).count()
    
    # Get account statistics
    players_with_accounts = db.session.query(Player).join(PlayerUser, Player.id == PlayerUser.player_id).count()
    players_without_accounts = total_players - players_with_accounts
    
    # Get total goals
    total_goals = PlayerStats.query.with_entities(db.func.sum(PlayerStats.goals)).scalar() or 0
    
    # Get top scorers with player details
    top_scorers = db.session.query(Player, PlayerStats).join(
        PlayerStats, Player.id == PlayerStats.player_id
    ).order_by(PlayerStats.goals.desc()).limit(5).all()
    
    # Get recent matches
    recent_matches = Match.query.order_by(Match.match_date.desc()).limit(5).all()
    
    # Get positions for filter dropdown
    positions = db.session.query(Player.position).distinct().all()
    positions = [p[0] for p in positions if p[0]]
    
    return render_template('players.html',
                           players=players_paginated.items,
                           pagination=players_paginated,
                           total_players=total_players,
                           active_players=active_players,
                           players_with_accounts=players_with_accounts,
                           players_without_accounts=players_without_accounts,
                           total_goals=total_goals,
                           top_scorers=top_scorers,
                           recent_matches=recent_matches,
                           positions=positions,
                           search=search,
                           selected_position=position,
                           selected_status=status)

@app.route('/players/<int:player_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_player(player_id):
    player = Player.query.get_or_404(player_id)
    
    if request.method == 'POST':
        try:
            # Update basic info
            player.first_name = request.form.get('first_name', player.first_name)
            player.last_name = request.form.get('last_name', player.last_name)
            player.position = request.form.get('position', player.position)
            player.status = request.form.get('status', player.status)
            player.bio = request.form.get('bio', player.bio)
            
            # Update contact info
            player.email = request.form.get('email', player.email)
            player.phone = request.form.get('phone', player.phone)
            
            # Update contract info
            if request.form.get('join_date'):
                player.join_date = datetime.strptime(request.form['join_date'], '%Y-%m-%d').date()
            if request.form.get('contract_end'):
                player.contract_end = datetime.strptime(request.form['contract_end'], '%Y-%m-%d').date()
            if request.form.get('salary'):
                player.salary = float(request.form['salary'])
            
            # Handle photo upload
            if 'photo' in request.files and request.files['photo'].filename:
                photo = request.files['photo']
                if photo.filename:
                    # Delete old photo if exists
                    if player.photo_url and os.path.exists(os.path.join('static', player.photo_url)):
                        try:
                            os.remove(os.path.join('static', player.photo_url))
                        except Exception as e:
                            print(f"Error removing old photo: {e}")
                    
                    # Save new photo
                    filename = secure_filename(f"player_{player.id}_{int(datetime.utcnow().timestamp())}.{photo.filename.rsplit('.', 1)[1].lower()}")
                    upload_dir = os.path.join('static', 'uploads', 'players')
                    os.makedirs(upload_dir, exist_ok=True)
                    photo_path = os.path.join(upload_dir, filename)
                    photo.save(photo_path)
                    player.photo_url = os.path.join('uploads', 'players', filename).replace('\\', '/')
            
            # Update stats if they exist
            if player.stats:
                player.stats.matches_played = int(request.form.get('matches_played', player.stats.matches_played or 0))
                player.stats.goals = int(request.form.get('goals', player.stats.goals or 0))
                player.stats.assists = int(request.form.get('assists', player.stats.assists or 0))
                player.stats.yellow_cards = int(request.form.get('yellow_cards', player.stats.yellow_cards or 0))
                player.stats.red_cards = int(request.form.get('red_cards', player.stats.red_cards or 0))
                player.stats.clean_sheets = int(request.form.get('clean_sheets', player.stats.clean_sheets or 0))
                player.stats.minutes_played = int(request.form.get('minutes_played', player.stats.minutes_played or 0))
            
            db.session.commit()
            flash('Player updated successfully!', 'success')
            return redirect(url_for('player_profile', player_id=player.id))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error updating player: {str(e)}")
            import traceback
            traceback.print_exc()
            flash('An error occurred while updating the player. Please try again.', 'error')
    
    # For GET request or if there was an error
    positions = {
        'GK': 'Goalkeeper',
        'DF': 'Defender',
        'MF': 'Midfielder',
        'FW': 'Forward'
    }
    
    return render_template('edit_player.html', 
                         player=player,
                         positions=positions,
                         today=datetime.utcnow().date().strftime('%Y-%m-%d'))

@app.route('/players/add', methods=['GET', 'POST'])
@login_required
def add_player():
    if request.method == 'POST':
        print("Form data received:", request.form)  # Debug log
        
        # Validate CSRF token
        from flask_wtf.csrf import validate_csrf
        try:
            validate_csrf(request.form.get('csrf_token'))
        except Exception as csrf_error:
            print(f"CSRF validation failed: {csrf_error}")
            flash('Security token expired. Please try again.', 'error')
            return redirect(url_for('add_player'))
        
        try:
            # Get form data with validation
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            
            print(f"Processing player: {first_name} {last_name}")  # Debug log
            
            # Validate required fields
            if not first_name or not last_name:
                flash('First name and last name are required.', 'error')
                return redirect(url_for('add_player'))
            
            # Handle date of birth with validation
            dob_str = request.form.get('date_of_birth')
            if not dob_str:
                flash('Date of birth is required.', 'error')
                return redirect(url_for('add_player'))
            
            try:
                date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format. Please use YYYY-MM-DD format.', 'error')
                return redirect(url_for('add_player'))
            
            position = request.form.get('position')
            jersey_number_str = request.form.get('jersey_number')
            
            # Validate position and jersey number
            if not position:
                flash('Position is required.', 'error')
                return redirect(url_for('add_player'))
            
            if not jersey_number_str:
                flash('Jersey number is required.', 'error')
                return redirect(url_for('add_player'))
            
            try:
                jersey_number = int(jersey_number_str)
                if not (1 <= jersey_number <= 99):
                    raise ValueError("Jersey number must be between 1 and 99")
            except ValueError as e:
                flash('Jersey number must be a valid number between 1 and 99.', 'error')
                return redirect(url_for('add_player'))
                
            nationality = request.form.get('nationality', 'Zambia')
            status = request.form.get('status', 'active')
            bio = request.form.get('bio', '')
            
            # Contract information
            join_date_str = request.form.get('join_date')
            join_date = datetime.strptime(join_date_str, '%Y-%m-%d').date() if join_date_str else datetime.utcnow().date()
            
            contract_end = None
            contract_end_str = request.form.get('contract_end')
            if contract_end_str:
                try:
                    contract_end = datetime.strptime(contract_end_str, '%Y-%m-%d').date()
                except ValueError:
                    contract_end = None
            
            salary = None
            salary_str = request.form.get('salary')
            if salary_str and salary_str.strip():
                try:
                    salary = float(salary_str)
                    if salary < 0:
                        raise ValueError("Salary cannot be negative")
                except ValueError:
                    salary = None
            
            # Contact information
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            
            # Handle photo upload
            photo_url = None
            if 'photo' in request.files:
                photo = request.files['photo']
                if photo.filename:  # Check if a file was selected
                    try:
                        file_ext = photo.filename.rsplit('.', 1)[1].lower() if '.' in photo.filename else ''
                        if file_ext not in ['jpg', 'jpeg', 'png', 'gif']:
                            raise ValueError("Invalid file type. Only JPG, PNG, and GIF are allowed.")
                            
                        filename = secure_filename(f"{first_name}_{last_name}_{int(datetime.utcnow().timestamp())}.{file_ext}")
                        
                        # Ensure the upload directory exists
                        upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'players')
                        os.makedirs(upload_dir, exist_ok=True)
                        
                        # Save the file
                        photo_path = os.path.join(upload_dir, filename)
                        photo.save(photo_path)
                        
                        # Set the photo URL for the database - use forward slashes for web
                        photo_url = f"uploads/players/{filename}"
                        print(f"Photo saved to: {photo_url}")  # Debug log
                        
                    except Exception as upload_error:
                        print(f"Error uploading photo: {str(upload_error)}")
                        flash('Error uploading player photo. Please try again with a different image.', 'error')
                        return redirect(url_for('add_player'))
            
            # Check if jersey number is already taken
            existing_player = Player.query.filter_by(jersey_number=jersey_number).first()
            if existing_player:
                flash(f'Jersey number {jersey_number} is already taken by {existing_player.first_name} {existing_player.last_name}. Please choose a different number.', 'error')
                return redirect(url_for('add_player'))
            
            # Create new player
            player = Player(
                first_name=first_name,
                last_name=last_name,
                date_of_birth=date_of_birth,
                position=position,
                jersey_number=jersey_number,
                nationality=nationality,
                status=status,
                bio=bio,
                join_date=join_date,
                contract_end=contract_end,
                salary=salary,
                email=email,
                phone=phone,
                photo_url=photo_url,
                is_active=True
            )
            
            # Add to database
            db.session.add(player)
            db.session.commit()
            
            print(f"Player {first_name} {last_name} added successfully with ID {player.id}")  # Debug log
            flash('Player added successfully!', 'success')
            return redirect(url_for('players'))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"Error adding player: {str(e)}"
            print(error_msg)  # Debug log
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            flash('An error occurred while saving the player. Please check the form and try again.', 'error')
            return redirect(url_for('add_player'))
    
    # For GET request, render the form
    today = datetime.utcnow().date().strftime('%Y-%m-%d')
    print(f"Rendering add_player form with today's date: {today}")  # Debug log
    return render_template('add_player.html', today=today)

@app.route('/players/<int:player_id>/download')
@login_required
def download_player_pdf(player_id):
    try:
        player = Player.query.get_or_404(player_id)
        team_settings = TeamSettings.query.first()
        
        # Set default values for missing team settings
        if not team_settings:
            team_settings = type('', (), {'primary_color': '#1a237e', 'logo_url': None, 'team_name': 'Team'})()
            
        # Ensure primary_color is always a valid hex color
        primary_color = team_settings.primary_color if team_settings and team_settings.primary_color else '#1a237e'
        if not primary_color.startswith('#'):
            primary_color = '#' + primary_color
            
        # Create color objects with fallback
        try:
            primary_color_obj = colors.HexColor(primary_color)
            light_color = colors.HexColor(primary_color)
        except Exception as e:
            print(f"Error creating color objects: {e}")
            # Fallback to default colors
            primary_color = '#1a237e'  # Default blue
            primary_color_obj = colors.HexColor(primary_color)
            light_color = colors.HexColor('#1a2377')
            
        # Ensure we have valid color objects
        if not primary_color_obj:
            primary_color_obj = colors.HexColor('#1a237e')
        if not light_color:
            light_color = colors.HexColor('#1a2377')
    except Exception as e:
        print(f"Error initializing PDF data: {str(e)}")
        flash('Error initializing PDF data. Please try again.', 'error')
        return redirect(url_for('view_player', player_id=player_id))
    
    # Create a file-like buffer to receive PDF data
    buffer = BytesIO()
    
    # Create the PDF object with smaller margins for more content
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    # Container for the 'Flowable' objects
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    styles.add(ParagraphStyle(
        name='Header1',
        parent=styles['Heading1'],
        fontSize=24,
        leading=28,
        textColor=colors.HexColor(primary_color),
        spaceAfter=20,
        alignment=1  # Center
    ))
    
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.white,
        backColor=colors.HexColor(primary_color),
        leftIndent=10,
        padding=5,
        spaceAfter=10
    ))
    
    styles.add(ParagraphStyle(
        name='PlayerInfo',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        spaceAfter=12
    ))
    
    # Create header table with simplified layout
    header_data = []
    
    # Player name and basic info with safe attribute access
    player_name = f"<b>{getattr(player, 'first_name', '')} {getattr(player, 'last_name', '')}</b>"
    player_details = [
        f"<b>Position:</b> {getattr(player, 'position', 'N/A')}",
        f"<b>Jersey:</b> {getattr(player, 'jersey_number', 'N/A')}",
        f"<b>Age:</b> {getattr(player, 'age', 'N/A')}",
        f"<b>Status:</b> {'Active' if getattr(player, 'is_active', False) else 'Inactive'}"
    ]
    
    # First row: Logo, Player Name, Photo
    first_row = []
    
    # Left cell - Team logo (if exists)
    logo_cell = Paragraph("", styles['Normal'])
    # Try to load team logo first, then fallback to default
    logo_loaded = False
    
    if team_settings and getattr(team_settings, 'logo_url', None):
        try:
            # Handle different logo path formats
            logo_url = team_settings.logo_url
            
            # Remove leading slash or 'static/' if present
            if logo_url.startswith('/static/'):
                logo_url = logo_url[8:]  # Remove '/static/'
            elif logo_url.startswith('static/'):
                logo_url = logo_url[7:]  # Remove 'static/'
            elif logo_url.startswith('/'):
                logo_url = logo_url[1:]  # Remove leading '/'
            
            # Construct the full path
            logo_path = os.path.join(app.root_path, 'static', logo_url)
            
            # Check if file exists and is a valid image
            if os.path.exists(logo_path) and os.path.isfile(logo_path):
                # Check file extension
                valid_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
                file_ext = os.path.splitext(logo_path)[1].lower()
                
                if file_ext in valid_extensions:
                    try:
                        logo = Image(logo_path, width=1.2*inch, height=1.2*inch, kind='proportional')
                        logo.hAlign = 'CENTER'
                        logo_cell = logo
                        logo_loaded = True
                    except Exception as img_error:
                        print(f"Error creating ReportLab image from {logo_path}: {img_error}")
                else:
                    print(f"Invalid image format for logo: {file_ext}")
            else:
                print(f"Logo file not found: {logo_path}")
                
        except Exception as e:
            print(f"Error processing team logo: {e}")
    
    # Use default logo if team logo wasn't loaded
    if not logo_loaded:
        try:
            default_logo_path = os.path.join(app.root_path, 'static', 'img', 'default-team-logo.png')
            if os.path.exists(default_logo_path):
                logo = Image(default_logo_path, width=1.2*inch, height=1.2*inch, kind='proportional')
                logo.hAlign = 'CENTER'
                logo_cell = logo
        except Exception as e:
            print(f"Error loading default logo: {e}")
    
    # Middle cell - Player name
    name_cell = Paragraph(player_name, styles['Header1'])
    
    # Right cell - Player photo (if exists)
    photo_cell = Paragraph("", styles['Normal'])
    # Try to load player photo first, then fallback to default
    photo_loaded = False
    
    if getattr(player, 'photo_url', None):
        try:
            # Handle different photo path formats
            photo_url = player.photo_url
            
            # Remove leading slash or 'static/' if present
            if photo_url.startswith('/static/'):
                photo_url = photo_url[8:]  # Remove '/static/'
            elif photo_url.startswith('static/'):
                photo_url = photo_url[7:]  # Remove 'static/'
            elif photo_url.startswith('/'):
                photo_url = photo_url[1:]  # Remove leading '/'
            
            # Construct the full path
            img_path = os.path.join(app.root_path, 'static', photo_url)
            
            # Check if file exists and is a valid image
            if os.path.exists(img_path) and os.path.isfile(img_path):
                # Check file extension
                valid_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
                file_ext = os.path.splitext(img_path)[1].lower()
                
                if file_ext in valid_extensions:
                    try:
                        photo = Image(img_path, width=1.5*inch, height=1.8*inch, kind='proportional')
                        photo.hAlign = 'CENTER'
                        photo_cell = photo
                        photo_loaded = True
                        print(f"✅ Successfully loaded player photo: {img_path}")
                    except Exception as img_error:
                        print(f"❌ Error creating ReportLab image from {img_path}: {img_error}")
                else:
                    print(f"Invalid image format for player photo: {file_ext}")
            else:
                print(f"Player photo file not found: {img_path}")
                
        except Exception as e:
            print(f"Error processing player photo: {e}")
    
    # Use default player image if player photo wasn't loaded
    if not photo_loaded:
        try:
            default_photo_path = os.path.join(app.root_path, 'static', 'img', 'default-player.png')
            if os.path.exists(default_photo_path):
                photo = Image(default_photo_path, width=1.5*inch, height=1.8*inch, kind='proportional')
                photo.hAlign = 'CENTER'
                photo_cell = photo
                print(f"📷 Using default player photo: {default_photo_path}")
            else:
                print(f"⚠️  Default player photo not found: {default_photo_path}")
        except Exception as e:
            print(f"❌ Error loading default player photo: {e}")
            # Continue without logo if all else fails
        
        # Add first row
        first_row = [logo_cell, name_cell, photo_cell]
        
        # Second row: Player details (span all columns)
        details_cell = Paragraph('<br/>'.join(player_details), styles['PlayerInfo'])
        
        # Create the table
        col_width = doc.width / 3.0
        table_data = [first_row]  # First row with logo, name, and photo
        
        # Add second row with details cell
        table_data.append([details_cell])
        
        # Create and style the header table
        try:
            # Ensure we have a valid color object for the grid
            grid_color = primary_color_obj
            if not grid_color:
                grid_color = colors.HexColor('#1a237e')  # Default blue color
            
            header_table = Table(table_data, colWidths=[col_width]*3, rowHeights=[1.5*inch, 0.6*inch])
            header_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('SPAN', (0, 1), (2, 1)),  # Make details span all columns
                ('GRID', (0, 0), (-1, -1), 0.5, grid_color),
            ]))
            elements.append(header_table)
        except Exception as e:
            print(f"Error creating header table: {e}")
            # Fallback to a simpler table without grid if there's an error
            try:
                header_table = Table(table_data, colWidths=[col_width]*3, rowHeights=[1.5*inch, 0.6*inch])
                header_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                    ('SPAN', (0, 1), (2, 1)),  # Make details span all columns
                ]))
                elements.append(header_table)
            except Exception as e2:
                print(f"Error in fallback header table: {e2}")
                # If all else fails, just add the player name
                elements.append(Paragraph(player_name, styles['Header1']))
    
    # Add a simple horizontal line using a table with a bottom border
    try:
        # Ensure we have a valid color object for the line
        line_color = primary_color_obj if primary_color_obj else colors.HexColor('#1a237e')
        
        line_table = Table([['']], colWidths=[doc.width], rowHeights=0.1*inch)
        line_table.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, -1), 1, line_color),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        elements.append(line_table)
    except Exception as e:
        print(f"Error creating line: {e}")
        try:
            # Try a simpler line without color
            elements.append(Spacer(1, 0.1*inch))
            elements.append(HRFlowable(width="100%", thickness=1, lineCap='round', 
                                     color=colors.HexColor('#1a237e'), 
                                     spaceBefore=10, spaceAfter=15))
        except:
            # Fallback to simple spacer if all else fails
            elements.append(Spacer(1, 15))
    
    # Player Details Section
    try:
        # Ensure we have a valid background color
        bg_color = colors.HexColor(primary_color if primary_color else '#1a237e')
        
        details_style = TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), bg_color),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey)
        ])
    except Exception as e:
        print(f"Error creating details style: {e}")
        # Fallback to a simpler style without background color
        details_style = TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey)
        ])
    
    # Player details data with safe attribute access
    def safe_get_date(date_attr):
        try:
            if not hasattr(player, date_attr) or not getattr(player, date_attr):
                return 'N/A'
            date_val = getattr(player, date_attr)
            if not date_val:
                return 'N/A'
            if hasattr(date_val, 'strftime'):
                return date_val.strftime('%B %d, %Y')
            return str(date_val)
        except Exception as e:
            print(f"Error getting date {date_attr}: {e}")
            return 'N/A'
    
    def safe_get_attr(attr, default='N/A'):
        try:
            if not hasattr(player, attr):
                return default
            val = getattr(player, attr)
            return str(val) if val is not None else default
        except Exception as e:
            print(f"Error getting attribute {attr}: {e}")
            return default
    
    def safe_get_numeric(attr, unit='', default='N/A'):
        try:
            if not hasattr(player, attr) or getattr(player, attr) is None:
                return default
            val = getattr(player, attr)
            if val is None:
                return default
            if isinstance(val, (int, float)):
                return f"{val} {unit}".strip()
            return str(val)
        except Exception as e:
            print(f"Error getting numeric {attr}: {e}")
            return default
    
    # Build details data with safe attribute access
    details_data = [
        ['Date of Birth', safe_get_date('date_of_birth')],
        ['Nationality', safe_get_attr('nationality')],
        ['Height', safe_get_numeric('height', 'cm')],
        ['Weight', safe_get_numeric('weight', 'kg')],
        ['Preferred Foot', safe_get_attr('preferred_foot')],
        ['Joined Date', safe_get_date('joined_date')],
        ['Email', safe_get_attr('email')],
        ['Phone', safe_get_attr('phone')]
    ]
    
    # Remove any fields that are 'N/A' if you want to hide empty fields
    details_data = [row for row in details_data if row[1] != 'N/A']
    
    # Create details table with error handling
    try:
        if not details_data or len(details_data) == 0:
            print("Warning: No player details data available")
            details_data = [['No details available', '']]
            
        details_table = Table(details_data, colWidths=[doc.width*0.3, doc.width*0.7])
        details_table.setStyle(details_style)
        
        # Add section header
        elements.append(Paragraph('PLAYER DETAILS', styles['SectionHeader']))
        elements.append(details_table)
        elements.append(Spacer(1, 20))
    except Exception as e:
        print(f"Error creating details table: {e}")
        # Add a simple error message if table creation fails
        elements.append(Paragraph('PLAYER DETAILS', styles['SectionHeader']))
        elements.append(Paragraph('Error loading player details. Some information may be missing.', styles['Normal']))
        elements.append(Spacer(1, 20))
    
    # Skills/Attributes Section (if available)
    try:
        if hasattr(player, 'skills') and player.skills:
            elements.append(Paragraph('PLAYER SKILLS', styles['SectionHeader']))
            
            # Define skill categories
            skill_categories = {
                'Technical': ['Dribbling', 'Passing', 'Shooting', 'Tackling', 'Heading'],
                'Physical': ['Pace', 'Stamina', 'Strength', 'Agility'],
                'Mental': ['Vision', 'Positioning', 'Teamwork', 'Decision Making']
            }
            
            # Create a table for skills
            skill_data = []
            
            for category, skills in skill_categories.items():
                try:
                    row = [Paragraph(f"<b>{category}</b>", styles['Normal'])]
                    for skill in skills:
                        try:
                            skill_attr = skill.lower().replace(' ', '_')
                            if hasattr(player.skills, skill_attr):
                                skill_value = getattr(player.skills, skill_attr, 0)
                                # Ensure skill_value is a number
                                skill_value = int(skill_value) if skill_value is not None and str(skill_value).isdigit() else 0
                                row.append(Paragraph(f"{skill}: {skill_value}/10", styles['Normal']))
                            else:
                                row.append(Paragraph(f"{skill}: N/A", styles['Normal']))
                        except Exception as e:
                            print(f"Error processing skill {skill}: {e}")
                            row.append(Paragraph(f"{skill}: N/A", styles['Normal']))
                    
                    if len(row) > 1:  # Only add if we have at least one skill
                        skill_data.append(row)
                except Exception as e:
                    print(f"Error processing category {category}: {e}")
            
            if skill_data:  # Only create table if we have data
                try:
                    # Calculate column widths
                    num_cols = max(len(row) for row in skill_data) if skill_data else 1
                    col_width = doc.width * 0.8 / (num_cols - 1) if num_cols > 1 else doc.width * 0.8
                    col_widths = [doc.width * 0.2] + [col_width] * (num_cols - 1)
                    
                    skills_table = Table(skill_data, colWidths=col_widths)
                    
                    # Create table style with safe color handling
                    try:
                        bg_color = colors.HexColor(primary_color if primary_color else '#1a237e')
                        table_style = [
                            ('BACKGROUND', (0, 0), (-1, 0), bg_color),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, -1), 9),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey)
                        ]
                        
                        try:
                            skills_table.setStyle(TableStyle(table_style))
                            elements.append(skills_table)
                            elements.append(Spacer(1, 20))
                        except Exception as e:
                            print(f"Error applying table style: {e}")
                            # Add a simple fallback if styling fails
                            elements.append(Paragraph('Skills information could not be displayed in table format.', styles['Normal']))
                    except Exception as e:
                        print(f"Error creating skills table style: {e}")
                        elements.append(Paragraph('Skills information could not be displayed.', styles['Normal']))
                except Exception as e:
                    print(f"Error creating skills table: {e}")
                    elements.append(Paragraph('Error loading skills information.', styles['Normal']))
    except Exception as e:
        print(f"Error in skills section: {e}")
        # Continue with the rest of the PDF generation even if skills section fails
    
    # Player Statistics Section
    if hasattr(player, 'stats') and player.stats:
        elements.append(Paragraph('SEASON STATISTICS', styles['SectionHeader']))
        
        # Helper function to safely get stat values
        def get_stat(stat_name, default=0):
            stat = getattr(player.stats, stat_name, None)
            return default if stat is None else stat
            
        # Main stats with safe attribute access and default values
        main_stats = [
            ['Matches Played', get_stat('matches_played')],
            ['Goals', get_stat('goals')],
            ['Assists', get_stat('assists')],
            ['Yellow Cards', get_stat('yellow_cards')],
            ['Red Cards', get_stat('red_cards')],
            ['Minutes Played', f"{get_stat('minutes_played')}'"]
        ]
        
        # Additional stats if available
        additional_stats = []
        
        # Safely get all stats with defaults
        clean_sheets = get_stat('clean_sheets')
        matches_played = get_stat('matches_played', 0)
        goals = get_stat('goals', 0)
        assists = get_stat('assists', 0)
        
        # Add clean sheets if available
        if clean_sheets is not None:
            additional_stats.append(['Clean Sheets', clean_sheets])
            
        # Calculate per-match statistics if player has played matches
        if matches_played > 0:
            additional_stats.extend([
                ['Goals per Match', f"{goals / matches_played:.2f}"],
                ['Assists per Match', f"{assists / matches_played:.2f}"]
            ])
        
        # Add other stats with safe attribute access
        def safe_get_attr(attr, default=0, is_percentage=False):
            try:
                value = getattr(player.stats, attr, default) or default
                if is_percentage and value is not None:
                    return f"{value}%"
                return value
            except:
                return default
                
        # Add additional stats with safe attribute access
        additional_stats.extend([
            ['Saves', safe_get_attr('saves', 0)],
            ['Tackles Won', safe_get_attr('tackles_won', 0, hasattr(player.stats, 'tackle_success_rate'))],
            ['Pass Accuracy', safe_get_attr('pass_accuracy', 0, True)],
            ['Shots on Target', safe_get_attr('shots_on_target', 0)],
            ['Fouls Committed', safe_get_attr('fouls_committed', 0)],
            ['Fouls Suffered', safe_get_attr('fouls_suffered', 0)]
        ])
        
        # Filter out any None values that might have slipped through
        additional_stats = [[k, v] for k, v in additional_stats if v is not None]
        
        # Combine all stats
        all_stats = main_stats + additional_stats
        
        # Create two columns for stats
        col1 = all_stats[:len(all_stats)//2 + len(all_stats)%2]
        col2 = all_stats[len(all_stats)//2 + len(all_stats)%2:]
        
        # Create stats tables
        stats_style = TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTWEIGHT', (0, 0), (0, -1), 'Bold'),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor(primary_color)),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey)
        ])
        
        # Create tables for each column
        stats_tables = []
        for col in [col1, col2]:
            if col:  # Only create table if column has data
                t = Table(col, colWidths=[doc.width*0.3, doc.width*0.2])
                t.setStyle(stats_style)
                stats_tables.append(t)
        
        # Add stats tables side by side
        if len(stats_tables) > 0:
            stats_combined = Table([[stats_tables[0], Spacer(10, 10), stats_tables[1] if len(stats_tables) > 1 else '']], 
                                 colWidths=[doc.width*0.5, 10, doc.width*0.5])
            elements.append(stats_combined)
            elements.append(Spacer(1, 20))
    
    # Add a notes section
    if hasattr(player, 'notes') and player.notes:
        elements.append(Paragraph('COACHES NOTES', styles['SectionHeader']))
        notes_style = ParagraphStyle(
            'Notes',
            parent=styles['Normal'],
            backColor=colors.HexColor('#f8f9fa'),
            borderWidth=1,
            borderColor=colors.lightgrey,
            borderPadding=10,
            leading=14
        )
        notes = Paragraph(player.notes, notes_style)
        elements.append(notes)
        elements.append(Spacer(1, 20))
    
    # Add footer with page number and generation info
    def add_page_number(canvas, doc, primary_color='#1a237e'):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        page_num = canvas.getPageNumber()
        text = f"Page {page_num} • Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        canvas.drawRightString(doc.width + doc.rightMargin, 0.4*inch, text)
        
        # Add a small colored line above the footer
        try:
            color = colors.HexColor(primary_color) if isinstance(primary_color, str) else primary_color
            canvas.setStrokeColor(color)
            canvas.setLineWidth(0.5)
            canvas.line(doc.leftMargin, 0.5*inch, doc.width + doc.leftMargin, 0.5*inch)
        except Exception as e:
            print(f"Error setting footer line color: {e}")
            # Fallback to default color
            canvas.setStrokeColor(colors.HexColor('#1a237e'))
            canvas.setLineWidth(0.5)
            canvas.line(doc.leftMargin, 0.5*inch, doc.width + doc.leftMargin, 0.5*inch)
        
        canvas.restoreState()
    
    try:
        # Build the PDF with the footer function
        def on_first_page(canvas, doc):
            return add_page_number(canvas, doc, primary_color)
            
        def on_later_pages(canvas, doc):
            return add_page_number(canvas, doc, primary_color)
            
        doc.build(elements, onFirstPage=on_first_page, onLaterPages=on_later_pages)
        
        # File response
        buffer.seek(0)
        response = make_response(buffer.getvalue())
        response.mimetype = 'application/pdf'
        filename = f"{getattr(player, 'last_name', 'player').lower()}_{getattr(player, 'first_name', 'profile').lower()}.pdf"
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        return response
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error generating PDF: {error_details}")
        app.logger.error(f"PDF Generation Error: {error_details}")
        flash(f'Error generating PDF: {str(e)}. Please check the logs for more details.', 'error')
        return redirect(url_for('view_player', player_id=player_id))

@app.route('/players/<int:player_id>', methods=['GET'])
@login_required
def view_player(player_id):
    player = Player.query.get_or_404(player_id)
    
    # Ensure the player has stats
    if not hasattr(player, 'stats') or player.stats is None:
        player.stats = PlayerStats()
        db.session.add(player)
        db.session.commit()
    
    return render_template('view_player.html', player=player)

@app.route('/players/<int:player_id>/delete', methods=['POST'])
@login_required
def delete_player(player_id):
    player = Player.query.get_or_404(player_id)
    
    try:
        # Check if player has an associated user account
        player_user = PlayerUser.query.filter_by(player_id=player_id).first()
        
        if player_user:
            # Delete the player user account first
            db.session.delete(player_user)
            message = f'Player account for {player.full_name} was also deleted.'
            if request.accept_mimetypes.accept_json:
                pass  # We'll include this in the JSON response
            else:
                flash(message, 'info')
        
        # Delete player photo if exists
        if player.photo_url and os.path.exists(os.path.join('static', player.photo_url)):
            try:
                os.remove(os.path.join('static', player.photo_url))
            except Exception as e:
                print(f"Error deleting player photo: {e}")
        
        # Delete the player
        db.session.delete(player)
        db.session.commit()
        
        if request.accept_mimetypes.accept_json:
            return jsonify({
                'success': True,
                'message': 'Player deleted successfully!',
                'player_id': player_id
            })
            
        flash('Player deleted successfully!', 'success')
        return redirect(url_for('players'))
        
    except Exception as e:
        db.session.rollback()
        error_msg = f'Error deleting player: {str(e)}'
        if request.accept_mimetypes.accept_json:
            return jsonify({
                'success': False,
                'message': error_msg
            }), 500
        flash(error_msg, 'danger')
        return redirect(url_for('view_player', player_id=player_id))
    return redirect(url_for('players'))
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = current_user
    
    if request.method == 'POST':
        # Validate CSRF token
        from flask_wtf.csrf import validate_csrf
        try:
            validate_csrf(request.form.get('csrf_token'))
        except Exception as csrf_error:
            app.logger.error(f"CSRF validation failed: {csrf_error}")
            flash('Security token expired. Please try again.', 'error')
            return redirect(url_for('profile'))
        
        # Update user information
        if 'update_profile' in request.form:
            new_username = request.form.get('username')
            new_email = request.form.get('email')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            
            # Check if username is already taken by another user
            if new_username != user.username and User.query.filter_by(username=new_username).first():
                flash('Username already taken. Please choose a different one.', 'danger')
                return redirect(url_for('profile'))
                
            # Check if email is already used by another user
            if new_email != user.email and User.query.filter_by(email=new_email).first():
                flash('Email already in use. Please use a different one.', 'danger')
                return redirect(url_for('profile'))
            
            # Handle profile picture upload
            if 'profile_picture' in request.files:
                file = request.files['profile_picture']
                if file and file.filename:
                    # Delete old profile picture if it exists
                    from utils import delete_old_profile_picture, save_profile_picture
                    delete_old_profile_picture(user.profile_picture)
                    # Save new profile picture
                    profile_pic = save_profile_picture(file, user.id)
                    if profile_pic:
                        user.profile_picture = profile_pic
            
            # Update user details
            user.username = new_username
            user.email = new_email
            user.first_name = first_name
            user.last_name = last_name
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
            
        # Change password
        elif 'change_password' in request.form:
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if not user.check_password(current_password):
                flash('Current password is incorrect.', 'danger')
            elif new_password != confirm_password:
                flash('New passwords do not match.', 'danger')
            elif len(new_password) < 8:
                flash('Password must be at least 8 characters long.', 'danger')
            else:
                user.set_password(new_password)
                db.session.commit()
                flash('Password updated successfully!', 'success')
            
            return redirect(url_for('profile'))
    
    return render_template('profile.html', user=user, team_settings=TeamSettings.get_settings())

# Player Dashboard Routes
@app.route('/player/login', methods=['GET', 'POST'])
def player_login():
    # Redirect all player login requests to the unified login page
    return redirect(url_for('login'))

@app.route('/player/dashboard')
@player_required
def player_dashboard():
    
    # Get recent news (last 5)
    recent_news = News.query.filter_by(is_published=True).order_by(News.created_at.desc()).limit(5).all()
    
    # Get upcoming training sessions (next 7 days)
    upcoming_trainings = TrainingSession.query.filter(
        TrainingSession.session_date >= datetime.utcnow(),
        TrainingSession.session_date <= datetime.utcnow() + timedelta(days=7)
    ).order_by(TrainingSession.session_date.asc()).all()
    
    # Get upcoming matches (next 3)
    upcoming_matches = Match.query.filter(
        Match.match_date >= datetime.utcnow()
    ).order_by(Match.match_date.asc()).limit(3).all()
    
    # Get player's recent attendance
    player_attendance = PlayerAttendance.query.filter_by(
        player_id=current_user.player_id
    ).join(TrainingSession).order_by(TrainingSession.session_date.desc()).limit(5).all()
    
    return render_template('player/dashboard.html',
                         recent_news=recent_news,
                         upcoming_trainings=upcoming_trainings,
                         upcoming_matches=upcoming_matches,
                         player_attendance=player_attendance,
                         player=current_user.player)

@app.route('/player/staff')
@player_required
def player_staff():
    """Display staff members to players"""
    staff_members = Staff.query.filter_by(is_active=True).order_by(Staff.role, Staff.last_name).all()
    
    # Process staff members to ensure photo URLs are properly formatted
    for staff in staff_members:
        if staff.photo_url:
            if staff.photo_url.startswith(('http://', 'https://')):
                # Keep external URLs as is
                continue
            elif staff.photo_url.startswith(('static/', '/static/')):
                # Convert static paths to use the uploaded_staff_photo route
                filename = os.path.basename(staff.photo_url)
                staff.photo_url = url_for('uploaded_staff_photo', filename=filename, _external=True)
            else:
                # Handle filenames without path
                staff.photo_url = url_for('uploaded_staff_photo', filename=staff.photo_url, _external=True)
    
    # Group staff by role
    staff_by_role = {}
    for staff in staff_members:
        if staff.role not in staff_by_role:
            staff_by_role[staff.role] = []
        staff_by_role[staff.role].append(staff)
    
    # Get team settings for the template
    team_settings = TeamSettings.get_settings()
    
    return render_template('player/staff.html', 
                         staff_by_role=staff_by_role,
                         team_settings=team_settings,
                         staff_members=staff_members)

@app.route('/player/news')
@player_required
def player_news():
    
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    
    query = News.query.filter_by(is_published=True)
    if category:
        query = query.filter_by(category=category)
    
    news = query.order_by(News.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    # Get categories for filter
    categories = db.session.query(News.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template('player/news.html', news=news, categories=categories, selected_category=category)

@app.route('/player/squad')
@player_required
def player_squad():
    
    # Get all active players grouped by position, ordered by jersey number
    goalkeepers = Player.query.filter_by(is_active=True, position='GK').order_by(Player.jersey_number.asc(), Player.last_name.asc(), Player.first_name.asc()).all()
    defenders = Player.query.filter(Player.is_active == True, Player.position.in_(['CB', 'LB', 'RB', 'DF'])).order_by(Player.jersey_number.asc(), Player.last_name.asc(), Player.first_name.asc()).all()
    midfielders = Player.query.filter(Player.is_active == True, Player.position.in_(['CDM', 'CM', 'CAM', 'LM', 'RM', 'MF'])).order_by(Player.jersey_number.asc(), Player.last_name.asc(), Player.first_name.asc()).all()
    forwards = Player.query.filter(Player.is_active == True, Player.position.in_(['LW', 'RW', 'CF', 'ST', 'FW'])).order_by(Player.jersey_number.asc(), Player.last_name.asc(), Player.first_name.asc()).all()
    
    return render_template('player/squad.html',
                         goalkeepers=goalkeepers,
                         defenders=defenders,
                         midfielders=midfielders,
                         forwards=forwards)

# Training Session Form
class TrainingSessionForm(FlaskForm):
    title = StringField('Title', [validators.DataRequired()])
    description = TextAreaField('Description')
    session_date = DateTimeField('Session Date & Time', format='%Y-%m-%dT%H:%M', validators=[validators.DataRequired()])
    duration = StringField('Duration (minutes)', [validators.DataRequired()])
    location = StringField('Location', [validators.DataRequired()])
    status = SelectField('Status', choices=[
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ])
    submit = SubmitField('Save')

# Admin Training Management
@app.route('/admin/trainings')
@login_required
@admin_required
def manage_trainings():
    # Get filter parameters
    status = request.args.get('status', 'all')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Build query
    query = TrainingSession.query
    
    # Apply filters
    if status != 'all':
        query = query.filter(TrainingSession.status == status)
    
    if date_from:
        query = query.filter(TrainingSession.session_date >= datetime.strptime(date_from, '%Y-%m-%d'))
    
    if date_to:
        next_day = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(TrainingSession.session_date < next_day)
    
    # Get paginated results
    page = request.args.get('page', 1, type=int)
    per_page = 10
    trainings = query.order_by(TrainingSession.session_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    # Get attendance stats for each training
    for training in trainings.items:
        training.attendance_count = PlayerAttendance.query.filter_by(
            training_session_id=training.id,
            status='present'
        ).count()
        training.total_players = Player.query.filter_by(is_active=True).count()
    
    return render_template('admin/manage_trainings.html', 
                         trainings=trainings,
                         status=status,
                         date_from=date_from,
                         date_to=date_to)

@app.route('/admin/trainings/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_training():
    form = TrainingSessionForm()
    
    if form.validate_on_submit():
        try:
            training = TrainingSession(
                title=form.title.data,
                description=form.description.data,
                session_date=form.session_date.data,
                duration=form.duration.data,
                location=form.location.data,
                status=form.status.data
            )
            db.session.add(training)
            db.session.commit()
            
            flash('Training session added successfully!', 'success')
            return redirect(url_for('manage_trainings'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding training session: {str(e)}', 'danger')
    
    return render_template('admin/training_form.html', form=form, title='Add Training Session')

@app.route('/admin/trainings/<int:training_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_training(training_id):
    training = TrainingSession.query.get_or_404(training_id)
    form = TrainingSessionForm(obj=training)
    
    if form.validate_on_submit():
        try:
            training.title = form.title.data
            training.description = form.description.data
            training.session_date = form.session_date.data
            training.duration = form.duration.data
            training.location = form.location.data
            training.status = form.status.data
            
            db.session.commit()
            flash('Training session updated successfully!', 'success')
            return redirect(url_for('manage_trainings'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating training session: {str(e)}', 'danger')
    
    return render_template('admin/training_form.html', form=form, title='Edit Training Session')

@app.route('/admin/trainings/<int:training_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_training(training_id):
    training = TrainingSession.query.get_or_404(training_id)
    
    try:
        # Delete associated attendance records
        PlayerAttendance.query.filter_by(training_session_id=training_id).delete()
        
        # Delete the training session
        db.session.delete(training)
        db.session.commit()
        
        flash('Training session deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting training session: {str(e)}', 'danger')
    
    return redirect(url_for('manage_trainings'))

@app.route('/admin/trainings/<int:training_id>/attendance')
@login_required
@admin_required
def training_attendance(training_id):
    training = TrainingSession.query.get_or_404(training_id)
    
    # Get all active players
    players = Player.query.filter_by(is_active=True).order_by(Player.last_name).all()
    
    # Get attendance records for this session
    attendance_records = {}
    for record in PlayerAttendance.query.filter_by(training_session_id=training_id).all():
        attendance_records[record.player_id] = record.status
    
    # Add players without attendance records
    for player in players:
        if player.id not in attendance_records:
            attendance_records[player.id] = 'not_recorded'
    
    return render_template('admin/training_attendance.html',
                         training=training,
                         players=players,
                         attendance_records=attendance_records)

@app.route('/admin/trainings/<int:training_id>/attendance/update', methods=['POST'])
@login_required
@admin_required
def update_attendance(training_id):
    training = TrainingSession.get_or_404(training_id)
    
    try:
        # Process attendance updates
        for player_id, status in request.form.items():
            if player_id.startswith('player_'):
                player_id = int(player_id.replace('player_', ''))
                
                # Find or create attendance record
                attendance = PlayerAttendance.query.filter_by(
                    training_session_id=training_id,
                    player_id=player_id
                ).first()
                
                if not attendance and status != 'not_recorded':
                    attendance = PlayerAttendance(
                        training_session_id=training_id,
                        player_id=player_id,
                        status=status,
                        recorded_by=current_user.id
                    )
                    db.session.add(attendance)
                elif attendance and status == 'not_recorded':
                    db.session.delete(attendance)
                elif attendance:
                    attendance.status = status
                    attendance.recorded_by = current_user.id
                    attendance.recorded_at = datetime.utcnow()
        
        db.session.commit()
        flash('Attendance updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating attendance: {str(e)}', 'danger')
    
    return redirect(url_for('training_attendance', training_id=training_id))

@app.route('/admin/trainings/export')
@login_required
@admin_required
def export_training_data():
    # Get filter parameters
    status = request.args.get('status', 'all')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Build query
    query = TrainingSession.query
    
    # Apply filters
    if status != 'all':
        query = query.filter(TrainingSession.status == status)
    
    if date_from:
        query = query.filter(TrainingSession.session_date >= datetime.strptime(date_from, '%Y-%m-%d'))
    
    if date_to:
        next_day = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(TrainingSession.session_date < next_day)
    
    # Get all matching trainings
    trainings = query.order_by(TrainingSession.session_date).all()
    
    # Generate CSV
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Title', 'Date', 'Time', 'Duration', 'Location', 'Status',
        'Total Players', 'Present', 'Absent', 'Excused', 'Attendance %'
    ])
    
    # Write data
    for training in trainings:
        # Get attendance stats
        attendance = db.session.query(
            PlayerAttendance.status,
            db.func.count(PlayerAttendance.id).label('count')
        ).filter(
            PlayerAttendance.training_session_id == training.id
        ).group_by(PlayerAttendance.status).all()
        
        attendance_dict = {status: count for status, count in attendance}
        total_players = Player.query.filter_by(is_active=True).count()
        present = attendance_dict.get('present', 0)
        attendance_pct = (present / total_players * 100) if total_players > 0 else 0
        
        writer.writerow([
            training.title,
            training.session_date.strftime('%Y-%m-%d'),
            training.session_date.strftime('%H:%M'),
            f"{training.duration} mins",
            training.location,
            training.status.title(),
            total_players,
            present,
            attendance_dict.get('absent', 0),
            attendance_dict.get('excused', 0),
            f"{attendance_pct:.1f}%"
        ])
    
    # Create response
    output.seek(0)
    date_str = datetime.now().strftime('%Y%m%d')
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=training_attendance_{date_str}.csv"}
    )

# Player Training View
@app.route('/player/training')
@login_required
def player_training():
    from models import PlayerUser, User
    
    # Check if user is admin
    is_admin = hasattr(current_user, 'role') and current_user.role == 'admin'
    
    # Check permissions
    if not (isinstance(current_user, PlayerUser) or is_admin):
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Check if player account is active (only for PlayerUser)
    if isinstance(current_user, PlayerUser) and not current_user.is_active:
        flash('Your player account is currently inactive. Please contact an administrator.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get upcoming training sessions
    upcoming_sessions = TrainingSession.query.filter(
        TrainingSession.session_date >= datetime.utcnow()
    ).order_by(TrainingSession.session_date.asc()).all()
    
    # Get past training sessions
    if is_admin:
        # For admin, get all past sessions with all attendances
        past_sessions = db.session.query(TrainingSession, PlayerAttendance).outerjoin(
            PlayerAttendance,
            (PlayerAttendance.training_session_id == TrainingSession.id)
        ).filter(
            TrainingSession.session_date < datetime.utcnow()
        ).order_by(TrainingSession.session_date.desc()).limit(10).all()
    else:
        # For players, only get their own attendances
        past_sessions = db.session.query(TrainingSession, PlayerAttendance).outerjoin(
            PlayerAttendance,
            (PlayerAttendance.training_session_id == TrainingSession.id) &
            (PlayerAttendance.player_id == current_user.player_id)
        ).filter(
            TrainingSession.session_date < datetime.utcnow()
        ).order_by(TrainingSession.session_date.desc()).limit(10).all()
    
    return render_template('player/training.html',
                         upcoming_sessions=upcoming_sessions,
                         past_sessions=past_sessions,
                         is_admin=is_admin)

@app.route('/player/profile')
@player_required
def player_profile():
    from datetime import date
    player = current_user.player
    
    # Process player photo URL
    if player.photo_url:
        if not player.photo_url.startswith(('http://', 'https://')):
            # Convert to use the uploaded_player_photo route
            filename = os.path.basename(player.photo_url)
            player.photo_url = url_for('uploaded_player_photo', filename=filename, _external=True)
    
    return render_template('player/profile.html', 
                         player=player,
                         today=date.today())

@app.route('/player/logout')
@login_required
def player_logout():
    logout_user()
    return redirect(url_for('login'))

# Admin News Management Routes

@app.route('/admin/news')
@login_required
@admin_required
def admin_news():
    """Admin view for managing news articles"""
    page = request.args.get('page', 1, type=int)
    query = News.query
    
    # Filter by status if provided
    status = request.args.get('status', '')
    if status == 'published':
        query = query.filter_by(is_published=True)
    elif status == 'draft':
        query = query.filter_by(is_published=False)
    
    # Search functionality
    search = request.args.get('search', '')
    if search:
        search = f"%{search}%"
        query = query.filter(News.title.ilike(search) | News.content.ilike(search))
    
    # Get categories for filter
    categories = db.session.query(News.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    # Paginate results
    news = query.order_by(News.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('admin/news/list.html', 
                         news=news, 
                         categories=categories,
                         status=status,
                         search=search)

@app.route('/admin/news/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_news():
    """Create a new news article"""
    form = NewsForm()
    
    if form.validate_on_submit():
        # Handle image upload
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                upload_folder = os.path.join(app.root_path, 'static', 'uploads', 'news')
                os.makedirs(upload_folder, exist_ok=True)
                file.save(os.path.join(upload_folder, filename))
                image_url = f"uploads/news/{filename}"
        
        # Create news article
        news = News(
            title=form.title.data,
            content=form.content.data,
            summary=form.summary.data,
            category=form.category.data,
            is_published=form.is_published.data,
            is_featured=form.is_featured.data,
            image_url=image_url,
            author_id=current_user.id
        )
        
        db.session.add(news)
        db.session.commit()
        
        flash('News article created successfully!', 'success')
        return redirect(url_for('admin_news'))
    
    # Pass current datetime to the template
    return render_template('admin/news/form.html', 
                         form=form, 
                         news=None, 
                         now=datetime.utcnow(),
                         form_action=url_for('new_news'))

@app.route('/admin/news/<int:news_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_news(news_id):
    """Edit an existing news article"""
    news = News.query.get_or_404(news_id)
    form = NewsForm(obj=news)
    
    if form.validate_on_submit():
        # Handle image upload
        if 'image' in request.files and request.files['image'].filename:
            file = request.files['image']
            if file and file.filename:
                # Delete old image if exists
                if news.image_url:
                    try:
                        old_image_path = os.path.join(app.root_path, 'static', news.image_url)
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                    except Exception as e:
                        current_app.logger.error(f"Error deleting old image: {e}")
                
                # Save new image
                filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                upload_folder = os.path.join(app.root_path, 'static', 'uploads', 'news')
                os.makedirs(upload_folder, exist_ok=True)
                file.save(os.path.join(upload_folder, filename))
                news.image_url = f"uploads/news/{filename}"
        
        # Update news article
        form.populate_obj(news)
        news.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('News article updated successfully!', 'success')
        return redirect(url_for('admin_news'))
    
    # Pass current datetime to the template
    return render_template('admin/news/form.html', 
                         form=form, 
                         news=news, 
                         now=datetime.utcnow(),
                         form_action=url_for('edit_news', news_id=news.id))

@app.route('/admin/news/<int:news_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_news(news_id):
    """Delete a news article"""
    news = News.query.get_or_404(news_id)
    
    # Delete associated image if exists
    if news.image_url:
        try:
            image_path = os.path.join(app.root_path, 'static', news.image_url)
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            current_app.logger.error(f"Error deleting news image: {e}")
    
    db.session.delete(news)
    db.session.commit()
    
    flash('News article deleted successfully!', 'success')
    return redirect(url_for('admin_news'))

@app.route('/admin/news/<int:news_id>/toggle-publish', methods=['POST'])
@login_required
@admin_required
def toggle_publish_news(news_id):
    """Toggle publish status of a news article"""
    news = News.query.get_or_404(news_id)
    news.is_published = not news.is_published
    news.updated_at = datetime.utcnow()
    db.session.commit()
    
    status = 'published' if news.is_published else 'unpublished'
    flash(f'News article {status} successfully!', 'success')
    return redirect(request.referrer or url_for('admin_news'))

# Admin routes for managing player accounts
@app.route('/admin/player-accounts')
@login_required
@admin_required
def admin_player_accounts():
    # Get all players with their account status
    players_with_accounts = db.session.query(Player, PlayerUser).outerjoin(
        PlayerUser, Player.id == PlayerUser.player_id
    ).filter(Player.is_active == True).all()
    
    return render_template('admin/player_accounts.html', players_with_accounts=players_with_accounts)

@app.route('/admin/create-player-account/<int:player_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def create_player_account(player_id):
    player = Player.query.get_or_404(player_id)
    
    # Check if account already exists
    existing_account = PlayerUser.query.filter_by(player_id=player_id).first()
    if existing_account:
        flash('Player account already exists!', 'warning')
        return redirect(url_for('admin_player_accounts'))
    
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            email = request.form.get('email')
            
            # Validate inputs
            if not username or not password:
                flash('Username and password are required!', 'danger')
                return render_template('admin/create_player_account.html', player=player)
            
            # Check if username already exists
            if PlayerUser.query.filter_by(username=username).first():
                flash('Username already exists! Please choose a different one.', 'danger')
                return render_template('admin/create_player_account.html', player=player)
            
            # Create player account
            player_user = PlayerUser(
                player_id=player_id,
                username=username,
                email=email or f"{username}@zambiafc.com"
            )
            player_user.set_password(password)
            
            db.session.add(player_user)
            db.session.commit()
            
            flash(f'Player account created successfully! Username: {username}', 'success')
            return redirect(url_for('admin_player_accounts'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating player account: {str(e)}', 'danger')
    
    # Generate suggested username and password
    suggested_username = f"{player.first_name.lower()}.{player.last_name.lower()}"
    suggested_password = f"{player.first_name.lower()}{player.jersey_number}"
    
    return render_template('admin/create_player_account.html', 
                         player=player,
                         suggested_username=suggested_username,
                         suggested_password=suggested_password)

from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SelectField, validators

class EditPlayerAccountForm(FlaskForm):
    username = StringField('Username', [validators.DataRequired()])
    email = StringField('Email')
    new_password = PasswordField('New Password')
    is_active = BooleanField('Account is active', false_values=(False, 'false', 0, '0'))

class RequestResetForm(FlaskForm):
    email = StringField('Email', [validators.DataRequired(), validators.Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', [validators.DataRequired()])
    confirm_password = PasswordField('Confirm New Password', 
                                   [validators.DataRequired(), 
                                    validators.EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Reset Password')

# CSRF protection is already initialized at the top of the file

@app.route('/admin/edit-player-account/<int:player_user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_player_account(player_user_id):
    player_user = PlayerUser.query.get_or_404(player_user_id)
    
    if request.method == 'POST':
        # Manually create form with request.form to get the CSRF token
        form = EditPlayerAccountForm(request.form)
        
        # Manually validate CSRF token
        try:
            from flask_wtf.csrf import validate_csrf
            validate_csrf(request.form.get('csrf_token'))
        except Exception as e:
            flash('The form could not be submitted. Please try again.', 'danger')
            return redirect(url_for('edit_player_account', player_user_id=player_user_id))
        
        if form.validate():
            try:
                # Check if username already exists (excluding current user)
                existing_user = PlayerUser.query.filter(
                    PlayerUser.username == form.username.data,
                    PlayerUser.id != player_user_id
                ).first()
                
                if existing_user:
                    flash('Username already exists! Please choose a different one.', 'danger')
                    return render_template('admin/edit_player_account.html', 
                                        player_user=player_user, 
                                        form=form)
                
                # Update player account
                player_user.username = form.username.data
                player_user.email = form.email.data or f"{form.username.data}@zambiafc.com"
                player_user.is_active = form.is_active.data
                
                # Update password if provided
                if form.new_password.data:
                    player_user.set_password(form.new_password.data)
                    flash_message = f'Player account updated successfully! New password: {form.new_password.data}'
                else:
                    flash_message = 'Player account updated successfully!'
                
                db.session.commit()
                flash(flash_message, 'success')
                return redirect(url_for('admin_player_accounts'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating player account: {str(e)}', 'danger')
        else:
            # Form validation failed
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{getattr(form, field).label.text}: {error}", 'danger')
    else:
        # GET request - create form with current data
        form = EditPlayerAccountForm(
            username=player_user.username,
            email=player_user.email,
            is_active=player_user.is_active
        )
    
    return render_template('admin/edit_player_account.html', 
                         player_user=player_user, 
                         form=form)

@app.route('/admin/delete-player-account/<int:player_user_id>', methods=['POST'])
@login_required
@admin_required
def delete_player_account(player_user_id):
    player_user = PlayerUser.query.get_or_404(player_user_id)
    player_name = player_user.player.full_name
    
    try:
        db.session.delete(player_user)
        db.session.commit()
        flash(f'Player account for {player_name} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting player account: {str(e)}', 'danger')
    
    return redirect(url_for('admin_player_accounts'))

@app.route('/admin/reset-player-password/<int:player_user_id>', methods=['POST'])
@login_required
@admin_required
def reset_player_password(player_user_id):
    player_user = PlayerUser.query.get_or_404(player_user_id)
    
    try:
        # Generate new password
        new_password = f"{player_user.player.first_name.lower()}{player_user.player.jersey_number}"
        player_user.set_password(new_password)
        
        db.session.commit()
        flash(f'Password reset successfully! New password: {new_password}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error resetting password: {str(e)}', 'danger')
    
    return redirect(url_for('admin_player_accounts'))

@app.route('/admin/bulk-create-player-accounts', methods=['POST'])
@login_required
@admin_required
def bulk_create_player_accounts():
    try:
        # Get all players without accounts
        players_without_accounts = db.session.query(Player).outerjoin(
            PlayerUser, Player.id == PlayerUser.player_id
        ).filter(
            PlayerUser.id.is_(None),
            Player.is_active == True
        ).all()
        
        created_accounts = []
        
        for player in players_without_accounts:
            # Generate username and password
            username = f"{player.first_name.lower()}.{player.last_name.lower()}"
            temp_password = f"{player.first_name.lower()}{player.jersey_number}"
            
            # Check if username already exists and make it unique
            counter = 1
            original_username = username
            while PlayerUser.query.filter_by(username=username).first():
                username = f"{original_username}{counter}"
                counter += 1
            
            # Create player account
            player_user = PlayerUser(
                player_id=player.id,
                username=username,
                email=player.email or f"{username}@zambiafc.com"
            )
            player_user.set_password(temp_password)
            
            db.session.add(player_user)
            created_accounts.append({
                'name': player.full_name,
                'username': username,
                'password': temp_password
            })
        
        db.session.commit()
        
        if created_accounts:
            # Create a summary message
            account_list = ', '.join([f"{acc['name']} ({acc['username']})" for acc in created_accounts])
            flash(f'Successfully created {len(created_accounts)} player accounts: {account_list}', 'success')
        else:
            flash('No accounts to create. All active players already have accounts.', 'info')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating player accounts: {str(e)}', 'danger')
    
    return redirect(url_for('admin_player_accounts'))

@app.route('/admin/create-player-account-modal', methods=['POST'])
@login_required
@admin_required
def create_player_account_from_modal():
    try:
        player_id = request.form.get('player_id')
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        # Validate inputs
        if not player_id or not username or not password:
            flash('Player, username, and password are required!', 'danger')
            return redirect(url_for('admin_player_accounts'))
        
        # Get player
        player = Player.query.get_or_404(player_id)
        
        # Check if account already exists
        existing_account = PlayerUser.query.filter_by(player_id=player_id).first()
        if existing_account:
            flash(f'Player account for {player.full_name} already exists!', 'warning')
            return redirect(url_for('admin_player_accounts'))
        
        # Check if username already exists
        if PlayerUser.query.filter_by(username=username).first():
            flash('Username already exists! Please choose a different one.', 'danger')
            return redirect(url_for('admin_player_accounts'))
        
        # Create player account
        player_user = PlayerUser(
            player_id=player_id,
            username=username,
            email=email or f"{username}@zambiafc.com"
        )
        player_user.set_password(password)
        
        db.session.add(player_user)
        db.session.commit()
        
        flash(f'Player account created successfully for {player.full_name}! Username: {username}', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating player account: {str(e)}', 'danger')
    
    return redirect(url_for('admin_player_accounts'))

# Contract Management Routes
@app.route('/admin/contracts')
@login_required
@admin_required
def player_contracts():
    """View and manage player contracts"""
    from datetime import timedelta
    
    # Get all players with contract information
    players = Player.query.filter_by(is_active=True).order_by(Player.contract_end.asc().nullslast()).all()
    
    # Categorize players by contract status
    today = datetime.utcnow().date()
    
    expired_contracts = []
    expiring_soon = []  # Within 30 days
    expiring_3_months = []  # Within 90 days
    expiring_6_months = []  # Within 180 days
    active_contracts = []
    no_contract = []
    
    for player in players:
        if not player.contract_end:
            no_contract.append(player)
        else:
            days_remaining = (player.contract_end - today).days
            
            if days_remaining < 0:
                expired_contracts.append(player)
            elif days_remaining <= 30:
                expiring_soon.append(player)
            elif days_remaining <= 90:
                expiring_3_months.append(player)
            elif days_remaining <= 180:
                expiring_6_months.append(player)
            else:
                active_contracts.append(player)
    
    # Calculate statistics
    total_players = len(players)
    players_with_contracts = total_players - len(no_contract)
    
    return render_template('admin/player_contracts.html',
                         expired_contracts=expired_contracts,
                         expiring_soon=expiring_soon,
                         expiring_3_months=expiring_3_months,
                         expiring_6_months=expiring_6_months,
                         active_contracts=active_contracts,
                         no_contract=no_contract,
                         total_players=total_players,
                         players_with_contracts=players_with_contracts)

@app.route('/admin/export-contract-report', methods=['POST'])
@login_required
@admin_required
def export_contract_report():
    """Export complete contract report"""
    try:
        players = Player.query.filter_by(is_active=True).order_by(Player.contract_end.asc().nullslast()).all()
        
        from io import StringIO
        import csv
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Player Name', 'Jersey Number', 'Position', 'Contract Start', 'Contract End', 
            'Days Remaining', 'Contract Status', 'Salary', 'Email', 'Phone'
        ])
        
        # Write data
        for player in players:
            writer.writerow([
                player.full_name,
                player.jersey_number,
                player.position,
                player.join_date.strftime('%Y-%m-%d') if player.join_date else 'N/A',
                player.contract_end.strftime('%Y-%m-%d') if player.contract_end else 'Not Set',
                player.contract_days_remaining if player.contract_days_remaining is not None else 'N/A',
                player.contract_status_text,
                player.salary if player.salary else 'N/A',
                player.email or 'N/A',
                player.phone or 'N/A'
            ])
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=contract_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    except Exception as e:
        flash(f'Error exporting contract report: {str(e)}', 'danger')
        return redirect(url_for('player_contracts'))

@app.route('/admin/export-expiring-contracts', methods=['POST'])
@login_required
@admin_required
def export_expiring_contracts():
    """Export expiring contracts only"""
    try:
        from datetime import timedelta
        today = datetime.utcnow().date()
        
        # Get contracts expiring within 6 months or already expired
        players = Player.query.filter(
            Player.is_active == True,
            Player.contract_end.isnot(None),
            Player.contract_end <= today + timedelta(days=180)
        ).order_by(Player.contract_end.asc()).all()
        
        from io import StringIO
        import csv
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Player Name', 'Jersey Number', 'Position', 'Contract End', 
            'Days Remaining', 'Priority', 'Salary', 'Email', 'Phone'
        ])
        
        # Write data
        for player in players:
            days_remaining = player.contract_days_remaining
            
            if days_remaining < 0:
                priority = 'URGENT - Expired'
            elif days_remaining <= 30:
                priority = 'HIGH - Expiring Soon'
            elif days_remaining <= 90:
                priority = 'MEDIUM - 3 Months'
            else:
                priority = 'LOW - 6 Months'
            
            writer.writerow([
                player.full_name,
                player.jersey_number,
                player.position,
                player.contract_end.strftime('%Y-%m-%d'),
                days_remaining,
                priority,
                player.salary if player.salary else 'N/A',
                player.email or 'N/A',
                player.phone or 'N/A'
            ])
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=expiring_contracts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    except Exception as e:
        flash(f'Error exporting expiring contracts: {str(e)}', 'danger')
        return redirect(url_for('player_contracts'))

@app.route('/admin/bulk-enable-accounts', methods=['POST'])
@login_required
@admin_required
def bulk_enable_accounts():
    try:
        account_ids = request.form.getlist('account_ids')
        if not account_ids:
            flash('No accounts selected.', 'warning')
            return redirect(url_for('admin_player_accounts'))
        
        # Update selected accounts to active
        updated_count = PlayerUser.query.filter(PlayerUser.id.in_(account_ids)).update(
            {PlayerUser.is_active: True}, synchronize_session=False
        )
        
        db.session.commit()
        flash(f'Successfully enabled {updated_count} player account(s).', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error enabling accounts: {str(e)}', 'danger')
    
    return redirect(url_for('admin_player_accounts'))

@app.route('/admin/bulk-disable-accounts', methods=['POST'])
@login_required
@admin_required
def bulk_disable_accounts():
    try:
        account_ids = request.form.getlist('account_ids')
        if not account_ids:
            flash('No accounts selected.', 'warning')
            return redirect(url_for('admin_player_accounts'))
        
        # Update selected accounts to inactive
        updated_count = PlayerUser.query.filter(PlayerUser.id.in_(account_ids)).update(
            {PlayerUser.is_active: False}, synchronize_session=False
        )
        
        db.session.commit()
        flash(f'Successfully disabled {updated_count} player account(s).', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error disabling accounts: {str(e)}', 'danger')
    
    return redirect(url_for('admin_player_accounts'))

@app.route('/admin/export-player-credentials', methods=['POST'])
@login_required
@admin_required
def export_player_credentials():
    try:
        account_ids = request.form.getlist('account_ids')
        if not account_ids:
            flash('No accounts selected.', 'warning')
            return redirect(url_for('admin_player_accounts'))
        
        # Get selected player accounts with player info
        player_accounts = db.session.query(PlayerUser, Player).join(
            Player, PlayerUser.player_id == Player.id
        ).filter(PlayerUser.id.in_(account_ids)).all()
        
        if not player_accounts:
            flash('No valid accounts found.', 'warning')
            return redirect(url_for('admin_player_accounts'))
        
        # Create CSV content
        from io import StringIO
        import csv
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Player Name', 'Jersey Number', 'Position', 'Username', 'Email', 'Account Status', 'Last Login'])
        
        # Write data
        for player_user, player in player_accounts:
            writer.writerow([
                player.full_name,
                player.jersey_number,
                player.position,
                player_user.username,
                player_user.email,
                'Active' if player_user.is_active else 'Disabled',
                player_user.last_login.strftime('%Y-%m-%d %H:%M') if player_user.last_login else 'Never'
            ])
        
        # Create response
        from flask import make_response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=player_credentials_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    except Exception as e:
        flash(f'Error exporting credentials: {str(e)}', 'danger')
        return redirect(url_for('admin_player_accounts'))

@app.route('/admin/export-all-player-credentials', methods=['POST'])
@login_required
@admin_required
def export_all_player_credentials():
    try:
        # Get all player accounts with player info
        player_accounts = db.session.query(PlayerUser, Player).join(
            Player, PlayerUser.player_id == Player.id
        ).order_by(Player.jersey_number).all()
        
        return generate_credentials_csv(player_accounts, 'all_player_credentials')
        
    except Exception as e:
        flash(f'Error exporting all credentials: {str(e)}', 'danger')
        return redirect(url_for('admin_player_accounts'))

@app.route('/admin/export-active-player-credentials', methods=['POST'])
@login_required
@admin_required
def export_active_player_credentials():
    try:
        # Get active player accounts with player info
        player_accounts = db.session.query(PlayerUser, Player).join(
            Player, PlayerUser.player_id == Player.id
        ).filter(PlayerUser.is_active == True).order_by(Player.jersey_number).all()
        
        return generate_credentials_csv(player_accounts, 'active_player_credentials')
        
    except Exception as e:
        flash(f'Error exporting active credentials: {str(e)}', 'danger')
        return redirect(url_for('admin_player_accounts'))

def generate_credentials_csv(player_accounts, filename_prefix):
    """Helper function to generate CSV for player credentials"""
    from io import StringIO
    import csv
    
    if not player_accounts:
        flash('No accounts found to export.', 'warning')
        return redirect(url_for('admin_player_accounts'))
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Player Name', 'Jersey Number', 'Position', 'Username', 'Email', 
        'Account Status', 'Created Date', 'Last Login', 'Login URL'
    ])
    
    # Write data
    for player_user, player in player_accounts:
        writer.writerow([
            player.full_name,
            player.jersey_number,
            player.position,
            player_user.username,
            player_user.email,
            'Active' if player_user.is_active else 'Disabled',
            player_user.created_at.strftime('%Y-%m-%d') if player_user.created_at else 'N/A',
            player_user.last_login.strftime('%Y-%m-%d %H:%M') if player_user.last_login else 'Never',
            request.url_root + 'auth'
        ])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename={filename_prefix}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    return response

# Unauthorized access handler
@app.route('/unauthorized')
def unauthorized():
    return render_template('errors/403.html'), 403

@app.route('/test-email')
def test_email():
    try:
        msg = Message(
            'Test Email from FCMS',
            recipients=['recipient@example.com'],  # Replace with your test email
            body='This is a test email from your FCMS application.',
            html='<h1>Test Email</h1><p>This is a test email from your FCMS application.</p>'
        )
        mail.send(msg)
        return 'Test email sent successfully! Check your email (including spam folder).'
    except Exception as e:
        return f'Error sending email: {str(e)}'

# Debug route to check user status (remove in production)
@app.route('/debug/user-status')
@login_required
def debug_user_status():
    user_info = {
        'is_authenticated': current_user.is_authenticated,
        'user_id': current_user.id if current_user.is_authenticated else None,
        'username': current_user.username if current_user.is_authenticated else None,
        'email': current_user.email if current_user.is_authenticated else None,
        'role': getattr(current_user, 'role', None) if current_user.is_authenticated else None,
        'is_admin': hasattr(current_user, 'is_admin') and current_user.is_admin if current_user.is_authenticated else False,
        'is_player': hasattr(current_user, 'is_player') and current_user.is_player if current_user.is_authenticated else False,
        'is_staff': hasattr(current_user, 'is_staff') and current_user.is_staff if current_user.is_authenticated else False
    }
    return jsonify(user_info)

# Debug route to list all users (remove in production)
@app.route('/debug/all-users')
def debug_all_users():
    users = User.query.all()
    player_users = PlayerUser.query.all()
    
    return jsonify({
        'regular_users': [{
            'id': u.id,
            'username': u.username,
            'role': u.role,
            'email': u.email
        } for u in users],
        'player_users': [{
            'id': pu.id,
            'username': pu.username,
            'email': pu.email,
            'is_active': pu.is_active,
            'player_name': pu.player.full_name if pu.player else 'N/A'
        } for pu in player_users]
    })

@app.route('/uploads/players/<filename>')
def uploaded_player_photo(filename):
    # First try the static/uploads/players directory (new location)
    upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'players')
    if os.path.exists(os.path.join(upload_dir, filename)):
        return send_from_directory(upload_dir, filename)
    
    # Fall back to the old location (uploads/players) for backward compatibility
    old_upload_dir = os.path.join(app.root_path, 'uploads', 'players')
    if os.path.exists(old_upload_dir):
        return send_from_directory(old_upload_dir, filename)
    
    # If file not found in either location, return 404
    return "Player photo not found", 404

@app.route('/uploads/staff/<filename>')
def uploaded_staff_photo(filename):
    return send_from_directory(os.path.join(app.root_path, 'static', 'uploads', 'staff'), filename)

if __name__ == '__main__':
    with app.app_context():
        # This will create the database and tables if they don't exist
        db.create_all()
        
        # Initialize default team settings if they don't exist
        init_team_settings()
        
        # Create admin user if it doesn't exist
        from models import User
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                role='admin',
                first_name='Admin',
                last_name='User'
            )
            db.session.add(admin)
            db.session.commit()
            print("Created default admin user")
    
    # Import and register socketio event handlers
    from fans_routes import register_socketio_handlers
    register_socketio_handlers(socketio)
    
    # Initialize socketio with the app
    socketio.init_app(app, async_mode='threading')
    
    # Run the application
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
