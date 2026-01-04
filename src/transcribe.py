#!/usr/bin/env python3
"""
Audio Transcription Script for Long Mixed-Language Files
Transcribes large audio files (2-4 hours) by chunking and using Google Gemini API.
Optimized for Vietnamese with English words.

This module provides a backward-compatible interface to the transcription service.
The actual implementation uses clean architecture with separated concerns.
"""

import argparse
import os
import sys
from pathlib import Path

# Add parent directory to path to allow imports when running as script
# This allows the script to be run directly: python3 src/transcribe.py
_script_dir = Path(__file__).parent
_project_root = _script_dir.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Import new clean architecture modules
from src.gemini_client import GeminiClient
from src.audio_processor import AudioProcessor
from src.transcription_service import TranscriptionService
from src.constants import DEFAULT_CHUNK_LENGTH_MINUTES, DEFAULT_LANGUAGE
from src.exceptions import TranscriptionError

# Backward compatibility exports
CHUNK_LENGTH_MINUTES = DEFAULT_CHUNK_LENGTH_MINUTES
CHUNK_LENGTH_MS = DEFAULT_CHUNK_LENGTH_MINUTES * 60 * 1000
LANGUAGE = DEFAULT_LANGUAGE
OUTPUT_ENCODING = "utf-8"


def chunk_audio(audio_path: str, chunk_length_ms: int = CHUNK_LENGTH_MS, progress_callback=None):
    """
    DEPRECATED: Use AudioProcessor.chunk_audio() instead.
    This function is kept for backward compatibility.
    """
    from typing import List, Tuple
    import tempfile
    from pydub import AudioSegment
    """
    Split a large audio file into smaller chunks.

    Args:
        audio_path: Path to the input audio file
        chunk_length_ms: Length of each chunk in milliseconds

    Returns:
        Tuple of (list of chunk file paths, temp directory path)
        
    Raises:
        RuntimeError: If audio file cannot be loaded or processed
    """
    print(f"Loading audio file: {audio_path}")

    # Load the audio file
    # pydub supports many formats: mp3, wav, m4a, flac, etc.
    # This uses subprocess calls to ffmpeg, which should be gevent-compatible
    # if monkey patching is enabled
    try:
        audio = AudioSegment.from_file(audio_path)
    except Exception as e:
        error_msg = (
            f"Failed to load audio file: {e}. "
            "Please ensure the file is a valid audio format and ffmpeg is available."
        )
        print(f"ERROR: {error_msg}")
        if progress_callback:
            progress_callback(0, error_msg)
        raise RuntimeError(error_msg) from e
    
    # Normalize audio volume to ensure it's loud enough for transcription
    # Low volume audio can cause processing issues and false safety filter blocks
    print("Analyzing audio volume...")
    audio_dBFS = audio.dBFS
    print(f"  Current audio level: {audio_dBFS:.1f} dBFS")
    
    # Normalize audio to -20 dBFS (good level for speech transcription)
    # If audio is quieter than -30 dBFS, it might be too quiet for reliable processing
    target_dBFS = -20.0
    if audio_dBFS < -30.0:
        print(f"  ⚠️  Audio is very quiet ({audio_dBFS:.1f} dBFS). Normalizing to {target_dBFS:.1f} dBFS...")
        # Calculate how much to increase volume
        change_in_dB = target_dBFS - audio_dBFS
        audio = audio.apply_gain(change_in_dB)
        print(f"  ✓ Audio normalized to {audio.dBFS:.1f} dBFS")
    elif audio_dBFS < target_dBFS:
        print(f"  Audio is slightly quiet ({audio_dBFS:.1f} dBFS). Normalizing to {target_dBFS:.1f} dBFS...")
        change_in_dB = target_dBFS - audio_dBFS
        audio = audio.apply_gain(change_in_dB)
        print(f"  ✓ Audio normalized to {audio.dBFS:.1f} dBFS")
    else:
        print(f"  ✓ Audio volume is adequate ({audio_dBFS:.1f} dBFS)")
    
    total_length_ms = len(audio)
    total_minutes = total_length_ms / (60 * 1000)

    print(f"Audio duration: {total_minutes:.2f} minutes ({total_length_ms} ms)")

    # Create temporary directory for chunks
    temp_dir = tempfile.mkdtemp(prefix="audio_chunks_")
    chunk_paths = []

    # Calculate number of chunks needed
    num_chunks = (total_length_ms // chunk_length_ms) + 1
    chunk_msg = (f"Splitting into approximately {num_chunks} chunks of "
                 f"~{CHUNK_LENGTH_MINUTES} minutes each...")
    print(chunk_msg)
    
    if progress_callback:
        progress_callback(15, f"Analyzing audio file ({total_minutes:.1f} minutes total)...")

    # Split audio into chunks
    for i in range(0, total_length_ms, chunk_length_ms):
        chunk = audio[i:i + chunk_length_ms]
        chunk_num = len(chunk_paths) + 1

        # Create temporary file for this chunk
        chunk_filename = f"chunk_{chunk_num:04d}.mp3"
        chunk_path = os.path.join(temp_dir, chunk_filename)

        # Export chunk as MP3 (you can change format if needed)
        # This uses subprocess calls to ffmpeg
        try:
            chunk.export(chunk_path, format="mp3")
        except Exception as e:
            error_msg = f"Failed to export chunk {chunk_num}: {e}"
            print(f"ERROR: {error_msg}")
            if progress_callback:
                progress_callback(0, error_msg)
            raise RuntimeError(error_msg) from e
        
        chunk_paths.append(chunk_path)

        chunk_minutes = len(chunk) / (60 * 1000)
        print(f"  Created chunk {chunk_num}: {chunk_minutes:.2f} minutes")
        
        if progress_callback:
            progress_callback(
                15 + int((chunk_num / num_chunks) * 10),
                f"Created chunk {chunk_num} of ~{num_chunks} ({chunk_minutes:.1f} min)"
            )

    print(f"Successfully created {len(chunk_paths)} chunks in {temp_dir}\n")
    
    if progress_callback:
        progress_callback(25, f"Successfully created {len(chunk_paths)} chunks. Starting transcription...")
    
    return chunk_paths, temp_dir


def transcribe_chunk(
    model: genai.GenerativeModel,
    chunk_path: str,
    chunk_num: int,
    total_chunks: int,
    progress_callback=None,
    model_has_safety_settings: bool = False
) -> str:
    """
    Transcribe a single audio chunk using Google Gemini API.

    Args:
        model: Gemini model instance
        chunk_path: Path to the audio chunk file
        chunk_num: Current chunk number (for progress display)
        total_chunks: Total number of chunks

    Returns:
        Transcribed text from the chunk
    """
    print(f"Transcribing chunk {chunk_num}/{total_chunks}...")
    
    if progress_callback:
        # Calculate progress: 25% (chunking done) to 85% (before combining)
        # Each chunk gets (85-25)/total_chunks percentage
        base_progress = 25
        progress_per_chunk = 60 / total_chunks
        current_progress = base_progress + int((chunk_num - 1) * progress_per_chunk)
        progress_callback(current_progress, f"Transcribing chunk {chunk_num} of {total_chunks}...")

    audio_file = None
    try:
        # Upload audio file to Gemini
        if progress_callback:
            progress_callback(current_progress + 2, f"Uploading chunk {chunk_num} to API...")
        audio_file = genai.upload_file(path=chunk_path)

        # Wait for the file to be processed
        print("  Waiting for file to be processed...")
        if progress_callback:
            progress_callback(current_progress + 5, f"Processing chunk {chunk_num}...")
        while audio_file.state.name == "PROCESSING":
            time.sleep(2)
            audio_file = genai.get_file(audio_file.name)

        if audio_file.state.name == "FAILED":
            raise RuntimeError(f"File processing failed: {audio_file.state.name}")

        # Create prompt for transcription with language hint
        # Explicitly state this is a transcription task to reduce false positives
        prompt = (
            f"This is an audio transcription task. Please transcribe this audio file verbatim. "
            f"The primary language is Vietnamese ({LANGUAGE}), but there may be some English words "
            f"mixed in. This is a legitimate transcription request for documentation purposes. "
            f"Provide only the exact transcription text, no additional commentary or interpretation."
        )

        # Call Gemini API for transcription
        if progress_callback:
            progress_callback(current_progress + 8, f"Transcribing chunk {chunk_num}...")
        
        # Configure safety settings to minimize false positives for transcription
        # If model was created with safety settings, we may not need per-request settings
        # But we'll still try per-request settings as a fallback
        safety_settings = None
        safety_settings_applied = False
        
        # Only configure per-request safety settings if model doesn't have them
        if not model_has_safety_settings:
            # Try to configure safety settings - this is critical for Vietnamese audio
            # which often gets false positives from safety filters
            try:
                from google.generativeai.types import HarmCategory, HarmBlockThreshold
                
                # Try BLOCK_NONE first (most permissive - disables safety filters)
                # This is appropriate for transcription which is a neutral documentation task
                try:
                    # Check what thresholds are available
                    available_thresholds = [attr for attr in dir(HarmBlockThreshold) if not attr.startswith('_')]
                    print(f"  Available safety thresholds: {available_thresholds}")
                    
                    # Try BLOCK_NONE first (most permissive)
                    if hasattr(HarmBlockThreshold, 'BLOCK_NONE'):
                        safety_settings = {
                            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                        }
                        print(f"  ✓ Using per-request BLOCK_NONE safety settings")
                        safety_settings_applied = True
                    elif hasattr(HarmBlockThreshold, 'BLOCK_ONLY_HIGH'):
                        # Fallback to BLOCK_ONLY_HIGH
                        safety_settings = {
                            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                        }
                        print(f"  ✓ Using per-request BLOCK_ONLY_HIGH safety settings")
                        safety_settings_applied = True
                    else:
                        print(f"  ⚠️  No suitable safety threshold found")
                except (AttributeError, ValueError, TypeError) as e:
                    print(f"  ⚠️  Error configuring safety settings: {e}")
            except (ImportError, AttributeError) as e:
                # Fallback if safety settings are not available in this API version
                print(f"  ⚠️  Safety settings not available: {type(e).__name__}")
                pass
        else:
            print(f"  ✓ Model already configured with safety settings, using model-level settings")
        
        # Generate content with safety settings, with retry logic for safety blocks
        max_retries = 3
        response = None
        
        for attempt in range(max_retries):
            try:
                # Try with safety settings first if available
                if safety_settings and safety_settings_applied and attempt == 0:
                    try:
                        # Also try using generation_config as an alternative method
                        try:
                            from google.generativeai.types import GenerationConfig
                            generation_config = GenerationConfig(
                                temperature=0.1,  # Low temperature for accurate transcription
                            )
                            response = model.generate_content(
                                [prompt, audio_file],
                                safety_settings=safety_settings,
                                generation_config=generation_config
                            )
                        except (ImportError, AttributeError, TypeError):
                            # Fallback to just safety_settings
                            response = model.generate_content(
                                [prompt, audio_file],
                                safety_settings=safety_settings
                            )
                        
                        # Check prompt_feedback to see if safety settings were applied
                        if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                            if hasattr(response.prompt_feedback, 'block_reason') and response.prompt_feedback.block_reason:
                                print(f"  ⚠️  Prompt was blocked despite safety settings: {response.prompt_feedback.block_reason}")
                    except Exception as safety_error:
                        # If safety settings fail, try without them
                        print(f"  ⚠️  Safety settings error: {safety_error}, trying without...")
                        safety_settings_applied = False
                        response = model.generate_content([prompt, audio_file])
                else:
                    # Try without safety settings - sometimes this works better
                    response = model.generate_content([prompt, audio_file])
                
                # Wait a moment for response to fully populate (Gemini may need time to process)
                # This helps avoid false positives where we retry before Gemini finishes processing
                import time
                time.sleep(0.5)  # Small delay to ensure response is complete
                
                # Check if response was blocked by safety filters
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    
                    # IMPORTANT: Check if we have actual content despite safety flag
                    # Gemini may return finish_reason=SAFETY but still include the transcription
                    # This happens when Gemini processes slowly - we retry before it finishes
                    has_actual_content = False
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text and part.text.strip():
                                    has_actual_content = True
                                    break
                    
                    if candidate.finish_reason == 1:  # SAFETY
                        # If we have content despite SAFETY flag, use it! (false positive)
                        if has_actual_content:
                            print(f"  ✓ Safety flag detected but content present - using transcription (false positive)")
                            # Break out of retry loop and proceed to text extraction
                            break
                        
                        # No content - this is a real safety block
                        # Get more details about why it was blocked
                        print(f"  ⚠️  SAFETY BLOCK DETECTED - Getting diagnostic information...")
                        
                        # Try to get safety ratings from candidate
                        try:
                            if hasattr(candidate, 'safety_ratings') and candidate.safety_ratings:
                                safety_info = []
                                for r in candidate.safety_ratings:
                                    cat = r.category.name if hasattr(r.category, 'name') else str(r.category)
                                    prob = r.probability.name if hasattr(r.probability, 'name') else str(r.probability)
                                    safety_info.append(f"{cat}={prob}")
                                if safety_info:
                                    print(f"  📊 Candidate safety ratings: {', '.join(safety_info)}")
                        except Exception as e:
                            print(f"  ⚠️  Could not read candidate safety ratings: {e}")
                        
                        # Check prompt_feedback for additional info
                        try:
                            if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                                if hasattr(response.prompt_feedback, 'block_reason'):
                                    block_reason = response.prompt_feedback.block_reason
                                    print(f"  📊 Prompt block reason: {block_reason}")
                                if hasattr(response.prompt_feedback, 'safety_ratings') and response.prompt_feedback.safety_ratings:
                                    prompt_safety_info = []
                                    for r in response.prompt_feedback.safety_ratings:
                                        cat = r.category.name if hasattr(r.category, 'name') else str(r.category)
                                        prob = r.probability.name if hasattr(r.probability, 'name') else str(r.probability)
                                        prompt_safety_info.append(f"{cat}={prob}")
                                    if prompt_safety_info:
                                        print(f"  📊 Prompt safety ratings: {', '.join(prompt_safety_info)}")
                        except Exception as e:
                            print(f"  ⚠️  Could not read prompt feedback: {e}")
                        
                        # Also try to get finish_reason as string for debugging
                        try:
                            finish_reason_str = getattr(candidate, 'finish_reason', None)
                            print(f"  📊 Finish reason code: {finish_reason_str} (1=SAFETY)")
                        except:
                            pass
                        
                        if attempt < max_retries - 1:
                            print(f"  ⚠️  Chunk {chunk_num} blocked by safety filters (attempt {attempt + 1}/{max_retries})")
                            
                            # Try different strategies on each retry
                            if attempt == 0:
                                # First retry: Try without safety settings (even though model has them)
                                print(f"  Retrying without per-request safety settings...")
                                safety_settings = None
                                safety_settings_applied = False
                            elif attempt == 1:
                                # Second retry: Try with shorter, more direct prompt
                                prompt = (
                                    f"Transcribe Vietnamese audio. Language: {LANGUAGE}. "
                                    f"Output transcription only."
                                )
                                print(f"  Retrying with shorter, more direct prompt...")
                            else:
                                # Third retry: Try minimal prompt
                                prompt = "Transcribe this audio."
                                print(f"  Retrying with minimal prompt...")
                            continue
                        else:
                            # Last attempt failed - provide helpful error message
                            error_msg = (
                                f"Content was blocked due to safety filters after {max_retries} retries. "
                                f"This is likely a false positive for Vietnamese audio. "
                                f"Note: Google updated Gemini models in December 2025 which may have changed "
                                f"safety filter behavior. The chunk will be marked as [ERROR] in the transcript."
                            )
                            raise ValueError(error_msg)
                
                # Success - break out of retry loop
                break
                
            except ValueError as ve:
                # Re-raise our custom ValueError about safety blocks
                if "blocked" in str(ve).lower() or "safety" in str(ve).lower():
                    if attempt < max_retries - 1:
                        print(f"  ⚠️  Retrying chunk {chunk_num} (attempt {attempt + 2}/{max_retries})...")
                        safety_settings = None
                        safety_settings_applied = False
                        continue
                    else:
                        raise
                else:
                    raise
            except Exception as api_error:
                # If safety settings cause an error, try without them
                if safety_settings_applied and "safety" in str(api_error).lower() and attempt < max_retries - 1:
                    print(f"  ⚠️  Safety settings error, retrying without safety settings...")
                    safety_settings = None
                    safety_settings_applied = False
                    continue
                elif attempt < max_retries - 1:
                    print(f"  ⚠️  Error on attempt {attempt + 1}, retrying...")
                    continue
                else:
                    raise
        
        if response is None:
            raise RuntimeError("Failed to get response after all retry attempts")

        # Extract text from response, handling safety blocks and empty responses
        try:
            # Check if response has valid content
            if not response.candidates or not response.candidates[0].content:
                # No content returned (likely blocked by safety filters)
                finish_reason = response.candidates[0].finish_reason if response.candidates else "UNKNOWN"
                raise ValueError(f"Response blocked (finish_reason: {finish_reason}). Content may have been filtered by safety settings.")
            
            # Check finish reason
            candidate = response.candidates[0]
            if candidate.finish_reason == 1:  # SAFETY
                raise ValueError("Content was blocked due to safety filters. The audio may contain content that violates safety policies.")
            
            # Extract text safely
            text = response.text.strip() if hasattr(response, 'text') and response.text else ""
            if not text:
                # Try to get text from parts
                if candidate.content and candidate.content.parts:
                    text = " ".join([part.text for part in candidate.content.parts if hasattr(part, 'text') and part.text]).strip()
                if not text:
                    raise ValueError(f"Empty response received (finish_reason: {candidate.finish_reason})")
        except (ValueError, AttributeError) as e:
            # Re-raise our custom errors
            if isinstance(e, ValueError):
                raise
            # Handle AttributeError from response.text access
            finish_reason = response.candidates[0].finish_reason if (response.candidates and len(response.candidates) > 0) else "UNKNOWN"
            raise ValueError(f"Invalid response format (finish_reason: {finish_reason}). The response may have been blocked or is malformed.")

        # Delete the uploaded file to free up quota
        genai.delete_file(audio_file.name)

        print(f"  ✓ Chunk {chunk_num} transcribed ({len(text)} characters)\n")
        
        if progress_callback:
            progress_callback(
                base_progress + int(chunk_num * progress_per_chunk),
                f"Completed chunk {chunk_num} of {total_chunks} ({len(text)} characters)"
            )
        
        return text

    except Exception as e:
        error_msg = str(e)
        print(f"  ✗ Error transcribing chunk {chunk_num}: {error_msg}\n")
        # Try to clean up uploaded file if it exists
        if audio_file is not None:
            try:
                genai.delete_file(audio_file.name)
            except Exception:
                pass
        
        # Provide more informative error message in the transcript
        if "safety filters" in error_msg.lower() or "blocked" in error_msg.lower():
            return (
                f"[ERROR: Chunk {chunk_num} was blocked by safety filters. "
                f"This is likely a false positive for Vietnamese audio. "
                f"Note: Google updated Gemini API in December 2025 which may have changed safety filter behavior. "
                f"The chunk was skipped.]"
            )
        elif "finish_reason" in error_msg.lower():
            return f"[ERROR: Chunk {chunk_num} failed to transcribe. {error_msg}]"
        else:
            return f"[ERROR: Failed to transcribe chunk {chunk_num}: {error_msg}]"


def transcribe_audio(
    input_path: str,
    output_path: str = None,
    api_key: str = None,
    chunk_length_minutes: int = CHUNK_LENGTH_MINUTES,
    progress_callback=None
) -> str:
    """
    Main function to transcribe a long audio file (backward-compatible wrapper).
    
    This function maintains backward compatibility while using the new clean architecture.
    
    Args:
        input_path: Path to input audio file
        output_path: Path to save the final transcript
        api_key: Google Gemini API key
        chunk_length_minutes: Length of each chunk in minutes
        progress_callback: Optional callback for progress updates
        
    Returns:
        Path to the output transcript file
    """
    # Get API key
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY")
    
    # Initialize services using clean architecture
    gemini_client = GeminiClient(api_key=api_key)
    audio_processor = AudioProcessor(chunk_length_ms=chunk_length_minutes * 60 * 1000)
    transcription_service = TranscriptionService(
        gemini_client=gemini_client,
        audio_processor=audio_processor,
        chunk_length_minutes=chunk_length_minutes,
        language=LANGUAGE
    )
    
    # Transcribe using the service
    result = transcription_service.transcribe(
        input_path=input_path,
        output_path=output_path,
        progress_callback=progress_callback
    )
    
    return result.output_path


def main():
    """Command-line interface for the transcription script."""
    parser = argparse.ArgumentParser(
        description="Transcribe long audio files using Google Gemini API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 transcribe.py input.mp3
  python3 transcribe.py input.mp3 --output transcript.txt
  python3 transcribe.py input.mp3 --chunk-length 15
        """
    )

    parser.add_argument(
        "input",
        help="Path to input audio file (mp3, wav, m4a, etc.)"
    )

    parser.add_argument(
        "-o", "--output",
        help="Path to output transcript file (default: input_name_transcript.txt)"
    )

    parser.add_argument(
        "-c", "--chunk-length",
        type=int,
        default=CHUNK_LENGTH_MINUTES,
        help=f"Chunk size in minutes (default: {CHUNK_LENGTH_MINUTES})"
    )

    parser.add_argument(
        "--api-key",
        help="Google Gemini API key (default: uses GEMINI_API_KEY env var)"
    )

    args = parser.parse_args()

    try:
        output_path = transcribe_audio(
            input_path=args.input,
            output_path=args.output,
            api_key=args.api_key,
            chunk_length_minutes=args.chunk_length
        )
        print(f"\n{'='*60}")
        print(f"SUCCESS: Transcript saved to {output_path}")
        print(f"{'='*60}")

    except Exception as e:
        print(f"\n{'='*60}")
        print(f"ERROR: {e}")
        print(f"{'='*60}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
