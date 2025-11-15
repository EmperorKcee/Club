#!/usr/bin/env python3
"""
Script to help fix the "Access denied. Player login required" error
"""

from app import app, db
from models import User, Player, PlayerUser

def fix_player_access_error():
    with app.app_context():
        print("🔧 Fixing 'Access denied. Player login required' Error")
        print("=" * 60)
        
        print("\n❌ **Problem Explanation:**")
        print("You're getting this error because:")
        print("1. You're logged in as an ADMIN user (User model)")
        print("2. But trying to access PLAYER routes (requires PlayerUser model)")
        print("3. The @player_required decorator blocks admin access to player routes")
        
        print("\n✅ **Solution:**")
        print("You need to logout and login with PLAYER credentials")
        
        # Show available accounts
        print("\n👨‍💼 Available Admin Accounts:")
        admin_users = User.query.all()
        for user in admin_users:
            print(f"  - Username: {user.username} (Role: {user.role})")
            print(f"    → Redirects to: Admin Dashboard (/dashboard)")
        
        print("\n⚽ Available Player Accounts:")
        player_accounts = PlayerUser.query.filter_by(is_active=True).all()
        
        if not player_accounts:
            print("  ❌ No active player accounts found!")
            print("  📝 Creating test player account...")
            create_test_player_account()
            player_accounts = PlayerUser.query.filter_by(is_active=True).all()
        
        for account in player_accounts:
            print(f"  - Username: {account.username}")
            print(f"    Player: {account.player.full_name} (#{account.player.jersey_number})")
            print(f"    → Redirects to: Player Dashboard (/player/dashboard)")
        
        print("\n🔄 **Step-by-Step Fix:**")
        print("=" * 25)
        print("1. 🚪 LOGOUT from current admin session")
        print("   - Click your profile dropdown (top-right)")
        print("   - Click 'Logout'")
        print("   - Or go to: http://localhost:5000/logout")
        
        print("\n2. 🔑 LOGIN with PLAYER credentials")
        print("   - Go to: http://localhost:5000/login")
        print("   - Use PLAYER username (not admin username)")
        
        if player_accounts:
            account = player_accounts[0]  # Show first account as example
            print(f"   - Example: Username = {account.username}")
            print(f"   - Password = [password set by admin]")
        
        print("\n3. ✅ VERIFY player interface")
        print("   - Should redirect to /player/dashboard")
        print("   - Should see SIDEBAR navigation (not top navigation)")
        print("   - Should see player name and jersey number")
        
        print("\n🎯 **Quick Test:**")
        print("=" * 15)
        print("If you don't know the player password:")
        print("1. Login as admin first")
        print("2. Go to 'Player Accounts' in navigation")
        print("3. Reset password for any player account")
        print("4. Note the new password")
        print("5. Logout and login as that player")
        
        print("\n💡 **Alternative: Create New Player Account**")
        print("=" * 45)
        print("1. Login as admin")
        print("2. Go to 'Player Accounts'")
        print("3. Click 'Create Account' for any player")
        print("4. Set username and password")
        print("5. Logout and login with those credentials")
        
        # Show current session info
        print("\n🔍 **Current Session Debug:**")
        print("=" * 25)
        print("The error occurs because:")
        print("- You're authenticated as an admin User")
        print("- Player routes check: isinstance(current_user, PlayerUser)")
        print("- Admin users fail this check → Access denied")
        print("- Solution: Login as PlayerUser instead")

def create_test_player_account():
    """Create a test player account if none exist"""
    try:
        # Get first player without account
        players_without_accounts = db.session.query(Player).outerjoin(
            PlayerUser, Player.id == PlayerUser.player_id
        ).filter(PlayerUser.id.is_(None)).all()
        
        if not players_without_accounts:
            print("  ℹ️ All players already have accounts")
            return
        
        player = players_without_accounts[0]
        
        # Create simple test account
        username = "testplayer"
        password = "test123"
        
        player_account = PlayerUser(
            player_id=player.id,
            username=username,
            email=f"{username}@zambiafc.com",
            is_active=True
        )
        player_account.set_password(password)
        
        db.session.add(player_account)
        db.session.commit()
        
        print(f"  ✅ Created test player account:")
        print(f"     Username: {username}")
        print(f"     Password: {password}")
        print(f"     Player: {player.full_name}")
        
    except Exception as e:
        db.session.rollback()
        print(f"  ❌ Error creating account: {e}")

if __name__ == '__main__':
    fix_player_access_error()