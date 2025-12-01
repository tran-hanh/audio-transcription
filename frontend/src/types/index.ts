/**
 * Type definitions for the application
 */

export enum AppState {
  IDLE = 'idle',
  PROCESSING = 'processing',
  RESULTS = 'results',
  ERROR = 'error',
}

export interface TranscriptionProgress {
  progress: number;
  message: string;
}

export interface TranscriptionResponse {
  transcript?: string;
  error?: string;
  progress?: number;
  message?: string;
}

export interface FileInfo {
  name: string;
  size: number;
  type: string;
}

