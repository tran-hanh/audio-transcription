"""
Audio processing utilities for chunking and normalization
"""

import os
import sys
import tempfile
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
            volume_dbfs=volume_dbfs
        )
    
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
        # Load audio segment
        audio_segment = AudioSegment.from_file(audio_file.path)
        
        # Normalize volume
        audio_segment = self.normalize_volume(audio_segment)
        
        # Create temporary directory for chunks
        temp_dir = tempfile.mkdtemp(prefix="audio_chunks_")
        chunk_objects = []
        
        total_length_ms = len(audio_segment)
        num_chunks = (total_length_ms // self.chunk_length_ms) + 1
        
        if progress_callback:
            progress_callback(
                15,
                f"Analyzing audio file ({audio_file.duration_minutes:.1f} minutes total)..."
            )
        
        # Split audio into chunks
        for i in range(0, total_length_ms, self.chunk_length_ms):
            chunk_segment = audio_segment[i:i + self.chunk_length_ms]
            chunk_num = len(chunk_objects) + 1
            
            # Create temporary file for this chunk
            chunk_filename = f"{chunk_num:04d}.{CHUNK_FILE_FORMAT}"
            chunk_path = os.path.join(temp_dir, chunk_filename)
            
            # Export chunk
            try:
                chunk_segment.export(chunk_path, format=CHUNK_FILE_FORMAT)
            except Exception as e:
                raise AudioProcessingError(
                    f"Failed to export chunk {chunk_num}: {e}"
                ) from e
            
            chunk_duration_ms = len(chunk_segment)
            chunk_duration_minutes = chunk_duration_ms / (60 * 1000)
            
            chunk = AudioChunk(
                path=chunk_path,
                chunk_number=chunk_num,
                duration_ms=chunk_duration_ms,
                duration_minutes=chunk_duration_minutes
            )
            chunk_objects.append(chunk)
            
            if progress_callback:
                progress_callback(
                    15 + int((chunk_num / num_chunks) * 10),
                    f"Created chunk {chunk_num} of ~{num_chunks} ({chunk_duration_minutes:.1f} min)"
                )
        
        if progress_callback:
            progress_callback(
                25,
                f"Successfully created {len(chunk_objects)} chunks. Starting transcription..."
            )
        
        return chunk_objects, temp_dir

