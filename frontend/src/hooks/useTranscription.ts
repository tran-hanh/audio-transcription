/**
 * Custom hook for transcription state management
 */

import { useState, useCallback } from 'react';
import { AppState } from '../types';
import { TranscriptionService } from '../services/transcriptionService';
import { validateAudioFile } from '../utils/fileUtils';

export function useTranscription(service: TranscriptionService) {
  const [state, setState] = useState<AppState>(AppState.IDLE);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [transcript, setTranscript] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [progress, setProgress] = useState<{ progress: number; message: string }>({
    progress: 0,
    message: '',
  });

  const handleFileSelect = useCallback((file: File) => {
    const validation = validateAudioFile(file);
    if (!validation.valid) {
      setError(validation.error || 'Invalid file');
      setState(AppState.ERROR);
      return;
    }

    setSelectedFile(file);
    setError('');
    setState(AppState.IDLE);
  }, []);

  const startTranscription = useCallback(
    async (chunkLength: number = 12) => {
      if (!selectedFile) return;

      setState(AppState.PROCESSING);
      setError('');
      setProgress({ progress: 0, message: 'Uploading...' });

      try {
        const result = await service.transcribe(
          selectedFile,
          chunkLength,
          (progressUpdate) => {
            setProgress(progressUpdate);
          }
        );

        setTranscript(result);
        setState(AppState.RESULTS);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'An error occurred';
        setError(errorMessage);
        setState(AppState.ERROR);
      }
    },
    [selectedFile, service]
  );

  const reset = useCallback(() => {
    setState(AppState.IDLE);
    setSelectedFile(null);
    setTranscript('');
    setError('');
    setProgress({ progress: 0, message: '' });
  }, []);

  return {
    state,
    selectedFile,
    transcript,
    error,
    progress,
    handleFileSelect,
    startTranscription,
    reset,
  };
}


