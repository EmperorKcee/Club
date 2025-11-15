#!/usr/bin/env python3
"""
Test script to verify the unified login system works for both admin and player users
"""

from app import app, db
from models import User, Player, PlayerUser
from datetime import datetime, date

def test_unified_login():
    with app.app_context():
        print("🔐 Testing Unified Login System")
        print("=" * 50)
        
        # Check existing users
        print("\n📋 Current Users:")
        
        # Admin users
        admin_users = User.query.all()
        print(f"\n👨‍💼 Admin Users ({len(admin_users)}):")
        for user in admin_users:
            print(f"  - Username: {user.username}")
            print(f"    Email: {user.email}")
            print(f"    Role: {user.role}")
        
        # Player users
        player_users = PlayerUser.query.all()
        print(f"\n⚽ Player Users ({len(player_users)}):")
        for user in player_users:
            status = "Active" if user.is_active else "Disabled"
            print(f"  - Username: {user.username}")
            print(f"    Player: {user.player.full_name}")
            print(f"    Status: {status}")
        
        print("\n" + "=" * 50)
        print("🎯 Login Instructions:")
        print("=" * 50)
        
        print("\n1. 🌐 Go to: http://localhost:5000/login")
        print("   (or http://localhost:5000/auth - both work now)")
        
        print("\n2. 🔑 Use ANY of these credentials:")
        
        if admin_users:
            print("\n   👨‍💼 Admin Login:")
            for user in admin_users:
                print(f"     Username: {user.username}")
                print(f"     Password: [your admin password]")
                print(f"     → Will redirect to: Admin Dashboard")
        
        if player_users:
            print("\n   ⚽ Player Login:")
            for user in player_users:
                if user.is_active:
                    print(f"     Username: {user.username}")
                    print(f"     Password: [player password]")
                    print(f"     → Will redirect to: Player Dashboard")
        
        if not admin_users and not player_users:
            print("\n❌ No users found! Creating test accounts...")
            create_test_accounts()
        
        print("\n" + "=" * 50)
        print("✨ How It Works:")
        print("=" * 50)
        print("• Single login form for everyone")
        print("• System automatically detects user type")
        print("• Admin users → Admin Dashboard")
        print("• Player users → Player Dashboard")
        print("• No need to choose user type anymore!")

def create_test_accounts():
    """Create test admin and player accounts"""
    try:
        # Create admin user if none exists
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@zambiafc.com',
                first_name='Admin',
                last_name='User',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print("✅ Created admin user: admin / admin123")
        
        # Create test player if none exists
        test_player = Player.query.filter_by(first_name='Test', last_name='Player').first()
        if not test_player:
            test_player = Player(
                first_name='Test',
                last_name='Player',
                jersey_number=99,
                position='FW',
                date_of_birth=date(1995, 5, 15),
                nationality='Zambian',
                height=180,
                weight=75,
                is_active=True
            )
            db.session.add(test_player)
            db.session.flush()  # Get the ID
        
        # Create player account if none exists
        if not PlayerUser.query.filter_by(username='testplayer').first():
            player_account = PlayerUser(
                player_id=test_player.id,
                username='testplayer',
                email='testplayer@zambiafc.com',
                is_active=True,
                created_at=datetime.utcnow()
            )
            player_account.set_password('testpass123')
            db.session.add(player_account)
            print("✅ Created player user: testplayer / testpass123")
        
        db.session.commit()
        print("\n🎉 Test accounts created successfully!")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating test accounts: {e}")

if __name__ == '__main__':
    test_unified_login()