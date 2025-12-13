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
    # Create a new blueprint for each call to avoid conflicts in tests
    api = Blueprint('api', __name__)
    
    @api.route('/health', methods=['GET', 'OPTIONS'])
    def health_check():
        """Health check endpoint"""
        return jsonify({'status': 'ok'}), 200
    
    @api.route('/transcribe', methods=['POST', 'OPTIONS'])
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
            
            # Create streaming response (CORS headers handled by Flask-CORS)
            # Important headers for long-running SSE connections:
            # - Connection: keep-alive - keeps HTTP connection open
            # - X-Accel-Buffering: no - prevents nginx/proxy buffering
            # - Cache-Control: no-cache - prevents caching of SSE stream
            response = Response(
                stream_with_context(generate()),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'X-Accel-Buffering': 'no',
                    'Transfer-Encoding': 'chunked',
                }
            )
            return response
            
        except Exception as e:
            logger.error(f"Request error: {e}", exc_info=True)
            return jsonify({'error': 'Internal server error'}), 500
    
    return api


