"""
Flask route handlers
"""

import logging
import os
import tempfile
from typing import Tuple

from flask import Blueprint, Response, jsonify, request, stream_with_context

from backend.services import FileUploadService, TranscriptionService
from backend.validators import FileValidator

logger = logging.getLogger(__name__)

api = Blueprint('api', __name__)


def create_routes(
    config,
    transcription_service: TranscriptionService,
    file_upload_service: FileUploadService
) -> Blueprint:
    """
    Create and configure API routes.
    
    Args:
        config: Application configuration
        transcription_service: Transcription service instance
        file_upload_service: File upload service instance
    
    Returns:
        Configured Blueprint
    """
    
    @api.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({'status': 'ok'}), 200
    
    @api.route('/transcribe', methods=['POST'])
    def transcribe():
        """Handle audio file upload and transcription"""
        try:
            # Validate request
            if 'audio' not in request.files:
                return jsonify({'error': 'No audio file provided'}), 400
            
            file = request.files['audio']
            
            # Get and validate chunk length
            try:
                chunk_length = int(request.form.get('chunk_length', config.default_chunk_length))
            except (ValueError, TypeError):
                chunk_length = config.default_chunk_length
            
            chunk_length = file_upload_service.validator.validate_chunk_length(chunk_length)
            
            # Save uploaded file
            temp_dir = tempfile.mkdtemp(prefix='audio_upload_')
            try:
                file_path = file_upload_service.save_uploaded_file(file, temp_dir)
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
            
            # Create generator for streaming response
            def generate():
                """Generator function for streaming transcription progress"""
                try:
                    yield from transcription_service.transcribe_file(
                        file_path=file_path,
                        chunk_length=chunk_length
                    )
                finally:
                    # Cleanup will be handled by service
                    pass
            
            return Response(
                stream_with_context(generate()),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'X-Accel-Buffering': 'no'
                }
            )
            
        except Exception as e:
            logger.error(f"Request error: {e}", exc_info=True)
            return jsonify({'error': 'Internal server error'}), 500
    
    return api

