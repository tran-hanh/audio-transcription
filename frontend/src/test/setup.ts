import { expect, afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers)

// Declare global types for Vitest
declare global {
  // eslint-disable-next-line no-var
  var global: typeof globalThis
}

// Cleanup after each test
afterEach(() => {
  cleanup()
})
