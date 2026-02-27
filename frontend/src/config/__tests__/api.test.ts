/**
 * Tests for API configuration
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

describe('API Configuration', () => {
  const originalHostname = window.location.hostname

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    // Restore original hostname
    Object.defineProperty(window, 'location', {
      value: { hostname: originalHostname },
      writable: true,
    })
  })

  it('should export API_BASE_URL', async () => {
    const { API_BASE_URL } = await import('../api')
    expect(API_BASE_URL).toBeDefined()
    expect(typeof API_BASE_URL).toBe('string')
  })

  it('should export API_ENDPOINTS', async () => {
    const { API_ENDPOINTS } = await import('../api')
    expect(API_ENDPOINTS).toBeDefined()
    expect(API_ENDPOINTS.HEALTH).toBe('/health')
    expect(API_ENDPOINTS.TRANSCRIBE).toBe('/transcribe')
    expect(typeof API_ENDPOINTS.TRANSCRIBE_STATUS).toBe('function')
    expect(API_ENDPOINTS.TRANSCRIBE_STATUS('abc-123')).toBe('/transcribe/status/abc-123')
  })

  it('should return localhost URL for localhost', async () => {
    Object.defineProperty(window, 'location', {
      value: { hostname: 'localhost' },
      writable: true,
    })
    
    // Clear module cache to get fresh import
    vi.resetModules()
    const { API_BASE_URL } = await import('../api')
    
    expect(API_BASE_URL).toBe('http://localhost:5001')
  })

  it('should return localhost URL for 127.0.0.1', async () => {
    Object.defineProperty(window, 'location', {
      value: { hostname: '127.0.0.1' },
      writable: true,
    })
    
    vi.resetModules()
    const { API_BASE_URL } = await import('../api')
    
    expect(API_BASE_URL).toBe('http://localhost:5001')
  })

  it('should return production URL for non-localhost', async () => {
    Object.defineProperty(window, 'location', {
      value: { hostname: 'example.com' },
      writable: true,
    })
    
    vi.resetModules()
    const { API_BASE_URL } = await import('../api')
    
    expect(API_BASE_URL).toBe('https://audio-transcription-90eh.onrender.com')
  })

  it('should have valid URL format', async () => {
    const { API_BASE_URL } = await import('../api')
    // Should be either localhost or https URL
    expect(API_BASE_URL).toMatch(/^(http:\/\/localhost:\d+|https:\/\/.+)$/)
  })
})


