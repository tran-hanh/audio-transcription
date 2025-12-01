"""
Business logic services
"""

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Generator, Optional

from werkzeug.utils import secure_filename

from backend.config import Config
from backend.validators import FileValidator

# Add src directory to path for transcription service
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from transcribe import transcribe_audio

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Service for handling audio transcription"""
    
    def __init__(self, config: Config):
        self.config = config
        self.validator = FileValidator(
            allowed_extensions=config.allowed_extensions,
            max_size=config.max_file_size
        )
    
    def send_progress(self, progress: int, message: str) -> str:
        """Format progress update as Server-Sent Event"""
        return f"data: {json.dumps({'progress': progress, 'message': message})}\n\n"
    
    def transcribe_file(
        self,
        file_path: str,
        chunk_length: int
    ) -> Generator[str, None, None]:
        """
        Transcribe an audio file and yield progress updates.
        
        Args:
            file_path: Path to the audio file
            chunk_length: Length of chunks in minutes
            
        Yields:
            Server-Sent Event formatted progress updates
        """
        temp_dir = None
        temp_output_path = None
        
        try:
            # Validate file size
            is_valid, error = self.validator.validate_file_size(file_path)
            if not is_valid:
                yield self.send_progress(0, error)
                yield f"data: {json.dumps({'error': error})}\n\n"
                return
            
            # Normalize chunk length
            chunk_length = self.validator.validate_chunk_length(chunk_length)
            
            # Create temporary output path
            temp_dir = tempfile.mkdtemp(prefix='audio_upload_')
            temp_output_path = os.path.join(temp_dir, 'transcript.txt')
            
            # Send initial progress
            yield self.send_progress(5, 'File uploaded, starting transcription...')
            yield self.send_progress(10, 'Processing audio chunks...')
            
            # Transcribe audio
            output_path = transcribe_audio(
                input_path=file_path,
                output_path=temp_output_path,
                api_key=self.config.gemini_api_key,
                chunk_length_minutes=chunk_length
            )
            
            yield self.send_progress(90, 'Reading transcript...')
            
            # Read transcript
            with open(output_path, 'r', encoding='utf-8') as f:
                transcript = f.read()
            
            # Send final result
            yield self.send_progress(100, 'Transcription complete!')
            yield f"data: {json.dumps({'transcript': transcript})}\n\n"
            
        except Exception as e:
            logger.error(f"Transcription error: {e}", exc_info=True)
            error_msg = str(e)
            yield f"data: {json.dumps({'error': error_msg})}\n\n"
        finally:
            # Cleanup temporary files
            self._cleanup_temp_files(temp_dir, file_path, temp_output_path)
    
    @staticmethod
    def _cleanup_temp_files(
        temp_dir: Optional[str],
        input_path: Optional[str],
        output_path: Optional[str]
    ):
        """Clean up temporary files and directories"""
        try:
            if output_path and os.path.exists(output_path):
                os.remove(output_path)
            if input_path and os.path.exists(input_path):
                os.remove(input_path)
            if temp_dir and os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except OSError as e:
            logger.warning(f"Error cleaning up temp files: {e}")


class FileUploadService:
    """Service for handling file uploads"""
    
    def __init__(self, validator: FileValidator):
        self.validator = validator
    
    def save_uploaded_file(self, file, upload_dir: str) -> str:
        """
        Save uploaded file to temporary directory.
        
        Args:
            file: Werkzeug FileStorage object
            upload_dir: Directory to save the file
            
        Returns:
            Path to saved file
            
        Raises:
            ValidationError: If file validation fails
        """
        # Validate filename
        is_valid, error = self.validator.validate_filename(file.filename)
        if not is_valid:
            raise ValueError(error)
        
        # Create directory if it doesn't exist
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        return file_path


