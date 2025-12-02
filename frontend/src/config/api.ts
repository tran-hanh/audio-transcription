/**
 * API configuration
 */

function getApiBaseUrl(): string {
  const hostname = window.location.hostname;
  const isLocal = hostname === 'localhost' || hostname === '127.0.0.1';
  
  if (isLocal) {
    return 'http://localhost:5001';
  }
  
  // Production - update with your backend URL
  return 'https://audio-transcription-90eh.onrender.com';
}

export const API_BASE_URL = getApiBaseUrl();

export const API_ENDPOINTS = {
  HEALTH: '/health',
  TRANSCRIBE: '/transcribe',
} as const;


