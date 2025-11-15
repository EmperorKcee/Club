#!/usr/bin/env python3
"""
Setup script for Player Dashboard
This script helps set up the player dashboard system with sample data.
"""

import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Player, PlayerStats, PlayerUser, News, TrainingSession, Staff
from werkzeug.security import generate_password_hash

def setup_player_dashboard():
    """Set up the player dashboard system"""
    print("🏆 Setting up Player Dashboard System")
    print("=" * 50)
    
    with app.app_context():
        try:
            # Create all tables
            print("📋 Creating database tables...")
            db.create_all()
            print("✅ Database tables created")
            
            # Ensure we have an admin user
            setup_admin_user()
            
            # Create sample players if none exist
            setup_sample_players()
            
            # Create player accounts
            setup_player_accounts()
            
            # Create sample news and training
            setup_sample_content()
            
            print("\n🎉 Player Dashboard setup completed successfully!")
            print_access_info()
            
        except Exception as e:
            print(f"❌ Setup failed: {str(e)}")
            db.session.rollback()
            return False
    
    return True

def setup_admin_user():
    """Ensure we have an admin user"""
    admin = User.query.filter_by(role='admin').first()
    
    if not admin:
        print("👤 Creating admin user...")
        admin = User(
            username='admin',
            email='admin@zambiafc.com',
            first_name='Admin',
            last_name='User',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created (username: admin, password: admin123)")
    else:
        print("✅ Admin user already exists")

def setup_sample_players():
    """Create sample players if none exist"""
    if Player.query.count() < 3:
        print("⚽ Creating sample players...")
        
        sample_players = [
            {
                'first_name': 'John',
                'last_name': 'Banda',
                'date_of_birth': datetime(1995, 3, 15).date(),
                'position': 'FW',
                'nationality': 'Zambia',
                'jersey_number': 10,
                'email': 'john.banda@zambiafc.com',
                'phone': '+260 123 456 789',
                'is_active': True,
                'status': 'active'
            },
            {
                'first_name': 'Peter',
                'last_name': 'Mwanza',
                'date_of_birth': datetime(1993, 7, 22).date(),
                'position': 'MF',
                'nationality': 'Zambia',
                'jersey_number': 8,
                'email': 'peter.mwanza@zambiafc.com',
                'phone': '+260 123 456 790',
                'is_active': True,
                'status': 'active'
            },
            {
                'first_name': 'David',
                'last_name': 'Phiri',
                'date_of_birth': datetime(1996, 11, 5).date(),
                'position': 'DF',
                'nationality': 'Zambia',
                'jersey_number': 5,
                'email': 'david.phiri@zambiafc.com',
                'phone': '+260 123 456 791',
                'is_active': True,
                'status': 'active'
            }
        ]
        
        for player_data in sample_players:
            # Check if player with this jersey number already exists
            existing = Player.query.filter_by(jersey_number=player_data['jersey_number']).first()
            if not existing:
                player = Player(**player_data)
                db.session.add(player)
        
        db.session.commit()
        print("✅ Sample players created")
    else:
        print("✅ Players already exist")

def setup_player_accounts():
    """Create player accounts for existing players"""
    print("🔑 Setting up player accounts...")
    
    players = Player.query.filter_by(is_active=True).all()
    created_count = 0
    
    for player in players:
        # Check if account already exists
        if not PlayerUser.query.filter_by(player_id=player.id).first():
            # Generate username and password
            username = f"{player.first_name.lower()}.{player.last_name.lower()}"
            temp_password = f"{player.first_name.lower()}{player.jersey_number}"
            
            # Check if username already exists
            counter = 1
            original_username = username
            while PlayerUser.query.filter_by(username=username).first():
                username = f"{original_username}{counter}"
                counter += 1
            
            player_user = PlayerUser(
                player_id=player.id,
                username=username,
                email=player.email or f"{username}@zambiafc.com"
            )
            player_user.set_password(temp_password)
            
            db.session.add(player_user)
            created_count += 1
            print(f"   • {player.full_name}: {username} / {temp_password}")
    
    if created_count > 0:
        db.session.commit()
        print(f"✅ Created {created_count} player accounts")
    else:
        print("✅ Player accounts already exist")

def setup_sample_content():
    """Create sample news and training content"""
    admin = User.query.filter_by(role='admin').first()
    
    if not admin:
        print("⚠️  No admin user found, skipping content creation")
        return
    
    # Create sample news
    if News.query.count() == 0:
        print("📰 Creating sample news...")
        
        news_articles = [
            {
                'title': 'Welcome to Player Portal',
                'content': 'Welcome to the new Zambia FC Player Portal! This platform will help you stay connected with your teammates, view training schedules, and access important team updates. Please bookmark this page and check it regularly for the latest information.',
                'summary': 'New player portal launched for better team communication.',
                'category': 'general',
                'is_featured': True,
                'is_published': True,
                'author_id': admin.id
            },
            {
                'title': 'Training Ground Maintenance',
                'content': 'Please note that the main training ground will undergo maintenance this weekend. All training sessions scheduled for Saturday and Sunday will be moved to the secondary field. Please arrive 15 minutes early to familiarize yourself with the new location.',
                'summary': 'Training ground maintenance - sessions moved to secondary field.',
                'category': 'training',
                'is_featured': False,
                'is_published': True,
                'author_id': admin.id
            }
        ]
        
        for article_data in news_articles:
            article = News(**article_data)
            db.session.add(article)
        
        print("✅ Sample news created")
    
    # Create sample training sessions
    if TrainingSession.query.count() == 0:
        print("🏃 Creating sample training sessions...")
        
        # Try to get a coach
        coach = Staff.query.filter(Staff.role.ilike('%coach%')).first()
        
        base_date = datetime.utcnow().replace(hour=16, minute=0, second=0, microsecond=0)
        
        training_sessions = [
            {
                'title': 'Team Training Session',
                'description': 'Regular team training focusing on ball control and passing.',
                'session_date': base_date.replace(day=base_date.day + 1),
                'duration_minutes': 90,
                'location': 'Main Training Ground',
                'session_type': 'training',
                'coach_id': coach.id if coach else None,
                'is_mandatory': True,
                'notes': 'Bring training boots and water bottle.',
                'created_by': admin.id
            }
        ]
        
        for session_data in training_sessions:
            session = TrainingSession(**session_data)
            db.session.add(session)
        
        print("✅ Sample training sessions created")
    
    db.session.commit()

def print_access_info():
    """Print access information for users"""
    print("\n" + "=" * 50)
    print("🌐 ACCESS INFORMATION")
    print("=" * 50)
    
    print("\n🔗 URLs:")
    print("   • Player Portal: http://localhost:5000/player/login")
    print("   • Admin Dashboard: http://localhost:5000/login")
    
    print("\n👤 Admin Login:")
    print("   • Username: admin")
    print("   • Password: admin123")
    
    print("\n⚽ Player Logins:")
    with app.app_context():
        player_users = PlayerUser.query.join(Player).all()
        if player_users:
            for pu in player_users:
                print(f"   • {pu.player.full_name}: {pu.username}")
        else:
            print("   • No player accounts created yet")
    
    print("\n📋 Next Steps:")
    print("   1. Start the application: python app.py")
    print("   2. Login as admin to manage content")
    print("   3. Create player accounts for your team")
    print("   4. Add news and training sessions")
    print("   5. Share login credentials with players")

if __name__ == '__main__':
    setup_player_dashboard()