from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os
from datetime import datetime, timedelta
import json
import uuid
from models import db, User, Player, PlayerStats, Match, Staff, TeamSettings

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///club.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Create uploads directory if it doesn't exist
os.makedirs(os.path.join(app.root_path, 'static', 'uploads'), exist_ok=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

# Routes
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
    recent_matches = Match.query.order_by(Match.date.desc()).limit(5).all()
    
    # Get upcoming matches (next 5)
    upcoming_matches = Match.query.filter(
        Match.date >= datetime.utcnow()
    ).order_by(Match.date.asc()).limit(5).all()
    
    # Get team settings for the site
    team_settings = TeamSettings.get_settings()
    
    return render_template(
        'index.html',
        total_players=total_players,
        top_scorers=top_scorers,
        total_goals=total_goals,
        recent_matches=recent_matches,
        upcoming_matches=upcoming_matches,
        team_settings=team_settings
    )

# Auth Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
            
        flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
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
    return render_template('settings.html', team_settings=team_settings)

@app.route('/settings/update', methods=['POST'])
@login_required
def update_settings():
    team_settings = TeamSettings.get_settings()
    
    # Update basic info
    team_settings.team_name = request.form.get('team_name', team_settings.team_name)
    team_settings.contact_email = request.form.get('contact_email', team_settings.contact_email)
    team_settings.contact_phone = request.form.get('contact_phone', team_settings.contact_phone)
    team_settings.address = request.form.get('address', team_settings.address)
    team_settings.founded_year = int(request.form.get('founded_year', team_settings.founded_year))
    team_settings.about = request.form.get('about', team_settings.about)
    
    # Update colors
    team_settings.primary_color = request.form.get('primary_color', team_settings.primary_color)
    team_settings.secondary_color = request.form.get('secondary_color', team_settings.secondary_color)
    
    # Handle logo upload
    if 'logo' in request.files and request.files['logo'].filename != '':
        logo = request.files['logo']
        if logo and allowed_file(logo.filename):
            # Create uploads directory if it doesn't exist
            upload_dir = os.path.join(app.root_path, 'static', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate a unique filename
            filename = f"logo_{uuid.uuid4().hex}.{logo.filename.rsplit('.', 1)[1].lower()}"
            logo_path = os.path.join('uploads', filename)
            logo.save(os.path.join(app.root_path, 'static', logo_path))
            
            # Delete old logo if it's not the default one
            if team_settings.logo_url and team_settings.logo_url != 'img/logo.png':
                old_logo_path = os.path.join(app.root_path, 'static', team_settings.logo_url)
                if os.path.exists(old_logo_path):
                    try:
                        os.remove(old_logo_path)
                    except Exception as e:
                        app.logger.error(f"Error deleting old logo: {e}")
            
            team_settings.logo_url = logo_path
    
    db.session.commit()
    flash('Settings updated successfully!', 'success')
    return redirect(url_for('settings'))

# Dashboard Route
@app.route('/dashboard')
@login_required
def dashboard():
    # Get player statistics
    total_players = Player.query.filter_by(is_active=True).count()
    active_players = Player.query.filter_by(is_active=True).all()
    
    # Get players by position
    players_by_position = db.session.query(
        Player.position,
        db.func.count(Player.id)
    ).filter(
        Player.is_active == True
    ).group_by(Player.position).all()
    
    # Get top scorers
    top_scorers = db.session.query(
        Player, 
        PlayerStats.goals
    ).join(Player.stats).filter(
        Player.is_active == True
    ).order_by(
        PlayerStats.goals.desc()
    ).limit(5).all()
    
    # Get recent players
    recent_players = Player.query.order_by(
        Player.joined_date.desc()
    ).limit(5).all()
    
    # Get upcoming matches
    upcoming_matches = Match.query.filter(
        Match.date >= datetime.utcnow()
    ).order_by(
        Match.date.asc()
    ).limit(5).all()
    
    # Get recent matches
    recent_matches = Match.query.filter(
        Match.date < datetime.utcnow()
    ).order_by(
        Match.date.desc()
    ).limit(5).all()
    
    # Calculate match statistics
    match_results = {'wins': 0, 'losses': 0, 'draws': 0}
    for match in Match.query.all():
        if match.home_goals > match.away_goals:
            match_results['wins'] += 1
        elif match.home_goals < match.away_goals:
            match_results['losses'] += 1
        else:
            match_results['draws'] += 1
    
    # Calculate total goals
    total_goals = sum(player.stats.goals for player in Player.query.all() if player.stats)
    
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
        now=now,
        timedelta=timedelta
    )

if __name__ == '__main__':
    with app.app_context():
        # This will create the database and tables if they don't exist
        db.create_all()
        
        # Create default admin user if no users exist
        if not User.query.first():
            admin = User(
                username='admin',
                email='admin@example.com',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            
            # Initialize team settings
            settings = TeamSettings.get_settings()
            db.session.add(settings)
            db.session.commit()
            
    app.run(debug=True)
