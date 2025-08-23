"""Configuration management for Mevzuat Yönetim Sistemi."""
import os
from pathlib import Path
from dotenv import load_dotenv
import yaml

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    """Base configuration."""
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    DEBUG = os.getenv('FLASK_ENV', 'development') == 'development'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///' + str(BASE_DIR / 'mevzuat.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File uploads
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', str(BASE_DIR / 'uploads'))
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    ALLOWED_EXTENSIONS = set(
        os.getenv('ALLOWED_EXTENSIONS', 'pdf,doc,docx,xls,xlsx,ppt,pptx,txt').split(',')
    )
    
    # ML Model
    MODEL_PATH = os.getenv('MODEL_PATH', str(BASE_DIR / 'models/bert-base-turkish-cased'))
    DEVICE = os.getenv('DEVICE', 'cpu')
    
    # API
    API_PREFIX = os.getenv('API_PREFIX', '/api/v1')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', str(BASE_DIR / 'logs/app.log'))
    
    # Create necessary directories
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

    @classmethod
    def init_app(cls, app):
        """Initialize Flask application with configuration."""
        app.config.from_object(cls)
        
        # Load YAML config if exists
        config_path = BASE_DIR / 'config' / f"{os.getenv('FLASK_ENV', 'development')}.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                app.config.update(yaml.safe_load(f))
        
        # Ensure upload folder exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_ECHO = False


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
