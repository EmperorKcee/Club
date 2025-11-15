#!/usr/bin/env python3
"""
Test script to demonstrate login page customization with team settings
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import TeamSettings

def test_login_customization():
    """Test login page customization"""
    with app.app_context():
        print("🎨 Testing Login Page Customization")
        print("=" * 50)
        
        # Get current settings
        settings = TeamSettings.get_settings()
        
        print("📋 Current Settings:")
        print(f"   Team Name: {settings.team_name}")
        print(f"   Logo: {settings.logo_url}")
        print(f"   Primary Color: {settings.primary_color}")
        
        # Test different team configurations
        test_configs = [
            {
                'name': 'Manchester United FC',
                'color': '#DA020E',
                'description': 'Classic red theme'
            },
            {
                'name': 'Barcelona FC', 
                'color': '#A50044',
                'description': 'Blue and red theme'
            },
            {
                'name': 'Real Madrid CF',
                'color': '#FEBE10', 
                'description': 'Gold and white theme'
            }
        ]
        
        print("\n🧪 Test Configurations Available:")
        for i, config in enumerate(test_configs, 1):
            print(f"   {i}. {config['name']} - {config['description']} ({config['color']})")
        
        print("\n🔧 To Test Different Configurations:")
        print("   1. Login as admin: http://localhost:5000/auth")
        print("   2. Go to Settings: http://localhost:5000/settings")
        print("   3. Change team name and primary color")
        print("   4. Visit login page: http://localhost:5000/auth")
        print("   5. See the changes immediately!")
        
        print("\n✨ What Changes on Login Page:")
        print("   🏷️  Page title (browser tab)")
        print("   🖼️  Team logo (if uploaded)")
        print("   📝 Welcome message ('Welcome to [Team Name]')")
        print("   🎨 Background gradient (uses primary color)")
        print("   🌈 Button colors (throughout the system)")
        
        print("\n🎯 Login Page Features:")
        print("   ✅ Dynamic team branding")
        print("   ✅ Responsive design")
        print("   ✅ Dual login system (Admin/Player)")
        print("   ✅ Team color theming")
        print("   ✅ Custom logo support")
        
        print("\n🚀 Quick Test:")
        print("   1. Visit: http://localhost:5000/auth")
        print("   2. Note current team name and colors")
        print("   3. Login as admin and change settings")
        print("   4. Return to login page to see changes")
        
        print(f"\n🔑 Admin Login: admin / admin123")
        print(f"🌐 Login URL: http://localhost:5000/auth")

if __name__ == '__main__':
    test_login_customization()