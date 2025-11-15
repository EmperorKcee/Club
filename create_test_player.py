#!/usr/bin/env python3
"""
Script to create a test player and player account for testing the player dashboard
"""

from app import app, db
from models import Player, PlayerUser
from datetime import datetime, date

def create_test_player():
    with app.app_context():
        # Check if test player already exists
        existing_player = Player.query.filter_by(first_name='Test', last_name='Player').first()
        
        if existing_player:
            print(f"Test player already exists: {existing_player.full_name}")
            
            # Check if player account exists
            player_account = PlayerUser.query.filter_by(player_id=existing_player.id).first()
            if player_account:
                print(f"Player account exists - Username: {player_account.username}")
                print("You can login with:")
                print(f"  Username: {player_account.username}")
                print(f"  Password: testpass123")
                return
        else:
            # Create test player
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
            db.session.commit()
            print(f"Created test player: {test_player.full_name}")
            existing_player = test_player
        
        # Create player account
        player_account = PlayerUser(
            player_id=existing_player.id,
            username='testplayer',
            email='testplayer@zambiafc.com',
            is_active=True,
            created_at=datetime.utcnow()
        )
        player_account.set_password('testpass123')
        
        db.session.add(player_account)
        db.session.commit()
        
        print("✅ Test player account created successfully!")
        print("\n🎮 Login Details:")
        print(f"  Username: {player_account.username}")
        print(f"  Password: testpass123")
        print(f"  Player: {existing_player.full_name} (#{existing_player.jersey_number})")
        
        print("\n🔗 Login Steps:")
        print("1. Go to: http://localhost:5000/auth")
        print("2. Click 'Player Portal' (green card)")
        print("3. Enter the credentials above")
        print("4. You'll be redirected to the player dashboard")

if __name__ == '__main__':
    create_test_player()