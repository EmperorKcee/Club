import os
from datetime import timedelta

class Config:
    # App Settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///club.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email Settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)
    
    # Player Portal URLs
    PLAYER_BASE_URL = os.environ.get('PLAYER_BASE_URL', 'http://localhost:5000/player')
    PLAYER_LOGIN_URL = f"{PLAYER_BASE_URL}/login"
    
    # Security
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT', 'your-password-salt-here')
    SECURITY_PASSWORD_HASH = 'bcrypt'
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # File Uploads
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # LogGING
    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
        },
        'handlers': {
            'file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/app.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'formatter': 'standard',
            },
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
            },
        },
        'loggers': {
            '': {
                'handlers': ['file', 'console'],
                'level': 'INFO',
                'propagate': True
            },
        }
    }


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True
    MAIL_DEBUG = True
    MAIL_SUPPRESS_SEND = False
    

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    MAIL_SUPPRESS_SEND = True


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False
    MAIL_DEBUG = False
    
    # Force HTTPS in production
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
