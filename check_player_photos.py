#!/usr/bin/env python3
"""
Script to check player photo URLs and file existence
"""

from app import app, db
from models import Player
import os

def check_player_photos():
    with app.app_context():
        print("📸 Checking Player Profile Pictures")
        print("=" * 50)
        
        # Get all players
        players = Player.query.all()
        
        print(f"\n👥 Total Players: {len(players)}")
        
        if not players:
            print("❌ No players found in database")
            return
        
        print("\n📋 Player Photo Status:")
        print("-" * 30)
        
        for player in players:
            print(f"\n🏃 {player.first_name} {player.last_name} (#{player.jersey_number})")
            
            if player.photo_url:
                print(f"  📷 Photo URL: {player.photo_url}")
                
                # Check if file exists
                photo_path = os.path.join('static', player.photo_url)
                if os.path.exists(photo_path):
                    file_size = os.path.getsize(photo_path)
                    print(f"  ✅ File exists: {photo_path} ({file_size} bytes)")
                else:
                    print(f"  ❌ File missing: {photo_path}")
            else:
                print(f"  ❌ No photo URL set")
        
        # Check default image
        print(f"\n🖼️ Default Image Check:")
        default_path = os.path.join('static', 'img', 'default-player.png')
        if os.path.exists(default_path):
            file_size = os.path.getsize(default_path)
            print(f"  ✅ Default image exists: {default_path} ({file_size} bytes)")
        else:
            print(f"  ❌ Default image missing: {default_path}")
        
        # Check static directory structure
        print(f"\n📁 Static Directory Structure:")
        static_dir = 'static'
        if os.path.exists(static_dir):
            print(f"  ✅ Static directory exists")
            
            # Check uploads directory
            uploads_dir = os.path.join(static_dir, 'uploads')
            if os.path.exists(uploads_dir):
                print(f"  ✅ Uploads directory exists")
                
                # Check players upload directory
                players_upload_dir = os.path.join(uploads_dir, 'players')
                if os.path.exists(players_upload_dir):
                    print(f"  ✅ Players upload directory exists")
                    files = os.listdir(players_upload_dir)
                    print(f"  📁 Files in players directory: {len(files)}")
                    for file in files[:5]:  # Show first 5 files
                        print(f"    - {file}")
                    if len(files) > 5:
                        print(f"    ... and {len(files) - 5} more files")
                else:
                    print(f"  ❌ Players upload directory missing: {players_upload_dir}")
            else:
                print(f"  ❌ Uploads directory missing: {uploads_dir}")
        else:
            print(f"  ❌ Static directory missing: {static_dir}")
        
        print(f"\n🔧 Troubleshooting Tips:")
        print("=" * 30)
        print("1. Check if player photo_url paths are correct")
        print("2. Verify files exist in static directory")
        print("3. Check file permissions")
        print("4. Ensure Flask static file serving is working")
        print("5. Check browser developer tools for 404 errors")

if __name__ == '__main__':
    check_player_photos()