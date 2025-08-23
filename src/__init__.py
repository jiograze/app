"""
Mevzuat - A legal document management and analysis system
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'web.login'

# Import models to ensure they are registered with SQLAlchemy
from src.core import models  # noqa

def create_app(config_name=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import config as config_module
    cfg = config_module.config[config_name or os.getenv('FLASK_ENV', 'development')]
    cfg.init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    CORS(app)
    
    # Register blueprints
    from mevzuat.api import api_bp
    from mevzuat.web import web_bp
    
    app.register_blueprint(api_bp, url_prefix=app.config['API_PREFIX'])
    app.register_blueprint(web_bp)
    
    # Create necessary directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register error handlers
    from mevzuat.core.errors import register_error_handlers
    register_error_handlers(app)
    
    # Register CLI commands
    from mevzuat.core import commands
    commands.init_app(app)
    
    return app
