/**
 * Processing/status display component
 */

import React from 'react';

interface ProcessingSectionProps {
  fileName: string;
  progress: number;
  message: string;
}

export const ProcessingSection: React.FC<ProcessingSectionProps> = ({
  fileName,
  progress,
  message,
}) => {
  return (
    <div className="processing-section" role="status" aria-live="polite" aria-atomic="true">
      <div className="file-display">
        <svg
          className="audio-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          aria-hidden="true"
        >
          <path d="M9 18V5l12-2v13"></path>
          <circle cx="6" cy="18" r="3"></circle>
          <circle cx="18" cy="16" r="3"></circle>
        </svg>
        <span className="file-name-display" aria-label={`Processing file: ${fileName}`}>
          {fileName}
        </span>
      </div>
      <div className="progress-container">
        <div
          className={`progress-bar ${progress === 0 ? 'indeterminate' : ''}`}
          role="progressbar"
          aria-valuenow={progress}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`Transcription progress: ${progress}%`}
        >
          <div
            className="progress-fill"
            style={{ width: progress > 0 ? `${progress}%` : '100%' }}
          />
        </div>
        {progress > 0 && (
          <div className="progress-percentage" aria-hidden="true">
            {progress}%
          </div>
        )}
      </div>
      <p className="status-text" aria-label={`Status: ${message}`}>
        {message}
      </p>
    </div>
  );
};


