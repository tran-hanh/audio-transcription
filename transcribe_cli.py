#!/usr/bin/env python3
"""
Simple CLI wrapper for audio transcription
Usage: python transcribe_cli.py <audio_file> [output_file]
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from transcribe import transcribe_audio


def print_progress(progress: int, message: str):
    """Print progress updates to terminal"""
    # Use carriage return to overwrite the same line
    progress_bar_length = 30
    filled = int(progress_bar_length * progress / 100)
    bar = '█' * filled + '░' * (progress_bar_length - filled)
    print(f'\r[{bar}] {progress:3d}% - {message}', end='', flush=True)
    if progress >= 100:
        print()  # New line when complete


def main():
    if len(sys.argv) < 2:
        print("Usage: python transcribe_cli.py <audio_file> [output_file]")
        print("\nExample:")
        print("  python transcribe_cli.py audio.m4a")
        print("  python transcribe_cli.py audio.m4a output.txt")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Generate output filename if not provided
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        input_path = Path(input_file)
        output_file = str(input_path.with_suffix('.txt'))
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        sys.exit(1)
    
    # Get API key from environment
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        print("Please set it with: export GEMINI_API_KEY='your-api-key'")
        sys.exit(1)
    
    print(f"Transcribing: {input_file}")
    print(f"Output will be saved to: {output_file}")
    print("This may take several minutes for large files...\n")
    
    try:
        output_path = transcribe_audio(
            input_path=input_file,
            output_path=output_file,
            api_key=api_key,
            chunk_length_minutes=12,
            progress_callback=print_progress
        )
        print(f"\n{'='*60}")
        print(f"SUCCESS: Transcript saved to {output_path}")
        print(f"{'='*60}")
        return 0
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"ERROR: {e}")
        print(f"{'='*60}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

