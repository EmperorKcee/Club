from app import app, db
from models import User, Player, Match, FinancialRecord

with app.app_context():
    # Create all database tables
    db.create_all()
    
    # Create an admin user if it doesn't exist
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@example.com',
            role='admin'
        )
        admin.set_password('admin123')  # Change this in production!
        db.session.add(admin)
        db.session.commit()
        print("Created admin user with username: admin and password: admin123")
    
    print("Database tables created successfully!")
