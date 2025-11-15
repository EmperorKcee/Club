#!/usr/bin/env python3
"""
Test script to debug player PDF photo issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import Player

def test_player_pdf_photos():
    """Test player photo paths for PDF generation"""
    print("📸 Testing Player PDF Photo Paths")
    print("=" * 50)
    
    with app.app_context():
        # Get a sample player
        player = Player.query.first()
        if not player:
            print("❌ No players found in database")
            return
        
        print(f"🎯 Testing player: {player.full_name}")
        print(f"   Player ID: {player.id}")
        print(f"   Photo URL: {player.photo_url}")
        
        # Test photo path resolution
        if player.photo_url:
            print("\n📁 Testing photo path resolution...")
            
            # Test different path formats
            photo_url = player.photo_url
            print(f"   Original photo_url: {photo_url}")
            
            # Remove leading slash or 'static/' if present
            if photo_url.startswith('/static/'):
                photo_url = photo_url[8:]  # Remove '/static/'
                print(f"   After removing '/static/': {photo_url}")
            elif photo_url.startswith('static/'):
                photo_url = photo_url[7:]  # Remove 'static/'
                print(f"   After removing 'static/': {photo_url}")
            elif photo_url.startswith('/'):
                photo_url = photo_url[1:]  # Remove leading '/'
                print(f"   After removing '/': {photo_url}")
            
            # Construct the full path
            img_path = os.path.join(app.root_path, 'static', photo_url)
            print(f"   Full path: {img_path}")
            
            # Check if file exists
            if os.path.exists(img_path):
                print("   ✅ Photo file exists")
                
                # Check if it's a file
                if os.path.isfile(img_path):
                    print("   ✅ Path is a file")
                    
                    # Check file extension
                    valid_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
                    file_ext = os.path.splitext(img_path)[1].lower()
                    print(f"   File extension: {file_ext}")
                    
                    if file_ext in valid_extensions:
                        print("   ✅ Valid image format")
                        
                        # Check file size
                        file_size = os.path.getsize(img_path)
                        print(f"   File size: {file_size} bytes")
                        
                        if file_size > 0:
                            print("   ✅ File has content")
                        else:
                            print("   ❌ File is empty")
                    else:
                        print("   ❌ Invalid image format")
                else:
                    print("   ❌ Path is not a file")
            else:
                print("   ❌ Photo file does not exist")
                
                # Check if directory exists
                photo_dir = os.path.dirname(img_path)
                if os.path.exists(photo_dir):
                    print(f"   📁 Directory exists: {photo_dir}")
                    # List files in directory
                    try:
                        files = os.listdir(photo_dir)
                        print(f"   Files in directory: {files[:10]}")  # Show first 10 files
                    except Exception as e:
                        print(f"   Error listing directory: {e}")
                else:
                    print(f"   ❌ Directory does not exist: {photo_dir}")
        else:
            print("   ⚠️  Player has no photo_url set")
        
        # Test default photo
        print("\n🖼️  Testing default player photo...")
        default_photo_path = os.path.join(app.root_path, 'static', 'img', 'default-player.png')
        print(f"   Default photo path: {default_photo_path}")
        
        if os.path.exists(default_photo_path):
            print("   ✅ Default photo exists")
            file_size = os.path.getsize(default_photo_path)
            print(f"   File size: {file_size} bytes")
        else:
            print("   ❌ Default photo does not exist")
            
            # Check if img directory exists
            img_dir = os.path.join(app.root_path, 'static', 'img')
            if os.path.exists(img_dir):
                print(f"   📁 img directory exists")
                try:
                    files = os.listdir(img_dir)
                    print(f"   Files in img directory: {files}")
                except Exception as e:
                    print(f"   Error listing img directory: {e}")
            else:
                print(f"   ❌ img directory does not exist: {img_dir}")
        
        # Test PDF generation
        print("\n📄 Testing PDF generation...")
        try:
            with app.test_client() as client:
                # Login as admin first
                with client.session_transaction() as sess:
                    sess['_user_id'] = '1'  # Assume admin user ID is 1
                    sess['_fresh'] = True
                
                response = client.get(f'/players/{player.id}/download')
                print(f"   PDF download status: {response.status_code}")
                
                if response.status_code == 200:
                    print("   ✅ PDF generated successfully")
                    print(f"   Content type: {response.content_type}")
                    print(f"   Content length: {len(response.data)} bytes")
                else:
                    print("   ❌ PDF generation failed")
                    
        except Exception as e:
            print(f"   ❌ Error testing PDF generation: {e}")

if __name__ == "__main__":
    test_player_pdf_photos()