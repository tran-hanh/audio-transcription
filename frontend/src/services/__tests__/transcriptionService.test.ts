/**
 * Tests for transcription service
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { TranscriptionService } from '../transcriptionService'

describe('TranscriptionService', () => {
  let service: TranscriptionService
  const mockBaseUrl = 'http://localhost:5001'

  beforeEach(() => {
    service = new TranscriptionService(mockBaseUrl)
    globalThis.fetch = vi.fn() as typeof fetch
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('healthCheck', () => {
    it('should return true when health endpoint responds with OK', async () => {
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        status: 200,
      })

      const result = await service.healthCheck()
      expect(result).toBe(true)
      expect(globalThis.fetch).toHaveBeenCalledWith(`${mockBaseUrl}/health`)
    })

    it('should return false when health endpoint fails', async () => {
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: false,
        status: 500,
      })

      const result = await service.healthCheck()
      expect(result).toBe(false)
    })

    it('should return false when fetch throws an error', async () => {
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        new Error('Network error')
      )

      const result = await service.healthCheck()
      expect(result).toBe(false)
    })
  })

  describe('transcribe', () => {
    const mockFile = new File(['audio content'], 'test.mp3', { type: 'audio/mpeg' })

    it('should send file and chunk length then poll status', async () => {
      const jobId = 'test-job-123'
      ;(globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
          status: 202,
          ok: true,
          json: vi.fn().mockResolvedValueOnce({ job_id: jobId, status: 'processing' }),
        } as unknown as Response)
        ;(globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
          ok: true,
          json: vi.fn().mockResolvedValueOnce({
            status: 'completed',
            progress: 100,
            message: 'Done',
            transcript: 'Test transcript',
          }),
        } as unknown as Response)

      const result = await service.transcribe(mockFile, 12, vi.fn())
      expect(result).toBe('Test transcript')
      expect(globalThis.fetch).toHaveBeenCalledWith(
        `${mockBaseUrl}/transcribe`,
        expect.objectContaining({ method: 'POST', body: expect.any(FormData), signal: expect.any(AbortSignal) })
      )
      expect(globalThis.fetch).toHaveBeenCalledWith(
        `${mockBaseUrl}/transcribe/status/${jobId}`,
        expect.objectContaining({ signal: expect.any(AbortSignal) })
      )
    })

    it('should handle server errors', async () => {
      const mockResponse: Response = {
        ok: false,
        status: 500,
        json: vi.fn().mockResolvedValueOnce({ error: 'Server error' }),
      } as unknown as Response

      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockResponse)

      await expect(
        service.transcribe(mockFile, 12, vi.fn())
      ).rejects.toThrow('Server error')
    })

    it('should retry on network error before failing', async () => {
      const networkError = new TypeError('Failed to fetch')
      const finalResponse: Response = {
        ok: false,
        status: 500,
        json: vi.fn().mockResolvedValue({ error: 'Server error' }),
      } as unknown as Response

      ;(globalThis.fetch as ReturnType<typeof vi.fn>)
        .mockRejectedValueOnce(networkError)
        .mockResolvedValueOnce(finalResponse)

      const progress = vi.fn()

      await expect(service.transcribe(mockFile, 12, progress)).rejects.toThrow('Server error')

      expect(progress).toHaveBeenCalledWith(
        expect.objectContaining({ message: expect.stringContaining('Connecting to server...') })
      )
    })

    it('should call onProgress when polling status', async () => {
      const progressCallback = vi.fn()
      const jobId = 'job-456'
      ;(globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
          status: 202,
          ok: true,
          json: vi.fn().mockResolvedValueOnce({ job_id: jobId }),
        } as unknown as Response)
        ;(globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
          ok: true,
          json: vi.fn().mockResolvedValueOnce({
            status: 'processing',
            progress: 50,
            message: 'Processing...',
          }),
        } as unknown as Response)
        ;(globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
          ok: true,
          json: vi.fn().mockResolvedValueOnce({
            status: 'completed',
            progress: 100,
            message: 'Done',
            transcript: 'Done transcript',
          }),
        } as unknown as Response)

      const result = await service.transcribe(mockFile, 12, progressCallback)
      expect(result).toBe('Done transcript')
      expect(progressCallback).toHaveBeenCalledWith(
        expect.objectContaining({ progress: 50, message: 'Processing...' })
      )
      expect(progressCallback).toHaveBeenCalledWith(
        expect.objectContaining({ progress: 100, message: 'Done' })
      )
    })

    it('should return transcript when job completes', async () => {
      const jobId = 'job-789'
      ;(globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
          status: 202,
          ok: true,
          json: vi.fn().mockResolvedValueOnce({ job_id: jobId }),
        } as unknown as Response)
        ;(globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
          ok: true,
          json: vi.fn().mockResolvedValueOnce({
            status: 'completed',
            progress: 100,
            message: 'Done',
            transcript: 'Test transcript',
          }),
        } as unknown as Response)

      const result = await service.transcribe(mockFile, 12, vi.fn())
      expect(result).toBe('Test transcript')
    })

    it('should throw when status check response is not ok', async () => {
      const jobId = 'job-status-error'
      ;(globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        status: 202,
        ok: true,
        json: vi.fn().mockResolvedValueOnce({ job_id: jobId }),
      } as unknown as Response)
      ;(globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: false,
        status: 500,
      } as unknown as Response)

      await expect(service.transcribe(mockFile, 12, vi.fn())).rejects.toThrow(
        'Status check failed: 500'
      )
    })

    it('should throw when job completes with no transcript', async () => {
      const jobId = 'job-no-transcript'
      ;(globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
          status: 202,
          ok: true,
          json: vi.fn().mockResolvedValueOnce({ job_id: jobId }),
        } as unknown as Response)
        ;(globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
          ok: true,
          json: vi.fn().mockResolvedValueOnce({
            status: 'completed',
            progress: 100,
            message: 'Done',
            transcript: null,
          }),
        } as unknown as Response)

      await expect(service.transcribe(mockFile, 12, vi.fn())).rejects.toThrow(
        'No transcript received from server'
      )
    })

    it('should throw when job status is failed', async () => {
      const jobId = 'job-fail'
      ;(globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
          status: 202,
          ok: true,
          json: vi.fn().mockResolvedValueOnce({ job_id: jobId }),
        } as unknown as Response)
        ;(globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
          ok: true,
          json: vi.fn().mockResolvedValueOnce({
            status: 'failed',
            progress: 0,
            message: 'Error',
            error: 'Transcription failed',
          }),
        } as unknown as Response)

      await expect(service.transcribe(mockFile, 12, vi.fn())).rejects.toThrow('Transcription failed')
    })

    it('should throw when 202 response has no job_id', async () => {
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        status: 202,
        ok: true,
        json: vi.fn().mockResolvedValueOnce({}),
      } as unknown as Response)

      await expect(service.transcribe(mockFile, 12, vi.fn())).rejects.toThrow(
        'Server did not return a job id'
      )
    })

    it('should throw when initial response is not 202', async () => {
      const okResponse: Response = {
        ok: true,
        status: 200,
        json: vi.fn().mockResolvedValue({}),
      } as unknown as Response

      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(okResponse)

      await expect(service.transcribe(mockFile, 12, vi.fn())).rejects.toThrow(
        'Unexpected response from server.'
      )
    })

    it('should throw when polling exceeds max wait time', async () => {
      const jobId = 'job-timeout'
      const nowSpy = vi.spyOn(Date, 'now')
      const start = 1_000_000
      const maxWaitMs = 30 * 60 * 1000

      // First call in service: startedAt
      nowSpy.mockReturnValueOnce(start)
      // Next call in loop: exceed maxWait immediately
      nowSpy.mockReturnValue(start + maxWaitMs + 1)

      ;(globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        status: 202,
        ok: true,
        json: vi.fn().mockResolvedValueOnce({ job_id: jobId }),
      } as unknown as Response)

      await expect(service.transcribe(mockFile, 12, vi.fn())).rejects.toThrow(
        'Transcription is taking longer than expected'
      )

      nowSpy.mockRestore()
    })

  })
})


