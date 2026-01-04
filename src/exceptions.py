"""
Custom exceptions for audio transcription domain
"""


class TranscriptionError(Exception):
    """Base exception for transcription errors"""
    pass


class AudioProcessingError(TranscriptionError):
    """Raised when audio file cannot be processed"""
    pass


class AudioFileNotFoundError(TranscriptionError):
    """Raised when audio file is not found"""
    pass


class TranscriptionAPIError(TranscriptionError):
    """Raised when API call fails"""
    pass


class SafetyFilterBlockError(TranscriptionAPIError):
    """Raised when content is blocked by safety filters"""
    pass


class ModelInitializationError(TranscriptionError):
    """Raised when Gemini model cannot be initialized"""
    pass


class ChunkProcessingError(TranscriptionError):
    """Raised when a chunk fails to process"""
    pass





