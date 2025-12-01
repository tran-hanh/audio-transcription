/**
 * Transcription results display component
 */

import React, { useCallback } from 'react';
import { downloadTextFile } from '../utils/fileUtils';

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
  const handleDownload = useCallback(() => {
    const fileName = originalFileName.replace(/\.[^/.]+$/, '') + '_transcript.txt';
    downloadTextFile(transcript, fileName);
  }, [transcript, originalFileName]);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(transcript);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  }, [transcript]);

  return (
    <div className="output-section">
      <h2 className="output-header">Transcription Result:</h2>
      <div className="text-area-container">
        <textarea
          className="transcript-textarea"
          value={transcript}
          readOnly
          rows={15}
        />
      </div>
      <div className="action-buttons">
        <button className="btn-primary" onClick={handleDownload}>
          <svg className="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          Download Script (.txt)
        </button>
        <button className="btn-secondary" onClick={handleCopy}>
          <svg className="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
          </svg>
          Copy to Clipboard
        </button>
        <button className="btn-tertiary" onClick={onReset}>
          Convert Another File
        </button>
      </div>
    </div>
  );
};


