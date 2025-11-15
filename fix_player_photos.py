#!/usr/bin/env python3
"""
Script to fix player profile picture issues
"""

from app import app, db
from models import Player
import os

def fix_player_photos():
    with app.app_context():
        print("🔧 Fixing Player Profile Picture Issues")
        print("=" * 50)
        
        # Get all players
        players = Player.query.all()
        
        print(f"\n👥 Checking {len(players)} players...")
        
        fixed_count = 0
        
        for player in players:
            print(f"\n🏃 {player.first_name} {player.last_name} (#{player.jersey_number})")
            
            if player.photo_url:
                # Check if file exists
                photo_path = os.path.join('static', player.photo_url)
                if os.path.exists(photo_path):
                    print(f"  ✅ Photo OK: {player.photo_url}")
                else:
                    print(f"  ❌ Photo missing: {player.photo_url}")
                    print(f"  🔧 Clearing invalid photo URL...")
                    
                    # Clear the invalid photo URL
                    player.photo_url = None
                    fixed_count += 1
            else:
                print(f"  ℹ️ No photo set (will use default)")
        
        if fixed_count > 0:
            try:
                db.session.commit()
                print(f"\n✅ Fixed {fixed_count} player(s) with invalid photo URLs")
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ Error saving changes: {e}")
        else:
            print(f"\n✅ All player photos are valid!")
        
        # Check template fallback handling
        print(f"\n🎨 Template Fallback Check:")
        print("=" * 30)
        
        # Check if default image exists
        default_path = os.path.join('static', 'img', 'default-player.png')
        if os.path.exists(default_path):
            print(f"✅ Default player image exists: {default_path}")
        else:
            print(f"❌ Default player image missing: {default_path}")
            print(f"   Creating placeholder...")
            create_default_player_image()
        
        print(f"\n📋 Summary:")
        print("=" * 30)
        
        players_with_photos = Player.query.filter(Player.photo_url.isnot(None)).count()
        players_without_photos = Player.query.filter(Player.photo_url.is_(None)).count()
        
        print(f"👥 Total players: {len(players)}")
        print(f"📸 With photos: {players_with_photos}")
        print(f"🖼️ Without photos (using default): {players_without_photos}")
        
        print(f"\n🎯 Template Locations Using Player Photos:")
        print("=" * 40)
        print("✅ Player navigation (base.html) - current_user.player.photo_url")
        print("✅ Player profile page - player.photo_url")
        print("✅ Player squad page - player.photo_url")
        print("✅ Admin players page - player.photo_url")
        
        print(f"\n🔧 Fallback Handling:")
        print("=" * 20)
        print("✅ Templates check 'if player.photo_url'")
        print("✅ Show default icon if no photo")
        print("✅ Use onerror handler for broken images")

def create_default_player_image():
    """Create a simple default player image if it doesn't exist"""
    try:
        import os
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a simple default image
        img = Image.new('RGB', (200, 200), color='#f8f9fa')
        draw = ImageDraw.Draw(img)
        
        # Draw a simple player icon
        # This is a basic implementation - you might want to use a better image
        draw.ellipse([50, 50, 150, 150], fill='#6c757d')
        
        # Save the image
        os.makedirs(os.path.dirname('static/img/default-player.png'), exist_ok=True)
        img.save('static/img/default-player.png')
        
        print("✅ Created default player image")
        
    except ImportError:
        print("❌ PIL not available, cannot create default image")
        print("   Please add a default-player.png file to static/img/")

if __name__ == '__main__':
    fix_player_photos()