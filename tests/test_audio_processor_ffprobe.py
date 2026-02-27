#!/usr/bin/env python3
"""
Additional coverage for AudioProcessor ffprobe/ffmpeg branches and error handling.
"""

import subprocess

import pytest
from unittest.mock import MagicMock, patch

from src.audio_processor import AudioProcessor
from src.exceptions import AudioProcessingError


@patch("src.audio_processor.shutil.which", return_value="/usr/bin/ffprobe")
@patch("src.audio_processor.subprocess.run")
def test_ffprobe_timeout_raises_audio_processing_error(mock_run, mock_which, tmp_path, monkeypatch):
    """If ffprobe times out, load_audio should raise AudioProcessingError with guidance."""
    # Ensure we are not in pytest-fast path that bypasses ffprobe
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    # Fake existing audio file
    audio_path = tmp_path / "audio.wav"
    audio_path.write_bytes(b"fake-audio")

    mock_run.side_effect = subprocess.TimeoutExpired(cmd=["ffprobe"], timeout=30)

    processor = AudioProcessor()

    with pytest.raises(AudioProcessingError) as exc_info:
        processor.load_audio(str(audio_path))

    msg = str(exc_info.value)
    assert "ffprobe timed out" in msg
    assert "WAV (PCM)" in msg or "WAV" in msg


@patch("src.audio_processor.shutil.which", return_value="/usr/bin/ffprobe")
@patch("src.audio_processor.subprocess.run")
def test_ffprobe_nonzero_exit_raises_audio_processing_error(mock_run, mock_which, tmp_path, monkeypatch):
    """If ffprobe exits non‑zero, load_audio should raise AudioProcessingError with details."""
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    audio_path = tmp_path / "audio.wav"
    audio_path.write_bytes(b"fake-audio")

    mock_run.return_value = subprocess.CompletedProcess(
        args=["ffprobe"],
        returncode=1,
        stdout="",
        stderr="some ffprobe error",
    )

    processor = AudioProcessor()

    with pytest.raises(AudioProcessingError) as exc_info:
        processor.load_audio(str(audio_path))

    msg = str(exc_info.value)
    assert "ffprobe failed" in msg or "ffprobe" in msg


