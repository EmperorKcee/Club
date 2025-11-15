import os
import sqlite3
from app import create_app, db

def fix_database():
    app = create_app()
    
    with app.app_context():
        try:
            # Get the database path
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            
            # Close any existing connections
            db.session.close()
            
            # Delete the database file if it exists
            if os.path.exists(db_path):
                os.remove(db_path)
                print(f"Removed existing database: {db_path}")
            
            # Create a new database
            db.create_all()
            print("Created a new database with all tables")
            
            # Verify the reset
            from models import Player, PlayerStats
            print(f"Players: {Player.query.count()}")
            print(f"PlayerStats: {PlayerStats.query.count()}")
            
            print("\nDatabase has been reset successfully!")
            
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        finally:
            if 'db' in locals():
                db.session.close()

if __name__ == '__main__':
    fix_database()
