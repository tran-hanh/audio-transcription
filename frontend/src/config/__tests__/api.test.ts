/**
 * Tests for API configuration
 */

import { describe, it, expect } from 'vitest'

describe('API Configuration', () => {
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
  })

  it('should have valid URL format', async () => {
    const { API_BASE_URL } = await import('../api')
    // Should be either localhost or https URL
    expect(API_BASE_URL).toMatch(/^(http:\/\/localhost:\d+|https:\/\/.+)$/)
  })
})


