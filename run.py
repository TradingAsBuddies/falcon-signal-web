"""Main entry point for the sangre-signal web application."""

import os
from app import create_app

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    # Run in development mode
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_ENV') == 'development'
    )