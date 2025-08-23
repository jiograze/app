""
Core package for Mevzuat Yönetim Sistemi.

This package contains the core functionality of the application,
including database models, services, and utilities.
"""

__all__ = ['create_app', 'db']

import os
import yaml
from pathlib import Path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def load_config(config_path=None):
    """Load configuration from YAML file."""
    if config_path is None:
        # Default to development config
        config_path = os.path.join(os.path.dirname(__file__), '../../config/development.yaml')
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Ensure upload folder exists
    upload_folder = config['storage'].get('upload_folder')
    if upload_folder:
        os.makedirs(upload_folder, exist_ok=True)
    
    return config

def create_app(config_path=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    config = load_config(config_path)
    app.config.update(config)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    from mevzuat.api import api_bp
    from mevzuat.web.views import web_bp
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(web_bp)
    
    # Create necessary directories
    os.makedirs(app.config['storage']['upload_folder'], exist_ok=True)
    
    return app
