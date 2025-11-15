#!/usr/bin/env python3
"""
Database migration script for Player Dashboard features
This script adds the new tables needed for the player dashboard system.
"""

import os
import sys
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import (
    User, Player, PlayerStats, Match, Staff, TeamSettings, 
    PlayerUser, News, TrainingSession, PlayerAttendance
)

def migrate_database():
    """Run database migrations for player dashboard"""
    with app.app_context():
        print("🔄 Starting database migration for Player Dashboard...")
        
        try:
            # Create all new tables
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Add sample data for demonstration
            add_sample_data()
            
            print("🎉 Database migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during migration: {str(e)}")
            db.session.rollback()
            return False
            
    return True

def add_sample_data():
    """Add sample data for demonstration purposes"""
    print("📝 Adding sample data...")
    
    # Create sample news articles
    if not News.query.first():
        # Get or create admin user
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            admin = User.query.first()
        
        if admin:
            sample_news = [
                {
                    'title': 'Welcome to the New Player Portal',
                    'content': 'We are excited to announce the launch of our new player portal! This platform will help you stay connected with the team, view training schedules, and access important team news. Please contact your manager if you need help accessing your account.',
                    'summary': 'New player portal launched for better team communication and scheduling.',
                    'category': 'general',
                    'is_featured': True,
                    'author_id': admin.id
                },
                {
                    'title': 'Training Schedule Updated',
                    'content': 'Please note that this week\'s training schedule has been updated. Tuesday\'s session has been moved to 4:00 PM due to field maintenance. All other sessions remain as scheduled. Make sure to check the training section regularly for updates.',
                    'summary': 'Tuesday training session rescheduled to 4:00 PM.',
                    'category': 'training',
                    'is_featured': False,
                    'author_id': admin.id
                },
                {
                    'title': 'Upcoming Match Against City FC',
                    'content': 'Our next match is scheduled for this Saturday against City FC at 3:00 PM. This is an important league match, so please ensure you attend all training sessions this week. Team selection will be announced on Friday after the final training session.',
                    'summary': 'Important league match against City FC this Saturday at 3:00 PM.',
                    'category': 'match',
                    'is_featured': True,
                    'author_id': admin.id
                }
            ]
            
            for news_data in sample_news:
                news = News(**news_data)
                db.session.add(news)
            
            print("✅ Sample news articles created")
    
    # Create sample training sessions
    if not TrainingSession.query.first():
        admin = User.query.filter_by(role='admin').first() or User.query.first()
        
        if admin:
            # Get a coach if available
            coach = Staff.query.filter(Staff.role.ilike('%coach%')).first()
            
            # Create training sessions for the next week
            base_date = datetime.utcnow().replace(hour=16, minute=0, second=0, microsecond=0)
            
            training_sessions = [
                {
                    'title': 'Technical Skills Training',
                    'description': 'Focus on ball control, passing accuracy, and first touch. Bring your training boots and water bottle.',
                    'session_date': base_date + timedelta(days=1),
                    'duration_minutes': 90,
                    'location': 'Main Training Ground',
                    'session_type': 'training',
                    'coach_id': coach.id if coach else None,
                    'is_mandatory': True,
                    'notes': 'All players must attend. Focus on improving technical skills.',
                    'created_by': admin.id
                },
                {
                    'title': 'Fitness and Conditioning',
                    'description': 'Cardio workout and strength training session. This session will help improve your match fitness.',
                    'session_date': base_date + timedelta(days=3),
                    'duration_minutes': 75,
                    'location': 'Fitness Center',
                    'session_type': 'fitness',
                    'coach_id': coach.id if coach else None,
                    'is_mandatory': True,
                    'notes': 'Bring gym clothes and towel.',
                    'created_by': admin.id
                },
                {
                    'title': 'Match Preparation',
                    'description': 'Tactical preparation for the upcoming match against City FC. We will review set pieces and team formations.',
                    'session_date': base_date + timedelta(days=5),
                    'duration_minutes': 120,
                    'location': 'Main Training Ground',
                    'session_type': 'match_prep',
                    'coach_id': coach.id if coach else None,
                    'is_mandatory': True,
                    'notes': 'Critical session before the match. All players must attend.',
                    'created_by': admin.id
                }
            ]
            
            for session_data in training_sessions:
                session = TrainingSession(**session_data)
                db.session.add(session)
            
            print("✅ Sample training sessions created")
    
    # Create player accounts for existing players (first 3 players only for demo)
    existing_players = Player.query.filter_by(is_active=True).limit(3).all()
    
    for player in existing_players:
        # Check if player already has an account
        if not PlayerUser.query.filter_by(player_id=player.id).first():
            # Generate username and password
            username = f"{player.first_name.lower()}.{player.last_name.lower()}"
            temp_password = f"{player.first_name.lower()}{player.jersey_number}"
            
            player_user = PlayerUser(
                player_id=player.id,
                username=username,
                email=player.email or f"{username}@zambiafc.com"
            )
            player_user.set_password(temp_password)
            
            db.session.add(player_user)
            print(f"✅ Created account for {player.full_name} - Username: {username}, Password: {temp_password}")
    
    # Commit all changes
    db.session.commit()
    print("✅ Sample data added successfully")

def print_summary():
    """Print a summary of what was created"""
    with app.app_context():
        print("\n📊 Migration Summary:")
        print(f"   • News articles: {News.query.count()}")
        print(f"   • Training sessions: {TrainingSession.query.count()}")
        print(f"   • Player accounts: {PlayerUser.query.count()}")
        print(f"   • Total players: {Player.query.count()}")
        
        print("\n🔑 Player Login Credentials:")
        player_users = PlayerUser.query.join(Player).all()
        for pu in player_users:
            print(f"   • {pu.player.full_name}: {pu.username}")
        
        print("\n🌐 Access URLs:")
        print("   • Player Login: http://localhost:5000/player/login")
        print("   • Admin Dashboard: http://localhost:5000/login")

if __name__ == '__main__':
    print("🚀 Player Dashboard Migration Script")
    print("=" * 50)
    
    if migrate_database():
        print_summary()
        print("\n✨ Migration completed! You can now use the player dashboard.")
    else:
        print("\n💥 Migration failed. Please check the error messages above.")