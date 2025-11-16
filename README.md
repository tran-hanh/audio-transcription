# Long Audio Transcription Tool

A Python application for transcribing very long audio files (2-4 hours) using Google's Gemini API. Optimized for mixed-language content, primarily Vietnamese with English words.

## Features

- **Handles large files**: Automatically chunks audio files to bypass API size limits
- **Vietnamese-optimized**: Uses language hints for best accuracy on Vietnamese content
- **Mixed-language support**: Still transcribes English words mixed into Vietnamese
- **Automatic cleanup**: Removes temporary chunk files after transcription

## Setup

### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

**Note:** `pydub` requires `ffmpeg` for audio processing. Install it:

- **macOS**: 
  - If you have Homebrew installed: `brew install ffmpeg`
  - If you don't have Homebrew, install it first:
    ```bash
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    ```
    Then run: `brew install ffmpeg`
  - Alternative: Download pre-built binary from [evermeet.cx/ffmpeg](https://evermeet.cx/ffmpeg/)
- **Ubuntu/Debian**: `sudo apt-get install ffmpeg`
- **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

### 2. Set Google Gemini API Key

You have two options:

**Option A: Environment Variable (Recommended)**
```bash
export GEMINI_API_KEY="your-api-key-here"
```

**Option B: Pass as Command-Line Argument**
```bash
python3 transcribe.py input.mp3 --api-key "your-api-key-here"
```

### 3. Get Your Google Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key" or "Get API Key"
4. Copy the API key and use it as shown above

**Note:** Google Gemini API offers a free tier with generous limits. Check [Google AI Studio](https://aistudio.google.com) for current pricing and limits.

## Usage

### Basic Usage

```bash
python3 transcribe.py input.mp3
```

This will create `input_transcript.txt` in the same directory.

### Specify Output File

```bash
python3 transcribe.py input.mp3 --output transcript.txt
```

### Adjust Chunk Size

Default chunk size is 12 minutes. To change it:

```bash
python3 transcribe.py input.mp3 --chunk-length 15
```

### Full Example

```bash
python3 transcribe.py long_audio.mp3 --output final_transcript.txt --chunk-length 10
```

## How It Works

1. **Load**: Reads the input audio file
2. **Chunk**: Splits audio into smaller pieces (default: 12 minutes each)
3. **Transcribe**: Sends each chunk to Google Gemini API with Vietnamese language hints
4. **Combine**: Merges all transcript segments in order
5. **Save**: Writes the complete transcript to the output file
6. **Cleanup**: Removes temporary chunk files and uploaded files from Gemini

## Supported Audio Formats

The script supports any format that `pydub` can handle, including:
- MP3
- WAV
- M4A
- FLAC
- OGG
- And more (via ffmpeg)

## Configuration

You can modify these constants in `transcribe.py`:

- `CHUNK_LENGTH_MINUTES`: Default chunk size (12 minutes)
- `LANGUAGE`: Primary language for transcription (`"vi"` for Vietnamese)
- `OUTPUT_ENCODING`: Text file encoding (`"utf-8"`)

## Troubleshooting

### "ffmpeg not found"
Install ffmpeg (see Setup section above).

### "Gemini API key not found"
Set the `GEMINI_API_KEY` environment variable or pass `--api-key`.

### "File too large" errors
Reduce chunk size with `--chunk-length` (e.g., `--chunk-length 10`).

### API rate limits
If you hit rate limits, the script will show errors. Wait a moment and re-run, or implement retry logic.

## License

This script is provided as-is for educational and personal use.

