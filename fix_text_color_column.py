import sqlite3
import os
from app import app

def add_text_color_column():
    # Get the database path from Flask config or use default
    db_path = os.path.join(app.instance_path, 'club.db')
    
    print(f"Connecting to database at: {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(team_settings)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'text_color' not in columns:
            print("Adding text_color column to team_settings table...")
            cursor.execute("""
                ALTER TABLE team_settings 
                ADD COLUMN text_color TEXT DEFAULT '#ffffff'
            """)
            conn.commit()
            print("Successfully added text_color column.")
            
            # Update any existing rows with the default value
            cursor.execute("""
                UPDATE team_settings 
                SET text_color = '#ffffff' 
                WHERE text_color IS NULL
            """)
            conn.commit()
            print("Updated existing rows with default text color.")
        else:
            print("text_color column already exists.")
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == '__main__':
    with app.app_context():
        add_text_color_column()
    print("Script completed.")
