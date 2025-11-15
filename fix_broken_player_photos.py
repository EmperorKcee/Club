#!/usr/bin/env python3
"""
Fix broken player photos by clearing photo_url for non-existent files
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Player

def fix_broken_player_photos():
    """Clear photo_url for players whose photo files don't exist"""
    print("🔧 Fixing Broken Player Photos")
    print("=" * 50)
    
    with app.app_context():
        players = Player.query.filter(Player.photo_url.isnot(None)).all()
        
        fixed_count = 0
        
        for player in players:
            print(f"\n👤 Player: {player.full_name}")
            print(f"   Current photo_url: {player.photo_url}")
            
            if player.photo_url:
                # Check if photo file exists
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
                else:
                    print("   ❌ Photo doesn't exist - clearing photo_url")
                    player.photo_url = None
                    db.session.commit()
                    fixed_count += 1
                    print("   ✅ Photo URL cleared - will show fallback icon")
        
        print(f"\n🎯 Fix Complete!")
        print(f"Fixed {fixed_count} broken photo URLs")
        print("Players with broken photos will now show fallback icons")
        print("This ensures a consistent user experience on player account cards")

if __name__ == "__main__":
    fix_broken_player_photos()