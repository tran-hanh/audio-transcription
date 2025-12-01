#!/usr/bin/env python3
"""
Audio Transcription Script for Long Mixed-Language Files
Transcribes large audio files (2-4 hours) by chunking and using Google Gemini API.
Optimized for Vietnamese with English words.
"""

import os
import sys
import tempfile
import time
from pathlib import Path
from typing import List, Tuple

import google.generativeai as genai
from pydub import AudioSegment


# Configuration
CHUNK_LENGTH_MINUTES = 12  # Chunk size in minutes
CHUNK_LENGTH_MS = CHUNK_LENGTH_MINUTES * 60 * 1000
LANGUAGE = "vi"  # Vietnamese - primary language for better accuracy
OUTPUT_ENCODING = "utf-8"


def chunk_audio(audio_path: str, chunk_length_ms: int = CHUNK_LENGTH_MS) -> Tuple[List[str], str]:
    """
    Split a large audio file into smaller chunks.

    Args:
        audio_path: Path to the input audio file
        chunk_length_ms: Length of each chunk in milliseconds

    Returns:
        Tuple of (list of chunk file paths, temp directory path)
    """
    print(f"Loading audio file: {audio_path}")

    # Load the audio file
    # pydub supports many formats: mp3, wav, m4a, flac, etc.
    audio = AudioSegment.from_file(audio_path)
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

    # Split audio into chunks
    for i in range(0, total_length_ms, chunk_length_ms):
        chunk = audio[i:i + chunk_length_ms]
        chunk_num = len(chunk_paths) + 1

        # Create temporary file for this chunk
        chunk_filename = f"chunk_{chunk_num:04d}.mp3"
        chunk_path = os.path.join(temp_dir, chunk_filename)

        # Export chunk as MP3 (you can change format if needed)
        chunk.export(chunk_path, format="mp3")
        chunk_paths.append(chunk_path)

        chunk_minutes = len(chunk) / (60 * 1000)
        print(f"  Created chunk {chunk_num}: {chunk_minutes:.2f} minutes")

    print(f"Successfully created {len(chunk_paths)} chunks in {temp_dir}\n")
    return chunk_paths, temp_dir


def transcribe_chunk(
    model: genai.GenerativeModel,
    chunk_path: str,
    chunk_num: int,
    total_chunks: int
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

    audio_file = None
    try:
        # Upload audio file to Gemini
        audio_file = genai.upload_file(path=chunk_path)

        # Wait for the file to be processed
        print("  Waiting for file to be processed...")
        while audio_file.state.name == "PROCESSING":
            time.sleep(2)
            audio_file = genai.get_file(audio_file.name)

        if audio_file.state.name == "FAILED":
            raise RuntimeError(f"File processing failed: {audio_file.state.name}")

        # Create prompt for transcription with language hint
        prompt = (
            f"Please transcribe this audio file. The primary language is "
            f"Vietnamese ({LANGUAGE}), but there may be some English words "
            f"mixed in. Provide only the transcription text, no additional "
            f"commentary."
        )

        # Call Gemini API for transcription
        response = model.generate_content([prompt, audio_file])

        # Extract text from response
        text = response.text.strip()

        # Delete the uploaded file to free up quota
        genai.delete_file(audio_file.name)

        print(f"  ✓ Chunk {chunk_num} transcribed ({len(text)} characters)\n")
        return text

    except Exception as e:
        print(f"  ✗ Error transcribing chunk {chunk_num}: {e}\n")
        # Try to clean up uploaded file if it exists
        if audio_file is not None:
            try:
                genai.delete_file(audio_file.name)
            except Exception:
                pass
        return f"[ERROR: Failed to transcribe chunk {chunk_num}]"


def transcribe_audio(
    input_path: str,
    output_path: str = None,
    api_key: str = None,
    chunk_length_minutes: int = CHUNK_LENGTH_MINUTES
) -> str:
    """
    Main function to transcribe a long audio file.

    Args:
        input_path: Path to input audio file
        output_path: Path to save the final transcript
        api_key: Google Gemini API key
        chunk_length_minutes: Length of each chunk in minutes

    Returns:
        Path to the output transcript file
    """
    # Validate input file
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Audio file not found: {input_path}")

    # Set default output path if not provided
    if output_path is None:
        input_stem = Path(input_path).stem
        output_path = f"{input_stem}_transcript.txt"

    # Initialize Gemini API
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "Gemini API key not found. Set GEMINI_API_KEY environment variable "
                "or pass api_key parameter."
            )

    genai.configure(api_key=api_key)

    # Find an available model that supports generateContent
    # Prefer models that support audio (1.5 series)
    model = None
    preferred_models = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']

    # First, try to get list of available models
    try:
        available_models = [
            m.name.split('/')[-1] for m in genai.list_models()
            if 'generateContent' in m.supported_generation_methods
        ]
        print(f"Available models: {', '.join(available_models)}")

        # Try preferred models in order
        for model_name in preferred_models:
            if model_name in available_models:
                model = genai.GenerativeModel(model_name)
                print(f"Using model: {model_name}")
                break

        # If none of the preferred models are available, use the first available
        if model is None and available_models:
            model_name = available_models[0]
            model = genai.GenerativeModel(model_name)
            print(f"Using available model: {model_name}")
    except Exception as e:
        print(f"Could not list models, trying default: {e}")
        # Fallback: try gemini-1.5-flash directly
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            print("Using model: gemini-1.5-flash")
        except Exception:
            model = genai.GenerativeModel('gemini-pro')
            print("Using model: gemini-pro")

    if model is None:
        raise ValueError("Could not initialize a Gemini model. "
                         "Please check your API key.")

    # Step 1: Chunk the audio file
    chunk_length_ms = chunk_length_minutes * 60 * 1000
    chunk_paths, temp_dir = chunk_audio(input_path, chunk_length_ms)

    # Step 2: Transcribe each chunk
    transcripts = []
    total_chunks = len(chunk_paths)

    print("=" * 60)
    print("Starting transcription process...")
    print("=" * 60 + "\n")

    for i, chunk_path in enumerate(chunk_paths, 1):
        transcript = transcribe_chunk(model, chunk_path, i, total_chunks)
        transcripts.append(transcript)

    # Step 3: Combine all transcripts
    print("=" * 60)
    print("Combining transcripts...")
    print("=" * 60 + "\n")

    # Join transcripts with double newline for readability
    final_transcript = "\n\n".join(transcripts)

    # Step 4: Save to output file
    print(f"Saving final transcript to: {output_path}")
    with open(output_path, "w", encoding=OUTPUT_ENCODING) as f:
        f.write(final_transcript)

    print(f"✓ Transcription complete! ({len(final_transcript)} characters)")

    # Cleanup: Remove temporary chunk files
    print(f"\nCleaning up temporary files in {temp_dir}...")
    for chunk_path in chunk_paths:
        try:
            os.remove(chunk_path)
        except Exception as e:
            print(f"  Warning: Could not remove {chunk_path}: {e}")

    try:
        os.rmdir(temp_dir)
        print("✓ Cleanup complete")
    except Exception as e:
        print(f"  Warning: Could not remove temp directory: {e}")

    return output_path


def main():
    """Command-line interface for the transcription script."""
    import argparse

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
