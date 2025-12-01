/**
 * Tests for file utility functions
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { formatFileSize, validateAudioFile, downloadTextFile } from '../fileUtils'

describe('formatFileSize', () => {
  it('should format bytes correctly', () => {
    expect(formatFileSize(0)).toBe('0 Bytes')
    expect(formatFileSize(1024)).toBe('1 KB')
    expect(formatFileSize(1048576)).toBe('1 MB')
    expect(formatFileSize(1073741824)).toBe('1 GB')
  })

  it('should handle decimal values', () => {
    expect(formatFileSize(1536)).toBe('1.5 KB')
    expect(formatFileSize(2621440)).toBe('2.5 MB')
  })
})

describe('validateAudioFile', () => {
  it('should accept valid audio files', () => {
    const validFile = new File([''], 'test.mp3', { type: 'audio/mpeg' })
    const result = validateAudioFile(validFile)
    expect(result.valid).toBe(true)
    expect(result.error).toBeUndefined()
  })

  it('should accept WAV files', () => {
    const wavFile = new File([''], 'test.wav', { type: 'audio/wav' })
    const result = validateAudioFile(wavFile)
    expect(result.valid).toBe(true)
  })

  it('should accept M4A files', () => {
    const m4aFile = new File([''], 'test.m4a', { type: 'audio/mp4' })
    const result = validateAudioFile(m4aFile)
    expect(result.valid).toBe(true)
  })

  it('should reject non-audio files', () => {
    const textFile = new File([''], 'test.txt', { type: 'text/plain' })
    const result = validateAudioFile(textFile)
    expect(result.valid).toBe(false)
    expect(result.error).toContain('valid audio file')
  })

  it('should reject files larger than 25MB', () => {
    const largeFile = new File(['x'.repeat(26 * 1024 * 1024)], 'test.mp3', {
      type: 'audio/mpeg',
    })
    const result = validateAudioFile(largeFile)
    expect(result.valid).toBe(false)
    expect(result.error).toContain('too large')
  })

  it('should accept files exactly at 25MB limit', () => {
    const fileAtLimit = new File(['x'.repeat(25 * 1024 * 1024)], 'test.mp3', {
      type: 'audio/mpeg',
    })
    const result = validateAudioFile(fileAtLimit)
    expect(result.valid).toBe(true)
  })
})

describe('downloadTextFile', () => {
  let createElementSpy: ReturnType<typeof vi.spyOn>
  let appendChildSpy: ReturnType<typeof vi.spyOn>
  let removeChildSpy: ReturnType<typeof vi.spyOn>
  let clickSpy: ReturnType<typeof vi.fn>
  let mockAnchor: HTMLAnchorElement
  let createObjectURLSpy: ReturnType<typeof vi.spyOn>
  let revokeObjectURLSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    // Mock URL.createObjectURL
    createObjectURLSpy = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:mock-url')
    revokeObjectURLSpy = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {})

    // Mock anchor element
    clickSpy = vi.fn()
    mockAnchor = {
      href: '',
      download: '',
      click: clickSpy,
    } as unknown as HTMLAnchorElement

    createElementSpy = vi.spyOn(document, 'createElement').mockReturnValue(mockAnchor)
    appendChildSpy = vi.spyOn(document.body, 'appendChild').mockImplementation(() => mockAnchor)
    removeChildSpy = vi.spyOn(document.body, 'removeChild').mockImplementation(() => mockAnchor)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should create and trigger download', () => {
    downloadTextFile('test content', 'test.txt')

    expect(createElementSpy).toHaveBeenCalledWith('a')
    expect(mockAnchor.href).toBe('blob:mock-url')
    expect(mockAnchor.download).toBe('test.txt')
    expect(appendChildSpy).toHaveBeenCalledWith(mockAnchor)
    expect(clickSpy).toHaveBeenCalled()
    expect(removeChildSpy).toHaveBeenCalledWith(mockAnchor)
    expect(revokeObjectURLSpy).toHaveBeenCalledWith('blob:mock-url')
  })

  it('should create blob with correct content and type', () => {
    const blobSpy = vi.spyOn(global, 'Blob')
    downloadTextFile('test content', 'test.txt')

    expect(blobSpy).toHaveBeenCalledWith(['test content'], {
      type: 'text/plain;charset=utf-8',
    })
  })
})


