"""
Main transcription service orchestrating audio processing and API calls
"""

import os
import sys
import threading
import time
from pathlib import Path
from typing import Optional, Callable, List

# Handle imports when running as script or as module
_script_dir = Path(__file__).parent
_project_root = _script_dir.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.audio_processor import AudioProcessor
from src.gemini_client import GeminiClient
from src.domain import (
    AudioFile,
    AudioChunk,
    TranscriptChunk,
    TranscriptionResult,
    TranscriptionProgress
)
from src.exceptions import (
    TranscriptionError,
    AudioFileNotFoundError,
    AudioProcessingError
)
from src.constants import (
    DEFAULT_CHUNK_LENGTH_MINUTES,
    DEFAULT_LANGUAGE,
    OUTPUT_ENCODING
)


class TranscriptionService:
    """Orchestrates the transcription process"""
    
    def __init__(
        self,
        gemini_client: GeminiClient,
        audio_processor: Optional[AudioProcessor] = None,
        chunk_length_minutes: int = DEFAULT_CHUNK_LENGTH_MINUTES,
        language: str = DEFAULT_LANGUAGE
    ):
        """
        Initialize transcription service
        
        Args:
            gemini_client: Configured GeminiClient instance
            audio_processor: Optional AudioProcessor (creates default if None)
            chunk_length_minutes: Length of chunks in minutes
            language: Primary language for transcription
        """
        self.gemini_client = gemini_client
        self.audio_processor = audio_processor or AudioProcessor(
            chunk_length_ms=chunk_length_minutes * 60 * 1000
        )
        self.chunk_length_minutes = chunk_length_minutes
        self.language = language
    
    def transcribe(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> TranscriptionResult:
        """
        Transcribe an audio file
        
        Args:
            input_path: Path to input audio file
            output_path: Optional path to save transcript (auto-generated if None)
            progress_callback: Optional callback for progress updates
            
        Returns:
            TranscriptionResult with transcript and metadata
            
        Raises:
            AudioFileNotFoundError: If input file doesn't exist
            AudioProcessingError: If audio processing fails
            TranscriptionError: If transcription fails
        """
        # Validate input file
        if not os.path.exists(input_path):
            raise AudioFileNotFoundError(f"Audio file not found: {input_path}")
        
        # Set default output path
        if output_path is None:
            input_stem = Path(input_path).stem
            output_path = f"{input_stem}_transcript.txt"
        
        # Step 1: Load and analyze audio
        if progress_callback:
            progress_callback(10, "Starting audio chunking...")
        if progress_callback:
            progress_callback(11, "Loading audio file... (this can take a few minutes for long files)")

        audio_file: Optional[AudioFile] = None
        load_error: Optional[BaseException] = None
        load_done = threading.Event()

        def _load() -> None:
            nonlocal audio_file, load_error
            try:
                audio_file = self.audio_processor.load_audio(input_path)
            except BaseException as e:
                load_error = e
            finally:
                load_done.set()

        t = threading.Thread(target=_load, daemon=True)
        t.start()

        started_at = time.time()
        last_heartbeat = started_at
        heartbeat_every_s = 10

        while not load_done.wait(timeout=1):
            if not progress_callback:
                continue
            now = time.time()
            if now - last_heartbeat >= heartbeat_every_s:
                elapsed_s = int(now - started_at)
                progress_callback(11, f"Loading audio file... ({elapsed_s}s elapsed)")
                last_heartbeat = now

        if load_error is not None:
            raise load_error
        if audio_file is None:
            raise AudioProcessingError("Failed to load audio file (unknown error).")

        if progress_callback:
            progress_callback(12, "Audio loaded, splitting into chunks...")
        
        # Step 2: Chunk audio
        chunks, temp_dir = self.audio_processor.chunk_audio(
            audio_file,
            progress_callback
        )
        
        # Step 3: Transcribe chunks
        if progress_callback:
            progress_callback(25, f"Starting transcription of {len(chunks)} chunks...")
        
        transcript_chunks = self._transcribe_chunks(
            chunks,
            progress_callback
        )
        
        # Step 4: Combine transcripts
        if progress_callback:
            progress_callback(85, "Combining all transcript chunks...")
        
        final_transcript = self._combine_transcripts(transcript_chunks)
        
        # Step 5: Save transcript
        if progress_callback:
            progress_callback(90, "Saving final transcript...")
        
        self._save_transcript(output_path, final_transcript, transcript_chunks)
        
        if progress_callback:
            progress_callback(95, f"Transcription complete! ({len(final_transcript)} characters)")
        
        # Step 6: Cleanup
        self._cleanup_temp_files(chunks, temp_dir)
        
        # Create result
        blocked_chunks = [
            chunk.chunk_number for chunk in transcript_chunks
            if chunk.is_error and "safety filters" in (chunk.error_message or "")
        ]
        failed_chunks = [
            chunk.chunk_number for chunk in transcript_chunks
            if chunk.is_error and chunk.chunk_number not in blocked_chunks
        ]
        successful_chunks = len(transcript_chunks) - len(failed_chunks) - len(blocked_chunks)
        
        return TranscriptionResult(
            transcript=final_transcript,
            output_path=output_path,
            total_chunks=len(chunks),
            successful_chunks=successful_chunks,
            failed_chunks=len(failed_chunks),
            blocked_chunks=blocked_chunks
        )
    
    def _transcribe_chunks(
        self,
        chunks: List[AudioChunk],
        progress_callback: Optional[Callable[[int, str], None]]
    ) -> List[TranscriptChunk]:
        """
        Transcribe all chunks
        
        Args:
            chunks: List of AudioChunk objects
            progress_callback: Optional progress callback
            
        Returns:
            List of TranscriptChunk objects
        """
        transcript_chunks = []
        
        for chunk in chunks:
            transcript_chunk = self.gemini_client.transcribe_chunk(
                chunk_path=chunk.path,
                chunk_number=chunk.chunk_number,
                total_chunks=len(chunks),
                language=self.language,
                progress_callback=progress_callback
            )
            transcript_chunks.append(transcript_chunk)
        
        return transcript_chunks
    
    def _combine_transcripts(self, transcript_chunks: List[TranscriptChunk]) -> str:
        """
        Combine transcript chunks into final transcript
        
        Args:
            transcript_chunks: List of TranscriptChunk objects
            
        Returns:
            Combined transcript text
        """
        transcript_parts = []
        
        for chunk in transcript_chunks:
            if chunk.is_error:
                error_msg = chunk.error_message or "Unknown error"
                transcript_parts.append(
                    f"[ERROR: Chunk {chunk.chunk_number} - {error_msg}]"
                )
            else:
                transcript_parts.append(chunk.text)
        
        final_transcript = "\n\n".join(transcript_parts)
        
        # Add summary if there are errors
        blocked_chunks = [
            chunk.chunk_number for chunk in transcript_chunks
            if chunk.is_error and "safety filters" in (chunk.error_message or "")
        ]
        failed_chunks = [
            chunk.chunk_number for chunk in transcript_chunks
            if chunk.is_error and chunk.chunk_number not in blocked_chunks
        ]
        
        if blocked_chunks or failed_chunks:
            summary_lines = [
                "\n" + "=" * 60,
                "TRANSCRIPTION SUMMARY",
                "=" * 60
            ]
            if blocked_chunks:
                summary_lines.append(
                    f"⚠️  {len(blocked_chunks)} chunk(s) blocked by safety filters: "
                    f"{', '.join(map(str, blocked_chunks))}"
                )
            if failed_chunks:
                summary_lines.append(
                    f"❌ {len(failed_chunks)} chunk(s) failed to transcribe: "
                    f"{', '.join(map(str, failed_chunks))}"
                )
            summary_lines.append("=" * 60 + "\n")
            final_transcript += "\n" + "\n".join(summary_lines)
        
        return final_transcript
    
    def _save_transcript(
        self,
        output_path: str,
        transcript: str,
        transcript_chunks: List[TranscriptChunk]
    ):
        """
        Save transcript to file
        
        Args:
            output_path: Path to save transcript
            transcript: Transcript text
            transcript_chunks: List of transcript chunks for validation
        """
        with open(output_path, "w", encoding=OUTPUT_ENCODING) as f:
            f.write(transcript)
    
    def _cleanup_temp_files(self, chunks: List[AudioChunk], temp_dir: str):
        """
        Clean up temporary chunk files
        
        Args:
            chunks: List of AudioChunk objects
            temp_dir: Temporary directory path
        """
        for chunk in chunks:
            try:
                if os.path.exists(chunk.path):
                    os.remove(chunk.path)
            except OSError:
                pass  # Ignore cleanup errors
        
        try:
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except OSError:
            pass  # Ignore cleanup errors

