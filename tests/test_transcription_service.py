#!/usr/bin/env python3
"""
Focused tests for src/transcription_service.TranscriptionService.
These are unit-style tests that exercise the orchestration logic and error paths
without calling the real audio pipeline or Gemini API.
"""

import os
import tempfile
from pathlib import Path
from typing import List

import pytest
from unittest.mock import MagicMock, Mock

from src.transcription_service import TranscriptionService
from src.domain import (
    AudioFile,
    AudioChunk,
    TranscriptChunk,
    TranscriptionResult,
)
from src.exceptions import AudioFileNotFoundError, AudioProcessingError


class DummyGeminiClient:
    """Simple stand-in for GeminiClient that returns preconfigured TranscriptChunks."""

    def __init__(self, transcript_chunks: List[TranscriptChunk]):
        self._chunks = transcript_chunks
        self._calls = []

    def transcribe_chunk(
        self,
        *,
        chunk_path: str,
        chunk_number: int,
        total_chunks: int,
        language: str,
        progress_callback=None,
    ) -> TranscriptChunk:
        self._calls.append(
            {
                "path": chunk_path,
                "number": chunk_number,
                "total": total_chunks,
                "language": language,
            }
        )
        # Return the matching TranscriptChunk by chunk_number if available,
        # otherwise fall back to the first one.
        for c in self._chunks:
            if c.chunk_number == chunk_number:
                return c
        return self._chunks[0]


def make_audio_file(path: str = "/tmp/dummy.wav") -> AudioFile:
    return AudioFile(
        path=path,
        duration_ms=60_000,
        duration_minutes=1.0,
        volume_dbfs=-20.0,
    )


def make_audio_chunk(path: str, number: int) -> AudioChunk:
    return AudioChunk(
        path=path,
        chunk_number=number,
        duration_ms=30_000,
        duration_minutes=0.5,
    )


def make_transcript_chunk_ok(number: int, text: str) -> TranscriptChunk:
    return TranscriptChunk(
        chunk_number=number,
        text=text,
        is_error=False,
        error_message=None,
    )


def make_transcript_chunk_error(number: int, msg: str) -> TranscriptChunk:
    return TranscriptChunk(
        chunk_number=number,
        text="",
        is_error=True,
        error_message=msg,
    )


class TestTranscriptionServiceCore:
    """Cover the core happy-path orchestration in TranscriptionService.transcribe."""

    def test_transcribe_happy_path(self, tmp_path, monkeypatch):
        # Arrange: fake input audio file on disk
        input_path = tmp_path / "audio.wav"
        input_path.write_bytes(b"fake-audio")

        # Fake audio_processor that returns a simple AudioFile and two chunks.
        fake_audio_file = make_audio_file(str(input_path))
        chunk1 = make_audio_chunk(str(tmp_path / "chunk1.wav"), 1)
        chunk2 = make_audio_chunk(str(tmp_path / "chunk2.wav"), 2)

        fake_audio_processor = MagicMock()
        fake_audio_processor.load_audio.return_value = fake_audio_file
        fake_audio_processor.chunk_audio.return_value = ([chunk1, chunk2], str(tmp_path / "chunks"))

        # Gemini client returns successful transcript chunks
        t1 = make_transcript_chunk_ok(1, "First part")
        t2 = make_transcript_chunk_ok(2, "Second part")
        dummy_client = DummyGeminiClient([t1, t2])

        service = TranscriptionService(
            gemini_client=dummy_client,
            audio_processor=fake_audio_processor,
            chunk_length_minutes=1,
            language="en",
        )

        progress_updates = []

        def progress_cb(p: int, msg: str) -> None:
            progress_updates.append((p, msg))

        # Act
        result = service.transcribe(str(input_path), progress_callback=progress_cb)

        # Assert
        assert isinstance(result, TranscriptionResult)
        assert "First part" in result.transcript
        assert "Second part" in result.transcript
        assert result.total_chunks == 2
        assert result.successful_chunks == 2
        assert result.failed_chunks == 0
        assert result.blocked_chunks == []
        # Ensure save_transcript created a file at the default path
        assert os.path.exists(result.output_path)
        # Should have emitted progress updates for load, chunking, and combining
        assert any(p == 10 for p, _ in progress_updates)
        assert any(p == 11 for p, _ in progress_updates)
        assert any(p == 12 for p, _ in progress_updates)
        assert any(p == 25 for p, _ in progress_updates)
        assert any(p == 85 for p, _ in progress_updates)
        assert any(p == 90 for p, _ in progress_updates)
        assert any(p == 95 for p, _ in progress_updates)

    def test_transcribe_missing_file_raises(self, tmp_path):
        missing = tmp_path / "does_not_exist.wav"
        dummy_client = DummyGeminiClient([])
        service = TranscriptionService(gemini_client=dummy_client)

        with pytest.raises(AudioFileNotFoundError):
            service.transcribe(str(missing))


class TestTranscriptionServiceErrorPaths:
    """Cover error handling branches in transcribe and helpers."""

    def test_transcribe_propagates_audio_processor_error(self, tmp_path):
        input_path = tmp_path / "audio.wav"
        input_path.write_bytes(b"fake-audio")

        fake_audio_processor = MagicMock()
        fake_audio_processor.load_audio.side_effect = AudioProcessingError("boom")

        dummy_client = DummyGeminiClient([])
        service = TranscriptionService(
            gemini_client=dummy_client,
            audio_processor=fake_audio_processor,
        )

        with pytest.raises(AudioProcessingError):
            service.transcribe(str(input_path))

    def test_transcribe_combines_failed_and_blocked_chunks(self, tmp_path):
        input_path = tmp_path / "audio.wav"
        input_path.write_bytes(b"fake-audio")

        fake_audio_file = make_audio_file(str(input_path))
        chunk1 = make_audio_chunk(str(tmp_path / "chunk1.wav"), 1)
        chunk2 = make_audio_chunk(str(tmp_path / "chunk2.wav"), 2)
        chunk3 = make_audio_chunk(str(tmp_path / "chunk3.wav"), 3)

        fake_audio_processor = MagicMock()
        fake_audio_processor.load_audio.return_value = fake_audio_file
        fake_audio_processor.chunk_audio.return_value = (
            [chunk1, chunk2, chunk3],
            str(tmp_path / "chunks"),
        )

        # Chunk 1: OK, Chunk 2: blocked by safety filters, Chunk 3: generic failure
        t1 = make_transcript_chunk_ok(1, "Good")
        t2 = make_transcript_chunk_error(2, "Blocked by safety filters: content")
        t3 = make_transcript_chunk_error(3, "API error")

        dummy_client = DummyGeminiClient([t1, t2, t3])
        service = TranscriptionService(
            gemini_client=dummy_client,
            audio_processor=fake_audio_processor,
        )

        result = service.transcribe(str(input_path))

        assert result.total_chunks == 3
        assert result.successful_chunks == 1
        assert result.failed_chunks == 1
        assert result.blocked_chunks == [2]
        # Summary footer should be appended
        assert "TRANSCRIPTION SUMMARY" in result.transcript
        assert "blocked by safety filters" in result.transcript
        assert "failed to transcribe" in result.transcript

