#!/usr/bin/env python3
"""
Flask API server for audio transcription
Handles file uploads and transcription requests
"""

import logging
import os

from flask import Flask
from flask_cors import CORS

from backend.config import Config
from backend.routes import create_routes
from backend.services import FileUploadService, TranscriptionService
from backend.validators import FileValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config: Config = None) -> Flask:
    """
    Application factory pattern.
    
    Args:
        config: Optional configuration object
    
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    CORS(app)  # Enable CORS for GitHub Pages
    
    # Load configuration
    if config is None:
        try:
            config = Config.from_env()
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            raise
    
    # Initialize services
    validator = FileValidator(
        allowed_extensions=config.allowed_extensions,
        max_size=config.max_file_size
    )
    transcription_service = TranscriptionService(config)
    file_upload_service = FileUploadService(validator)
    
    # Register routes
    api_blueprint = create_routes(
        config=config,
        transcription_service=transcription_service,
        file_upload_service=file_upload_service
    )
    app.register_blueprint(api_blueprint)
    
    return app


# Create app instance
app = create_app()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
