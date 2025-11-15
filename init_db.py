from app import create_app, db
from models import Player, PlayerStats

def init_db():
    app = create_app()
    with app.app_context():
        # Create all database tables
        db.create_all()
        
        # For existing players, ensure they have stats
        players_without_stats = Player.query.filter(Player.stats == None).all()
        for player in players_without_stats:
            player.stats = PlayerStats()
        
        if players_without_stats:
            db.session.commit()
            print(f"Added stats for {len(players_without_stats)} players.")
        else:
            print("No players without stats found.")

if __name__ == '__main__':
    init_db()
