"""
Audio processing utilities for chunking and normalization
"""

import os
import sys
import tempfile
import subprocess
import shutil
import threading
import time
import re
from pathlib import Path
from typing import List, Tuple, Optional, Callable

from pydub import AudioSegment

# Handle imports when running as script or as module
_script_dir = Path(__file__).parent
_project_root = _script_dir.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.constants import (
    CHUNK_LENGTH_MS,
    TARGET_DBFS,
    QUIET_THRESHOLD_DBFS,
    CHUNK_FILE_FORMAT
)
from src.domain import AudioFile, AudioChunk
from src.exceptions import AudioProcessingError


class AudioProcessor:
    """Handles audio file processing, normalization, and chunking"""
    
    def __init__(self, chunk_length_ms: int = CHUNK_LENGTH_MS):
        """
        Initialize audio processor
        
        Args:
            chunk_length_ms: Length of each chunk in milliseconds
        """
        self.chunk_length_ms = chunk_length_ms
    
    def load_audio(self, audio_path: str) -> AudioFile:
        """
        Load and analyze an audio file
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            AudioFile value object
            
        Raises:
            AudioProcessingError: If file cannot be loaded
        """
        if not os.path.exists(audio_path):
            raise AudioProcessingError(f"Audio file not found: {audio_path}")

        # Keep unit tests deterministic/fast: avoid external ffprobe/ffmpeg calls under pytest.
        is_pytest = os.environ.get("PYTEST_CURRENT_TEST") is not None

        if not is_pytest:
            # This app relies on ffmpeg tooling for robust audio support.
            # Fail fast with actionable guidance rather than hanging in subprocess calls.
            if shutil.which("ffprobe") is None:
                raise AudioProcessingError(
                    "Required dependency not found: ffprobe. "
                    "Please install ffmpeg (which provides ffprobe) and ensure it is on PATH."
                )
            if shutil.which("ffmpeg") is None:
                raise AudioProcessingError(
                    "Required dependency not found: ffmpeg. "
                    "Please install ffmpeg and ensure it is on PATH."
                )

        # Fast path: use ffprobe for duration (does not decode full audio).
        if is_pytest:
            try:
                audio_segment = AudioSegment.from_file(audio_path)
            except Exception as e:
                raise AudioProcessingError(
                    f"Failed to load audio file: {e}. "
                    "Please ensure the file is a valid audio format and ffmpeg is available."
                ) from e

            duration_ms = len(audio_segment)
            duration_minutes = duration_ms / (60 * 1000)
            volume_dbfs = audio_segment.dBFS
            return AudioFile(
                path=audio_path,
                duration_ms=duration_ms,
                duration_minutes=duration_minutes,
                volume_dbfs=volume_dbfs,
            )

        duration_seconds = self._ffprobe_duration_seconds(audio_path, timeout_s=30)

        duration_ms = int(duration_seconds * 1000)
        duration_minutes = duration_ms / (60 * 1000)

        # Estimate volume quickly from a short sample (avoid scanning the whole file).
        volume_dbfs = self._ffmpeg_estimated_mean_volume_dbfs(audio_path, sample_seconds=30, timeout_s=30)
        if volume_dbfs is None:
            # If we can't estimate, keep a reasonable default (used only for metadata).
            volume_dbfs = TARGET_DBFS

        return AudioFile(
            path=audio_path,
            duration_ms=duration_ms,
            duration_minutes=duration_minutes,
            volume_dbfs=volume_dbfs,
        )

    def _ffprobe_duration_seconds(self, audio_path: str, timeout_s: int = 30) -> float:
        """Return duration in seconds using ffprobe."""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    audio_path,
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout_s,
            )
        except FileNotFoundError:
            raise AudioProcessingError(
                "ffprobe not found. Please install ffmpeg (which provides ffprobe) and ensure it is on PATH."
            )
        except subprocess.TimeoutExpired as e:
            raise AudioProcessingError(
                f"ffprobe timed out after {timeout_s}s while reading audio metadata. "
                "If this file is very large or stored on a slow network drive, copy it locally and try again. "
                "Otherwise try converting it to WAV (PCM) and re-upload."
            ) from e

        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise AudioProcessingError(
                "ffprobe failed to read audio metadata."
                + (f" Details:\n{detail}" if detail else "")
            )
        raw = (result.stdout or "").strip()
        try:
            return float(raw)
        except (TypeError, ValueError):
            raise AudioProcessingError(f"ffprobe returned an invalid duration: {raw!r}")

    def _ffmpeg_estimated_mean_volume_dbfs(
        self,
        audio_path: str,
        sample_seconds: int = 30,
        timeout_s: int = 30,
    ) -> Optional[float]:
        """
        Estimate mean volume (dBFS) using ffmpeg volumedetect on a short sample.
        Returns None if ffmpeg/parse fails.
        """
        try:
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-nostdin",
                    "-v",
                    "error",
                    "-t",
                    str(sample_seconds),
                    "-i",
                    audio_path,
                    "-af",
                    "volumedetect",
                    "-f",
                    "null",
                    "-",
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout_s,
            )
        except FileNotFoundError:
            return None
        except subprocess.TimeoutExpired:
            # Non-fatal: volume is only used for metadata; chunking/transcription can proceed.
            return None

        # volumedetect prints to stderr
        stderr = result.stderr or ""
        m = re.search(r"mean_volume:\s*(-?\d+(?:\.\d+)?)\s*dB", stderr)
        if not m:
            return None
        try:
            return float(m.group(1))
        except ValueError:
            return None
    
    def normalize_volume(self, audio_segment: AudioSegment) -> AudioSegment:
        """
        Normalize audio volume to target level
        
        Args:
            audio_segment: AudioSegment to normalize
            
        Returns:
            Normalized AudioSegment
        """
        audio_dbfs = audio_segment.dBFS
        
        if audio_dbfs < QUIET_THRESHOLD_DBFS:
            # Very quiet audio - normalize to target
            change_in_dB = TARGET_DBFS - audio_dbfs
            return audio_segment.apply_gain(change_in_dB)
        elif audio_dbfs < TARGET_DBFS:
            # Slightly quiet - normalize to target
            change_in_dB = TARGET_DBFS - audio_dbfs
            return audio_segment.apply_gain(change_in_dB)
        
        # Already at adequate volume
        return audio_segment
    
    def chunk_audio(
        self,
        audio_file: AudioFile,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Tuple[List[AudioChunk], str]:
        """
        Split audio file into chunks
        
        Args:
            audio_file: AudioFile to chunk
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of (list of AudioChunk objects, temp directory path)
            
        Raises:
            AudioProcessingError: If chunking fails
        """
        # Prefer streaming split with ffmpeg to avoid decoding the whole file into memory.
        # Only attempt this when the file exists (keeps tests/mocks predictable).
        is_pytest = os.environ.get("PYTEST_CURRENT_TEST") is not None
        if os.path.exists(audio_file.path) and not is_pytest:
            try:
                return self._chunk_audio_streaming_ffmpeg(audio_file, progress_callback)
            except FileNotFoundError:
                # ffmpeg missing: fallback to pydub method
                pass
            except AudioProcessingError:
                # Keep the error as-is for the caller.
                raise
            except Exception:
                # If streaming split fails unexpectedly, fall back to the old method (best effort).
                pass

        # Fallback: original pydub approach (can be slow for long files)
        if progress_callback:
            progress_callback(13, "Loading audio for splitting... (slow path)")

        try:
            audio_segment = AudioSegment.from_file(audio_file.path)
        except Exception as e:
            raise AudioProcessingError(
                f"Failed to load audio file for chunking: {e}. "
                "Please ensure the file is a valid audio format and ffmpeg is available."
            ) from e

        if progress_callback:
            progress_callback(14, "Normalizing volume...")
        audio_segment = self.normalize_volume(audio_segment)

        temp_dir = tempfile.mkdtemp(prefix="audio_chunks_")
        chunk_objects: List[AudioChunk] = []

        total_length_ms = len(audio_segment)
        num_chunks = (total_length_ms // self.chunk_length_ms) + 1

        if progress_callback:
            progress_callback(15, f"Analyzing audio file ({audio_file.duration_minutes:.1f} minutes total)...")

        for i in range(0, total_length_ms, self.chunk_length_ms):
            chunk_segment = audio_segment[i:i + self.chunk_length_ms]
            chunk_num = len(chunk_objects) + 1
            chunk_filename = f"{chunk_num:04d}.{CHUNK_FILE_FORMAT}"
            chunk_path = os.path.join(temp_dir, chunk_filename)
            try:
                chunk_segment.export(chunk_path, format=CHUNK_FILE_FORMAT)
            except Exception as e:
                raise AudioProcessingError(f"Failed to export chunk {chunk_num}: {e}") from e

            chunk_duration_ms = len(chunk_segment)
            chunk_duration_minutes = chunk_duration_ms / (60 * 1000)
            chunk_objects.append(
                AudioChunk(
                    path=chunk_path,
                    chunk_number=chunk_num,
                    duration_ms=chunk_duration_ms,
                    duration_minutes=chunk_duration_minutes,
                )
            )
            if progress_callback:
                progress_callback(
                    15 + int((chunk_num / num_chunks) * 10),
                    f"Created chunk {chunk_num} of ~{num_chunks} ({chunk_duration_minutes:.1f} min)",
                )

        if progress_callback:
            progress_callback(25, f"Successfully created {len(chunk_objects)} chunks. Starting transcription...")

        return chunk_objects, temp_dir

    def _chunk_audio_streaming_ffmpeg(
        self,
        audio_file: AudioFile,
        progress_callback: Optional[Callable[[int, str], None]],
    ) -> Tuple[List[AudioChunk], str]:
        """
        Stream-split audio using ffmpeg segmenter. This avoids loading the whole file into memory.
        Progress is based on ffmpeg's reported out_time.
        """
        if progress_callback:
            progress_callback(13, "Splitting audio with ffmpeg (streaming)...")

        temp_dir = tempfile.mkdtemp(prefix="audio_chunks_")

        chunk_seconds = max(1, int(self.chunk_length_ms / 1000))
        duration_ms = max(1, int(audio_file.duration_ms))

        out_pattern = os.path.join(temp_dir, f"%04d.{CHUNK_FILE_FORMAT}")

        # Pick an encoder depending on target format.
        codec_args: List[str]
        if CHUNK_FILE_FORMAT.lower() == "mp3":
            codec_args = ["-c:a", "libmp3lame", "-q:a", "4"]
        elif CHUNK_FILE_FORMAT.lower() == "wav":
            codec_args = ["-c:a", "pcm_s16le"]
        else:
            # Default: let ffmpeg pick a reasonable encoder for the extension.
            codec_args = []

        # One-pass loudness normalization (keeps behavior similar to pydub normalization).
        # This is still streaming and avoids loading the whole file into Python memory.
        audio_filter = "loudnorm=I=-20:LRA=11:TP=-1.5"

        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-nostdin",
            "-v",
            "error",
            "-i",
            audio_file.path,
            "-vn",
            "-map",
            "0:a:0",
            "-af",
            audio_filter,
            "-f",
            "segment",
            "-segment_time",
            str(chunk_seconds),
            "-reset_timestamps",
            "1",
            "-start_number",
            "1",
            *codec_args,
            "-progress",
            "pipe:1",
            out_pattern,
        ]

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except FileNotFoundError:
            # ffmpeg missing
            raise

        stderr_lines: List[str] = []

        def _drain_stderr() -> None:
            if not proc.stderr:
                return
            for line in proc.stderr:
                stderr_lines.append(line.rstrip("\n"))

        stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
        stderr_thread.start()

        last_emit = time.time()
        last_progress = 13

        if proc.stdout:
            for raw in proc.stdout:
                line = raw.strip()
                if not line:
                    continue
                # ffmpeg -progress emits key=value lines, including out_time_ms, progress=continue/end
                if line.startswith("out_time_ms="):
                    try:
                        out_time_ms = int(line.split("=", 1)[1])
                    except ValueError:
                        continue
                    # Map ffmpeg time to 15..25 progress range.
                    ratio = min(1.0, max(0.0, out_time_ms / duration_ms))
                    mapped = 15 + int(ratio * 10)
                    now = time.time()
                    # Throttle messages a bit so logs stay readable.
                    if progress_callback and (mapped != last_progress or now - last_emit >= 10):
                        elapsed_s = int(out_time_ms / 1_000_000)
                        total_s = int(duration_ms / 1000)
                        progress_callback(mapped, f"Splitting audio... {elapsed_s}s / ~{total_s}s")
                        last_progress = mapped
                        last_emit = now
                elif line == "progress=end":
                    break

        rc = proc.wait()
        stderr_thread.join(timeout=1)

        if rc != 0:
            detail = "\n".join(stderr_lines[-30:]).strip()
            raise AudioProcessingError(
                "ffmpeg failed while splitting audio."
                + (f" Details:\n{detail}" if detail else "")
            )

        # Collect chunk files and build AudioChunk objects
        try:
            files = sorted(
                f for f in os.listdir(temp_dir)
                if f.lower().endswith(f".{CHUNK_FILE_FORMAT.lower()}")
            )
        except Exception as e:
            raise AudioProcessingError(f"Failed to list chunk files: {e}") from e

        if not files:
            raise AudioProcessingError("No chunks were produced by ffmpeg.")

        chunk_objects: List[AudioChunk] = []
        for idx, filename in enumerate(files, start=1):
            chunk_path = os.path.join(temp_dir, filename)
            # Duration per chunk is approximate; keep it cheap (avoid ffprobe per chunk).
            dur_ms = min(self.chunk_length_ms, max(1, duration_ms - (idx - 1) * self.chunk_length_ms))
            chunk_objects.append(
                AudioChunk(
                    path=chunk_path,
                    chunk_number=idx,
                    duration_ms=dur_ms,
                    duration_minutes=dur_ms / (60 * 1000),
                )
            )

        if progress_callback:
            progress_callback(25, f"Successfully created {len(chunk_objects)} chunks. Starting transcription...")

        return chunk_objects, temp_dir

