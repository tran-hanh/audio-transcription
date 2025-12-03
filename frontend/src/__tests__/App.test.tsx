/**
 * Tests for App component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AppState } from '../types'

// Mock the API config first
vi.mock('../config/api', () => ({
  API_BASE_URL: 'http://localhost:5001',
  API_ENDPOINTS: {
    HEALTH: '/health',
    TRANSCRIBE: '/transcribe',
  },
}))

// Mock the transcription service
vi.mock('../services/transcriptionService', () => ({
  TranscriptionService: vi.fn().mockImplementation(() => ({
    transcribe: vi.fn(),
    healthCheck: vi.fn(),
  })),
}))

// Mock useTranscription hook
const mockHandleFileSelect = vi.fn()
const mockStartTranscription = vi.fn()
const mockReset = vi.fn()

vi.mock('../hooks/useTranscription', () => ({
  useTranscription: vi.fn(() => ({
    state: AppState.IDLE,
    selectedFile: null,
    transcript: '',
    error: '',
    progress: { progress: 0, message: '' },
    handleFileSelect: mockHandleFileSelect,
    startTranscription: mockStartTranscription,
    reset: mockReset,
  })),
}))

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render the app with header', async () => {
    const { App } = await import('../App')
    render(<App />)
    
    expect(screen.getByText('Audio Scribe')).toBeInTheDocument()
    expect(screen.getByText(/Upload an MP3 or WAV file/)).toBeInTheDocument()
  })

  it('should show drop zone initially', async () => {
    const { App } = await import('../App')
    render(<App />)
    
    expect(screen.getByText('Drag & Drop your audio file here')).toBeInTheDocument()
  })

  it('should show processing section when processing', async () => {
    const { useTranscription } = await import('../hooks/useTranscription')
    vi.mocked(useTranscription).mockReturnValue({
      state: AppState.PROCESSING,
      selectedFile: new File(['test'], 'test.mp3', { type: 'audio/mpeg' }),
      transcript: '',
      error: '',
      progress: { progress: 50, message: 'Processing...' },
      handleFileSelect: mockHandleFileSelect,
      startTranscription: mockStartTranscription,
      reset: mockReset,
    })

    const { App } = await import('../App')
    render(<App />)
    
    expect(screen.getByText('test.mp3')).toBeInTheDocument()
    expect(screen.getByText('Processing...')).toBeInTheDocument()
  })

  it('should show output section when results are ready', async () => {
    const { useTranscription } = await import('../hooks/useTranscription')
    vi.mocked(useTranscription).mockReturnValue({
      state: AppState.RESULTS,
      selectedFile: new File(['test'], 'test.mp3', { type: 'audio/mpeg' }),
      transcript: 'Test transcript content',
      error: '',
      progress: { progress: 100, message: 'Complete' },
      handleFileSelect: mockHandleFileSelect,
      startTranscription: mockStartTranscription,
      reset: mockReset,
    })

    const { App } = await import('../App')
    render(<App />)
    
    expect(screen.getByText('Test transcript content')).toBeInTheDocument()
  })

  it('should show error alert when error occurs', async () => {
    const { useTranscription } = await import('../hooks/useTranscription')
    vi.mocked(useTranscription).mockReturnValue({
      state: AppState.ERROR,
      selectedFile: null,
      transcript: '',
      error: 'Test error message',
      progress: { progress: 0, message: '' },
      handleFileSelect: mockHandleFileSelect,
      startTranscription: mockStartTranscription,
      reset: mockReset,
    })

    const { App } = await import('../App')
    render(<App />)
    
    expect(screen.getByText('Test error message')).toBeInTheDocument()
    expect(screen.getByText('Drag & Drop your audio file here')).toBeInTheDocument()
  })

  it('should handle processing state without selectedFile', async () => {
    const { useTranscription } = await import('../hooks/useTranscription')
    vi.mocked(useTranscription).mockReturnValue({
      state: AppState.PROCESSING,
      selectedFile: null,
      transcript: '',
      error: '',
      progress: { progress: 50, message: 'Processing...' },
      handleFileSelect: mockHandleFileSelect,
      startTranscription: mockStartTranscription,
      reset: mockReset,
    })

    const { App } = await import('../App')
    render(<App />)
    
    // Should not crash when selectedFile is null in PROCESSING state
    expect(screen.getByText('Audio Scribe')).toBeInTheDocument()
  })

  it('should handle results state with null selectedFile', async () => {
    const { useTranscription } = await import('../hooks/useTranscription')
    vi.mocked(useTranscription).mockReturnValue({
      state: AppState.RESULTS,
      selectedFile: null,
      transcript: 'Test transcript',
      error: '',
      progress: { progress: 100, message: 'Complete' },
      handleFileSelect: mockHandleFileSelect,
      startTranscription: mockStartTranscription,
      reset: mockReset,
    })

    const { App } = await import('../App')
    render(<App />)
    
    expect(screen.getByText('Test transcript')).toBeInTheDocument()
  })

  it('should handle processing state with empty progress message', async () => {
    const { useTranscription } = await import('../hooks/useTranscription')
    vi.mocked(useTranscription).mockReturnValue({
      state: AppState.PROCESSING,
      selectedFile: new File(['test'], 'test.mp3', { type: 'audio/mpeg' }),
      transcript: '',
      error: '',
      progress: { progress: 50, message: '' },
      handleFileSelect: mockHandleFileSelect,
      startTranscription: mockStartTranscription,
      reset: mockReset,
    })

    const { App } = await import('../App')
    render(<App />)
    
    expect(screen.getByText('test.mp3')).toBeInTheDocument()
    expect(screen.getByText('Processing...')).toBeInTheDocument()
  })
})

