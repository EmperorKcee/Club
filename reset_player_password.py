#!/usr/bin/env python3
"""
Script to reset player password so you can login as a player
"""

from app import app, db
from models import PlayerUser

def reset_player_password():
    with app.app_context():
        print("🔑 Resetting Player Password")
        print("=" * 30)
        
        # Get player accounts
        player_accounts = PlayerUser.query.filter_by(is_active=True).all()
        
        if not player_accounts:
            print("❌ No active player accounts found!")
            return
        
        print("Available player accounts:")
        for i, account in enumerate(player_accounts, 1):
            print(f"{i}. Username: {account.username} | Player: {account.player.full_name}")
        
        # Reset password for first account (chisala)
        account = player_accounts[0]
        new_password = "player123"
        
        try:
            account.set_password(new_password)
            db.session.commit()
            
            print(f"\n✅ Password reset successful!")
            print(f"Username: {account.username}")
            print(f"New Password: {new_password}")
            print(f"Player: {account.player.full_name}")
            
            print(f"\n🔄 Now follow these steps:")
            print("1. 🚪 Logout from current session: http://localhost:5000/logout")
            print("2. 🔑 Login with player credentials: http://localhost:5000/login")
            print(f"   Username: {account.username}")
            print(f"   Password: {new_password}")
            print("3. ✅ Should redirect to player dashboard with sidebar navigation")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error resetting password: {e}")

if __name__ == '__main__':
    reset_player_password()