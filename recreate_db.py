import os
import sys
from app import app, db
from models import User
from werkzeug.security import generate_password_hash

def create_tables():
    with app.app_context():
        try:
            print("Dropping all tables...")
            db.drop_all()
            print("Creating all tables...")
            db.create_all()
            
            # Create admin user
            admin = User(
                username='admin',
                email='admin@example.com',
                first_name='Admin',
                last_name='User',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            
            print("Database recreated successfully!")
            print("Admin user created:")
            print(f"Username: admin")
            print(f"Password: admin123")
            
        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()
            sys.exit(1)

if __name__ == '__main__':
    print("=== Database Recreator ===")
    print("This will DROP ALL TABLES and recreate them.")
    response = input("Are you sure you want to continue? (yes/no): ")
    if response.lower() in ('y', 'yes'):
        create_tables()
    else:
        print("Operation cancelled.")
