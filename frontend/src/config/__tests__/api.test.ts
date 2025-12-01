/**
 * Tests for API configuration
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest'

describe('API Configuration', () => {
  const originalLocation = window.location

  beforeEach(() => {
    // Reset location mock
    delete (window as { location?: unknown }).location
  })

  afterEach(() => {
    // Restore original location
    Object.defineProperty(window, 'location', {
      value: originalLocation,
      writable: true,
      configurable: true,
    })
  })

  it('should use localhost URL for local development', async () => {
    Object.defineProperty(window, 'location', {
      value: {
        hostname: 'localhost',
      } as Location,
      writable: true,
    })

    // Re-import to get fresh config
    const { API_BASE_URL } = await import('../api')
    expect(API_BASE_URL).toBe('http://localhost:5001')
  })

  it('should use localhost URL for 127.0.0.1', async () => {
    Object.defineProperty(window, 'location', {
      value: {
        hostname: '127.0.0.1',
      } as Location,
      writable: true,
    })

    const { API_BASE_URL } = await import('../api')
    expect(API_BASE_URL).toBe('http://localhost:5001')
  })

  it('should use production URL for GitHub Pages', async () => {
    Object.defineProperty(window, 'location', {
      value: {
        hostname: 'username.github.io',
      } as Location,
      writable: true,
    })

    const { API_BASE_URL } = await import('../api')
    expect(API_BASE_URL).toBe('https://your-backend-url.onrender.com')
  })
})


