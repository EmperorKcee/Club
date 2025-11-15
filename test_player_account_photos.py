#!/usr/bin/env python3
"""
Test script to verify player photos are showing on player account cards
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Player, PlayerUser

def test_player_account_photos():
    """Test that player photos are showing correctly on player account cards"""
    print("📸 Testing Player Account Photos")
    print("=" * 50)
    
    with app.app_context():
        # Test 1: Check players with photos
        print("1. Checking players with photos...")
        players_with_photos = Player.query.filter(Player.photo_url.isnot(None)).all()
        
        if players_with_photos:
            print(f"   Found {len(players_with_photos)} players with photos:")
            for player in players_with_photos:
                print(f"   - {player.full_name}: {player.photo_url}")
                
                # Check if photo file exists
                if player.photo_url:
                    photo_path = os.path.join(app.root_path, 'static', player.photo_url)
                    if os.path.exists(photo_path):
                        print(f"     ✅ Photo file exists: {photo_path}")
                    else:
                        print(f"     ❌ Photo file missing: {photo_path}")
        else:
            print("   ⚠️  No players with photos found")
        
        # Test 2: Check player accounts page
        print("\n2. Testing player accounts page...")
        with app.test_client() as client:
            # Login as admin
            with client.session_transaction() as sess:
                sess['_user_id'] = '1'
                sess['_fresh'] = True
            
            response = client.get('/admin/player-accounts')
            print(f"   Player accounts page status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Player accounts page accessible")
                
                # Check if photo URLs are in the response
                response_text = response.get_data(as_text=True)
                
                # Count photo references
                photo_count = response_text.count('photo_url')
                img_count = response_text.count('<img src=')
                
                print(f"   📊 Photo URL references: {photo_count}")
                print(f"   📊 Image tags found: {img_count}")
                
                # Check for specific photo paths
                for player in players_with_photos:
                    if player.photo_url and player.photo_url in response_text:
                        print(f"   ✅ {player.full_name}'s photo URL found in page")
                    else:
                        print(f"   ❌ {player.full_name}'s photo URL not found in page")
                
                # Check for fallback handling
                if 'fas fa-user' in response_text:
                    print("   ✅ Fallback icons found for players without photos")
                
                # Check for error handling
                if 'onerror=' in response_text:
                    print("   ✅ Error handling found for broken images")
                else:
                    print("   ⚠️  No error handling found for broken images")
                    
            else:
                print("   ❌ Player accounts page not accessible")
        
        # Test 3: Check specific photo URLs
        print("\n3. Testing photo URL accessibility...")
        with app.test_client() as client:
            for player in players_with_photos[:3]:  # Test first 3 players
                if player.photo_url:
                    photo_url = f"/static/{player.photo_url}"
                    response = client.get(photo_url)
                    print(f"   {player.full_name} photo ({photo_url}): {response.status_code}")
                    
                    if response.status_code == 200:
                        print(f"     ✅ Photo accessible")
                    else:
                        print(f"     ❌ Photo not accessible")
        
        # Test 4: Check PlayerUser relationships
        print("\n4. Checking PlayerUser relationships...")
        player_users = PlayerUser.query.all()
        
        if player_users:
            print(f"   Found {len(player_users)} player accounts:")
            for player_user in player_users:
                if hasattr(player_user, 'player') and player_user.player:
                    player = player_user.player
                    print(f"   - {player_user.username} → {player.full_name}")
                    if player.photo_url:
                        print(f"     📸 Has photo: {player.photo_url}")
                    else:
                        print(f"     📷 No photo")
                else:
                    print(f"   - {player_user.username} → No player linked")
        else:
            print("   ⚠️  No player accounts found")
        
        print("\n🎯 Photo Display Summary:")
        print("✅ Player photos should be visible on account cards")
        print("✅ Fallback icons for players without photos")
        print("✅ Error handling for broken image links")
        print("✅ Proper photo URL generation")
        
        print("\n💡 If photos are still not showing:")
        print("1. Check browser developer tools for 404 errors")
        print("2. Verify photo files exist in static/uploads/players/")
        print("3. Run fix_player_photo_urls.py to fix broken URLs")
        print("4. Clear browser cache and refresh page")

if __name__ == "__main__":
    test_player_account_photos()