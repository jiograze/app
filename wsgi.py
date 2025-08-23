"""
WSGI entry point for the Mevzuat Yönetim Sistemi.

This module is used by production WSGI servers like Gunicorn.
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.absolute())
src_path = os.path.join(project_root, 'src')

if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Set the environment to production by default
os.environ.setdefault('FLASK_ENV', 'production')

# Import the application factory
from mevzuat import create_app

# Create the application instance
app = create_app()

# For development server (not used in production)
if __name__ == "__main__":
    import logging
    from werkzeug.middleware.proxy_fix import ProxyFix
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('app.log')
        ]
    )
    
    # Use ProxyFix if running behind a reverse proxy
    app.wsgi_app = ProxyFix(
        app.wsgi_app, 
        x_for=1, 
        x_proto=1, 
        x_host=1, 
        x_prefix=1
    )
    
    # Run the development server
    app.run(
        host=app.config.get('HOST', '0.0.0.0'),
        port=int(app.config.get('PORT', 5000)),
        use_reloader=app.debug,
        threaded=True,
        ssl_context='adhoc' if app.config.get('USE_SSL', False) else None
    )
