/**
 * File drop zone component
 */

import React, { useCallback, useRef } from 'react';
import { formatFileSize } from '../utils/fileUtils';

interface DropZoneProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
  selectedFile?: File | null;
}

export const DropZone: React.FC<DropZoneProps> = ({ onFileSelect, disabled = false, selectedFile }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = React.useState(false);

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        onFileSelect(file);
        // Reset the input value so the same file can be selected again
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      }
    },
    [onFileSelect]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    if (disabled) return;
    e.preventDefault();
    setIsDragging(true);
  }, [disabled]);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      if (disabled) return;
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) {
        onFileSelect(file);
      }
    },
    [disabled, onFileSelect]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (disabled) return;
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        fileInputRef.current?.click();
      }
    },
    [disabled]
  );

  return (
    <div className="drop-zone-wrapper">
      <label
        className={`drop-zone ${isDragging ? 'dragover' : ''} ${disabled ? 'disabled' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onKeyDown={handleKeyDown}
        tabIndex={disabled ? -1 : 0}
        aria-label="Upload audio file"
        aria-disabled={disabled}
      >
        <input
          ref={fileInputRef}
          type="file"
          id="fileInput"
          accept="audio/*"
          onChange={handleFileChange}
          style={{ display: 'none' }}
          disabled={disabled}
          aria-label="Select audio file"
        />
        <svg
          className="upload-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          aria-hidden="true"
        >
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="17 8 12 3 7 8"></polyline>
          <line x1="12" y1="3" x2="12" y2="15"></line>
        </svg>
        <p className="drop-zone-primary">Drag & Drop your audio file here</p>
        <p className="drop-zone-secondary">or click to browse files</p>
        <p className="drop-zone-formats">Supports MP3, WAV, M4A (Max 1GB)</p>
      </label>
      {selectedFile && (
        <div className="file-info" role="status" aria-live="polite">
          <div className="file-info-row">
            <span className="file-info-label">Selected file:</span>
            <span className="file-info-value" aria-label={`File name: ${selectedFile.name}`}>
              {selectedFile.name}
            </span>
          </div>
          <div className="file-info-row">
            <span className="file-info-label">File size:</span>
            <span className="file-info-value" aria-label={`File size: ${formatFileSize(selectedFile.size)}`}>
              {formatFileSize(selectedFile.size)}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

