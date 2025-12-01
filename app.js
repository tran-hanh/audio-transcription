// Configuration - API Base URL
// Automatically detects environment and uses appropriate backend URL
function getApiBaseUrl() {
    // Check if we're running on GitHub Pages (production)
    const hostname = window.location.hostname;
    const isProduction = hostname.includes('github.io') || hostname.includes('github.com');
    
    // Check if we're running locally
    const isLocal = hostname === 'localhost' || hostname === '127.0.0.1';
    
    if (isLocal) {
        // Local development - use localhost backend
        return 'http://localhost:5001';
    } else if (isProduction) {
        // Production on GitHub Pages - use your deployed backend URL
        // TODO: Replace this with your actual deployed backend URL
        // Example: 'https://audio-transcription-api.onrender.com'
        return 'https://your-backend-url.onrender.com';
    } else {
        // Fallback for other environments
        return 'https://your-backend-url.onrender.com';
    }
}

const API_BASE_URL = getApiBaseUrl();

// Application States
const STATE = {
    IDLE: 'idle',
    PROCESSING: 'processing',
    RESULTS: 'results',
    ERROR: 'error'
};

// DOM Elements
const dropZoneSection = document.getElementById('dropZoneSection');
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const processingSection = document.getElementById('processingSection');
const fileNameDisplay = document.getElementById('fileNameDisplay');
const progressBar = document.getElementById('progressBar');
const progressFill = document.getElementById('progressFill');
const statusText = document.getElementById('statusText');
const outputSection = document.getElementById('outputSection');
const transcriptTextarea = document.getElementById('transcriptTextarea');
const downloadBtn = document.getElementById('downloadBtn');
const copyBtn = document.getElementById('copyBtn');
const resetBtn = document.getElementById('resetBtn');
const errorAlert = document.getElementById('errorAlert');
const errorText = document.getElementById('errorText');
const apiKeyContainer = document.getElementById('apiKeyContainer');
const apiKeyInput = document.getElementById('apiKeyInput');

// State Management
let currentState = STATE.IDLE;
let selectedFile = null;
let currentTranscript = null;

// Load API key from localStorage
const savedApiKey = localStorage.getItem('gemini_api_key');
if (savedApiKey) {
    apiKeyInput.value = savedApiKey;
} else {
    // Show API key input if not saved
    apiKeyContainer.style.display = 'block';
}

// Save API key to localStorage when changed
apiKeyInput.addEventListener('input', () => {
    localStorage.setItem('gemini_api_key', apiKeyInput.value);
    if (apiKeyInput.value.trim()) {
        apiKeyContainer.style.display = 'none';
    }
});

// File Input Handling
dropZone.addEventListener('click', () => {
    if (currentState === STATE.IDLE) {
        fileInput.click();
    }
});

dropZone.addEventListener('dragover', (e) => {
    if (currentState === STATE.IDLE) {
        e.preventDefault();
        dropZone.classList.add('dragover');
    }
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    if (currentState === STATE.IDLE) {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

function handleFileSelect(file) {
    // Validate file type
    if (!file.type.startsWith('audio/')) {
        setState(STATE.ERROR, 'Please select a valid audio file.');
        return;
    }

    // Validate file size (25MB max)
    const maxSize = 25 * 1024 * 1024; // 25MB
    if (file.size > maxSize) {
        setState(STATE.ERROR, 'File too large. Maximum size is 25MB.');
        return;
    }

    selectedFile = file;
    
    // Check if API key is available
    const apiKey = apiKeyInput.value.trim();
    if (!apiKey) {
        setState(STATE.ERROR, 'Please enter your Google Gemini API key first.');
        apiKeyContainer.style.display = 'block';
        return;
    }

    // Auto-start transcription
    startTranscription();
}

function setState(newState, errorMessage = null) {
    currentState = newState;

    // Hide all sections first
    dropZoneSection.style.display = 'none';
    processingSection.style.display = 'none';
    outputSection.style.display = 'none';
    errorAlert.style.display = 'none';

    switch (newState) {
        case STATE.IDLE:
            dropZoneSection.style.display = 'block';
            selectedFile = null;
            currentTranscript = null;
            fileInput.value = '';
            break;

        case STATE.PROCESSING:
            processingSection.style.display = 'block';
            if (selectedFile) {
                fileNameDisplay.textContent = selectedFile.name;
            }
            // Set indeterminate progress
            progressBar.classList.add('indeterminate');
            progressFill.style.width = '100%';
            break;

        case STATE.RESULTS:
            outputSection.style.display = 'block';
            if (currentTranscript) {
                transcriptTextarea.value = currentTranscript;
            }
            break;

        case STATE.ERROR:
            dropZoneSection.style.display = 'block';
            errorAlert.style.display = 'flex';
            if (errorMessage) {
                errorText.textContent = errorMessage;
            }
            break;
    }
}

async function startTranscription() {
    if (!selectedFile) return;

    const apiKey = apiKeyInput.value.trim();
    if (!apiKey) {
        setState(STATE.ERROR, 'API key is required.');
        return;
    }

    setState(STATE.PROCESSING);
    updateStatus('Uploading...');

    try {
        const formData = new FormData();
        formData.append('audio', selectedFile);
        formData.append('chunk_length', '12'); // Default chunk length
        formData.append('api_key', apiKey);

        const response = await fetch(`${API_BASE_URL}/transcribe`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Unknown error occurred' }));
            throw new Error(errorData.error || `Server error: ${response.status}`);
        }

        // Handle streaming response for progress updates
        updateStatus('Transcribing audio... This may take a moment.');
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep incomplete line in buffer

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        if (data.progress !== undefined) {
                            updateProgress(data.progress, data.message || 'Processing...');
                        }
                        if (data.transcript) {
                            // Transcription complete
                            currentTranscript = data.transcript;
                            setState(STATE.RESULTS);
                            return;
                        }
                        if (data.error) {
                            throw new Error(data.error);
                        }
                    } catch (e) {
                        // Ignore JSON parse errors for incomplete chunks
                    }
                }
            }
        }

        // If we get here, try to parse the final response
        const finalData = await response.json().catch(() => null);
        if (finalData && finalData.transcript) {
            currentTranscript = finalData.transcript;
            setState(STATE.RESULTS);
        } else {
            throw new Error('No transcript received from server');
        }

    } catch (error) {
        console.error('Transcription error:', error);
        setState(STATE.ERROR, error.message || 'An error occurred during transcription. Please try again.');
    }
}

function updateProgress(percentage, message) {
    if (percentage !== undefined) {
        progressBar.classList.remove('indeterminate');
        progressFill.style.width = `${percentage}%`;
    }
    if (message) {
        updateStatus(message);
    }
}

function updateStatus(message) {
    statusText.textContent = message;
}

// Download Button
downloadBtn.addEventListener('click', () => {
    if (!currentTranscript) return;

    const blob = new Blob([currentTranscript], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const fileName = selectedFile ? selectedFile.name.replace(/\.[^/.]+$/, '') + '_transcript.txt' : 'transcript.txt';
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
});

// Copy Button
copyBtn.addEventListener('click', async () => {
    if (!currentTranscript) return;

    try {
        await navigator.clipboard.writeText(currentTranscript);
        // Visual feedback
        const originalText = copyBtn.innerHTML;
        copyBtn.innerHTML = '<svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>Copied!';
        setTimeout(() => {
            copyBtn.innerHTML = originalText;
        }, 2000);
    } catch (err) {
        console.error('Failed to copy:', err);
        setState(STATE.ERROR, 'Failed to copy to clipboard.');
    }
});

// Reset Button
resetBtn.addEventListener('click', () => {
    setState(STATE.IDLE);
});

// Initialize to IDLE state
setState(STATE.IDLE);
