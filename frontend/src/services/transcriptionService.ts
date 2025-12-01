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
    let transcript = '';

    // eslint-disable-next-line no-constant-condition
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data: TranscriptionResponse = JSON.parse(line.slice(6));
            
            if (data.progress !== undefined && data.message) {
              onProgress({ progress: data.progress, message: data.message });
            }
            
            if (data.transcript) {
              transcript = data.transcript;
            }
            
            if (data.error) {
              throw new Error(data.error);
            }
          } catch (e) {
            // Ignore JSON parse errors for incomplete chunks
            if (e instanceof Error && !e.message.includes('JSON')) {
              throw e;
            }
          }
        }
      }
    }

    if (!transcript) {
      throw new Error('No transcript received from server');
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


