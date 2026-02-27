/**
 * Transcription results display component
 */

import React, { useCallback, useState } from 'react';
import { downloadTextFile } from '../utils/fileUtils';
import { Toast } from './Toast';

interface OutputSectionProps {
  transcript: string;
  originalFileName: string;
  onReset: () => void;
}

export const OutputSection: React.FC<OutputSectionProps> = ({
  transcript,
  originalFileName,
  onReset,
}) => {
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  const handleDownload = useCallback(() => {
    const fileName = originalFileName.replace(/\.[^/.]+$/, '') + '_transcript.txt';
    downloadTextFile(transcript, fileName);
  }, [transcript, originalFileName]);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(transcript);
      setToastMessage('Copied to clipboard!');
      setShowToast(true);
    } catch (err) {
      console.error('Failed to copy:', err);
      setToastMessage('Failed to copy. Please try again.');
      setShowToast(true);
    }
  }, [transcript]);

  return (
    <div className="output-section">
      <h2 className="output-header">Transcription Result:</h2>
      <div className="text-area-container">
        <label htmlFor="transcript-textarea" className="sr-only">
          Transcription text
        </label>
        <textarea
          id="transcript-textarea"
          className="transcript-textarea"
          value={transcript}
          readOnly
          rows={15}
          aria-label="Transcription result"
          aria-readonly="true"
        />
      </div>
      <div className="action-buttons" role="group" aria-label="Transcription actions">
        <button
          className="btn-primary"
          onClick={handleDownload}
          aria-label="Download transcript as text file"
        >
          <svg className="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          Download Script (.txt)
        </button>
        <button
          className="btn-secondary"
          onClick={handleCopy}
          aria-label="Copy transcript to clipboard"
        >
          <svg className="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
          </svg>
          Copy to Clipboard
        </button>
        <button
          className="btn-tertiary"
          onClick={onReset}
          aria-label="Convert another audio file"
        >
          Convert Another File
        </button>
      </div>
      {showToast && (
        <Toast
          message={toastMessage}
          type={toastMessage.includes('Failed') ? 'error' : 'success'}
          onClose={() => setShowToast(false)}
        />
      )}
    </div>
  );
};


