"""
Data models for transcription service
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TranscriptionConfig:
    """Configuration for transcription process"""
    chunk_length_minutes: int = 12
    language: str = "vi"
    output_encoding: str = "utf-8"
    min_chunk_length: int = 1
    max_chunk_length: int = 30
    
    def validate(self) -> None:
        """Validate configuration values"""
        if not (self.min_chunk_length <= self.chunk_length_minutes <= self.max_chunk_length):
            raise ValueError(
                f"Chunk length must be between {self.min_chunk_length} "
                f"and {self.max_chunk_length} minutes"
            )


@dataclass
class AudioChunk:
    """Represents an audio chunk"""
    path: str
    chunk_number: int
    duration_ms: int
    
    @property
    def duration_minutes(self) -> float:
        """Get duration in minutes"""
        return self.duration_ms / (60 * 1000)


@dataclass
class TranscriptionResult:
    """Result of transcription process"""
    transcript: str
    output_path: str
    total_chunks: int
    success: bool = True
    error: Optional[str] = None


