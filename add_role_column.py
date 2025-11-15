from app import app, db
from sqlalchemy import text

def add_role_column():
    with app.app_context():
        # Add the role column with a default value of 'player'
        with db.engine.connect() as connection:
            connection.execute(text('ALTER TABLE player_user ADD COLUMN role VARCHAR(20) DEFAULT "player"'))
            connection.commit()
        print("Successfully added 'role' column to player_user table")

if __name__ == '__main__':
    add_role_column()
