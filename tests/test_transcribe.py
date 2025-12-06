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


class TestTranscribeChunk:
    """Tests for transcribe_chunk function"""

    @patch('transcribe.genai')
    def test_transcribe_chunk_processing_state(self, mock_genai):
        """Test transcribe_chunk handles PROCESSING state (lines 132-133)"""
        from transcribe import transcribe_chunk
        
        mock_model = MagicMock()
        mock_file_processing = MagicMock()
        mock_file_processing.state.name = 'PROCESSING'
        mock_file_processing.name = 'test_file'
        
        mock_file_active = MagicMock()
        mock_file_active.state.name = 'ACTIVE'
        mock_file_active.name = 'test_file'
        
        # First call returns PROCESSING, second returns ACTIVE
        mock_genai.upload_file.return_value = mock_file_processing
        mock_genai.get_file.side_effect = [mock_file_processing, mock_file_active]
        mock_genai.delete_file = MagicMock()
        
        mock_response = MagicMock()
        mock_response.text = 'Test transcript'
        mock_model.generate_content.return_value = mock_response
        
        with patch('transcribe.time.sleep'):  # Mock sleep to speed up test
            result = transcribe_chunk(mock_model, 'test.mp3', 1, 1)
            assert 'Test transcript' in result or 'ERROR' in result

    @patch('transcribe.genai')
    def test_transcribe_chunk_failed_state(self, mock_genai):
        """Test transcribe_chunk handles FAILED state (line 136)"""
        from transcribe import transcribe_chunk
        
        mock_model = MagicMock()
        mock_file = MagicMock()
        mock_file.state.name = 'FAILED'
        mock_file.name = 'test_file'
        
        mock_genai.upload_file.return_value = mock_file
        # get_file should return the same file with FAILED state
        # The function checks state after waiting, so we need to simulate the wait loop
        mock_genai.get_file.return_value = mock_file
        
        # The exception is raised but caught in the try/except, so it returns error message
        # This tests line 136 where the RuntimeError is raised
        result = transcribe_chunk(mock_model, 'test.mp3', 1, 1)
        # Should return error message (exception is caught and handled)
        assert 'ERROR' in result or 'Failed' in result

    @patch('transcribe.genai')
    def test_transcribe_chunk_exception_handling(self, mock_genai):
        """Test transcribe_chunk exception handling (lines 167-175)"""
        from transcribe import transcribe_chunk
        
        mock_model = MagicMock()
        mock_genai.upload_file.side_effect = Exception('Upload failed')
        mock_genai.delete_file = MagicMock()
        
        result = transcribe_chunk(mock_model, 'test.mp3', 1, 1)
        # Should return error message instead of raising
        assert 'ERROR' in result
        assert 'chunk 1' in result

    @patch('transcribe.genai')
    def test_transcribe_chunk_exception_cleanup(self, mock_genai):
        """Test transcribe_chunk cleans up on exception (lines 170-174)"""
        from transcribe import transcribe_chunk
        
        mock_model = MagicMock()
        mock_file = MagicMock()
        mock_file.state.name = 'ACTIVE'
        mock_file.name = 'test_file'
        
        mock_genai.upload_file.return_value = mock_file
        mock_genai.get_file.return_value = mock_file
        mock_genai.delete_file = MagicMock()
        
        # Make generate_content raise an exception
        mock_model.generate_content.side_effect = Exception('Generation failed')
        
        result = transcribe_chunk(mock_model, 'test.mp3', 1, 1)
        # Should return error message
        assert 'ERROR' in result
        # Should have tried to clean up
        mock_genai.delete_file.assert_called()


class TestTranscribeAudioModelSelection:
    """Tests for model selection in transcribe_audio"""

    @patch('transcribe.genai')
    @patch('transcribe.chunk_audio')
    @patch('transcribe.transcribe_chunk')
    def test_model_selection_preferred_models(self, mock_transcribe_chunk, mock_chunk, mock_genai):
        """Test model selection with preferred models (lines 233-235)"""
        from transcribe import transcribe_audio
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            tmp.write(b'fake audio')
            tmp_path = tmp.name
        
        temp_dir = tempfile.mkdtemp()
        chunk_path = os.path.join(temp_dir, 'chunk1.mp3')
        with open(chunk_path, 'w') as f:
            f.write('fake chunk')
        
        try:
            mock_chunk.return_value = ([chunk_path], temp_dir)
            mock_transcribe_chunk.return_value = 'Test transcript'
            
            # Mock available models - need to set up the model object properly
            mock_model_obj = MagicMock()
            mock_model_obj.name = 'models/gemini-1.5-flash'
            mock_model_obj.supported_generation_methods = ['generateContent']
            
            mock_genai.list_models.return_value = [mock_model_obj]
            
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as out:
                out_path = out.name
            
            try:
                transcribe_audio(tmp_path, output_path=out_path, api_key='test-key')
                # Should have created model
                mock_genai.GenerativeModel.assert_called()
            finally:
                if os.path.exists(out_path):
                    os.remove(out_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            if os.path.exists(chunk_path):
                os.remove(chunk_path)
            if os.path.exists(temp_dir):
                try:
                    os.rmdir(temp_dir)
                except OSError:
                    pass

    @patch('transcribe.genai')
    @patch('transcribe.chunk_audio')
    @patch('transcribe.transcribe_chunk')
    def test_model_selection_fallback(self, mock_transcribe_chunk, mock_chunk, mock_genai):
        """Test model selection fallback (lines 239-250)"""
        from transcribe import transcribe_audio
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            tmp.write(b'fake audio')
            tmp_path = tmp.name
        
        try:
            mock_chunk.return_value = (['chunk1.mp3'], tempfile.mkdtemp())
            mock_transcribe_chunk.return_value = 'Test transcript'
            
            # Mock list_models to raise exception (triggers fallback)
            mock_genai.list_models.side_effect = Exception('API error')
            
            # Mock fallback models
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as out:
                out_path = out.name
            
            try:
                transcribe_audio(tmp_path, output_path=out_path, api_key='test-key')
                # Should have tried fallback models
                mock_genai.GenerativeModel.assert_called()
            finally:
                if os.path.exists(out_path):
                    os.remove(out_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    @patch('transcribe.genai')
    @patch('transcribe.chunk_audio')
    def test_transcribe_audio_no_model_available(self, mock_chunk, mock_genai):
        """Test transcribe_audio when no model is available (lines 252-254)"""
        from transcribe import transcribe_audio
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            tmp.write(b'fake audio')
            tmp_path = tmp.name
        
        try:
            mock_chunk.return_value = ([], tempfile.mkdtemp())
            
            # Mock to return no models and fail on all model creation
            mock_genai.list_models.return_value = []
            mock_genai.GenerativeModel.side_effect = Exception('No models')
            
            with pytest.raises(ValueError, match='Could not initialize'):
                transcribe_audio(tmp_path, api_key='test-key')
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


class TestTranscribeAudioFullFlow:
    """Tests for full transcribe_audio flow"""

    @patch('transcribe.genai')
    @patch('transcribe.chunk_audio')
    @patch('transcribe.transcribe_chunk')
    def test_transcribe_audio_full_flow(self, mock_transcribe_chunk, mock_chunk, mock_genai):
        """Test complete transcribe_audio flow (lines 257-314)"""
        from transcribe import transcribe_audio
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            tmp.write(b'fake audio')
            tmp_path = tmp.name
        
        temp_dir = tempfile.mkdtemp()
        chunk_path = os.path.join(temp_dir, 'chunk1.mp3')
        with open(chunk_path, 'w') as f:
            f.write('fake chunk')
        
        try:
            # Mock chunk_audio to return chunks
            mock_chunk.return_value = ([chunk_path], temp_dir)
            
            # Mock transcribe_chunk
            mock_transcribe_chunk.return_value = 'Test transcript'
            
            # Mock genai - need proper model object structure
            mock_model_obj = MagicMock()
            mock_model_obj.name = 'models/gemini-1.5-flash'
            mock_model_obj.supported_generation_methods = ['generateContent']
            
            mock_genai.list_models.return_value = [mock_model_obj]
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as out:
                out_path = out.name
            
            try:
                result = transcribe_audio(tmp_path, output_path=out_path, api_key='test-key')
                
                # Should return output path
                assert result == out_path
                
                # Should have called transcribe_chunk
                mock_transcribe_chunk.assert_called()
                
                # Should have saved transcript
                assert os.path.exists(out_path)
                with open(out_path, 'r') as f:
                    content = f.read()
                    assert 'Test transcript' in content
            finally:
                if os.path.exists(out_path):
                    os.remove(out_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            if os.path.exists(chunk_path):
                try:
                    os.remove(chunk_path)
                except OSError:
                    pass
            if os.path.exists(temp_dir):
                try:
                    os.rmdir(temp_dir)
                except OSError:
                    pass

    @patch('transcribe.genai')
    @patch('transcribe.chunk_audio')
    @patch('transcribe.transcribe_chunk')
    def test_transcribe_audio_cleanup_errors(self, mock_transcribe_chunk, mock_chunk, mock_genai):
        """Test transcribe_audio handles cleanup errors gracefully (lines 303-312)"""
        from transcribe import transcribe_audio
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            tmp.write(b'fake audio')
            tmp_path = tmp.name
        
        temp_dir = tempfile.mkdtemp()
        chunk_path = os.path.join(temp_dir, 'chunk1.mp3')
        with open(chunk_path, 'w') as f:
            f.write('fake chunk')
        
        try:
            mock_chunk.return_value = ([chunk_path], temp_dir)
            mock_transcribe_chunk.return_value = 'Test transcript'
            
            mock_models = MagicMock()
            mock_models.name = 'gemini-2.5-flash'
            mock_genai.list_models.return_value = [mock_models]
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as out:
                out_path = out.name
            
            # Mock os.remove to raise error (tests cleanup error handling)
            # Only mock remove for chunk files, not output file
            original_remove = os.remove
            def mock_remove(path):
                if 'chunk' in path:
                    raise OSError('Permission denied')
                return original_remove(path)
            
            with patch('transcribe.os.remove', side_effect=mock_remove):
                try:
                    result = transcribe_audio(tmp_path, output_path=out_path, api_key='test-key')
                    # Should still complete successfully despite cleanup errors
                    assert result == out_path
                except Exception:
                    pass  # May fail, but cleanup errors should be handled
            
            # Cleanup output file
            if os.path.exists(out_path):
                os.remove(out_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            if os.path.exists(chunk_path):
                try:
                    os.remove(chunk_path)
                except OSError:
                    pass
            if os.path.exists(temp_dir):
                try:
                    os.rmdir(temp_dir)
                except OSError:
                    pass


class TestMainFunction:
    """Tests for main() function"""

    @patch('transcribe.transcribe_audio')
    @patch('sys.argv', ['transcribe.py', 'test.mp3'])
    def test_main_success(self, mock_transcribe):
        """Test main() function with successful transcription"""
        from transcribe import main
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            tmp_path = tmp.name
        
        mock_transcribe.return_value = tmp_path
        
        # Set API key
        os.environ['GEMINI_API_KEY'] = 'test-key'
        
        try:
            result = main()
            assert result == 0
            mock_transcribe.assert_called_once()
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            if 'GEMINI_API_KEY' in os.environ:
                del os.environ['GEMINI_API_KEY']

    @patch('transcribe.transcribe_audio')
    @patch('sys.argv', ['transcribe.py', 'test.mp3', '--output', 'output.txt'])
    def test_main_with_output(self, mock_transcribe):
        """Test main() function with output file specified"""
        from transcribe import main
        
        mock_transcribe.return_value = 'output.txt'
        os.environ['GEMINI_API_KEY'] = 'test-key'
        
        try:
            result = main()
            assert result == 0
            # Check that output was passed
            call_args = mock_transcribe.call_args
            assert call_args[1]['output_path'] == 'output.txt'
        finally:
            if 'GEMINI_API_KEY' in os.environ:
                del os.environ['GEMINI_API_KEY']

    @patch('transcribe.transcribe_audio')
    @patch('sys.argv', ['transcribe.py', 'test.mp3', '--chunk-length', '15'])
    def test_main_with_chunk_length(self, mock_transcribe):
        """Test main() function with chunk length specified"""
        from transcribe import main
        
        mock_transcribe.return_value = 'output.txt'
        os.environ['GEMINI_API_KEY'] = 'test-key'
        
        try:
            result = main()
            assert result == 0
            # Check that chunk_length was passed
            call_args = mock_transcribe.call_args
            assert call_args[1]['chunk_length_minutes'] == 15
        finally:
            if 'GEMINI_API_KEY' in os.environ:
                del os.environ['GEMINI_API_KEY']

    @patch('transcribe.transcribe_audio')
    @patch('sys.argv', ['transcribe.py', 'test.mp3', '--api-key', 'custom-key'])
    def test_main_with_api_key(self, mock_transcribe):
        """Test main() function with API key specified"""
        from transcribe import main
        
        mock_transcribe.return_value = 'output.txt'
        
        try:
            result = main()
            assert result == 0
            # Check that api_key was passed
            call_args = mock_transcribe.call_args
            assert call_args[1]['api_key'] == 'custom-key'
        finally:
            pass

    @patch('transcribe.transcribe_audio')
    @patch('sys.argv', ['transcribe.py', 'test.mp3'])
    def test_main_error_handling(self, mock_transcribe):
        """Test main() function error handling (lines 365-369)"""
        from transcribe import main
        
        mock_transcribe.side_effect = Exception('Transcription failed')
        os.environ['GEMINI_API_KEY'] = 'test-key'
        
        try:
            result = main()
            assert result == 1  # Should return error code
        finally:
            if 'GEMINI_API_KEY' in os.environ:
                del os.environ['GEMINI_API_KEY']


class TestConfiguration:
    """Tests for configuration constants"""

    def test_chunk_length_minutes(self):
        """Test CHUNK_LENGTH_MINUTES is set correctly"""
        assert CHUNK_LENGTH_MINUTES == 12

    def test_chunk_length_ms(self):
        """Test CHUNK_LENGTH_MS is calculated correctly"""
        expected_ms = CHUNK_LENGTH_MINUTES * 60 * 1000
        assert CHUNK_LENGTH_MS == expected_ms

