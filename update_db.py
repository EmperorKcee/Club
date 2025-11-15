from app import app, db

def update_database():
    with app.app_context():
        # This will add any missing columns to existing tables
        db.create_all()
        print("Database schema updated successfully!")

if __name__ == '__main__':
    update_database()
