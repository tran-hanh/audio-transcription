"""
Business logic services
"""

import json
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Generator, Optional

from werkzeug.utils import secure_filename

from backend.config import Config
from backend.job_store import JobStore
from backend.validators import FileValidator

# Use gevent.sleep for gevent workers (non-blocking)
# This is critical for preventing worker timeouts with gevent workers
try:
    import gevent
    SLEEP = gevent.sleep
except ImportError:
    # Fallback to time.sleep if gevent is not available
    SLEEP = time.sleep

# Add src directory to path for transcription service
import sys
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.audio_processor import AudioProcessor
from src.gemini_client import GeminiClient
from src.transcription_service import TranscriptionService as CleanTranscriptionService

logger = logging.getLogger(__name__)

def transcribe_audio(
    *,
    input_path: str,
    output_path: str,
    api_key: str,
    chunk_length_minutes: int,
    progress_callback,
) -> str:
    """
    Thin wrapper around the clean-architecture transcription pipeline.

    Exists primarily so tests can patch `backend.services.transcribe_audio` and so the
    backend implementation stays stable while the src/ internals evolve.
    """
    gemini_client = GeminiClient(api_key=api_key)
    audio_processor = AudioProcessor(
        chunk_length_ms=int(chunk_length_minutes) * 60 * 1000
    )
    clean_service = CleanTranscriptionService(
        gemini_client=gemini_client,
        audio_processor=audio_processor,
        chunk_length_minutes=int(chunk_length_minutes),
        language="vi",
    )
    result = clean_service.transcribe(
        input_path=input_path,
        output_path=output_path,
        progress_callback=progress_callback,
    )
    return result.output_path


class TranscriptionService:
    """Service for handling audio transcription"""

    def __init__(self, config: Config, job_store: Optional[JobStore] = None):
        self.config = config
        self.job_store = job_store
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
            
            # Transcribe audio with progress callback
            # Use gevent-compatible queue if available, otherwise use standard queue
            try:
                from gevent import queue as gevent_queue
                transcription_result = gevent_queue.Queue()
                transcription_error = gevent_queue.Queue()
                progress_queue = gevent_queue.Queue()
                QUEUE_EMPTY = gevent_queue.Empty
            except ImportError:
                import queue
                transcription_result = queue.Queue()
                transcription_error = queue.Queue()
                progress_queue = queue.Queue()
                QUEUE_EMPTY = queue.Empty
            
            def progress_callback(progress: int, message: str):
                """Callback function to report transcription progress"""
                progress_queue.put((progress, message))
            
            def run_transcription():
                try:
                    output_path = transcribe_audio(
                        input_path=file_path,
                        output_path=temp_output_path,
                        api_key=self.config.gemini_api_key,
                        chunk_length_minutes=chunk_length,
                        progress_callback=progress_callback
                    )
                    transcription_result.put(output_path)
                except Exception as e:
                    transcription_error.put(e)
            
            # Start transcription in background using gevent if available
            try:
                import gevent
                transcription_greenlet = gevent.spawn(run_transcription)
                transcription_alive = lambda: not transcription_greenlet.ready()
            except ImportError:
                # Fallback to threading if gevent not available
                import threading
                transcription_thread = threading.Thread(target=run_transcription, daemon=True)
                transcription_thread.start()
                transcription_alive = lambda: transcription_thread.is_alive()
            
            # Process progress updates and send them to client
            last_progress_time = time.time()
            # Send heartbeat every 8 seconds to keep connection alive
            # More frequent than frontend timeout (5 min) to ensure connection stays open
            # for long operations (15-20 minutes)
            heartbeat_interval = 8  # Send heartbeat every 8 seconds to keep connection alive
            
            try:
                while transcription_alive():
                    # Check for errors
                    try:
                        error = transcription_error.get_nowait()
                        raise error
                    except QUEUE_EMPTY:
                        pass
                    
                    # Check for progress updates (non-blocking)
                    try:
                        while True:
                            progress, message = progress_queue.get_nowait()
                            yield self.send_progress(progress, message)
                            last_progress_time = time.time()
                    except QUEUE_EMPTY:
                        pass
                    
                    # Send heartbeat frequently to keep connection alive and prevent timeout
                    # This is critical for long operations (15-20 minutes) to prevent browser/proxy timeouts
                    current_time = time.time()
                    if current_time - last_progress_time >= heartbeat_interval:
                        # Send a heartbeat with current progress to keep connection alive
                        # Use a generic message that doesn't change too often
                        elapsed_minutes = int((current_time - last_progress_time) / 60)
                        yield self.send_progress(
                            50, 
                            f'Transcription in progress... This may take 15-20 minutes for large files. Please keep this page open.'
                        )
                        last_progress_time = current_time
                    
                    # Small sleep to avoid busy waiting (use gevent.sleep for gevent workers)
                    # Wrap in try-except to handle SystemExit from worker timeout gracefully
                    try:
                        SLEEP(0.5)  # Check every 500ms for progress updates
                        # Ensure we yield execution even if SLEEP is mocked in tests.
                        # If gevent is available, yield to the hub so greenlets can run.
                        try:
                            import gevent
                            gevent.sleep(0)
                        except ImportError:
                            time.sleep(0)
                    except (SystemExit, KeyboardInterrupt):
                        # Worker is being killed (timeout or shutdown)
                        # Log the event
                        logger.warning("Worker timeout/shutdown detected during transcription")
                        # Try to yield a message about the timeout
                        try:
                            yield self.send_progress(
                                50,
                                'Worker timeout detected. The transcription may have been interrupted.'
                            )
                            yield f"data: {json.dumps({'error': 'Worker timeout detected. The transcription may have been interrupted. Please try again with a smaller file or contact support.'})}\n\n"
                        except:
                            pass  # Connection may be closed, ignore
                        # Break out of loop to allow cleanup
                        # Don't re-raise SystemExit here - we've handled it
                        return
            except (SystemExit, KeyboardInterrupt):
                # Handle worker timeout/shutdown gracefully at outer level
                logger.warning("SystemExit caught in transcription loop - worker timeout or shutdown")
                # Try to yield error message if connection is still open
                try:
                    yield f"data: {json.dumps({'error': 'Worker timeout detected. The transcription may have been interrupted. Please try again with a smaller file or contact support.'})}\n\n"
                except:
                    pass  # Connection may be closed, ignore
                # Don't re-raise - we've handled the error
                return
            
            # Process any remaining progress updates
            try:
                while True:
                    progress, message = progress_queue.get_nowait()
                    yield self.send_progress(progress, message)
            except QUEUE_EMPTY:
                pass
            
            # Get the result
            try:
                output_path = transcription_result.get(timeout=1)
            except QUEUE_EMPTY:
                # Check for errors
                try:
                    error = transcription_error.get_nowait()
                    raise error
                except QUEUE_EMPTY:
                    raise RuntimeError("Transcription completed but no result was returned")
            
            yield self.send_progress(95, 'Reading transcript...')
            
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

    def start_async_transcription(
        self,
        file_path: str,
        chunk_length: int,
        job_id: str,
    ) -> None:
        """
        Run transcription in the background and update job state in job_store.
        Caller must have already created the job and saved the file.
        """
        if not self.job_store:
            raise RuntimeError("JobStore is required for async transcription")

        def progress_callback(progress: int, message: str) -> None:
            self.job_store.update(job_id, progress=progress, message=message)

        def run() -> None:
            temp_dir = None
            temp_output_path = None
            try:
                is_valid, err_msg = self.validator.validate_file_size(file_path)
                if not is_valid:
                    self.job_store.update(
                        job_id, status="failed", progress=0, message=err_msg, error=err_msg
                    )
                    return
                valid_chunk_length = self.validator.validate_chunk_length(chunk_length)
                temp_dir = tempfile.mkdtemp(prefix="audio_upload_")
                temp_output_path = os.path.join(temp_dir, "transcript.txt")
                self.job_store.update(job_id, progress=5, message="Starting transcription...")
                output_path = transcribe_audio(
                    input_path=file_path,
                    output_path=temp_output_path,
                    api_key=self.config.gemini_api_key,
                    chunk_length_minutes=valid_chunk_length,
                    progress_callback=progress_callback,
                )
                if not os.path.exists(output_path):
                    self.job_store.update(
                        job_id,
                        status="failed",
                        progress=95,
                        message="Transcript file not found",
                        error="Transcript file not found",
                    )
                    return
                with open(output_path, "r", encoding="utf-8") as f:
                    transcript = f.read()
                if not transcript or not transcript.strip():
                    transcript = "[No transcript generated. The audio file may be empty or contain no speech.]"
                self.job_store.update(
                    job_id,
                    status="completed",
                    progress=100,
                    message="Transcription complete!",
                    transcript=transcript,
                )
            except Exception as e:
                logger.exception("Async transcription failed for job %s", job_id)
                self.job_store.update(
                    job_id,
                    status="failed",
                    message=str(e),
                    error=str(e),
                )
            finally:
                self._cleanup_temp_files(temp_dir, file_path, temp_output_path)

        # Use a real OS thread for background work.
        #
        # Rationale: gevent greenlets are cooperative; this pipeline does blocking subprocess/file I/O
        # and CPU work. Running it in a greenlet can starve the Flask dev server (and even status
        # polling) making the app appear "stuck". A daemon thread keeps the HTTP server responsive.
        import threading
        thread = threading.Thread(target=run, daemon=True)
        thread.start()


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


