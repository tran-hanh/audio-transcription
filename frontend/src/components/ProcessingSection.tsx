/**
 * Processing/status display component
 */

import React from 'react';

interface ProcessingSectionProps {
  fileName: string;
  progress: number;
  message: string;
  estimatedTimeRemaining?: string | null;
  onCancel?: () => void;
}

export const ProcessingSection: React.FC<ProcessingSectionProps> = ({
  fileName,
  progress,
  message,
  estimatedTimeRemaining,
  onCancel,
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
        <div className="progress-header">
          <span className="progress-label">Progress</span>
          <div className="progress-stats">
            {estimatedTimeRemaining && (
              <span className="estimated-time" aria-label={`Estimated time remaining: ${estimatedTimeRemaining}`}>
                ~{estimatedTimeRemaining}
              </span>
            )}
            <span className="progress-percentage" aria-hidden="true">
              {progress > 0 ? `${progress}%` : progress === 0 ? '0%' : '—'}
            </span>
          </div>
        </div>
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
      </div>
      <div className="status-footer">
        <p className="status-text" aria-label={`Status: ${message}`}>
          {message}
        </p>
        {onCancel && (
          <button
            className="btn-cancel"
            onClick={onCancel}
            aria-label="Cancel transcription"
          >
            <svg className="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
            Cancel
          </button>
        )}
      </div>
    </div>
  );
};


