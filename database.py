from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from sqlalchemy import event
import os

# Initialize SQLAlchemy
db = SQLAlchemy()

# Association Tables
player_team = db.Table('player_team',
    db.Column('player_id', db.Integer, db.ForeignKey('player.id'), primary_key=True),
    db.Column('team_id', db.Integer, db.ForeignKey('team.id'), primary_key=True)
)

# Models
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    player = db.relationship('Player', back_populates='user', uselist=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Player(db.Model):
    __tablename__ = 'player'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    position = db.Column(db.String(30), nullable=False)  # GK, DF, MF, FW
    nationality = db.Column(db.String(50))
    jersey_number = db.Column(db.Integer, unique=True)
    join_date = db.Column(db.Date, default=date.today)
    contract_end = db.Column(db.Date)
    salary = db.Column(db.Float)
    photo_url = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(20), default='active')  # active, injured, suspended, inactive
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    bio = db.Column(db.Text)
    
    # Relationships
    user = db.relationship('User', back_populates='player')
    stats = db.relationship('PlayerStats', back_populates='player', uselist=False, cascade='all, delete-orphan')
    teams = db.relationship('Team', secondary=player_team, back_populates='players')
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
    
    def __repr__(self):
        return f'<Player {self.full_name}>'

class PlayerStats(db.Model):
    __tablename__ = 'player_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), unique=True)
    matches_played = db.Column(db.Integer, default=0)
    goals = db.Column(db.Integer, default=0)
    assists = db.Column(db.Integer, default=0)
    yellow_cards = db.Column(db.Integer, default=0)
    red_cards = db.Column(db.Integer, default=0)
    clean_sheets = db.Column(db.Integer, default=0)  # For goalkeepers
    minutes_played = db.Column(db.Integer, default=0)
    
    # Relationships
    player = db.relationship('Player', back_populates='stats')

class Team(db.Model):
    __tablename__ = 'team'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    short_name = db.Column(db.String(10))
    founded = db.Column(db.Integer)
    stadium = db.Column(db.String(100))
    logo_url = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    players = db.relationship('Player', secondary=player_team, back_populates='teams')
    
    def __repr__(self):
        return f'<Team {self.name}>'

class Match(db.Model):
    __tablename__ = 'match'
    
    id = db.Column(db.Integer, primary_key=True)
    home_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    away_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    competition = db.Column(db.String(100))
    match_date = db.Column(db.DateTime, nullable=False)
    home_goals = db.Column(db.Integer, default=0)
    away_goals = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, ongoing, completed, postponed, cancelled
    venue = db.Column(db.String(100))
    
    # Relationships
    home_team = db.relationship('Team', foreign_keys=[home_team_id])
    away_team = db.relationship('Team', foreign_keys=[away_team_id])
    events = db.relationship('MatchEvent', back_populates='match', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Match {self.home_team.name} vs {self.away_team.name} - {self.match_date}>'

class MatchEvent(db.Model):
    __tablename__ = 'match_event'
    
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    event_type = db.Column(db.String(20))  # goal, yellow_card, red_card, substitution, etc.
    minute = db.Column(db.Integer)
    is_home_team = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    
    # Relationships
    match = db.relationship('Match', back_populates='events')
    player = db.relationship('Player')
    
    def __repr__(self):
        return f'<MatchEvent {self.event_type} by {self.player.full_name if self.player else "Unknown"} at {self.minute}>'

def init_app(app):
    """Initialize the database with the Flask app."""
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create default admin user if not exists
        if not User.query.filter_by(is_admin=True).first():
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True,
                is_active=True
            )
            admin.set_password('admin123')  # Change this in production!
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created with username: admin, password: admin123")

# Event listeners
@event.listens_for(Player, 'after_insert')
def create_player_stats(mapper, connection, target):
    """Automatically create stats record when a new player is created."""
    stats = PlayerStats(player_id=target.id)
    db.session.add(stats)
    db.session.commit()

@event.listens_for(Player, 'after_delete')
def delete_user_on_player_delete(mapper, connection, target):
    """Delete associated user when a player is deleted."""
    if target.user:
        db.session.delete(target.user)
        db.session.commit()
