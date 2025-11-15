from app import create_app, db
from models import TrainingSession, PlayerAttendance

def clear_training_data():
    app = create_app()
    with app.app_context():
        try:
            # First delete all player attendance records
            PlayerAttendance.query.delete()
            
            # Then delete all training sessions
            num_deleted = TrainingSession.query.delete()
            
            db.session.commit()
            print(f"Successfully deleted {num_deleted} training sessions and all related attendance records.")
        except Exception as e:
            db.session.rollback()
            print(f"An error occurred: {str(e)}")

if __name__ == '__main__':
    clear_training_data()
