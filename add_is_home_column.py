from app import app, db
from models import Match
from sqlalchemy import text

def add_is_home_column():
    with app.app_context():
        # Check if the column exists
        inspector = db.inspect(db.engine)
        columns = [column['name'] for column in inspector.get_columns('match')]
        
        if 'is_home' not in columns:
            # Add the column if it doesn't exist
            with db.engine.connect() as connection:
                connection.execute(text('ALTER TABLE "match" ADD COLUMN is_home BOOLEAN DEFAULT TRUE'))
                connection.commit()
            print("Added 'is_home' column to 'match' table with default value True")
        else:
            print("'is_home' column already exists in 'match' table")

if __name__ == '__main__':
    add_is_home_column()
