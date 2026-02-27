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

### 1. Virtual environment (recommended on macOS/Homebrew)

If you see **"externally-managed-environment"** when running pip, use a venv:

```bash
cd /path/to/audio_transcription
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Then run the app or CLI from the same terminal (with the venv activated), or activate the venv in each new terminal.

### 2. Install Dependencies (without venv)

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

### 3. Set Google Gemini API Key

You have two options:

**Option A: Environment Variable (Recommended)**
```bash
export GEMINI_API_KEY="your-api-key-here"
```

**Option B: Pass as Command-Line Argument**
```bash
python3 src/transcribe.py input.mp3 --api-key "your-api-key-here"
```

### 4. Get Your Google Gemini API Key

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

**CLI:** Same as below (load → chunk → transcribe → combine → save).

**Web app (async):** Upload triggers a background job so the request returns quickly (avoids timeouts on Render).

1. **Upload**: You send the file to `POST /transcribe`; the server saves it and returns **202** with a `job_id`.
2. **Poll**: The frontend polls `GET /transcribe/status/<job_id>` until the job is `completed` or `failed`.
3. **Backend**: The server chunks the audio, sends each chunk to Gemini, combines the text, and updates the job (progress then transcript or error).
4. **Result**: When the job is completed, the frontend shows the transcript and download; no coding or manual GET needed.

**Where you see progress:** If you use the **browser UI** (frontend), it polls the status URL automatically and shows a progress bar and message. In the **backend terminal** you’ll see a line like `Accepted job xxxxxxxx; poll GET /transcribe/status/...` when a file is submitted, then repeated `GET /transcribe/status/<job_id>` requests and progress lines (e.g. `Job xxxxxxxx: 25% - Transcribing chunk 2/5`) as the UI polls. If you only call `POST /transcribe` with curl or Postman, nothing will poll for you—use `GET /transcribe/status/<job_id>` (from the 202 response’s `job_id`) to check progress.

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

### E2E (deployed on Render + GitHub Pages) not working

- **CORS / "blocked by CORS"**: The backend allows all origins (`*`). If you still see CORS errors, ensure the backend is using the latest code (root `/` and `/health` routes, CORS headers).
- **Wrong backend URL**: The frontend uses `VITE_API_BASE_URL` at build time if set; otherwise it uses the fallback in `frontend/src/config/api.ts`. If your Render service has a different URL, set `VITE_API_BASE_URL` in your frontend build (e.g. in GitHub Actions) or change the fallback.
- **"Server is starting" / 502 or 503**: On Render free tier the service spins down after inactivity. The frontend will retry a few times and show "Server waking up...". Wait for the first request to finish (can take 30–60 seconds), then try again.
- **Health check failing on Render**: In Render dashboard set **Health Check Path** to `/health`. The app also responds with `200` at `/` for platforms that ping the root.
- **GEMINI_API_KEY**: Must be set in Render → Environment. If missing, the service may fail to start or return 500 on `/transcribe`.
- **Long uploads / first-byte timeout**: Render may impose a request timeout (e.g. ~30s). Very large file uploads can exceed it; try a smaller file or consider a paid plan with longer limits.

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

2. **Set backend API URL** (if your Render URL is not the default):
   - Set `VITE_API_BASE_URL` when building the frontend (e.g. in GitHub Actions env) to your Render backend URL, **or**
   - Edit the fallback in `frontend/src/config/api.ts` to your backend URL

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

2. **Create a new Web Service** (or use the repo's `render.yaml`):
   - Connect your GitHub repository and use **Blueprint** if you have `render.yaml`
   - Or configure manually:
     - **Name**: `audio-transcription-api`
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn -c gunicorn_config.py backend.app:app`
     - **Health Check Path**: `/health` (so Render pings the API correctly)
     - **Plan**: Free (or paid for better performance)

3. **Set Environment Variables**:
   - Go to Environment tab
   - Add `GEMINI_API_KEY` with your API key

4. **Deploy**:
   - Render will automatically deploy
   - Copy the service URL (e.g., `https://audio-transcription-api.onrender.com`)

5. **Point frontend to your backend**:
   - If your Render URL differs from the default in code, set `VITE_API_BASE_URL` to your backend URL when building the frontend (e.g. in GitHub Actions), or edit the fallback in `frontend/src/config/api.ts`
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

1. **Create and activate a virtual environment** (avoids "externally-managed-environment" on Homebrew Python):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Start the backend** (from the project root, with venv activated):
   ```bash
   python3 -m backend.app
   ```
   Backend will run on `http://localhost:5001`.  
   If you see `ModuleNotFoundError: No module named 'backend'`, you must run from the project root and use `python3 -m backend.app` (not `python3 backend/app.py`).

3. **Update `frontend/src/config/api.ts`** (if needed):
   ```typescript
   export const API_BASE_URL = 'http://localhost:5001';
   ```

4. **Run the frontend development server**:
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

### Development standards

All code changes and new features must follow **clean code** principles and **TDD**: add or update **unit**, **integration**, and **e2e** tests as relevant, and update **all relevant documentation** (e.g. README, `tests/README.md`, docstrings). See **[CONTRIBUTING.md](CONTRIBUTING.md)** for the full checklist. For how BMAD agents work together (sequential workflows and Party Mode), see **[docs/AGENTS-AND-WORKFLOWS.md](docs/AGENTS-AND-WORKFLOWS.md)**.

### Testing

**Backend tests and coverage (recommended before pushing):**
```bash
pip install -r requirements-test.txt
pytest tests/ -v
```

**Frontend type-check and tests (from `frontend/`):**
```bash
cd frontend
npm install
npm run type-check
npm test
```

See `tests/README.md` for detailed testing documentation.

### Important Notes

- **API Key Security**: The API key is stored server-side in Render environment variables (never exposed to frontend)
- **File Size Limits**: The backend has a 1GB file size limit. Adjust `MAX_FILE_SIZE` environment variable if needed
- **CORS**: The backend has CORS enabled for GitHub Pages. If deploying to a custom domain, update CORS settings in `backend/app.py`
- **Python Version**: Use Python 3.12 (3.13 has compatibility issues with pydub)

## License

This script is provided as-is for educational and personal use.

