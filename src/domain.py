"""
Domain models and value objects for audio transcription
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class AudioFile:
    """Value object representing an audio file"""
    path: str
    duration_ms: int
    duration_minutes: float
    volume_dbfs: float
    
    @property
    def filename(self) -> str:
        """Get the filename from the path"""
        return Path(self.path).name
    
    @property
    def exists(self) -> bool:
        """Check if the file exists"""
        return Path(self.path).exists()


@dataclass(frozen=True)
class AudioChunk:
    """Value object representing an audio chunk"""
    path: str
    chunk_number: int
    duration_ms: int
    duration_minutes: float
    
    @property
    def filename(self) -> str:
        """Get the filename from the path"""
        return Path(self.path).name


@dataclass(frozen=True)
class TranscriptChunk:
    """Value object representing a transcribed chunk"""
    chunk_number: int
    text: str
    is_error: bool
    error_message: Optional[str] = None
    
    @property
    def is_successful(self) -> bool:
        """Check if transcription was successful"""
        return not self.is_error


@dataclass
class TranscriptionProgress:
    """Value object representing transcription progress"""
    progress_percentage: int
    message: str
    current_chunk: Optional[int] = None
    total_chunks: Optional[int] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'progress': self.progress_percentage,
            'message': self.message,
            'current_chunk': self.current_chunk,
            'total_chunks': self.total_chunks
        }


@dataclass
class TranscriptionResult:
    """Value object representing the final transcription result"""
    transcript: str
    output_path: str
    total_chunks: int
    successful_chunks: int
    failed_chunks: int
    blocked_chunks: List[int]
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.total_chunks == 0:
            return 0.0
        return (self.successful_chunks / self.total_chunks) * 100





