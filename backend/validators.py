"""
Input validation utilities
"""

from pathlib import Path
from typing import Optional, Tuple


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class FileValidator:
    """Validates uploaded files"""
    
    def __init__(
        self,
        allowed_extensions: set,
        max_size: int
    ):
        self.allowed_extensions = allowed_extensions
        self.max_size = max_size
    
    def validate_filename(self, filename: str) -> Tuple[bool, Optional[str]]:
        """
        Validate file name and extension.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not filename or filename.strip() == '':
            return False, 'No file selected'
        
        if '.' not in filename:
            return False, 'File must have an extension'
        
        extension = filename.rsplit('.', 1)[1].lower()
        if extension not in self.allowed_extensions:
            allowed = ', '.join(sorted(self.allowed_extensions))
            return False, f'File type not allowed. Allowed types: {allowed}'
        
        return True, None
    
    def validate_file_size(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate file size.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            file_size = Path(file_path).stat().st_size
            if file_size > self.max_size:
                max_size_mb = self.max_size / (1024 * 1024)
                return False, f'File too large. Maximum size: {max_size_mb:.0f} MB'
            return True, None
        except OSError as e:
            return False, f'Cannot read file size: {str(e)}'
    
    def validate_chunk_length(self, chunk_length: int) -> int:
        """
        Validate and normalize chunk length.
        
        Returns:
            Normalized chunk length
        """
        if chunk_length < 1:
            return 12
        if chunk_length > 30:
            return 12
        return chunk_length


