import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Boolean, Date, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Add the current directory to the path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the app and db
from app import create_app, db
from models import Match

def update_database():
    app = create_app()
    with app.app_context():
        # Check if the column already exists
        inspector = db.inspect(db.engine)
        columns = [column['name'] for column in inspector.get_columns('match')]
        
        if 'opponent_logo' not in columns:
            print("Adding opponent_logo column to match table...")
            # Create a new engine with SQLite pragma to support ALTER TABLE
            from sqlalchemy import text
            
            # Add the new column
            with db.engine.connect() as conn:
                # Enable foreign key support
                conn.execute(text('PRAGMA foreign_keys=OFF'))
                # Create a new table with the new schema
                conn.execute(text('''
                    CREATE TABLE match_new (
                        id INTEGER NOT NULL, 
                        opponent VARCHAR(100) NOT NULL, 
                        opponent_logo VARCHAR(200), 
                        match_date DATETIME NOT NULL, 
                        venue VARCHAR(50) NOT NULL, 
                        competition VARCHAR(100), 
                        home_goals INTEGER, 
                        away_goals INTEGER, 
                        status VARCHAR(20), 
                        match_report TEXT, 
                        PRIMARY KEY (id)
                    )
                '''))
                
                # Copy data from old table to new table
                conn.execute(text('''
                    INSERT INTO match_new (id, opponent, match_date, venue, competition, home_goals, away_goals, status, match_report)
                    SELECT id, opponent, match_date, venue, competition, home_goals, away_goals, status, match_report
                    FROM "match"
                '''))
                
                # Drop the old table
                conn.execute(text('DROP TABLE "match"'))
                
                # Rename new table to match
                conn.execute(text('ALTER TABLE match_new RENAME TO "match"'))
                
                # Recreate indexes if any
                # conn.execute(text('CREATE INDEX ix_match_status ON "match" (status)'))
                
                # Commit the transaction
                conn.commit()
                
            print("Database schema updated successfully!")
        else:
            print("opponent_logo column already exists in match table.")

if __name__ == '__main__':
    update_database()
