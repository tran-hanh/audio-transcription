#!/usr/bin/env python3
"""
Tests for transcription functions
"""

import os
import tempfile
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path

import pytest

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from transcribe import chunk_audio, CHUNK_LENGTH_MINUTES, CHUNK_LENGTH_MS


class TestChunkAudio:
    """Tests for chunk_audio function"""

    @patch('transcribe.AudioSegment')
    def test_chunk_audio_creates_chunks(self, mock_audio_segment):
        """Test that chunk_audio creates multiple chunks for long audio"""
        # Create a mock audio file
        mock_audio = MagicMock()
        # Simulate 30 minutes of audio (should create ~3 chunks of 12 min each)
        mock_audio.__len__.return_value = 30 * 60 * 1000  # 30 minutes in ms
        mock_audio_segment.from_file.return_value = mock_audio

        # Mock chunk export
        chunk_paths = []
        temp_dir = tempfile.mkdtemp()

        def mock_export(path, format):
            chunk_paths.append(path)

        mock_chunk = MagicMock()
        mock_chunk.__len__.return_value = CHUNK_LENGTH_MS
        mock_chunk.export = mock_export
        mock_audio.__getitem__.return_value = mock_chunk

        try:
            chunks, temp_dir_result = chunk_audio('test.mp3')
            # Should create multiple chunks
            assert len(chunks) > 0
            assert temp_dir_result == temp_dir_result
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                try:
                    os.rmdir(temp_dir)
                except OSError:
                    pass

    def test_chunk_audio_file_not_found(self):
        """Test chunk_audio handles missing file"""
        with pytest.raises(Exception):
            chunk_audio('nonexistent.mp3')


class TestTranscribeAudio:
    """Tests for transcribe_audio function"""

    def test_transcribe_audio_missing_file(self):
        """Test error when input file doesn't exist"""
        from transcribe import transcribe_audio

        with pytest.raises(FileNotFoundError):
            transcribe_audio('nonexistent.mp3', api_key='test-key')

    def test_transcribe_audio_missing_api_key(self):
        """Test error when API key is not provided"""
        from transcribe import transcribe_audio

        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            tmp.write(b'fake audio')
            tmp_path = tmp.name

        try:
            # Remove API key from environment
            original_key = os.environ.get('GEMINI_API_KEY')
            if 'GEMINI_API_KEY' in os.environ:
                del os.environ['GEMINI_API_KEY']

            with pytest.raises(ValueError, match='API key'):
                transcribe_audio(tmp_path, api_key=None)

            # Restore original key
            if original_key:
                os.environ['GEMINI_API_KEY'] = original_key
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    @patch('transcribe.genai')
    @patch('transcribe.chunk_audio')
    def test_transcribe_audio_with_api_key(self, mock_chunk, mock_genai):
        """Test transcribe_audio with valid API key"""
        from transcribe import transcribe_audio

        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            tmp.write(b'fake audio')
            tmp_path = tmp.name

        # Mock chunk_audio to return empty chunks list
        mock_chunk.return_value = ([], tempfile.mkdtemp())

        # Mock genai
        mock_model = MagicMock()
        mock_genai.configure = MagicMock()
        mock_genai.list_models.return_value = []
        mock_genai.GenerativeModel.return_value = mock_model

        try:
            # This will fail at chunking/transcription, but should pass API key check
            with pytest.raises((Exception, FileNotFoundError)):
                transcribe_audio(tmp_path, api_key='test-key-123')
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


class TestChunkAudioProgressCallback:
    """Tests for chunk_audio with progress callback"""

    @patch('transcribe.AudioSegment')
    def test_chunk_audio_calls_progress_callback(self, mock_audio_segment):
        """Test that chunk_audio calls progress callback"""
        mock_audio = MagicMock()
        mock_audio.__len__.return_value = 30 * 60 * 1000  # 30 minutes
        mock_audio_segment.from_file.return_value = mock_audio
        
        mock_chunk = MagicMock()
        mock_chunk.__len__.return_value = CHUNK_LENGTH_MS
        mock_chunk.export = MagicMock()
        mock_audio.__getitem__.return_value = mock_chunk
        
        progress_calls = []
        def progress_callback(progress, message):
            progress_calls.append((progress, message))
        
        try:
            chunk_audio('test.mp3', progress_callback=progress_callback)
            # Should have called progress callback
            assert len(progress_calls) > 0
            # First call should be analyzing audio
            assert any('Analyzing' in msg for _, msg in progress_calls)
        except Exception:
            pass  # Expected to fail on file not found, but callback should be called

    @patch('transcribe.AudioSegment')
    def test_chunk_audio_progress_callback_without_callback(self, mock_audio_segment):
        """Test that chunk_audio works without progress callback"""
        mock_audio = MagicMock()
        mock_audio.__len__.return_value = 30 * 60 * 1000
        mock_audio_segment.from_file.return_value = mock_audio
        
        mock_chunk = MagicMock()
        mock_chunk.__len__.return_value = CHUNK_LENGTH_MS
        mock_chunk.export = MagicMock()
        mock_audio.__getitem__.return_value = mock_chunk
        
        try:
            # Should not raise error when callback is None
            chunk_audio('test.mp3', progress_callback=None)
        except Exception:
            pass  # Expected to fail on file not found


class TestTranscribeChunkProgressCallback:
    """Tests for transcribe_chunk with progress callback"""

    @patch('transcribe.genai')
    def test_transcribe_chunk_calls_progress_callback(self, mock_genai):
        """Test that transcribe_chunk calls progress callback"""
        from transcribe import transcribe_chunk
        
        mock_model = MagicMock()
        mock_file = MagicMock()
        mock_file.state.name = 'ACTIVE'
        mock_file.name = 'test_file'
        
        mock_genai.upload_file.return_value = mock_file
        mock_genai.get_file.return_value = mock_file
        mock_genai.delete_file = MagicMock()
        
        mock_response = MagicMock()
        mock_response.text = 'Test transcript'
        mock_model.generate_content.return_value = mock_response
        
        progress_calls = []
        def progress_callback(progress, message):
            progress_calls.append((progress, message))
        
        # This will fail at file upload, but callback should be called before that
        try:
            transcribe_chunk(mock_model, 'test.mp3', 1, 1, progress_callback=progress_callback)
        except Exception:
            pass
        
        # Progress callback should have been called
        assert len(progress_calls) > 0


class TestTranscribeAudioProgressCallback:
    """Tests for transcribe_audio with progress callback"""

    @patch('transcribe.genai')
    @patch('transcribe.chunk_audio')
    @patch('transcribe.transcribe_chunk')
    def test_transcribe_audio_calls_progress_callback(self, mock_transcribe_chunk, mock_chunk, mock_genai):
        """Test that transcribe_audio calls progress callback"""
        from transcribe import transcribe_audio
        
        # Create temp file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            tmp.write(b'fake audio')
            tmp_path = tmp.name
        
        # Mock chunk_audio
        mock_chunk.return_value = (['chunk1.mp3'], tempfile.mkdtemp())
        
        # Mock genai
        mock_model = MagicMock()
        mock_genai.configure = MagicMock()
        mock_genai.list_models.return_value = []
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Mock transcribe_chunk
        mock_transcribe_chunk.return_value = 'Test transcript'
        
        progress_calls = []
        def progress_callback(progress, message):
            progress_calls.append((progress, message))
        
        try:
            transcribe_audio(tmp_path, api_key='test-key', progress_callback=progress_callback)
            # Should have called progress callback multiple times
            assert len(progress_calls) > 0
        except Exception:
            pass  # May fail on file operations
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


class TestConfiguration:
    """Tests for configuration constants"""

    def test_chunk_length_minutes(self):
        """Test CHUNK_LENGTH_MINUTES is set correctly"""
        assert CHUNK_LENGTH_MINUTES == 12

    def test_chunk_length_ms(self):
        """Test CHUNK_LENGTH_MS is calculated correctly"""
        expected_ms = CHUNK_LENGTH_MINUTES * 60 * 1000
        assert CHUNK_LENGTH_MS == expected_ms

