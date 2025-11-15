from app import app, db
from flask_migrate import Migrate, upgrade, migrate as migrate_cmd, init, stamp
import os

def run_migrations():
    # Set the FLASK_APP environment variable
    os.environ['FLASK_APP'] = 'app.py'
    
    # Initialize the app context
    with app.app_context():
        # Initialize migrations directory if it doesn't exist
        if not os.path.exists('migrations'):
            print("Initializing migrations...")
            init()
            
            # Stamp the initial migration
            print("Stamping initial migration...")
            stamp()
        
        # Create a new migration
        print("Creating migration...")
        migrate_cmd(message='Add text_color to team_settings')
        
        # Apply the migration
        print("Applying migration...")
        upgrade()
        
        print("Database migration completed successfully!")

if __name__ == '__main__':
    run_migrations()
