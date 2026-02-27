"""
Flask route handlers
"""

import json
import logging
import tempfile

from flask import Blueprint, jsonify, request

from backend.job_store import JobStore
from backend.services import FileUploadService, TranscriptionService
from backend.validators import FileValidator

logger = logging.getLogger(__name__)


def create_routes(
    config,
    transcription_service: TranscriptionService,
    file_upload_service: FileUploadService,
    job_store: JobStore,
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

    @api.route('/', methods=['GET', 'OPTIONS'])
    def root():
        """Root health check for Render and other platforms that ping / by default."""
        return jsonify({'status': 'ok', 'service': 'audio-transcription-api'}), 200

    @api.route('/health', methods=['GET', 'OPTIONS'])
    def health_check():
        """Health check endpoint"""
        return jsonify({'status': 'ok'}), 200
    
    @api.route('/transcribe', methods=['POST', 'OPTIONS'])
    def transcribe():
        """Accept upload, start async transcription, return 202 with job_id."""
        try:
            if 'audio' not in request.files:
                return jsonify({'error': 'No audio file provided'}), 400

            file = request.files['audio']

            try:
                chunk_length = int(request.form.get('chunk_length', config.default_chunk_length))
            except (ValueError, TypeError):
                chunk_length = config.default_chunk_length
            chunk_length = file_upload_service.validator.validate_chunk_length(chunk_length)

            temp_dir = tempfile.mkdtemp(prefix='audio_upload_')
            try:
                file_path = file_upload_service.save_uploaded_file(file, temp_dir)
            except ValueError as e:
                return jsonify({'error': str(e)}), 400

            is_valid, size_error = transcription_service.validator.validate_file_size(file_path)
            if not is_valid:
                return jsonify({'error': size_error}), 400

            job_id = job_store.create(
                status='processing',
                progress=0,
                message='File uploaded, starting transcription...',
            )
            transcription_service.start_async_transcription(
                file_path=file_path,
                chunk_length=chunk_length,
                job_id=job_id,
            )
            status_path = f'/transcribe/status/{job_id}'
            logger.info("Accepted job %s; poll GET %s for progress", job_id[:8], status_path)
            return (
                jsonify({
                    'job_id': job_id,
                    'status': 'processing',
                    'status_url': status_path,
                }),
                202,
            )
        except Exception as e:
            logger.error(f"Request error: {e}", exc_info=True)
            return jsonify({'error': 'Internal server error'}), 500

    @api.route('/transcribe/status/<job_id>', methods=['GET', 'OPTIONS'])
    def transcribe_status(job_id):
        """Return current job status (for polling)."""
        job = job_store.get(job_id)
        if not job:
            logger.warning("Status requested for unknown job: %s", job_id)
            return jsonify({'error': 'Job not found'}), 404
        # Log progress so you can see activity in the backend terminal
        if job['status'] == 'processing':
            logger.info("Job %s: %s%% - %s", job_id[:8], job.get('progress', 0), job.get('message', ''))
        elif job['status'] in ('completed', 'failed'):
            logger.info("Job %s: %s", job_id[:8], job['status'])
        return jsonify({
            'id': job['id'],
            'status': job['status'],
            'progress': job['progress'],
            'message': job['message'],
            'transcript': job.get('transcript'),
            'error': job.get('error'),
        })

    return api


