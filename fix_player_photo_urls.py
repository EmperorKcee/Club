#!/usr/bin/env python3
"""
Fix player photo URLs to point to existing files
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Player

def fix_player_photo_urls():
    """Fix player photo URLs to point to existing files"""
    print("🔧 Fixing Player Photo URLs")
    print("=" * 50)
    
    with app.app_context():
        players = Player.query.all()
        
        for player in players:
            print(f"\n👤 Player: {player.full_name}")
            print(f"   Current photo_url: {player.photo_url}")
            
            if player.photo_url:
                # Check if current photo exists
                photo_url = player.photo_url
                if photo_url.startswith('/static/'):
                    photo_url = photo_url[8:]
                elif photo_url.startswith('static/'):
                    photo_url = photo_url[7:]
                elif photo_url.startswith('/'):
                    photo_url = photo_url[1:]
                
                img_path = os.path.join(app.root_path, 'static', photo_url)
                
                if os.path.exists(img_path):
                    print("   ✅ Photo exists - no change needed")
                    continue
                else:
                    print("   ❌ Photo doesn't exist - looking for alternatives...")
                    
                    # Look for other photos for this player
                    player_name = f"{player.first_name}_{player.last_name}"
                    uploads_dir = os.path.join(app.root_path, 'static', 'uploads', 'players')
                    
                    if os.path.exists(uploads_dir):
                        files = os.listdir(uploads_dir)
                        player_files = [f for f in files if f.startswith(player_name)]
                        
                        if player_files:
                            # Use the most recent file (highest timestamp)
                            player_files.sort(reverse=True)
                            new_photo = player_files[0]
                            new_photo_url = f"uploads/players/{new_photo}"
                            
                            print(f"   🔄 Found alternative: {new_photo}")
                            print(f"   📝 Updating photo_url to: {new_photo_url}")
                            
                            player.photo_url = new_photo_url
                            db.session.commit()
                            print("   ✅ Updated successfully")
                        else:
                            print("   ⚠️  No alternative photos found")
                    else:
                        print("   ❌ Uploads directory doesn't exist")
            else:
                print("   ⚠️  No photo_url set")
        
        print("\n🎯 Photo URL Fix Complete!")
        print("Now test the PDF generation again to see player photos.")

if __name__ == "__main__":
    fix_player_photo_urls()