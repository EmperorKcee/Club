from app import app, db
from models import Player, PlayerStats

def cleanup_database():
    with app.app_context():
        try:
            # Delete all PlayerStats records
            num_stats = PlayerStats.query.delete()
            
            # Reset SQLite sequence for PlayerStats table
            db.session.execute("DELETE FROM sqlite_sequence WHERE name='player_stats'")
            
            # Commit the changes
            db.session.commit()
            
            print(f"Successfully removed {num_stats} PlayerStats records.")
            print("Database cleanup complete!")
            
        except Exception as e:
            db.session.rollback()
            print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    cleanup_database()
