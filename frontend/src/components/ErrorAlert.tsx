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
    <div className="error-alert" role="alert" aria-live="assertive" aria-atomic="true">
      <span className="error-icon" aria-hidden="true">⚠️</span>
      <span className="error-text">{message}</span>
    </div>
  );
};


