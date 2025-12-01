/**
 * Main application component
 */

import React, { useEffect } from 'react';
import { AppState } from './types';
import { TranscriptionService } from './services/transcriptionService';
import { useTranscription } from './hooks/useTranscription';
import { DropZone } from './components/DropZone';
import { ProcessingSection } from './components/ProcessingSection';
import { OutputSection } from './components/OutputSection';
import { ErrorAlert } from './components/ErrorAlert';
import { API_BASE_URL } from './config/api';
import './App.css';

const transcriptionService = new TranscriptionService(API_BASE_URL);

export const App: React.FC = () => {
  const {
    state,
    selectedFile,
    transcript,
    error,
    progress,
    handleFileSelect,
    startTranscription,
    reset,
  } = useTranscription(transcriptionService);

  // Auto-start transcription when file is selected
  useEffect(() => {
    if (selectedFile && state === AppState.IDLE) {
      startTranscription(12); // Default chunk length
    }
  }, [selectedFile, state, startTranscription]);

  return (
    <div className="main-container">
      <header className="header-section">
        <h1>Audio Scribe</h1>
        <p className="subtitle">
          Upload an MP3 or WAV file to generate a text transcript, then download the result.
        </p>
      </header>

      {error && <ErrorAlert message={error} />}

      {state === AppState.IDLE && (
        <div className="drop-zone-section">
          <DropZone onFileSelect={handleFileSelect} disabled={false} />
        </div>
      )}

      {state === AppState.PROCESSING && selectedFile && (
        <ProcessingSection
          fileName={selectedFile.name}
          progress={progress.progress}
          message={progress.message || 'Processing...'}
        />
      )}

      {state === AppState.RESULTS && (
        <OutputSection
          transcript={transcript}
          originalFileName={selectedFile?.name || 'transcript'}
          onReset={reset}
        />
      )}

      {state === AppState.ERROR && (
        <div className="drop-zone-section">
          <DropZone onFileSelect={handleFileSelect} disabled={false} />
        </div>
      )}
    </div>
  );
};

