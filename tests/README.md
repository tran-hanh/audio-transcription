# Testing Guide

This document describes how to run tests for the Audio Transcription application.

## Backend Tests

### Setup

1. Install test dependencies:
```bash
pip install -r requirements-test.txt
```

2. Set up test environment:
```bash
export GEMINI_API_KEY=test-key-for-testing
```

### Running Tests

Run all tests:
```bash
pytest tests/ -v
```

Run specific test file:
```bash
pytest tests/test_app.py -v
pytest tests/test_transcribe.py -v
```

Run with coverage:
```bash
pytest tests/ --cov=app --cov=transcribe --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

### Test Structure

- `tests/test_app.py` - Tests for Flask API endpoints
  - Health check endpoint
  - File upload validation
  - Transcription endpoint
  - Error handling
  - CORS headers

- `tests/test_transcribe.py` - Tests for transcription functions
  - Audio chunking
  - File validation
  - API key handling
  - Configuration constants

## Frontend Tests

Frontend tests are currently manual. See `tests/test_frontend.js` for test cases and checklist.

### Manual Testing Checklist

1. **File Upload**
   - [ ] Click on drop zone opens file picker
   - [ ] Drag and drop audio file works
   - [ ] File picker only shows audio files
   - [ ] Invalid file type shows error
   - [ ] File too large (250MB+) shows error
   - [ ] Valid file starts transcription automatically

2. **Transcription Process**
   - [ ] Progress bar shows during transcription
   - [ ] Status text updates correctly
   - [ ] File name displays during processing
   - [ ] Error message shows on failure
   - [ ] Success shows transcript in textarea

3. **Download & Copy**
   - [ ] Download button downloads transcript as .txt
   - [ ] Downloaded file has correct name
   - [ ] Copy button copies transcript to clipboard
   - [ ] Copy button shows feedback when clicked

4. **Reset**
   - [ ] Reset button returns to initial state
   - [ ] Can upload new file after reset

5. **API URL Detection**
   - [ ] Local development uses localhost:5001
   - [ ] GitHub Pages uses production backend URL

## Integration Tests

To test the full flow:

1. Start the backend server:
```bash
export GEMINI_API_KEY=your-real-api-key
python app.py
```

2. Open the frontend in a browser:
```bash
# Serve the frontend
python -m http.server 8000
# Open http://localhost:8000
```

3. Test the full workflow:
   - Upload an audio file
   - Wait for transcription
   - Download the transcript
   - Verify the content

## Continuous Integration

Tests run automatically on:
- Push to main branch
- Pull requests

See `.github/workflows/test.yml` for CI configuration.

## Test Coverage Goals

- Backend API: >80% coverage
- Core functions: >90% coverage
- Error handling: All error paths tested

## Running Tests in CI

Tests are automatically run in GitHub Actions on:
- Python 3.12
- Python 3.13

Coverage reports are generated and can be viewed in the Actions tab.

