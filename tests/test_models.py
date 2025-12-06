#!/usr/bin/env python3
"""
Tests for src/models.py
"""

import pytest
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from models import TranscriptionConfig, AudioChunk, TranscriptionResult


class TestTranscriptionConfig:
    """Tests for TranscriptionConfig class"""

    def test_default_values(self):
        """Test TranscriptionConfig with default values"""
        config = TranscriptionConfig()
        assert config.chunk_length_minutes == 12
        assert config.language == "vi"
        assert config.output_encoding == "utf-8"
        assert config.min_chunk_length == 1
        assert config.max_chunk_length == 30

    def test_custom_values(self):
        """Test TranscriptionConfig with custom values"""
        config = TranscriptionConfig(
            chunk_length_minutes=15,
            language="en",
            output_encoding="ascii"
        )
        assert config.chunk_length_minutes == 15
        assert config.language == "en"
        assert config.output_encoding == "ascii"

    def test_validate_valid(self):
        """Test validate with valid chunk length"""
        config = TranscriptionConfig(chunk_length_minutes=15)
        # Should not raise
        config.validate()

    def test_validate_too_small(self):
        """Test validate with chunk length below minimum"""
        config = TranscriptionConfig(chunk_length_minutes=0)
        with pytest.raises(ValueError, match="Chunk length must be between"):
            config.validate()

    def test_validate_too_large(self):
        """Test validate with chunk length above maximum"""
        config = TranscriptionConfig(chunk_length_minutes=31)
        with pytest.raises(ValueError, match="Chunk length must be between"):
            config.validate()

    def test_validate_at_boundaries(self):
        """Test validate at boundary values"""
        config_min = TranscriptionConfig(chunk_length_minutes=1)
        config_min.validate()  # Should pass

        config_max = TranscriptionConfig(chunk_length_minutes=30)
        config_max.validate()  # Should pass


class TestAudioChunk:
    """Tests for AudioChunk class"""

    def test_audio_chunk_creation(self):
        """Test AudioChunk creation"""
        chunk = AudioChunk(
            path="/tmp/chunk1.mp3",
            chunk_number=1,
            duration_ms=720000  # 12 minutes
        )
        assert chunk.path == "/tmp/chunk1.mp3"
        assert chunk.chunk_number == 1
        assert chunk.duration_ms == 720000

    def test_duration_minutes_property(self):
        """Test duration_minutes property"""
        chunk = AudioChunk(
            path="/tmp/chunk1.mp3",
            chunk_number=1,
            duration_ms=720000  # 12 minutes
        )
        assert chunk.duration_minutes == 12.0

    def test_duration_minutes_fractional(self):
        """Test duration_minutes with fractional minutes"""
        chunk = AudioChunk(
            path="/tmp/chunk1.mp3",
            chunk_number=1,
            duration_ms=90000  # 1.5 minutes
        )
        assert chunk.duration_minutes == 1.5


class TestTranscriptionResult:
    """Tests for TranscriptionResult class"""

    def test_successful_result(self):
        """Test TranscriptionResult for successful transcription"""
        result = TranscriptionResult(
            transcript="Test transcript",
            output_path="/tmp/transcript.txt",
            total_chunks=3
        )
        assert result.transcript == "Test transcript"
        assert result.output_path == "/tmp/transcript.txt"
        assert result.total_chunks == 3
        assert result.success is True
        assert result.error is None

    def test_failed_result(self):
        """Test TranscriptionResult for failed transcription"""
        result = TranscriptionResult(
            transcript="",
            output_path="",
            total_chunks=0,
            success=False,
            error="Transcription failed"
        )
        assert result.success is False
        assert result.error == "Transcription failed"

    def test_default_success(self):
        """Test TranscriptionResult defaults success to True"""
        result = TranscriptionResult(
            transcript="Test",
            output_path="/tmp/test.txt",
            total_chunks=1
        )
        assert result.success is True

