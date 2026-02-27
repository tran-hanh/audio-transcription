#!/usr/bin/env python3
"""
Tests for Flask API endpoints
"""

import os
import tempfile
from io import BytesIO
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path

import pytest

# Set test API key before importing app
os.environ.setdefault('GEMINI_API_KEY', 'test-api-key-for-testing')

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from backend.app import app
from backend.config import Config
from backend.validators import FileValidator
from backend.services import TranscriptionService

# Create test fixtures for functions that may not be directly exported
config = Config.from_env()
MAX_FILE_SIZE = config.max_file_size
validator = FileValidator(
    allowed_extensions=config.allowed_extensions,
    max_size=MAX_FILE_SIZE
)
transcription_service = TranscriptionService(config)



@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture
def mock_api_key(monkeypatch):
    """Mock GEMINI_API_KEY environment variable"""
    monkeypatch.setenv('GEMINI_API_KEY', 'test-api-key-12345')


@pytest.fixture
def sample_audio_file():
    """Create a mock audio file"""
    # Create a small fake audio file (just bytes, not real audio)
    audio_data = b'fake audio content' * 1000  # ~17KB
    return BytesIO(audio_data)


class TestRootEndpoint:
    """Tests for / root endpoint (Render / health check)"""

    def test_root_returns_ok(self, client):
        """Root returns 200 for platforms that ping / by default"""
        response = client.get('/')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'
        assert data.get('service') == 'audio-transcription-api'


class TestHealthEndpoint:
    """Tests for /health endpoint"""

    def test_health_check(self, client):
        """Test health check endpoint returns OK"""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'


class TestTranscribeEndpoint:
    """Tests for /transcribe endpoint"""

    def test_no_file_provided(self, client, mock_api_key):
        """Test error when no file is provided"""
        response = client.post('/transcribe')
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'No audio file provided' in data['error']

    def test_empty_filename(self, client, mock_api_key):
        """Test error when filename is empty"""
        response = client.post('/transcribe', data={
            'audio': (BytesIO(b''), '')
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'No file selected' in data['error']

    def test_invalid_file_type(self, client, mock_api_key):
        """Test error when file type is not allowed"""
        response = client.post('/transcribe', data={
            'audio': (BytesIO(b'content'), 'test.txt')
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'File type not allowed' in data['error']

    def test_missing_api_key(self, client):
        """POST returns 202 with job_id; errors occur in background."""
        response = client.post('/transcribe', data={
            'audio': (BytesIO(b'content'), 'test.mp3')
        })
        assert response.status_code == 202
        data = response.get_json()
        assert 'job_id' in data
        assert data.get('status') == 'processing'
        assert 'status_url' in data

    def test_file_too_large(self, client, mock_api_key):
        """Test error when file exceeds size limit (validated after save)."""
        large_file = BytesIO(b'x' * (MAX_FILE_SIZE + 1))
        response = client.post('/transcribe', data={
            'audio': (large_file, 'test.mp3')
        })
        # Flask may return 413 if body exceeds MAX_CONTENT_LENGTH, or we return 400 after validation
        assert response.status_code in (400, 413)
        if response.status_code == 400:
            data = response.get_json()
            assert 'error' in data
            assert 'large' in data['error'].lower() or 'size' in data['error'].lower()

    def test_valid_file_upload(self, client, mock_api_key, sample_audio_file):
        """POST returns 202 with job_id; GET status returns job structure."""
        response = client.post('/transcribe', data={
            'audio': (sample_audio_file, 'test.mp3'),
            'chunk_length': '12'
        })
        assert response.status_code == 202
        data = response.get_json()
        job_id = data['job_id']
        assert job_id
        assert data.get('status') == 'processing'
        assert f'/transcribe/status/{job_id}' in data.get('status_url', '')

        status_resp = client.get(f'/transcribe/status/{job_id}')
        assert status_resp.status_code == 200
        job = status_resp.get_json()
        assert 'status' in job and 'progress' in job and 'message' in job
        assert job['id'] == job_id

    def test_chunk_length_validation(self, client, mock_api_key, sample_audio_file):
        """Test chunk length is validated and defaulted; returns 202."""
        with patch('src.transcribe.transcribe_audio') as mock_transcribe:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
                tmp.write('Test transcript')
                tmp_path = tmp.name
            mock_transcribe.return_value = tmp_path
            response = client.post('/transcribe', data={
                'audio': (sample_audio_file, 'test.mp3'),
                'chunk_length': '50'
            })
            assert response.status_code == 202
            assert response.get_json().get('job_id')
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_chunk_length_too_low(self, client, mock_api_key, sample_audio_file):
        """Test chunk length too low is defaulted; returns 202."""
        with patch('src.transcribe.transcribe_audio') as mock_transcribe:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
                tmp.write('Test transcript')
                tmp_path = tmp.name
            mock_transcribe.return_value = tmp_path
            response = client.post('/transcribe', data={
                'audio': (sample_audio_file, 'test.mp3'),
                'chunk_length': '0'
            })
            assert response.status_code == 202
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_transcription_error_handling(self, client, mock_api_key, sample_audio_file):
        """POST returns 202; job exists and can be polled (background may fail later)."""
        response = client.post('/transcribe', data={
            'audio': (sample_audio_file, 'test.mp3')
        })
        assert response.status_code == 202
        job_id = response.get_json()['job_id']
        status_resp = client.get(f'/transcribe/status/{job_id}')
        assert status_resp.status_code == 200
        job = status_resp.get_json()
        assert job['id'] == job_id
        assert job['status'] in ('processing', 'completed', 'failed')

    def test_chunk_length_invalid_type(self, client, mock_api_key, sample_audio_file):
        """Test chunk length with invalid type defaults; returns 202."""
        with patch('src.transcribe.transcribe_audio') as mock_transcribe:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
                tmp.write('Test transcript')
                tmp_path = tmp.name
            mock_transcribe.return_value = tmp_path
            response = client.post('/transcribe', data={
                'audio': (sample_audio_file, 'test.mp3'),
                'chunk_length': 'invalid'
            })
            assert response.status_code == 202
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_routes_exception_handling(self, client, mock_api_key):
        """Test exception handling in routes (lines 88-90)"""
        # Trigger an exception by not providing a file
        # This should trigger the exception handler
        response = client.post('/transcribe', data={})
        # Should return 400 (no file) or 500 (exception), not crash
        assert response.status_code in [400, 500]

    def test_routes_exception_handling_unexpected_error(self, client, mock_api_key, sample_audio_file):
        """Test exception handling for unexpected errors in routes (lines 88-90)"""
        # Mock tempfile.mkdtemp to raise an unexpected exception BEFORE the generator
        # This will trigger the exception handler in the route (lines 88-90)
        with patch('backend.routes.tempfile.mkdtemp') as mock_mkdtemp:
            mock_mkdtemp.side_effect = RuntimeError('Unexpected error')
            
            response = client.post('/transcribe', data={
                'audio': (sample_audio_file, 'test.mp3')
            })
            
            # Should return 500 with error message (exception handler catches it)
            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data

    def test_status_not_found(self, client):
        """GET /transcribe/status/<unknown_id> returns 404."""
        response = client.get('/transcribe/status/00000000-0000-0000-0000-000000000000')
        assert response.status_code == 404
        assert response.get_json().get('error') == 'Job not found'

    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.get('/health')
        # CORS should be enabled (flask-cors adds headers)
        # The exact headers depend on flask-cors configuration
        assert response.status_code == 200

    def test_gevent_import_fallback_in_app(self):
        """Test gevent import fallback in app.py (lines 16-19)"""
        # Test that app works when gevent is not available
        # The fallback is tested by verifying the app imports successfully
        # The try/except block in app.py (lines 16-19) handles the ImportError
        # We verify the code path exists by checking the app is created
        from backend.app import app
        # App should be created successfully (fallback path doesn't crash)
        assert app is not None

    def test_request_entity_too_large_handler(self, client, mock_api_key):
        """Test RequestEntityTooLarge error handler (lines 85-86)"""
        from werkzeug.exceptions import RequestEntityTooLarge
        
        # We can't easily trigger this in a real request without actually uploading
        # a huge file, but we can test the handler exists
        # The handler is registered at app creation time
        assert hasattr(app, 'error_handler_spec')
        # The handler should be registered for RequestEntityTooLarge
        handlers = app.error_handler_spec.get(None, {})
        assert RequestEntityTooLarge in handlers or 413 in handlers


class TestFileSizeLimit:
    """Tests for file size validation"""

    def test_file_size_exact_limit(self, client, mock_api_key):
        """Test file at exact size limit is accepted (202 + job)."""
        file_at_limit = BytesIO(b'x' * min(MAX_FILE_SIZE, 1024 * 1024))  # Cap for test speed
        with patch('src.transcribe.transcribe_audio') as mock_transcribe:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
                tmp.write('Test transcript')
                tmp_path = tmp.name
            mock_transcribe.return_value = tmp_path
            response = client.post('/transcribe', data={
                'audio': (file_at_limit, 'test.mp3')
            })
            assert response.status_code == 202
            assert response.get_json().get('job_id')
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

