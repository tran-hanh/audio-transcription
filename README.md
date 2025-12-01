# Long Audio Transcription Tool

A Python application for transcribing very long audio files (2-4 hours) using Google's Gemini API. Optimized for mixed-language content, primarily Vietnamese with English words.

**Now available as a web app!** Upload audio files directly through your browser and download transcripts instantly.

## Project Structure

This project follows a clean monorepo structure:

```
audio_transcription/
├── backend/          # Flask API server
│   └── app.py
├── src/              # Core transcription library
│   └── transcribe.py
├── frontend/         # Web application
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── tests/            # Test suite
│   └── README.md     # Testing documentation
└── .github/workflows/
    └── ci-cd.yml     # CI/CD pipeline
```

## Features

- **Web Interface**: Beautiful, modern web app deployable to GitHub Pages
- **Handles large files**: Automatically chunks audio files to bypass API size limits
- **Vietnamese-optimized**: Uses language hints for best accuracy on Vietnamese content
- **Mixed-language support**: Still transcribes English words mixed into Vietnamese
- **Automatic cleanup**: Removes temporary chunk files after transcription
- **Real-time progress**: See transcription progress in real-time

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
python3 src/transcribe.py input.mp3 --api-key "your-api-key-here"
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
python3 src/transcribe.py input.mp3
```

This will create `input_transcript.txt` in the same directory.

### Specify Output File

```bash
python3 src/transcribe.py input.mp3 --output transcript.txt
```

### Adjust Chunk Size

Default chunk size is 12 minutes. To change it:

```bash
python3 src/transcribe.py input.mp3 --chunk-length 15
```

### Full Example

```bash
python3 src/transcribe.py long_audio.mp3 --output final_transcript.txt --chunk-length 10
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

You can modify these constants in `src/transcribe.py`:

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

## Web App Deployment

The project includes a web interface that can be deployed to GitHub Pages with a backend API.

### Architecture

- **Frontend**: Static HTML/CSS/JS files (deployed to GitHub Pages)
- **Backend**: Flask API server (deployed to Render, Railway, or similar)

### Deploying the Frontend to GitHub Pages

1. **Enable GitHub Pages**:
   - Go to your repository Settings → Pages
   - Select "GitHub Actions" as the source
   - The workflow in `.github/workflows/ci-cd.yml` will automatically deploy on push

2. **Update API URL**:
   - Open `frontend/src/config/api.ts`
   - Update `API_BASE_URL` with your backend API URL (after deploying backend)

3. **Push to main branch**:
   ```bash
   git add .
   git commit -m "Deploy web app"
   git push origin main
   ```

   Your site will be available at: `https://yourusername.github.io/audio_transcription/`

### Deploying the Backend API

#### Option 1: Render (Recommended - Free tier available)

1. **Create a Render account** at [render.com](https://render.com)

2. **Create a new Web Service**:
   - Connect your GitHub repository
   - Select the repository
   - Use these settings:
     - **Name**: `audio-transcription-api`
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn backend.app:app --bind 0.0.0.0:$PORT`
     - **Plan**: Free (or paid for better performance)

3. **Set Environment Variables**:
   - Go to Environment tab
   - Add `GEMINI_API_KEY` with your API key

4. **Deploy**:
   - Render will automatically deploy
   - Copy the service URL (e.g., `https://audio-transcription-api.onrender.com`)

5. **Update Frontend**:
   - Update `API_BASE_URL` in `frontend/src/config/api.ts` with your Render URL
   - Commit and push to trigger GitHub Pages redeploy

#### Option 2: Railway

1. **Create a Railway account** at [railway.app](https://railway.app)

2. **Create a new project** from GitHub repository

3. **Configure**:
   - Railway will auto-detect Python
   - Add environment variable: `GEMINI_API_KEY`
   - Railway will auto-deploy

4. **Get URL** and update `frontend/src/config/api.ts` as above

#### Option 3: Heroku

1. **Create a Heroku account** and install Heroku CLI

2. **Create app**:
   ```bash
   heroku create your-app-name
   ```

3. **Set environment variable**:
   ```bash
   heroku config:set GEMINI_API_KEY=your-api-key
   ```

4. **Deploy**:
   ```bash
   git push heroku main
   ```

5. **Get URL** and update `frontend/src/config/api.ts`

### Local Development

To test the web app locally:

1. **Start the backend**:
   ```bash
   python backend/app.py
   ```
   Backend will run on `http://localhost:5001`

2. **Update `frontend/src/config/api.ts`**:
   ```typescript
   export const API_BASE_URL = 'http://localhost:5001';
   ```

3. **Run the frontend development server**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Opens automatically at `http://localhost:8000`

### CI/CD Pipeline

The project includes automated testing and deployment:

- **Tests**: Run automatically on every push/PR
- **Linting**: Code quality checks with pylint
- **Deployment**: Automatic deployment to GitHub Pages after tests pass
- **Coverage**: Test coverage reports generated automatically

See `.github/workflows/ci-cd.yml` for the pipeline configuration.

### Testing

Run tests locally:
```bash
pip install -r requirements-test.txt
pytest tests/ -v
```

See `tests/README.md` for detailed testing documentation.

### Important Notes

- **API Key Security**: The API key is stored server-side in Render environment variables (never exposed to frontend)
- **File Size Limits**: The backend has a 25MB file size limit. Adjust `MAX_FILE_SIZE` in `backend/app.py` if needed
- **CORS**: The backend has CORS enabled for GitHub Pages. If deploying to a custom domain, update CORS settings in `backend/app.py`
- **Python Version**: Use Python 3.12 (3.13 has compatibility issues with pydub)

## License

This script is provided as-is for educational and personal use.

