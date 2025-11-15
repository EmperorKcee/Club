from app import app, db
from models import Player, Match

def remove_sample_data():
    with app.app_context():
        try:
            # Delete all matches
            num_matches = Match.query.delete()
            
            # Delete all players
            num_players = Player.query.delete()
            
            # Commit the changes
            db.session.commit()
            
            print(f"Successfully removed {num_players} players and {num_matches} matches from the database.")
            
        except Exception as e:
            db.session.rollback()
            print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    remove_sample_data()
