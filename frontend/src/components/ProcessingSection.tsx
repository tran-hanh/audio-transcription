/**
 * Processing/status display component
 */

import React from 'react';
import { FileInfo } from '../types';
import { formatFileSize } from '../utils/fileUtils';

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
    <div className="processing-section">
      <div className="file-display">
        <svg className="audio-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M9 18V5l12-2v13"></path>
          <circle cx="6" cy="18" r="3"></circle>
          <circle cx="18" cy="16" r="3"></circle>
        </svg>
        <span className="file-name-display">{fileName}</span>
      </div>
      <div className="progress-container">
        <div className={`progress-bar ${progress === 0 ? 'indeterminate' : ''}`}>
          <div
            className="progress-fill"
            style={{ width: progress > 0 ? `${progress}%` : '100%' }}
          />
        </div>
      </div>
      <p className="status-text">{message}</p>
    </div>
  );
};

