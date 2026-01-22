"""Flask application initialization for sangre-signal web interface."""

from flask import Flask
from flask_wtf.csrf import CSRFProtect


def create_app():
    """Create and configure the Flask application.
    
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600
    
    # Enable CSRF protection
    csrf = CSRFProtect(app)
    
    # Register blueprints/routes
    from .routes import main_bp
    app.register_blueprint(main_bp)
    
    return app