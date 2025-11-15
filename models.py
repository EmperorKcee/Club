from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask import current_app, url_for
from sqlalchemy import func, event
from werkzeug.utils import secure_filename
import os

# This import is moved to the bottom to avoid circular imports
# from app import login_manager

class TicketPurchase(db.Model):
    """Represents a purchase of one or more tickets"""
    __tablename__ = 'ticket_purchases'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(20), default='pending')  # pending, completed, failed, refunded
    payment_reference = db.Column(db.String(50), unique=True)
    payment_method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(100))
    status = db.Column(db.String(20), default='active')  # active, cancelled, refunded
    
    # Relationships
    user = db.relationship('User', backref='ticket_purchases')
    match = db.relationship('Match', backref='ticket_purchases')
    tickets = db.relationship('Ticket', backref='purchase', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<TicketPurchase {self.id} - {self.user.username} - {self.match.opponent}>'
    
    @property
    def ticket_count(self):
        return len(self.tickets)
    
    @classmethod
    def get_user_purchases(cls, user_id):
        """Get all ticket purchases for a user"""
        return cls.query.filter_by(user_id=user_id).order_by(cls.purchase_date.desc()).all()
    
    @classmethod
    def get_match_sales(cls, match_id):
        """Get all ticket sales for a match"""
        return cls.query.filter_by(match_id=match_id, status='completed').all()
    
    def get_total_sales(cls):
        """Get total ticket sales across all matches"""
        result = db.session.query(
            func.sum(cls.total_amount).label('total_sales')
        ).filter(
            cls.status == 'completed'
        ).first()
        return result[0] or 0.0


class Ticket(db.Model):
    """Represents an individual ticket in the system"""
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey('ticket_purchases.id'), nullable=False)
    ticket_type = db.Column(db.String(20), nullable=False)  # general, premium, vip, etc.
    price = db.Column(db.Float, nullable=False)
    seat_number = db.Column(db.String(20), unique=True, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Ticket {self.id} - {self.ticket_type} - {self.seat_number}>'
    
    @property
    def match(self):
        return self.purchase.match if self.purchase else None
    
    @property
    def user(self):
        return self.purchase.user if self.purchase else None
    
    @classmethod
    def generate_seat_number(cls, ticket_type):
        """Generate a unique seat number"""
        import random
        import string
        
        prefix = {
            'general': 'GEN',
            'premium': 'PRM',
            'vip': 'VIP'
        }.get(ticket_type.lower(), 'TKT')
        
        while True:
            # Generate a random 6-character alphanumeric string
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            seat_number = f"{prefix}-{random_str}"
            
            # Check if seat number already exists
            if not cls.query.filter_by(seat_number=seat_number).first():
                return seat_number
    
    def mark_as_used(self):
        """Mark this ticket as used"""
        if not self.is_used:
            self.is_used = True
            self.used_at = datetime.utcnow()
            db.session.commit()
            return True
        return False

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    profile_picture = db.Column(db.String(200), default='img/default-avatar.png')
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user')
    join_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class PlayerStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), unique=True, nullable=False)
    matches_played = db.Column(db.Integer, default=0)
    goals = db.Column(db.Integer, default=0)
    assists = db.Column(db.Integer, default=0)
    yellow_cards = db.Column(db.Integer, default=0)
    red_cards = db.Column(db.Integer, default=0)
    clean_sheets = db.Column(db.Integer, default=0)  # For goalkeepers and defenders
    minutes_played = db.Column(db.Integer, default=0)
    
    # Relationship
    player = db.relationship('Player', back_populates='stats', uselist=False)

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    position = db.Column(db.String(30), nullable=False)  # GK, DF, MF, FW
    nationality = db.Column(db.String(50))
    jersey_number = db.Column(db.Integer, unique=True)
    join_date = db.Column(db.Date, default=datetime.utcnow)
    contract_end = db.Column(db.Date)
    salary = db.Column(db.Float)
    photo_url = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(20), default='active')  # active, injured, suspended, inactive
    email = db.Column(db.String(120))  # Player's email for dashboard access
    phone = db.Column(db.String(20))  # Player's phone number
    bio = db.Column(db.Text)  # Player biography/notes
    
    # Relationships
    stats = db.relationship('PlayerStats', back_populates='player', uselist=False, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super(Player, self).__init__(**kwargs)
        # Initialize stats when a new player is created
        if self.stats is None:
            self.stats = PlayerStats()
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
        
    @property
    def age(self):
        today = datetime.utcnow().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    @property
    def contract_status(self):
        """Get contract status based on end date"""
        if not self.contract_end:
            return 'no_contract'
        
        today = datetime.utcnow().date()
        days_remaining = (self.contract_end - today).days
        
        if days_remaining < 0:
            return 'expired'
        elif days_remaining <= 30:
            return 'expiring_soon'
        elif days_remaining <= 90:
            return 'expiring_3_months'
        elif days_remaining <= 180:
            return 'expiring_6_months'
        else:
            return 'active'
    
    @property
    def contract_days_remaining(self):
        """Get number of days remaining on contract"""
        if not self.contract_end:
            return None
        
        today = datetime.utcnow().date()
        return (self.contract_end - today).days
    
    @property
    def contract_status_text(self):
        """Get human-readable contract status"""
        status = self.contract_status
        days = self.contract_days_remaining
        
        if status == 'no_contract':
            return 'No Contract'
        elif status == 'expired':
            return f'Expired ({abs(days)} days ago)'
        elif status == 'expiring_soon':
            return f'Expires in {days} days'
        elif status == 'expiring_3_months':
            return f'Expires in {days} days'
        elif status == 'expiring_6_months':
            return f'Expires in {days} days'
        else:
            return f'Active ({days} days remaining)'

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    opponent = db.Column(db.String(100), nullable=False)
    opponent_logo = db.Column(db.String(200))  # Path to the opponent's logo
    match_date = db.Column(db.DateTime, nullable=False)
    venue = db.Column(db.String(200), nullable=False)  # Actual venue name (e.g., 'National Stadium, Lusaka')
    is_home = db.Column(db.Boolean, default=True)  # True for home games, False for away games
    competition = db.Column(db.String(100))
    home_goals = db.Column(db.Integer, default=0)
    away_goals = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, ongoing, completed, postponed
    match_report = db.Column(db.Text)
    
    @property
    def home_team_logo(self):
        # Return the path to the home team's logo (Zambia FC)
        return url_for('static', filename='img/logo.png')
        
    @property
    def away_team_logo(self):
        # Return the path to the opponent's logo or a default if not set
        if self.opponent_logo:
            # First try the root uploads directory (where logos are actually stored)
            if os.path.exists(os.path.join(current_app.static_folder, 'uploads', self.opponent_logo)):
                return url_for('static', filename=f'uploads/{self.opponent_logo}')
            # Fallback to the teams subdirectory (for backward compatibility)
            return url_for('static', filename=f'uploads/teams/{self.opponent_logo}')
        return url_for('static', filename='img/default-team-logo.png')

class FinancialRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # 'income' or 'expense'
    category = db.Column(db.String(50))  # ticket sales, merchandise, salary, etc.
    recorded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationship
    recorder = db.relationship('User', backref='financial_records')

class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(100), nullable=False)  # e.g., Coach, Manager, Physio, etc.
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20))
    hire_date = db.Column(db.Date, default=datetime.utcnow)
    salary = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True)
    photo_url = db.Column(db.String(200))
    bio = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Staff {self.first_name} {self.last_name} - {self.role}>'


class TeamSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(100), default='Zambia FC')
    logo_url = db.Column(db.String(200), default='img/logo.png')
    primary_color = db.Column(db.String(7), default='#b11601')  # Default red color
    secondary_color = db.Column(db.String(7), default='#f8f9fa')  # Light gray
    text_color = db.Column(db.String(7), default='#ffffff')  # White text color for buttons
    contact_email = db.Column(db.String(120), default='info@zambiafc.com')
    contact_phone = db.Column(db.String(20), default='+260 123 456 789')
    address = db.Column(db.Text, default='123 Soccer Way, Lusaka, Zambia')
    founded_year = db.Column(db.Integer, default=2020)
    about = db.Column(db.Text, default='A professional football club based in Zambia')
    
    @classmethod
    def get_settings(cls):
        settings = cls.query.first()
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings

class PlayerUser(UserMixin, db.Model):
    """Player login accounts for the player dashboard"""
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), unique=True, nullable=False)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='player')
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    player = db.relationship('Player', backref=db.backref('user_account', uselist=False), uselist=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        return self.player.full_name if self.player else self.username

class News(db.Model):
    """Team news and announcements"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.String(500))  # Short summary for previews
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), default='general')  # general, match, transfer, etc.
    is_published = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)  # Featured news appear prominently
    image_url = db.Column(db.String(200))  # Optional news image
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    author = db.relationship('User', backref='news_articles')
    
    @property
    def formatted_date(self):
        return self.created_at.strftime('%B %d, %Y')

class TrainingSession(db.Model):
    """Training sessions and updates"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    session_date = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=90)  # Training duration
    location = db.Column(db.String(100), default='Training Ground')
    session_type = db.Column(db.String(50), default='training')  # training, match_prep, fitness, etc.
    coach_id = db.Column(db.Integer, db.ForeignKey('staff.id'))
    is_mandatory = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)  # Additional notes or instructions
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    coach = db.relationship('Staff', backref='training_sessions')
    creator = db.relationship('User', backref='created_training_sessions')
    
    @property
    def formatted_date(self):
        return self.session_date.strftime('%A, %B %d, %Y at %H:%M')
    
    @property
    def is_upcoming(self):
        return self.session_date > datetime.utcnow()

class PlayerAttendance(db.Model):
    """Track player attendance for training sessions"""
    __tablename__ = 'player_attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    training_session_id = db.Column(db.Integer, db.ForeignKey('training_session.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, present, absent, excused
    notes = db.Column(db.Text)
    recorded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    player = db.relationship('Player', backref='training_attendance')
    training_session = db.relationship('TrainingSession', backref='player_attendance')
    recorder = db.relationship('User', backref='recorded_attendance')


class ProductCategory(db.Model):
    """Categories for organizing products in the team shop"""
    __tablename__ = 'product_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<ProductCategory {self.name}>'
    
    @staticmethod
    def get_active_categories():
        """Get all active product categories"""
        return ProductCategory.query.filter_by(is_active=True).order_by(ProductCategory.name).all()


class Product(db.Model):
    """Products available in the team shop"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    sale_price = db.Column(db.Float)
    sku = db.Column(db.String(50), unique=True)
    stock_quantity = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'), nullable=False)
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    images = db.relationship('ProductImage', backref='product', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Product {self.name}>'
    
    @property
    def main_image(self):
        """Get the main product image or a default"""
        if self.images:
            main_img = next((img for img in self.images if img.is_main), None)
            if main_img:
                return main_img.image_url
            # If no image is marked as main, return the first one
            return self.images[0].image_url
        return 'img/no-image-available.png'
    
    @property
    def current_price(self):
        """Get the current price (sale price if available, otherwise regular price)"""
        return self.sale_price if self.sale_price and self.sale_price < self.price else self.price
    
    @property
    def is_on_sale(self):
        """Check if the product is on sale"""
        return self.sale_price is not None and self.sale_price < self.price
    
    @classmethod
    def get_featured_products(cls, limit=8):
        """Get featured products"""
        return cls.query.filter_by(is_featured=True, is_active=True).limit(limit).all()
    
    @classmethod
    def get_products_by_category(cls, category_slug):
        """Get all active products in a category"""
        return cls.query.join(ProductCategory)\
                       .filter(Product.slug == category_slug, 
                              Product.is_active == True,
                              ProductCategory.is_active == True)\
                       .all()


class ProductImage(db.Model):
    """Images for products"""
    __tablename__ = 'product_images'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    alt_text = db.Column(db.String(100))
    is_main = db.Column(db.Boolean, default=False)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ProductImage {self.id} for Product {self.product_id}>'


class Subscription(db.Model):
    """Model for storing fan newsletter subscriptions"""
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    unsubscribed_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Subscription {self.email}>'


class FanMessage(db.Model):
    """Model for storing fan chat messages"""
    __tablename__ = 'fan_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    username = db.Column(db.String(64), nullable=False)
    message = db.Column(db.Text, nullable=False)
    avatar = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='fan_messages')
    
    def __repr__(self):
        return f'<FanMessage {self.id} by {self.username}>'
    
    def to_dict(self):
        """Convert message to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'message': self.message,
            'avatar': url_for('static', filename=self.avatar) if self.avatar else url_for('static', filename='img/default-avatar.png'),
            'created_at': self.created_at.isoformat(),
            'is_current_user': self.user_id == getattr(current_user, 'id', None)
        }
