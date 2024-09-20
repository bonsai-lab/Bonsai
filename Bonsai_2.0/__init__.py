# __init__.py

from flask import Flask
from db import init_db

def create_app():
    app = Flask(__name__)

    # Initialize the database
    with app.app_context():
        init_db()

    # Register routes and other setup
    from . import routes  # Import your routes module (e.g., routes.py)
    app.register_blueprint(routes.bp)

    return app
