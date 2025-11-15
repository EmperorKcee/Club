#!/usr/bin/env python3
"""
Script to fix admin user role issues
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User

def fix_admin_user():
    """Fix admin user role and create if doesn't exist"""
    with app.app_context():
        print("🔧 Fixing admin user...")
        
        # Check for existing admin user by username
        admin = User.query.filter_by(username='admin').first()
        
        if admin:
            print(f"Found admin user: {admin.username}")
            print(f"Current role: {admin.role}")
            
            # Fix the role if it's not 'admin'
            if admin.role != 'admin':
                admin.role = 'admin'
                db.session.commit()
                print("✅ Fixed admin user role")
            else:
                print("✅ Admin user role is already correct")
        else:
            print("No admin user found, creating one...")
            
            # Create new admin user
            admin = User(
                username='admin',
                email='admin@zambiafc.com',
                first_name='Admin',
                last_name='User',
                role='admin'
            )
            admin.set_password('admin123')
            
            db.session.add(admin)
            db.session.commit()
            print("✅ Created new admin user")
        
        # Verify the admin user
        admin = User.query.filter_by(username='admin').first()
        print(f"\n📋 Admin User Details:")
        print(f"   Username: {admin.username}")
        print(f"   Email: {admin.email}")
        print(f"   Role: {admin.role}")
        print(f"   ID: {admin.id}")
        
        # Check all users
        all_users = User.query.all()
        print(f"\n👥 All Users ({len(all_users)}):")
        for user in all_users:
            print(f"   {user.username} - {user.role}")
        
        print(f"\n🎉 Admin user is ready!")
        print(f"   Login URL: http://localhost:5000/auth?type=admin")
        print(f"   Username: admin")
        print(f"   Password: admin123")

if __name__ == '__main__':
    fix_admin_user()