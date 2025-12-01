# Render Deployment Setup Guide

## Critical: Set Python Version to 3.12

Render is currently using Python 3.13, which causes issues with `pydub`. You **must** set Python 3.12 in the Render dashboard.

## Steps to Fix Python Version in Render

1. **Go to Render Dashboard**
   - Navigate to https://dashboard.render.com
   - Click on your service: `audio-transcription-api`

2. **Open Settings**
   - Click on "Settings" tab in the left sidebar

3. **Find Python Version Setting**
   - Scroll down to "Environment" section
   - Look for "Python Version" or "Python" dropdown
   - If you don't see it, look for "Build & Deploy" section

4. **Set Python Version**
   - Select **Python 3.12.7** (or any 3.12.x version)
   - **DO NOT** use Python 3.13

5. **Save and Redeploy**
   - Click "Save Changes"
   - Go to "Manual Deploy" tab
   - Click "Deploy latest commit"

## Alternative: If Python Version Setting is Not Visible

If you can't find the Python version setting:

1. **Delete and Recreate Service**
   - Delete the current service
   - Create a new Web Service
   - Connect your GitHub repository
   - In the creation form, look for "Python Version" and select 3.12.7
   - Use these settings:
     - **Name**: `audio-transcription-api`
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
     - **Python Version**: `3.12.7` (IMPORTANT!)

2. **Set Environment Variable**
   - Go to "Environment" tab
   - Add: `GEMINI_API_KEY` = `your-api-key-here`

## Verification

After setting Python 3.12, check the build logs:
- Look for: `Python 3.12.x` in the build output
- Should NOT see: `Python 3.13`

## Why This Matters

- Python 3.13 removed the `audioop` module
- `pydub` requires `audioop` (or `audioop-lts` for 3.13)
- Python 3.12 includes `audioop` natively
- Using Python 3.12 is the most reliable solution

## Fallback Solution

If you must use Python 3.13, the `requirements.txt` includes `audioop-lts` as a conditional dependency, but Python 3.12 is strongly recommended.


