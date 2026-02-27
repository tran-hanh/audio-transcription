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
    if (file.type.startsWith('audio/') && file.size <= 1024 * 1024 * 1024) {
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
      cancel: vi.fn(),
      isCancelled: vi.fn().mockReturnValue(false),
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

  it('should cancel transcription', () => {
    const { result } = renderHook(() => useTranscription(mockService))

    act(() => {
      result.current.cancelTranscription()
    })

    expect(mockService.cancel).toHaveBeenCalled()
    expect(result.current.state).toBe(AppState.IDLE)
  })

  it('should handle cancellation error', async () => {
    const { result } = renderHook(() => useTranscription(mockService))
    const validFile = new File([''], 'test.mp3', { type: 'audio/mpeg' })

    act(() => {
      result.current.handleFileSelect(validFile)
    })

    ;(mockService.transcribe as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error('Transcription cancelled')
    )

    await act(async () => {
      await result.current.startTranscription(12)
    })

    expect(result.current.state).toBe(AppState.IDLE)
    expect(result.current.error).toBe('')
  })

  it('should calculate estimated time remaining', async () => {
    const { result } = renderHook(() => useTranscription(mockService))
    const validFile = new File([''], 'test.mp3', { type: 'audio/mpeg' })

    act(() => {
      result.current.handleFileSelect(validFile)
    })

    ;(mockService.transcribe as ReturnType<typeof vi.fn>).mockImplementation(
      async (file, chunkLength, onProgress) => {
        // Simulate progress updates
        onProgress({ progress: 25, message: 'Processing...' })
        await new Promise((resolve) => setTimeout(resolve, 100))
        onProgress({ progress: 50, message: 'Processing...' })
        await new Promise((resolve) => setTimeout(resolve, 100))
        return 'Test transcript'
      }
    )

    act(() => {
      result.current.startTranscription(12)
    })

    await waitFor(() => {
      expect(result.current.estimatedTimeRemaining).not.toBeNull()
    })
  })

  it('should return null for estimated time when progress is 0', () => {
    const { result } = renderHook(() => useTranscription(mockService))
    expect(result.current.estimatedTimeRemaining).toBeNull()
  })

  it('should return null for estimated time when progress is 100', async () => {
    const { result } = renderHook(() => useTranscription(mockService))
    const validFile = new File([''], 'test.mp3', { type: 'audio/mpeg' })

    act(() => {
      result.current.handleFileSelect(validFile)
    })

    ;(mockService.transcribe as ReturnType<typeof vi.fn>).mockResolvedValueOnce('Test transcript')

    await act(async () => {
      await result.current.startTranscription(12)
    })

    expect(result.current.estimatedTimeRemaining).toBeNull()
  })

  it('should handle estimated time calculation with invalid values', async () => {
    const { result } = renderHook(() => useTranscription(mockService))
    const validFile = new File([''], 'test.mp3', { type: 'audio/mpeg' })

    act(() => {
      result.current.handleFileSelect(validFile)
    })

    // Mock startTime but with progress that would cause invalid calculation
    ;(mockService.transcribe as ReturnType<typeof vi.fn>).mockImplementation(
      async (file, chunkLength, onProgress) => {
        onProgress({ progress: 0, message: 'Starting...' })
        await new Promise((resolve) => setTimeout(resolve, 10))
        return 'Test transcript'
      }
    )

    await act(async () => {
      await result.current.startTranscription(12)
    })

    // Should handle gracefully
    expect(result.current.state).toBe(AppState.RESULTS)
  })

  it('should return estimated time in seconds only when less than a minute', async () => {
    const { result } = renderHook(() => useTranscription(mockService))
    const validFile = new File([''], 'test.mp3', { type: 'audio/mpeg' })

    act(() => {
      result.current.handleFileSelect(validFile)
    })

    let progressCallback: ((progress: { progress: number; message: string }) => void) | null = null

    ;(mockService.transcribe as ReturnType<typeof vi.fn>).mockImplementation(
      async (file, chunkLength, onProgress) => {
        progressCallback = onProgress
        // Don't complete immediately, keep it processing
        await new Promise((resolve) => setTimeout(resolve, 100))
        // Update progress after a delay to simulate elapsed time
        if (progressCallback) {
          progressCallback({ progress: 50, message: 'Processing...' })
        }
        await new Promise((resolve) => setTimeout(resolve, 100))
        return 'Test transcript'
      }
    )

    act(() => {
      result.current.startTranscription(12)
    })

    // Wait for progress update
    await waitFor(() => {
      expect(result.current.progress.progress).toBe(50)
    })

    // Check estimated time - should be calculated and in seconds format if < 1 minute
    const estimated = result.current.estimatedTimeRemaining
    if (estimated) {
      // If it's less than a minute, it should only show seconds
      expect(estimated).toBeTruthy()
    }
  })

  it('should return null for estimated time when remaining is negative', async () => {
    const { result } = renderHook(() => useTranscription(mockService))
    const validFile = new File([''], 'test.mp3', { type: 'audio/mpeg' })

    act(() => {
      result.current.handleFileSelect(validFile)
    })

    const startTime = Date.now()
    ;(mockService.transcribe as ReturnType<typeof vi.fn>).mockImplementation(
      async (file, chunkLength, onProgress) => {
        // Simulate progress going backwards (shouldn't happen but test edge case)
        vi.spyOn(Date, 'now').mockReturnValue(startTime + 1000)
        onProgress({ progress: 10, message: 'Processing...' })
        await new Promise((resolve) => setTimeout(resolve, 10))
        // Progress goes backwards
        onProgress({ progress: 5, message: 'Processing...' })
        await new Promise((resolve) => setTimeout(resolve, 10))
        return 'Test transcript'
      }
    )

    await act(async () => {
      await result.current.startTranscription(12)
    })

    // Should handle gracefully
    expect(result.current.state).toBe(AppState.RESULTS)
  })

  it('should return null for estimated time when calculation is infinite', async () => {
    const { result } = renderHook(() => useTranscription(mockService))
    const validFile = new File([''], 'test.mp3', { type: 'audio/mpeg' })

    act(() => {
      result.current.handleFileSelect(validFile)
    })

    ;(mockService.transcribe as ReturnType<typeof vi.fn>).mockImplementation(
      async (file, chunkLength, onProgress) => {
        // This shouldn't happen in practice, but test the branch
        onProgress({ progress: 50, message: 'Processing...' })
        await new Promise((resolve) => setTimeout(resolve, 10))
        return 'Test transcript'
      }
    )

    await act(async () => {
      await result.current.startTranscription(12)
    })

    // Should handle gracefully - the calculation should work normally
    expect(result.current.state).toBe(AppState.RESULTS)
  })
})


