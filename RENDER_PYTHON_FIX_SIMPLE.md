# Simple Fix: Set Python 3.12 in Render

## Method 1: Add Environment Variable (Easiest)

1. **Go to Render Dashboard**
   - Visit: https://dashboard.render.com
   - Click on your service: `audio-transcription-api`

2. **Go to Environment Tab**
   - Click **"Environment"** in the left sidebar

3. **Add Environment Variable**
   - Click **"Add Environment Variable"** button
   - **Key**: `PYTHON_VERSION`
   - **Value**: `3.12.7`
   - Click **"Save Changes"**

4. **Redeploy**
   - Go to **"Manual Deploy"** tab
   - Click **"Deploy latest commit"**

That's it! Render will use Python 3.12.7 on the next deployment.

## Method 2: Using .python-version File (Already Done)

I've already created a `.python-version` file in your repository with `3.12.7`.

Just commit and push:
```bash
git add .python-version
git commit -m "Set Python version to 3.12.7"
git push origin main
```

Render will automatically detect this file and use Python 3.12.7.

## Verification

After deploying, check the build logs:
- Look for: `Python 3.12.7` in the build output
- Should NOT see: `Python 3.13`

## If Still Using Python 3.13

If Render still uses Python 3.13 after these steps, the `audioop-lts` package in `requirements.txt` will handle it automatically. But Python 3.12 is preferred.

