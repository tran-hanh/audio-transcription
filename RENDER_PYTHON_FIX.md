# How to Set Python Version in Render (Step-by-Step)

## Method 1: In Service Settings (Most Common)

1. **Go to Render Dashboard**
   - Visit: https://dashboard.render.com
   - Log in to your account

2. **Select Your Service**
   - Click on `audio-transcription-api` service

3. **Go to Settings Tab**
   - Look at the left sidebar
   - Click on **"Settings"** (it's usually the 3rd or 4th option)

4. **Find Environment Section**
   - Scroll down in the Settings page
   - Look for a section called:
     - **"Environment"** OR
     - **"Build & Deploy"** OR
     - **"Build Settings"**

5. **Look for Python Version**
   - In the Environment/Build section, you should see:
     - A dropdown labeled **"Python Version"** OR
     - A field labeled **"Python"** OR
     - **"Runtime"** dropdown
   - It might show "3.13" or "Latest" currently

6. **Change to Python 3.12**
   - Click the dropdown
   - Select **"3.12.7"** or **"Python 3.12"**
   - If you see options like "3.12", "3.12.7", "python-3.12", choose any 3.12 version

7. **Save**
   - Click **"Save Changes"** button (usually at the bottom)
   - Render will automatically trigger a new deployment

## Method 2: If You Can't Find It - Recreate Service

If you cannot find the Python version setting, recreate the service:

### Step 1: Note Your Current Settings
- Write down your service URL
- Note your environment variables (especially GEMINI_API_KEY)

### Step 2: Delete Current Service
1. Go to your service
2. Click **"Settings"**
3. Scroll to the bottom
4. Click **"Delete Service"**
5. Confirm deletion

### Step 3: Create New Service
1. Click **"New +"** button (top right)
2. Select **"Web Service"**
3. Connect your GitHub repository
4. Select the `audio_transcription` repository
5. **Configure the service:**
   - **Name**: `audio-transcription-api`
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Root Directory**: (leave empty, or `./` if needed)
   - **Environment**: Select **"Python 3"**
   - **Python Version**: **IMPORTANT!** Look for this dropdown and select **"3.12.7"** or **"Python 3.12"**
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`

6. **Add Environment Variable**
   - Click **"Add Environment Variable"**
   - Key: `GEMINI_API_KEY`
   - Value: (paste your API key)

7. **Create Service**
   - Click **"Create Web Service"**
   - Wait for deployment

## Method 3: Using render.yaml (If Supported)

If your Render account supports `render.yaml`:

1. The `render.yaml` file already has `pythonVersion: 3.12.0`
2. When creating a new service, Render should detect `render.yaml`
3. Select **"Apply render.yaml"** option
4. It should use Python 3.12 automatically

## Method 4: Contact Render Support

If none of the above work:

1. Go to: https://render.com/docs/support
2. Contact support and ask: "How do I change Python version from 3.13 to 3.12 for my web service?"
3. They can help you find the setting or change it manually

## Verification

After setting Python 3.12, check the build logs:

1. Go to your service
2. Click **"Events"** or **"Logs"** tab
3. Look at the latest build log
4. You should see: `Python 3.12.x` somewhere in the output
5. Should NOT see: `Python 3.13`

## Quick Screenshot Guide

The Python version setting is usually located in one of these places:

```
Render Dashboard
└── Your Service (audio-transcription-api)
    └── Settings Tab
        ├── Environment Section
        │   └── Python Version: [Dropdown] ← HERE
        └── Build & Deploy Section
            └── Python Version: [Dropdown] ← OR HERE
```

## Alternative: Use audioop-lts (Temporary Fix)

If you absolutely cannot change Python version, the `requirements.txt` already includes `audioop-lts` which should work with Python 3.13. However, Python 3.12 is still recommended for better compatibility.

