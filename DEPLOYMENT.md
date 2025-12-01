# Quick Deployment Guide

## Step 1: Deploy Backend API

Choose one of these platforms:

### Render (Easiest - Free tier)

1. Sign up at [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `audio-transcription-api`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
5. Add environment variable: `GEMINI_API_KEY` = `your-api-key`
6. Click "Create Web Service"
7. Wait for deployment and copy the URL (e.g., `https://audio-transcription-api.onrender.com`)

### Railway

1. Sign up at [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Add environment variable: `GEMINI_API_KEY`
5. Railway auto-detects and deploys
6. Copy the generated URL

## Step 2: Update Frontend API URL

1. Open `app.js`
2. Find this line:
   ```javascript
   const API_BASE_URL = 'https://your-backend-url.onrender.com';
   ```
3. Replace with your actual backend URL from Step 1
4. Save the file

## Step 3: Deploy Frontend to GitHub Pages

1. **Enable GitHub Pages**:
   - Go to repository → Settings → Pages
   - Under "Source", select "GitHub Actions"
   - Save

2. **Push your changes**:
   ```bash
   git add .
   git commit -m "Deploy web app"
   git push origin main
   ```

3. **Wait for deployment**:
   - Go to Actions tab to see deployment progress
   - Your site will be at: `https://yourusername.github.io/audio_transcription/`

## Step 4: Test

1. Open your GitHub Pages URL
2. Enter your Gemini API key (or it will be saved from localStorage)
3. Upload an audio file
4. Click "Start Transcription"
5. Wait for completion and download the transcript

## Troubleshooting

### Backend not responding
- Check that `GEMINI_API_KEY` is set correctly
- Check backend logs for errors
- Verify the backend URL is correct in `app.js`

### CORS errors
- Make sure CORS is enabled in `app.py` (it should be by default)
- Verify the frontend URL matches what's allowed

### File upload fails
- Check file size (max 500MB by default)
- Verify file format is supported
- Check backend logs

### Transcription fails
- Verify API key is valid
- Check API quota/limits
- Review backend error logs

