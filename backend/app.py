#!/usr/bin/env python3
"""
Flask API server for audio transcription
Handles file uploads and transcription requests
"""

import logging
import os

from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import RequestEntityTooLarge

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
    
    # Set Flask's MAX_CONTENT_LENGTH to allow large file uploads
    # Set it significantly higher than max_file_size to allow validation in service layer
    # This gives us protection against extremely large files while allowing service-level validation
    # Use 2x max_file_size to ensure files can pass through for validation
    app.config['MAX_CONTENT_LENGTH'] = config.max_file_size * 2
    
    # Register error handler for file size limit
    @app.errorhandler(RequestEntityTooLarge)
    def handle_request_entity_too_large(e):
        """Handle 413 Request Entity Too Large errors"""
        max_size_mb = config.max_file_size / (1024 * 1024)
        return jsonify({'error': f'File too large. Maximum size: {max_size_mb:.0f} MB'}), 413
    
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
