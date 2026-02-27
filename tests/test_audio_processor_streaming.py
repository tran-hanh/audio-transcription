#!/usr/bin/env python3
"""
Extra coverage for AudioProcessor ffmpeg-based helpers.
"""

import subprocess
from pathlib import Path

import pytest
from unittest.mock import MagicMock, patch

from src.audio_processor import AudioProcessor
from src.domain import AudioFile
from src.exceptions import AudioProcessingError


@patch("src.audio_processor.subprocess.run")
def test_ffmpeg_estimated_mean_volume_parses_output(mock_run, tmp_path):
    """_ffmpeg_estimated_mean_volume_dbfs returns a float when ffmpeg output contains mean_volume."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=["ffmpeg"],
        returncode=0,
        stdout="",
        stderr="some log\n[Parsed_volumedetect_0 @ 0x0] mean_volume: -18.5 dB\nmore\n",
    )

    processor = AudioProcessor()
    value = processor._ffmpeg_estimated_mean_volume_dbfs("dummy.wav", sample_seconds=5, timeout_s=5)
    assert isinstance(value, float)
    assert value == pytest.approx(-18.5)


@patch("src.audio_processor.subprocess.Popen")
@patch("src.audio_processor.tempfile.mkdtemp")
@patch("src.audio_processor.os.listdir")
def test_chunk_audio_streaming_ffmpeg_success(mock_listdir, mock_mkdtemp, mock_popen, tmp_path, monkeypatch):
    """_chunk_audio_streaming_ffmpeg creates AudioChunk objects from ffmpeg output."""
    # Avoid pytest guard in chunk_audio by calling the helper directly.
    temp_dir = str(tmp_path / "chunks")
    Path(temp_dir).mkdir(parents=True, exist_ok=True)
    mock_mkdtemp.return_value = temp_dir

    # Pretend ffmpeg wrote three chunk files by actually creating them so os.listdir sees them.
    # Use the configured CHUNK_FILE_FORMAT (mp3) so the filter matches.
    for name in ["0001.mp3", "0002.mp3", "0003.mp3"]:
        (Path(temp_dir) / name).write_bytes(b"data")
    mock_listdir.return_value = ["0001.mp3", "0002.mp3", "0003.mp3"]

    # Fake Popen object with progress lines and clean exit
    proc = MagicMock()
    proc.stdout = iter(
        [
            "out_time_ms=0\n",
            "out_time_ms=15000\n",
            "out_time_ms=30000\n",
            "progress=end\n",
        ]
    )
    proc.stderr = iter(["ffmpeg stderr line\n"])
    proc.wait.return_value = 0
    mock_popen.return_value = proc

    audio_file = AudioFile(
        path=str(tmp_path / "input.wav"),
        duration_ms=30_000,
        duration_minutes=0.5,
        volume_dbfs=-20.0,
    )

    progress_calls = []

    def progress_cb(pct: int, msg: str) -> None:
        progress_calls.append((pct, msg))

    processor = AudioProcessor(chunk_length_ms=10_000)
    chunks, out_dir = processor._chunk_audio_streaming_ffmpeg(audio_file, progress_cb)

    assert out_dir == temp_dir
    assert len(chunks) == 3
    assert [c.chunk_number for c in chunks] == [1, 2, 3]
    # Ensure at least one progress update from streaming path
    assert any("Splitting audio..." in msg for _, msg in progress_calls)


@patch("src.audio_processor.subprocess.Popen")
@patch("src.audio_processor.tempfile.mkdtemp")
@patch("src.audio_processor.os.listdir", side_effect=OSError("list error"))
def test_chunk_audio_streaming_ffmpeg_listdir_error_raises(mock_listdir, mock_mkdtemp, mock_popen, tmp_path):
    """Listdir failures are wrapped as AudioProcessingError."""
    temp_dir = str(tmp_path / "chunks")
    mock_mkdtemp.return_value = temp_dir

    proc = MagicMock()
    proc.stdout = iter(["progress=end\n"])
    proc.stderr = iter([])
    proc.wait.return_value = 0
    mock_popen.return_value = proc

    audio_file = AudioFile(
        path=str(tmp_path / "input.wav"),
        duration_ms=10_000,
        duration_minutes=0.166,
        volume_dbfs=-20.0,
    )

    processor = AudioProcessor()
    with pytest.raises(AudioProcessingError):
        processor._chunk_audio_streaming_ffmpeg(audio_file, None)

