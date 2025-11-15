from app import app, db
from flask_migrate import Migrate, upgrade

def run_migrations():
    with app.app_context():
        # Create the database and tables if they don't exist
        db.create_all()
        
        # Get the migration directory
        from flask_migrate import stamp
        import os
        
        # Initialize migrations if the migrations directory doesn't exist
        if not os.path.exists('migrations'):
            from flask_migrate import init
            init()
            
            # Stamp the initial migration
            stamp()
        
        # Create a new migration
        from flask_migrate import migrate as migrate_cmd
        migrate_cmd(message='Add text_color to team_settings')
        
        # Apply the migration
        upgrade()

if __name__ == '__main__':
    run_migrations()
