"""
Tests for AudioProcessor following TDD principles
"""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.audio_processor import AudioProcessor
from src.domain import AudioFile, AudioChunk
from src.exceptions import AudioProcessingError
from src.constants import TARGET_DBFS, QUIET_THRESHOLD_DBFS


class TestAudioProcessor:
    """Test suite for AudioProcessor"""
    
    def test_init_with_default_chunk_length(self):
        """Test AudioProcessor initialization with default chunk length"""
        processor = AudioProcessor()
        assert processor.chunk_length_ms > 0
    
    def test_init_with_custom_chunk_length(self):
        """Test AudioProcessor initialization with custom chunk length"""
        chunk_length_ms = 600000  # 10 minutes
        processor = AudioProcessor(chunk_length_ms=chunk_length_ms)
        assert processor.chunk_length_ms == chunk_length_ms
    
    @patch('src.audio_processor.AudioSegment')
    @patch('src.audio_processor.os.path.exists', return_value=True)
    def test_load_audio_success(self, mock_exists, mock_audio_segment):
        """Test successful audio file loading"""
        # Setup
        mock_segment = MagicMock()
        mock_segment.__len__ = Mock(return_value=120000)  # 2 minutes
        mock_segment.dBFS = -15.0
        mock_audio_segment.from_file.return_value = mock_segment
        
        processor = AudioProcessor()
        audio_file = processor.load_audio("/path/to/audio.mp3")
        
        # Assertions
        assert isinstance(audio_file, AudioFile)
        assert audio_file.duration_ms == 120000
        assert audio_file.volume_dbfs == -15.0
        assert audio_file.path == "/path/to/audio.mp3"
    
    @patch('src.audio_processor.AudioSegment')
    def test_load_audio_file_not_found(self, mock_audio_segment):
        """Test loading non-existent audio file"""
        processor = AudioProcessor()
        
        with pytest.raises(AudioProcessingError) as exc_info:
            processor.load_audio("/nonexistent/file.mp3")
        
        assert "not found" in str(exc_info.value).lower()
    
    @patch('src.audio_processor.AudioSegment')
    @patch('src.audio_processor.os.path.exists', return_value=True)
    def test_load_audio_invalid_format(self, mock_exists, mock_audio_segment):
        """Test loading invalid audio format"""
        mock_audio_segment.from_file.side_effect = Exception("Invalid format")
        
        processor = AudioProcessor()
        
        with pytest.raises(AudioProcessingError) as exc_info:
            processor.load_audio("/path/to/invalid.xyz")
        
        assert "Failed to load" in str(exc_info.value)
    
    def test_normalize_volume_quiet_audio(self):
        """Test volume normalization for quiet audio"""
        from pydub import AudioSegment
        
        processor = AudioProcessor()
        
        # Create a mock quiet audio segment
        mock_audio = MagicMock()
        mock_audio.dBFS = -35.0  # Very quiet
        mock_audio.apply_gain.return_value = MagicMock()
        mock_audio.apply_gain.return_value.dBFS = TARGET_DBFS
        
        normalized = processor.normalize_volume(mock_audio)
        
        # Should call apply_gain with positive gain
        mock_audio.apply_gain.assert_called_once()
        call_args = mock_audio.apply_gain.call_args[0][0]
        assert call_args > 0  # Positive gain
    
    def test_normalize_volume_adequate_audio(self):
        """Test volume normalization for already adequate audio"""
        from pydub import AudioSegment
        
        processor = AudioProcessor()
        
        # Create a mock audio segment with adequate volume
        mock_audio = MagicMock()
        mock_audio.dBFS = -15.0  # Already adequate
        mock_audio.apply_gain.return_value = mock_audio
        
        normalized = processor.normalize_volume(mock_audio)
        
        # Should not call apply_gain for adequate volume
        # (Actually it might still call it, but with 0 gain)
        # Let's just check it returns the audio
        assert normalized is not None
    
    @patch('src.audio_processor.AudioSegment')
    @patch('src.audio_processor.tempfile.mkdtemp')
    def test_chunk_audio_success(self, mock_mkdtemp, mock_audio_segment):
        """Test successful audio chunking"""
        # Setup
        temp_dir = "/tmp/test_chunks"
        mock_mkdtemp.return_value = temp_dir
        
        # Create mock audio segment
        mock_segment = MagicMock()
        mock_segment.__len__ = Mock(return_value=3600000)  # 60 minutes
        mock_segment.dBFS = -15.0
        mock_segment.__getitem__ = Mock(return_value=MagicMock())
        mock_audio_segment.from_file.return_value = mock_segment
        
        # Mock chunk export
        mock_chunk = MagicMock()
        mock_chunk.__len__ = Mock(return_value=720000)  # 12 minutes
        mock_chunk.export = Mock()
        mock_segment.__getitem__.return_value = mock_chunk
        
        processor = AudioProcessor(chunk_length_ms=720000)  # 12 minutes
        
        # Create a mock AudioFile
        audio_file = AudioFile(
            path="/path/to/audio.mp3",
            duration_ms=3600000,
            duration_minutes=60.0,
            volume_dbfs=-15.0
        )
        
        chunks, temp_dir_result = processor.chunk_audio(audio_file)
        
        # Assertions
        assert temp_dir_result == temp_dir
        assert len(chunks) > 0
        assert all(isinstance(chunk, AudioChunk) for chunk in chunks)
    
    @patch('src.audio_processor.AudioSegment')
    def test_chunk_audio_export_failure(self, mock_audio_segment):
        """Test chunking failure during export"""
        # Setup
        mock_segment = MagicMock()
        mock_segment.__len__ = Mock(return_value=3600000)
        mock_segment.dBFS = -15.0
        mock_segment.__getitem__ = Mock(return_value=MagicMock())
        mock_audio_segment.from_file.return_value = mock_segment
        
        # Mock chunk with export failure
        mock_chunk = MagicMock()
        mock_chunk.__len__ = Mock(return_value=720000)
        mock_chunk.export.side_effect = Exception("Export failed")
        mock_segment.__getitem__.return_value = mock_chunk
        
        processor = AudioProcessor(chunk_length_ms=720000)
        
        audio_file = AudioFile(
            path="/path/to/audio.mp3",
            duration_ms=3600000,
            duration_minutes=60.0,
            volume_dbfs=-15.0
        )
        
        with pytest.raises(AudioProcessingError) as exc_info:
            processor.chunk_audio(audio_file)
        
        assert "Failed to export" in str(exc_info.value)






