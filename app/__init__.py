"""
Flask Application for WikiGraph API

Provides RESTful API endpoints for the multi-language Wikipedia knowledge graph.
"""

from flask import Flask
from flask_cors import CORS
from pathlib import Path
import os

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Enable CORS for all routes
    CORS(app)

    # Load configuration
    app.config.from_object('app.config.Config')

    # Register blueprints
    from app.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
