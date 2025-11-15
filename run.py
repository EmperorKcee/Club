from app import app, db, manager
from flask_migrate import Migrate, MigrateCommand

# Initialize Flask-Migrate
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
