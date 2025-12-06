#!/usr/bin/env python3
"""
Tests for backend services module
"""

import os
import tempfile
import json
import pytest
from unittest.mock import patch, MagicMock, Mock
from backend.config import Config
from backend.services import TranscriptionService, FileUploadService
from backend.validators import FileValidator


@pytest.fixture
def test_config():
    """Create a test configuration"""
    return Config(
        gemini_api_key='test-api-key',
        max_file_size=100 * 1024 * 1024,  # 100MB for testing
        default_chunk_length=12
    )


@pytest.fixture
def transcription_service(test_config):
    """Create a TranscriptionService instance"""
    return TranscriptionService(test_config)


@pytest.fixture
def file_validator(test_config):
    """Create a FileValidator instance"""
    return FileValidator(
        allowed_extensions=test_config.allowed_extensions,
        max_size=test_config.max_file_size
    )


@pytest.fixture
def file_upload_service(file_validator):
    """Create a FileUploadService instance"""
    return FileUploadService(file_validator)


class TestTranscriptionService:
    """Tests for TranscriptionService class"""

    def test_init(self, test_config):
        """Test TranscriptionService initialization"""
        service = TranscriptionService(test_config)
        assert service.config == test_config
        assert service.validator is not None
        assert isinstance(service.validator, FileValidator)

    def test_send_progress(self, transcription_service):
        """Test send_progress method formats correctly"""
        result = transcription_service.send_progress(50, 'Test message')
        assert result.startswith('data: ')
        assert result.endswith('\n\n')
        
        # Parse the JSON
        json_str = result[6:-2]  # Remove 'data: ' and '\n\n'
        data = json.loads(json_str)
        assert data['progress'] == 50
        assert data['message'] == 'Test message'

    def test_transcribe_file_file_too_large(self, transcription_service):
        """Test transcribe_file with file exceeding size limit"""
        # Create a file that's too large
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b'x' * (150 * 1024 * 1024))  # 150MB > 100MB limit
            tmp_path = tmp.name
        
        try:
            generator = transcription_service.transcribe_file(tmp_path, 12)
            results = list(generator)
            
            # Should yield error messages
            assert len(results) >= 2
            assert 'error' in results[1].lower() or 'too large' in results[1].lower()
        finally:
            # File might have been cleaned up by the service, so check if it exists
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_transcribe_file_invalid_chunk_length(self, transcription_service):
        """Test transcribe_file normalizes chunk length"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b'x' * 1000)  # Small file
            tmp_path = tmp.name
        
        try:
            # Mock transcribe_audio to avoid actual API calls
            with patch('backend.services.transcribe_audio') as mock_transcribe:
                mock_transcribe.return_value = tmp_path
                
                # Create a temporary output file
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as out:
                    out.write('Test transcript')
                    out_path = out.name
                
                mock_transcribe.return_value = out_path
                
                generator = transcription_service.transcribe_file(tmp_path, 50)  # Invalid chunk length
                # Should normalize to 12
                results = list(generator)
                
                # Verify chunk_length was normalized
                mock_transcribe.assert_called_once()
                call_args = mock_transcribe.call_args
                assert call_args[1]['chunk_length_minutes'] == 12  # Normalized
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            if os.path.exists(out_path):
                os.unlink(out_path)

    @patch('backend.services.transcribe_audio')
    def test_transcribe_file_success(self, mock_transcribe, transcription_service):
        """Test successful transcription"""
        # Create test files
        with tempfile.NamedTemporaryFile(delete=False) as input_file:
            input_file.write(b'x' * 1000)
            input_path = input_file.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as output_file:
            output_file.write('Test transcript content')
            output_path = output_file.name
        
        try:
            mock_transcribe.return_value = output_path
            
            generator = transcription_service.transcribe_file(input_path, 12)
            results = list(generator)
            
            # Should yield progress updates and final transcript
            assert len(results) > 0
            # Last result should contain transcript
            final_result = results[-1]
            assert 'transcript' in final_result.lower() or 'test transcript content' in final_result
            
            mock_transcribe.assert_called_once()
        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('backend.services.transcribe_audio')
    def test_transcribe_file_empty_transcript(self, mock_transcribe, transcription_service):
        """Test transcription with empty transcript file"""
        with tempfile.NamedTemporaryFile(delete=False) as input_file:
            input_file.write(b'x' * 1000)
            input_path = input_file.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as output_file:
            output_file.write('')  # Empty transcript
            output_path = output_file.name
        
        try:
            mock_transcribe.return_value = output_path
            
            generator = transcription_service.transcribe_file(input_path, 12)
            results = list(generator)
            
            # Should handle empty transcript gracefully
            assert len(results) > 0
        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('backend.services.transcribe_audio')
    def test_transcribe_file_transcript_not_found(self, mock_transcribe, transcription_service):
        """Test transcription when output file doesn't exist"""
        with tempfile.NamedTemporaryFile(delete=False) as input_file:
            input_file.write(b'x' * 1000)
            input_path = input_file.name
        
        try:
            # Mock the transcription to return a non-existent file path
            # The transcription runs in a background greenlet/thread, so we need to mock it
            def mock_transcribe_func(*args, **kwargs):
                # Simulate the transcription completing and returning a non-existent path
                return '/nonexistent/file.txt'
            
            mock_transcribe.side_effect = mock_transcribe_func
            
            generator = transcription_service.transcribe_file(input_path, 12)
            results = list(generator)
            
            # The FileNotFoundError is caught and converted to an error message in the generator
            # So we should check for the error in the results instead of expecting an exception
            assert len(results) > 0
            # Last result should contain the error
            error_result = results[-1]
            assert 'error' in error_result.lower() or 'not found' in error_result.lower() or 'transcript file not found' in error_result.lower()
        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)

    @patch('backend.services.transcribe_audio')
    def test_transcribe_file_error_handling(self, mock_transcribe, transcription_service):
        """Test error handling during transcription"""
        with tempfile.NamedTemporaryFile(delete=False) as input_file:
            input_file.write(b'x' * 1000)
            input_path = input_file.name
        
        try:
            mock_transcribe.side_effect = Exception('Transcription failed')
            
            generator = transcription_service.transcribe_file(input_path, 12)
            results = list(generator)
            
            # Should yield error message
            assert len(results) > 0
            error_result = results[-1]
            assert 'error' in error_result.lower() or 'transcription failed' in error_result.lower()
        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)


class TestFileUploadService:
    """Tests for FileUploadService class"""

    def test_init(self, file_validator):
        """Test FileUploadService initialization"""
        service = FileUploadService(file_validator)
        assert service.validator == file_validator

    def test_save_uploaded_file_valid(self, file_upload_service):
        """Test saving a valid uploaded file"""
        # Create a mock file object
        mock_file = MagicMock()
        mock_file.filename = 'test.mp3'
        mock_file.save = MagicMock()
        
        upload_dir = tempfile.mkdtemp()
        
        try:
            file_path = file_upload_service.save_uploaded_file(mock_file, upload_dir)
            
            assert file_path is not None
            assert 'test.mp3' in file_path or 'test' in file_path
            mock_file.save.assert_called_once()
        finally:
            if os.path.exists(upload_dir):
                import shutil
                shutil.rmtree(upload_dir)

    def test_save_uploaded_file_invalid_extension(self, file_upload_service):
        """Test saving file with invalid extension"""
        mock_file = MagicMock()
        mock_file.filename = 'test.txt'
        
        upload_dir = tempfile.mkdtemp()
        
        try:
            with pytest.raises(ValueError, match='not allowed'):
                file_upload_service.save_uploaded_file(mock_file, upload_dir)
        finally:
            if os.path.exists(upload_dir):
                import shutil
                shutil.rmtree(upload_dir)

    def test_save_uploaded_file_empty_filename(self, file_upload_service):
        """Test saving file with empty filename"""
        mock_file = MagicMock()
        mock_file.filename = ''
        
        upload_dir = tempfile.mkdtemp()
        
        try:
            with pytest.raises(ValueError, match='No file selected'):
                file_upload_service.save_uploaded_file(mock_file, upload_dir)
        finally:
            if os.path.exists(upload_dir):
                import shutil
                shutil.rmtree(upload_dir)

    def test_save_uploaded_file_creates_directory(self, file_upload_service):
        """Test that save_uploaded_file creates directory if needed"""
        mock_file = MagicMock()
        mock_file.filename = 'test.mp3'
        mock_file.save = MagicMock()
        
        upload_dir = os.path.join(tempfile.mkdtemp(), 'subdir', 'nested')
        
        try:
            file_path = file_upload_service.save_uploaded_file(mock_file, upload_dir)
            assert os.path.exists(upload_dir)
            mock_file.save.assert_called_once()
        finally:
            if os.path.exists(upload_dir):
                import shutil
                shutil.rmtree(os.path.dirname(os.path.dirname(upload_dir)))

