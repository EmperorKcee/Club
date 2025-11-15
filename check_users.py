#!/usr/bin/env python3
"""
Script to check existing users and player accounts
"""

from app import app, db
from models import User, Player, PlayerUser

def check_users():
    with app.app_context():
        print("=== ADMIN USERS ===")
        admin_users = User.query.all()
        for user in admin_users:
            print(f"- {user.username} ({user.email}) - Role: {user.role}")
        
        print(f"\nTotal admin users: {len(admin_users)}")
        
        print("\n=== PLAYERS ===")
        players = Player.query.filter_by(is_active=True).all()
        for player in players:
            print(f"- {player.full_name} (#{player.jersey_number}) - {player.position}")
        
        print(f"\nTotal active players: {len(players)}")
        
        print("\n=== PLAYER ACCOUNTS ===")
        player_accounts = PlayerUser.query.all()
        for account in player_accounts:
            status = "Active" if account.is_active else "Disabled"
            print(f"- {account.username} -> {account.player.full_name} ({status})")
        
        print(f"\nTotal player accounts: {len(player_accounts)}")
        
        if len(player_accounts) == 0:
            print("\n❌ No player accounts found!")
            print("You need to create a player account to access the player dashboard.")
            print("\nOptions:")
            print("1. Login as admin and go to Admin -> Player Accounts")
            print("2. Create accounts for existing players")
            print("3. Run the create_test_player.py script")

if __name__ == '__main__':
    check_users()