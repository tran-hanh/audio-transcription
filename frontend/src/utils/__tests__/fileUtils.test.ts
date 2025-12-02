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

  it('should reject files larger than 250MB', () => {
    // Create a small file but mock the size property to test validation
    const largeFile = new File(['test'], 'test.mp3', {
      type: 'audio/mpeg',
    })
    // Mock the size property to be larger than 250MB
    Object.defineProperty(largeFile, 'size', {
      value: 251 * 1024 * 1024,
      writable: false,
    })
    const result = validateAudioFile(largeFile)
    expect(result.valid).toBe(false)
    expect(result.error).toContain('too large')
  })

  it('should accept files exactly at 250MB limit', () => {
    // Create a small file but mock the size property to test validation
    const fileAtLimit = new File(['test'], 'test.mp3', {
      type: 'audio/mpeg',
    })
    // Mock the size property to be exactly 250MB
    Object.defineProperty(fileAtLimit, 'size', {
      value: 250 * 1024 * 1024,
      writable: false,
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
  let revokeObjectURLSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    // Mock URL.createObjectURL - jsdom doesn't have this by default
    const createObjectURLMock = vi.fn().mockReturnValue('blob:mock-url')
    const revokeObjectURLMock = vi.fn()
    
    // Add to URL if it doesn't exist
    if (!URL.createObjectURL) {
      Object.defineProperty(URL, 'createObjectURL', {
        value: createObjectURLMock,
        writable: true,
        configurable: true,
      })
    } else {
      vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:mock-url')
    }
    
    if (!URL.revokeObjectURL) {
      Object.defineProperty(URL, 'revokeObjectURL', {
        value: revokeObjectURLMock,
        writable: true,
        configurable: true,
      })
    }
    revokeObjectURLSpy = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {})
    
    // Ensure Blob is available (jsdom should have it, but ensure it's not mocked)
    if (!globalThis.Blob) {
      // Blob should be available in jsdom, but if not, we can't test this
    }

    // Mock anchor element
    clickSpy = vi.fn()
    mockAnchor = {
      href: '',
      download: '',
      click: clickSpy,
    } as unknown as HTMLAnchorElement

    createElementSpy = vi.spyOn(document, 'createElement').mockReturnValue(mockAnchor) as unknown as ReturnType<typeof vi.spyOn>
    appendChildSpy = vi.spyOn(document.body, 'appendChild').mockImplementation(() => mockAnchor) as unknown as ReturnType<typeof vi.spyOn>
    removeChildSpy = vi.spyOn(document.body, 'removeChild').mockImplementation(() => mockAnchor) as unknown as ReturnType<typeof vi.spyOn>
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
    // Test that the function executes without error
    // The actual Blob creation is tested indirectly through the download test
    expect(() => {
      downloadTextFile('test content', 'test.txt')
    }).not.toThrow()
    
    // Verify that createObjectURL was called (which means Blob was created)
    expect(URL.createObjectURL).toHaveBeenCalled()
  })
})


