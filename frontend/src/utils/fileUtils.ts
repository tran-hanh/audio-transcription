/**
 * File utility functions
 */

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

export function validateAudioFile(file: File): { valid: boolean; error?: string } {
  // Validate file type
  if (!file.type.startsWith('audio/')) {
    return { valid: false, error: 'Please select a valid audio file.' };
  }

  // Validate file size (25MB max)
  const maxSize = 25 * 1024 * 1024; // 25MB
  if (file.size > maxSize) {
    return { valid: false, error: 'File too large. Maximum size is 25MB.' };
  }

  return { valid: true };
}

export function downloadTextFile(content: string, filename: string): void {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}


