/**
 * API configuration
 * Production URL: set VITE_API_BASE_URL at build time (e.g. in GitHub Actions) to match your Render backend.
 */

function getApiBaseUrl(): string {
  const hostname = window.location.hostname;
  const isLocal = hostname === 'localhost' || hostname === '127.0.0.1';

  if (isLocal) {
    return 'http://localhost:5001';
  }

  // Build-time override for deployed frontend (e.g. GitHub Actions env)
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (envUrl && typeof envUrl === 'string' && envUrl.trim() !== '') {
    return envUrl.replace(/\/$/, ''); // strip trailing slash
  }

  // Fallback: default Render URL (update this or set VITE_API_BASE_URL when you create a new service)
  return 'https://audio-transcription-90eh.onrender.com';
}

export const API_BASE_URL = getApiBaseUrl();

export const API_ENDPOINTS = {
  HEALTH: '/health',
  TRANSCRIBE: '/transcribe',
  TRANSCRIBE_STATUS: (jobId: string) => `/transcribe/status/${jobId}`,
} as const;


