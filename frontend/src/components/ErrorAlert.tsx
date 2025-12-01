/**
 * Error alert component
 */

import React from 'react';

interface ErrorAlertProps {
  message: string;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({ message }) => {
  if (!message) return null;

  return (
    <div className="error-alert">
      <span className="error-icon">⚠️</span>
      <span className="error-text">{message}</span>
    </div>
  );
};


