import os
import sys
import time
import sqlite3
from app import app, db

def reset_database():
    with app.app_context():
        # Close any existing database connections
        db.session.close()
        
        # Database files to handle
        db_files = [
            os.path.join('instance', 'club.db'),
            os.path.join('instance', 'football_club.db')
        ]
        
        for db_file in db_files:
            if os.path.exists(db_file):
                print(f"Attempting to remove {db_file}...")
                try:
                    # Try to remove the file
                    os.remove(db_file)
                    print(f"Successfully deleted {db_file}")
                    # Wait a moment to ensure the file is released
                    time.sleep(1)
                except PermissionError as e:
                    print(f"Error deleting {db_file}: {e}")
                    print("Please make sure the Flask server is not running and try again.")
                    sys.exit(1)
                except Exception as e:
                    print(f"Unexpected error with {db_file}: {e}")
                    sys.exit(1)
        
        try:
            # Create all tables
            print("Creating database tables...")
            db.create_all()
            print("Database tables created successfully!")
            
            # Add a default admin user if needed
            from models import User
            from werkzeug.security import generate_password_hash
            
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
            print("Created default admin user (username: admin, password: admin123)")
            
        except Exception as e:
            print(f"Error creating database: {e}")
            sys.exit(1)

if __name__ == '__main__':
    print("=== Database Reset Tool ===")
    print("WARNING: This will delete all data in the database!")
    response = input("Are you sure you want to continue? (yes/no): ")
    if response.lower() in ('y', 'yes'):
        reset_database()
    else:
        print("Database reset cancelled.")
        sys.exit(0)
