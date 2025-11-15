import os
from app import create_app, db
from models import Player, PlayerStats, Match, User, FinancialRecord

def reset_database():
    # Create the Flask application
    app = create_app()
    
    with app.app_context():
        try:
            print("Dropping all tables...")
            # Drop all tables
            db.drop_all()
            
            print("Creating all tables...")
            # Recreate all tables
            db.create_all()
            
            # Reset SQLite sequences
            if db.engine.url.drivername == 'sqlite':
                db.session.execute("DELETE FROM sqlite_sequence")
            
            db.session.commit()
            print("Database has been reset successfully!")
            
            # Verify the reset
            print("\nVerification:")
            print(f"Players: {Player.query.count()}")
            print(f"PlayerStats: {PlayerStats.query.count()}")
            print(f"Matches: {Match.query.count()}")
            
        except Exception as e:
            db.session.rollback()
            print(f"An error occurred: {str(e)}")
        finally:
            db.session.close()

if __name__ == '__main__':
    reset_database()
