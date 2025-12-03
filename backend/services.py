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
            
            # Transcribe audio in a separate thread to allow progress updates
            import threading
            import queue
            transcription_result = queue.Queue()
            transcription_error = queue.Queue()
            
            def run_transcription():
                try:
                    output_path = transcribe_audio(
                        input_path=file_path,
                        output_path=temp_output_path,
                        api_key=self.config.gemini_api_key,
                        chunk_length_minutes=chunk_length
                    )
                    transcription_result.put(output_path)
                except Exception as e:
                    transcription_error.put(e)
            
            # Start transcription in background thread
            transcription_thread = threading.Thread(target=run_transcription, daemon=True)
            transcription_thread.start()
            
            # Send heartbeat messages while transcription is running
            import time
            last_heartbeat = time.time()
            heartbeat_interval = 20  # Send heartbeat every 20 seconds to prevent timeout
            
            while transcription_thread.is_alive():
                # Check for errors
                try:
                    error = transcription_error.get_nowait()
                    raise error
                except queue.Empty:
                    pass
                
                # Send heartbeat to keep connection alive
                current_time = time.time()
                if current_time - last_heartbeat >= heartbeat_interval:
                    yield self.send_progress(50, 'Transcription in progress... This may take several minutes. Please keep this page open.')
                    last_heartbeat = current_time
                
                # Small sleep to avoid busy waiting
                time.sleep(0.5)  # Check more frequently
            
            # Get the result
            try:
                output_path = transcription_result.get(timeout=1)
            except queue.Empty:
                # Check for errors
                try:
                    error = transcription_error.get_nowait()
                    raise error
                except queue.Empty:
                    raise RuntimeError("Transcription thread completed but no result was returned")
            
            yield self.send_progress(90, 'Reading transcript...')
            
            # Read transcript
            if not os.path.exists(output_path):
                raise FileNotFoundError(f"Transcript file not found: {output_path}")
            
            with open(output_path, 'r', encoding='utf-8') as f:
                transcript = f.read()
            
            # Validate transcript is not empty
            if not transcript or not transcript.strip():
                logger.warning("Transcript file is empty")
                transcript = "[No transcript generated. The audio file may be empty or contain no speech.]"
            
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


