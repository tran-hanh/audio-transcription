/**
 * Transcription API service
 */

import { API_BASE_URL, API_ENDPOINTS } from '../config/api';
import { TranscriptionProgress, TranscriptionResponse } from '../types';

export class TranscriptionService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async transcribe(
    file: File,
    chunkLength: number,
    onProgress: (progress: TranscriptionProgress) => void
  ): Promise<string> {
    const formData = new FormData();
    formData.append('audio', file);
    formData.append('chunk_length', chunkLength.toString());

    const response = await fetch(`${this.baseUrl}${API_ENDPOINTS.TRANSCRIBE}`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Unknown error occurred' }));
      throw new Error(errorData.error || `Server error: ${response.status}`);
    }

    // Handle streaming response
    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

    const decoder = new TextDecoder();
    let buffer = '';
    let transcript: string | undefined = undefined;
    let hasError = false;
    let lastDataTime = Date.now();
    const HEARTBEAT_TIMEOUT_MS = 2 * 60 * 1000; // 2 minutes without data = timeout

    // eslint-disable-next-line no-constant-condition
    while (true) {
      // Check for timeout
      const now = Date.now();
      if (now - lastDataTime > HEARTBEAT_TIMEOUT_MS) {
        throw new Error('Connection timeout. The transcription is taking longer than expected. Please try again.');
      }

      const { done, value } = await reader.read();
      if (done) break;

      // Update last data time
      lastDataTime = Date.now();

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data: TranscriptionResponse = JSON.parse(line.slice(6));
            
            // Update last data time when we receive any data
            lastDataTime = Date.now();
            
            if (data.progress !== undefined && data.message) {
              onProgress({ progress: data.progress, message: data.message });
            }
            
            if (data.transcript !== undefined) {
              transcript = data.transcript;
            }
            
            if (data.error) {
              hasError = true;
              throw new Error(data.error);
            }
          } catch (e) {
            // Ignore JSON parse errors for incomplete chunks
            if (e instanceof Error) {
              if (e.message.includes('JSON')) {
                // Continue parsing other lines
                continue;
              }
              // Re-throw actual errors
              throw e;
            }
          }
        }
      }
    }

    // If we got an error, it should have been thrown above
    if (hasError) {
      throw new Error('Transcription failed');
    }

    // Check if we received a transcript (even if empty, we should have received something)
    // The transcript might be empty if the audio had no speech
    if (transcript === undefined || transcript === null) {
      throw new Error('No transcript received from server. The transcription may have failed.');
    }

    return transcript;
  }

  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}${API_ENDPOINTS.HEALTH}`);
      return response.ok;
    } catch {
      return false;
    }
  }
}


