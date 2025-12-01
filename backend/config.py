"""
Configuration management for the Flask application
"""

import os
from dataclasses import dataclass
from typing import Set


@dataclass
class Config:
    """Application configuration"""
    # API Configuration
    gemini_api_key: str
    max_file_size: int = 25 * 1024 * 1024  # 25 MB
    allowed_extensions: Set[str] = None
    default_chunk_length: int = 12
    min_chunk_length: int = 1
    max_chunk_length: int = 30
    
    # Server Configuration
    host: str = '0.0.0.0'
    port: int = 5001
    debug: bool = False
    
    def __post_init__(self):
        """Initialize default values"""
        if self.allowed_extensions is None:
            self.allowed_extensions = {
                'mp3', 'wav', 'm4a', 'flac', 'ogg', 'aac', 'wma'
            }
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create configuration from environment variables"""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError(
                'GEMINI_API_KEY not configured. '
                'Please set it in environment variables.'
            )
        
        return cls(
            gemini_api_key=api_key,
            max_file_size=int(os.getenv('MAX_FILE_SIZE', 25 * 1024 * 1024)),
            default_chunk_length=int(os.getenv('DEFAULT_CHUNK_LENGTH', 12)),
            port=int(os.getenv('PORT', 5001)),
            debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        )

