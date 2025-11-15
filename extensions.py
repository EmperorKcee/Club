from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_socketio import SocketIO

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'login'
migrate = Migrate()
mail = Mail()
csrf = CSRFProtect()
socketio = SocketIO(cors_allowed_origins="*")
