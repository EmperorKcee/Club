from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from models import db, Player, PlayerUser, TeamSettings, TrainingSession, Staff
from forms import AssignPlayerLoginForm, TrainingSessionForm
from werkzeug.security import generate_password_hash
from utils.email import send_player_credentials
from datetime import datetime, timedelta
import secrets
import string

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
@login_required
def require_admin():
    if not current_user.is_authenticated or current_user.role != 'admin':
        return redirect(url_for('unauthorized'))

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    # Get team settings
    team_settings = TeamSettings.query.first()
    
    # Get player statistics
    total_players = Player.query.count()
    active_players = Player.query.filter_by(is_active=True).count()
    
    # Get training session statistics
    now = datetime.utcnow()
    upcoming_trainings = TrainingSession.query.filter(
        TrainingSession.session_date >= now
    ).order_by(TrainingSession.session_date.asc()).limit(5).all()
    
    # Get recent player logins
    recent_logins = PlayerUser.query.order_by(
        PlayerUser.last_login.desc()
    ).limit(5).all()
    
    # Prepare stats dictionary for the dashboard
    stats = {
        'total_players': total_players,
        'active_players': active_players,
        'upcoming_matches': 0,  # You can update this with actual data
        'pending_tasks': 0,     # You can update this with actual data
        'training_sessions': len(upcoming_trainings),
        'total_goals': 0,       # You can update this with actual data
        'team_rating': 0,       # You can update this with actual data
        'injuries': 0           # You can update this with actual data
    }
    
    # Prepare recent activities
    recent_activities = []
    for login in recent_logins:
        if login.last_login:
            recent_activities.append({
                'type': 'login',
                'title': f'Login: {login.username}',
                'description': 'Player logged in',
                'time_ago': f'{(now - login.last_login).seconds // 60} minutes ago',
                'user': login.username
            })
    
    # Prepare upcoming events
    upcoming_events = []
    for training in upcoming_trainings:
        upcoming_events.append({
            'title': f'Training: {training.title}',
            'date_time': training.session_date,
            'location': training.location or 'Training Ground',
            'type': 'training',
            'status': 'confirmed'
        })
    
    return render_template('admin/dashboard.html',
                         team_settings=team_settings,
                         stats=stats,
                         recent_activities=recent_activities,
                         upcoming_events=upcoming_events,
                         now=now,
                         timedelta=timedelta)

def generate_random_password(length=12):
    """Generate a random password with letters, digits, and special characters."""
    alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
    while True:
        password = ''.join(secrets.choice(alphabet) for i in range(length))
        # Ensure password has at least one lowercase, one uppercase, one digit, and one special char
        if (any(c.islower() for c in password) and 
            any(c.isupper() for c in password) and 
            any(c.isdigit() for c in password) and 
            any(not c.isalnum() for c in password)):
            return password

@admin_bp.route('/players/assign-login', methods=['GET', 'POST'])
@login_required
def assign_player_login():
    form = AssignPlayerLoginForm()
    
    if form.validate_on_submit():
        # Check if username or email already exists
        if PlayerUser.query.filter_by(username=form.username.data).first():
            flash('Username already exists', 'danger')
        elif PlayerUser.query.filter_by(email=form.email.data).first():
            flash('Email already in use', 'danger')
        else:
            # Generate a random password if not provided
            password = form.password.data or generate_random_password()
            
            # Create new player user account
            player_user = PlayerUser(
                player_id=form.player_id.data,
                username=form.username.data,
                email=form.email.data,
                is_active=form.is_active.data
            )
            player_user.set_password(password)
            
            db.session.add(player_user)
            
            try:
                db.session.commit()
                
                # Send email with credentials if account is active
                if form.is_active.data:
                    try:
                        send_player_credentials(player_user, password)
                        flash('Player login credentials have been created and sent via email!', 'success')
                    except Exception as e:
                        current_app.logger.error(f"Failed to send email: {str(e)}")
                        flash('Account created, but failed to send email with credentials. Please notify the player manually.', 'warning')
                else:
                    flash('Player account has been created but is inactive. No email was sent.', 'info')
                
                return redirect(url_for('admin.manage_players'))
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error creating player account: {str(e)}")
                flash('An error occurred while creating the account. Please try again.', 'danger')
    
    return render_template('admin/assign_player_login.html', form=form)

@admin_bp.route('/players/manage')
@login_required
def manage_players():
    # Get all players with their user accounts
    players = Player.query.outerjoin(PlayerUser).all()
    return render_template('admin/manage_players.html', players=players)

@admin_bp.route('/trainings')
@login_required
def manage_trainings():
    # View all training sessions, upcoming first, then past
    now = datetime.utcnow()
    upcoming = TrainingSession.query.filter(
        TrainingSession.session_date >= now
    ).order_by(TrainingSession.session_date.asc()).all()
    
    past = TrainingSession.query.filter(
        TrainingSession.session_date < now
    ).order_by(TrainingSession.session_date.desc()).all()
    
    # Get all staff for the coach dropdown
    staff = Staff.query.filter_by(is_active=True).order_by(Staff.first_name, Staff.last_name).all()
    
    return render_template('admin/manage_trainings.html', 
                         upcoming_trainings=upcoming,
                         past_trainings=past,
                         staff=staff,
                         now=now,
                         timedelta=timedelta)

@admin_bp.route('/trainings/add', methods=['GET', 'POST'])
@login_required
def add_training():
    form = TrainingSessionForm()
    
    # Populate coach dropdown
    form.coach_id.choices = [(0, 'No Coach')] + [(s.id, f"{s.first_name} {s.last_name}") 
                                              for s in Staff.query.filter_by(is_active=True).order_by(Staff.first_name).all()]
    
    if form.validate_on_submit():
        try:
            training = TrainingSession(
                title=form.title.data,
                description=form.description.data,
                session_date=form.session_date.data,
                duration_minutes=form.duration_minutes.data,
                location=form.location.data,
                session_type=form.session_type.data,
                is_mandatory=form.is_mandatory.data,
                notes=form.notes.data,
                coach_id=form.coach_id.data if form.coach_id.data != 0 else None,
                created_by=current_user.id
            )
            db.session.add(training)
            db.session.commit()
            flash('Training session added successfully!', 'success')
            return redirect(url_for('admin.manage_trainings'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error adding training session: {str(e)}', exc_info=True)
            flash('An error occurred while adding the training session.', 'danger')
    
    # For GET requests or invalid form submissions, show the form again
    return render_template('admin/training_form.html', 
                         form=form, 
                         title='Add Training Session',
                         submit_text='Add Training')

@admin_bp.route('/trainings/<int:training_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_training(training_id):
    training = TrainingSession.query.get_or_404(training_id)
    form = TrainingSessionForm(obj=training)
    
    # Populate coach dropdown
    form.coach_id.choices = [(0, 'No Coach')] + [(s.id, f"{s.first_name} {s.last_name}") 
                                              for s in Staff.query.filter_by(is_active=True).order_by(Staff.first_name).all()]
    
    if form.validate_on_submit():
        try:
            form.populate_obj(training)
            training.coach_id = form.coach_id.data if form.coach_id.data != 0 else None
            db.session.commit()
            flash('Training session updated successfully!', 'success')
            return redirect(url_for('admin.manage_trainings'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating training session: {str(e)}', exc_info=True)
            flash('An error occurred while updating the training session.', 'danger')
    
    # For GET request, pre-fill the form
    return render_template('admin/training_form.html', 
                         form=form, 
                         title='Edit Training Session',
                         submit_text='Update Training')

@admin_bp.route('/trainings/<int:training_id>/delete', methods=['POST'])
@login_required
def delete_training(training_id):
    """Delete a training session"""
    training = TrainingSession.query.get_or_404(training_id)
    
    try:
        db.session.delete(training)
        db.session.commit()
        flash('Training session deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting training session: {str(e)}")
        flash('Failed to delete training session. Please try again.', 'danger')
    
    return redirect(url_for('admin.manage_trainings'))
