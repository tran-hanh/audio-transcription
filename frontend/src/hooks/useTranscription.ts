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
  const [startTime, setStartTime] = useState<number | null>(null);

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
      setStartTime(Date.now());

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
        setStartTime(null);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'An error occurred';
        if (errorMessage === 'Transcription cancelled') {
          setState(AppState.IDLE);
          setError('');
          setProgress({ progress: 0, message: '' });
        } else {
          setError(errorMessage);
          setState(AppState.ERROR);
        }
        setStartTime(null);
      }
    },
    [selectedFile, service]
  );

  const cancelTranscription = useCallback(() => {
    service.cancel();
    setState(AppState.IDLE);
    setError('');
    setProgress({ progress: 0, message: '' });
    setStartTime(null);
  }, [service]);

  const reset = useCallback(() => {
    service.cancel();
    setState(AppState.IDLE);
    setSelectedFile(null);
    setTranscript('');
    setError('');
    setProgress({ progress: 0, message: '' });
    setStartTime(null);
  }, [service]);

  // Calculate estimated time remaining
  const getEstimatedTimeRemaining = useCallback((): string | null => {
    if (!startTime || progress.progress <= 0 || progress.progress >= 100) {
      return null;
    }

    const elapsed = Date.now() - startTime;
    const progressDecimal = progress.progress / 100;
    
    if (progressDecimal === 0) {
      return null;
    }

    const estimatedTotal = elapsed / progressDecimal;
    const remaining = estimatedTotal - elapsed;

    if (remaining < 0 || !isFinite(remaining)) {
      return null;
    }

    const minutes = Math.floor(remaining / 60000);
    const seconds = Math.floor((remaining % 60000) / 1000);

    if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    }
    return `${seconds}s`;
  }, [startTime, progress.progress]);

  return {
    state,
    selectedFile,
    transcript,
    error,
    progress,
    startTime,
    estimatedTimeRemaining: getEstimatedTimeRemaining(),
    handleFileSelect,
    startTranscription,
    cancelTranscription,
    reset,
  };
}


