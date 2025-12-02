/**
 * Tests for useTranscription hook
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useTranscription } from '../useTranscription'
import { TranscriptionService } from '../../services/transcriptionService'
import { AppState } from '../../types'

// Mock the service
vi.mock('../../services/transcriptionService')
vi.mock('../../utils/fileUtils', () => ({
  validateAudioFile: vi.fn((file) => {
    if (file.type.startsWith('audio/') && file.size <= 250 * 1024 * 1024) {
      return { valid: true }
    }
    return { valid: false, error: 'Invalid file' }
  }),
}))

describe('useTranscription', () => {
  let mockService: TranscriptionService

  beforeEach(() => {
    mockService = {
      transcribe: vi.fn(),
    } as unknown as TranscriptionService
    vi.clearAllMocks()
  })

  it('should initialize with IDLE state', () => {
    const { result } = renderHook(() => useTranscription(mockService))

    expect(result.current.state).toBe(AppState.IDLE)
    expect(result.current.selectedFile).toBeNull()
    expect(result.current.transcript).toBe('')
    expect(result.current.error).toBe('')
  })

  it('should handle valid file selection', () => {
    const { result } = renderHook(() => useTranscription(mockService))

    const validFile = new File([''], 'test.mp3', { type: 'audio/mpeg' })

    act(() => {
      result.current.handleFileSelect(validFile)
    })

    expect(result.current.selectedFile).toBe(validFile)
    expect(result.current.state).toBe(AppState.IDLE)
    expect(result.current.error).toBe('')
  })

  it('should handle invalid file selection', () => {
    const { result } = renderHook(() => useTranscription(mockService))

    const invalidFile = new File([''], 'test.txt', { type: 'text/plain' })

    act(() => {
      result.current.handleFileSelect(invalidFile)
    })

    expect(result.current.state).toBe(AppState.ERROR)
    expect(result.current.error).toBe('Invalid file')
  })

  it('should start transcription with valid file', async () => {
    const { result } = renderHook(() => useTranscription(mockService))

    const validFile = new File([''], 'test.mp3', { type: 'audio/mpeg' })
    const mockTranscript = 'Test transcript'

    ;(mockService.transcribe as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
      mockTranscript
    )

    act(() => {
      result.current.handleFileSelect(validFile)
    })

    await act(async () => {
      await result.current.startTranscription(12)
    })

    expect(mockService.transcribe).toHaveBeenCalledWith(
      validFile,
      12,
      expect.any(Function)
    )
    expect(result.current.transcript).toBe(mockTranscript)
    expect(result.current.state).toBe(AppState.RESULTS)
  })

  it('should handle transcription errors', async () => {
    const { result } = renderHook(() => useTranscription(mockService))

    const validFile = new File([''], 'test.mp3', { type: 'audio/mpeg' })
    const errorMessage = 'Transcription failed'

    ;(mockService.transcribe as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error(errorMessage)
    )

    act(() => {
      result.current.handleFileSelect(validFile)
    })

    await act(async () => {
      await result.current.startTranscription(12)
    })

    expect(result.current.state).toBe(AppState.ERROR)
    expect(result.current.error).toBe(errorMessage)
  })

  it('should update progress during transcription', async () => {
    const { result } = renderHook(() => useTranscription(mockService))

    const validFile = new File([''], 'test.mp3', { type: 'audio/mpeg' })
    let progressCallback: (progress: { progress: number; message: string }) => void

    ;(mockService.transcribe as ReturnType<typeof vi.fn>).mockImplementation(
      async (_file, _chunkLength, onProgress) => {
        progressCallback = onProgress
        await new Promise((resolve) => setTimeout(resolve, 10))
        return 'Final transcript'
      }
    )

    act(() => {
      result.current.handleFileSelect(validFile)
    })

    act(() => {
      result.current.startTranscription(12)
    })

    await waitFor(() => {
      if (progressCallback!) {
        act(() => {
          progressCallback({ progress: 50, message: 'Processing...' })
        })
      }
    })

    expect(result.current.progress.progress).toBe(50)
    expect(result.current.progress.message).toBe('Processing...')
  })

  it('should reset state', () => {
    const { result } = renderHook(() => useTranscription(mockService))

    const validFile = new File([''], 'test.mp3', { type: 'audio/mpeg' })

    act(() => {
      result.current.handleFileSelect(validFile)
    })

    act(() => {
      result.current.reset()
    })

    expect(result.current.state).toBe(AppState.IDLE)
    expect(result.current.selectedFile).toBeNull()
    expect(result.current.transcript).toBe('')
    expect(result.current.error).toBe('')
  })

  it('should not start transcription without selected file', async () => {
    const { result } = renderHook(() => useTranscription(mockService))

    await act(async () => {
      await result.current.startTranscription(12)
    })

    expect(mockService.transcribe).not.toHaveBeenCalled()
  })
})


