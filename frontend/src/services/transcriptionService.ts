/**
 * Transcription API service
 */

import { API_BASE_URL, API_ENDPOINTS } from '../config/api';
import { TranscriptionProgress, TranscriptionResponse } from '../types';

const COLD_START_RETRIES = 3;
const COLD_START_DELAYS_MS = [3000, 6000, 10000];

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

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

    const url = `${this.baseUrl}${API_ENDPOINTS.TRANSCRIBE}`;
    let lastError: Error | null = null;
    let response: Response | null = null;

    for (let attempt = 0; attempt <= COLD_START_RETRIES; attempt++) {
      try {
        response = await fetch(url, { method: 'POST', body: formData });
        if (response.ok) break;
        if (response.status === 502 || response.status === 503) {
          lastError = new Error('Server is starting or temporarily unavailable. Please wait.');
          if (attempt < COLD_START_RETRIES) {
            onProgress({
              progress: 0,
              message: `Server waking up... (retry ${attempt + 1}/${COLD_START_RETRIES + 1})`,
            });
            await delay(COLD_START_DELAYS_MS[attempt]);
            continue;
          }
        }
        const errorData = await response.json().catch(() => ({ error: 'Unknown error occurred' }));
        throw new Error(errorData.error || `Server error: ${response.status}`);
      } catch (e) {
        const isNetworkError =
          e instanceof TypeError && (e.message === 'Failed to fetch' || e.message.includes('NetworkError'));
        if (isNetworkError && attempt < COLD_START_RETRIES) {
          lastError = e as Error;
          onProgress({
            progress: 0,
            message: `Connecting to server... (retry ${attempt + 1}/${COLD_START_RETRIES + 1})`,
          });
          await delay(COLD_START_DELAYS_MS[attempt]);
          continue;
        }
        throw e;
      }
    }

    if (!response || !response.ok) {
      throw lastError || new Error('Server error');
    }

    // Async flow: 202 + job_id -> poll status until completed/failed
    if (response.status === 202) {
      const body = await response.json();
      const jobId = body.job_id as string;
      if (!jobId) {
        throw new Error('Server did not return a job id.');
      }
      const statusUrl = `${this.baseUrl}${API_ENDPOINTS.TRANSCRIBE_STATUS(jobId)}`;
      const pollIntervalMs = 1500;
      const maxWaitMs = 30 * 60 * 1000; // 30 minutes
      const startedAt = Date.now();

      // eslint-disable-next-line no-constant-condition
      while (true) {
        if (Date.now() - startedAt > maxWaitMs) {
          throw new Error('Transcription is taking longer than expected. Please try again with a shorter file.');
        }
        const statusResponse = await fetch(statusUrl);
        if (!statusResponse.ok) {
          throw new Error(`Status check failed: ${statusResponse.status}`);
        }
        const job = (await statusResponse.json()) as {
          status: string;
          progress: number;
          message: string;
          transcript?: string;
          error?: string;
        };
        onProgress({ progress: job.progress, message: job.message || 'Processing...' });
        if (job.status === 'completed') {
          if (job.transcript === undefined || job.transcript === null) {
            throw new Error('No transcript received from server.');
          }
          return job.transcript;
        }
        if (job.status === 'failed') {
          throw new Error(job.error || 'Transcription failed.');
        }
        await delay(pollIntervalMs);
      }
    }

    throw new Error('Unexpected response from server.');
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


