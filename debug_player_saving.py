#!/usr/bin/env python3
"""
Debug script to identify player saving issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Player, PlayerStats

def debug_player_saving():
    """Debug common player saving issues"""
    print("🔍 Debugging Player Saving Issues")
    print("=" * 50)
    
    with app.app_context():
        # Test 1: Check database connection
        print("1. Testing database connection...")
        try:
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            print("   ✅ Database connection working")
        except Exception as e:
            print(f"   ❌ Database connection failed: {e}")
            return
        
        # Test 2: Check Player model
        print("\n2. Testing Player model...")
        try:
            player_count = Player.query.count()
            print(f"   ✅ Player model working - {player_count} players found")
        except Exception as e:
            print(f"   ❌ Player model error: {e}")
            return
        
        # Test 3: Check PlayerStats model
        print("\n3. Testing PlayerStats model...")
        try:
            stats_count = PlayerStats.query.count()
            print(f"   ✅ PlayerStats model working - {stats_count} stats records found")
        except Exception as e:
            print(f"   ❌ PlayerStats model error: {e}")
        
        # Test 4: Test creating a player
        print("\n4. Testing player creation...")
        try:
            test_player = Player(
                first_name="Test",
                last_name="Player",
                position="MF",
                jersey_number=999,  # Use a unique number
                nationality="Zambia",
                status="active",
                is_active=True
            )
            
            db.session.add(test_player)
            db.session.flush()  # Don't commit yet, just check for errors
            print("   ✅ Player creation successful (not committed)")
            
            # Test PlayerStats creation
            if not hasattr(test_player, 'stats') or test_player.stats is None:
                test_stats = PlayerStats(player_id=test_player.id)
                db.session.add(test_stats)
                db.session.flush()
                print("   ✅ PlayerStats creation successful (not committed)")
            
            db.session.rollback()  # Don't actually save the test player
            print("   ✅ Test player creation rolled back")
            
        except Exception as e:
            db.session.rollback()
            print(f"   ❌ Player creation failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 5: Check for common constraint issues
        print("\n5. Checking for constraint issues...")
        
        # Check for duplicate jersey numbers
        try:
            jersey_numbers = db.session.query(Player.jersey_number).all()
            jersey_list = [j[0] for j in jersey_numbers if j[0] is not None]
            duplicates = set([x for x in jersey_list if jersey_list.count(x) > 1])
            
            if duplicates:
                print(f"   ⚠️  Duplicate jersey numbers found: {duplicates}")
            else:
                print("   ✅ No duplicate jersey numbers")
                
        except Exception as e:
            print(f"   ❌ Error checking jersey numbers: {e}")
        
        # Test 6: Check upload directory
        print("\n6. Checking upload directory...")
        try:
            upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'players')
            if os.path.exists(upload_dir):
                print(f"   ✅ Upload directory exists: {upload_dir}")
                
                # Check if writable
                test_file = os.path.join(upload_dir, 'test_write.txt')
                try:
                    with open(test_file, 'w') as f:
                        f.write('test')
                    os.remove(test_file)
                    print("   ✅ Upload directory is writable")
                except Exception as e:
                    print(f"   ❌ Upload directory not writable: {e}")
            else:
                print(f"   ⚠️  Upload directory doesn't exist: {upload_dir}")
                try:
                    os.makedirs(upload_dir, exist_ok=True)
                    print("   ✅ Created upload directory")
                except Exception as e:
                    print(f"   ❌ Failed to create upload directory: {e}")
                    
        except Exception as e:
            print(f"   ❌ Error checking upload directory: {e}")
        
        # Test 7: Check CSRF configuration
        print("\n7. Checking CSRF configuration...")
        try:
            from flask_wtf.csrf import generate_csrf
            with app.test_request_context():
                csrf_token = generate_csrf()
                print(f"   ✅ CSRF token generation working: {csrf_token[:20]}...")
        except Exception as e:
            print(f"   ❌ CSRF token generation failed: {e}")
        
        print("\n🎯 Debug Summary:")
        print("If player saving is still failing, check:")
        print("1. Browser console for JavaScript errors")
        print("2. Flask server logs for detailed error messages")
        print("3. Form data being submitted correctly")
        print("4. File upload permissions and disk space")

if __name__ == "__main__":
    debug_player_saving()