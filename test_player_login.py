#!/usr/bin/env python3
"""
Test script to check player login system and create test accounts
"""

from app import app, db
from models import Player, PlayerUser, User
from datetime import datetime, date

def test_player_login_system():
    with app.app_context():
        print("🔐 Testing Player Login System")
        print("=" * 50)
        
        # Check existing admin users
        admin_users = User.query.all()
        print(f"\n👨‍💼 Admin Users ({len(admin_users)}):")
        for user in admin_users:
            print(f"  - Username: {user.username} | Role: {user.role}")
        
        # Check existing players
        players = Player.query.all()
        print(f"\n🏃 Players ({len(players)}):")
        for player in players:
            print(f"  - {player.full_name} (#{player.jersey_number}) - {player.position}")
        
        # Check existing player accounts
        player_accounts = PlayerUser.query.all()
        print(f"\n🔐 Player Accounts ({len(player_accounts)}):")
        for account in player_accounts:
            status = "Active" if account.is_active else "Disabled"
            print(f"  - Username: {account.username} | Player: {account.player.full_name} | Status: {status}")
        
        # Create test player account if none exist
        if len(player_accounts) == 0:
            print(f"\n❌ No player accounts found! Creating test account...")
            create_test_player_account()
        
        print(f"\n🎯 Login Instructions:")
        print("=" * 25)
        print("1. 🌐 Go to: http://localhost:5000/login")
        print("2. 🔑 Use these credentials:")
        
        if admin_users:
            print(f"\n   👨‍💼 Admin Login:")
            for user in admin_users:
                print(f"     Username: {user.username}")
                print(f"     → Redirects to: Admin Dashboard (/dashboard)")
        
        if player_accounts:
            print(f"\n   ⚽ Player Login:")
            for account in player_accounts:
                if account.is_active:
                    print(f"     Username: {account.username}")
                    print(f"     Player: {account.player.full_name}")
                    print(f"     → Redirects to: Player Dashboard (/player/dashboard)")
        
        print(f"\n🔧 How Admin Creates Player Accounts:")
        print("=" * 35)
        print("1. Login as admin")
        print("2. Go to 'Player Accounts' in navigation")
        print("3. Click 'Create Account' for any player")
        print("4. Set username and password")
        print("5. Player can then login with those credentials")

def create_test_player_account():
    """Create a test player account for testing"""
    try:
        # Get the first player without an account
        players_without_accounts = db.session.query(Player).outerjoin(
            PlayerUser, Player.id == PlayerUser.player_id
        ).filter(PlayerUser.id.is_(None)).all()
        
        if not players_without_accounts:
            print("❌ All players already have accounts or no players exist")
            return
        
        player = players_without_accounts[0]
        
        # Create player account
        username = f"{player.first_name.lower()}.{player.last_name.lower()}"
        password = "player123"  # Default password
        
        player_account = PlayerUser(
            player_id=player.id,
            username=username,
            email=f"{username}@zambiafc.com",
            is_active=True,
            created_at=datetime.utcnow()
        )
        player_account.set_password(password)
        
        db.session.add(player_account)
        db.session.commit()
        
        print(f"✅ Created test player account:")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print(f"   Player: {player.full_name}")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating test account: {e}")

if __name__ == '__main__':
    test_player_login_system()