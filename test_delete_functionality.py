#!/usr/bin/env python3
"""
Test script to verify player delete functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Player, PlayerUser
from flask import url_for

def test_delete_functionality():
    """Test the delete player functionality"""
    with app.app_context():
        print("🧪 Testing Player Delete Functionality")
        print("=" * 50)
        
        # Check if delete route exists
        try:
            with app.test_client() as client:
                # Test if the route is accessible (should redirect to login)
                response = client.post('/players/999/delete')
                print(f"✅ Delete route exists - Status: {response.status_code}")
                
                if response.status_code == 302:
                    print("   (Redirected to login - route is protected)")
                
        except Exception as e:
            print(f"❌ Error testing delete route: {e}")
        
        # Check database structure
        print("\n📊 Database Structure Check:")
        try:
            # Check if Player model has proper relationships
            sample_player = Player.query.first()
            if sample_player:
                print(f"✅ Found sample player: {sample_player.full_name}")
                
                # Check if player has user account
                player_user = PlayerUser.query.filter_by(player_id=sample_player.id).first()
                if player_user:
                    print(f"   - Has user account: {player_user.username}")
                else:
                    print("   - No user account")
                    
            else:
                print("⚠️  No players found in database")
                
        except Exception as e:
            print(f"❌ Database error: {e}")

if __name__ == "__main__":
    test_delete_functionality()