/**
 * Tests for ThemeToggle component
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeToggle } from '../ThemeToggle'

describe('ThemeToggle', () => {
  const mockMatchMedia = vi.fn()
  const mockLocalStorage = {
    getItem: vi.fn(),
    setItem: vi.fn(),
  }

  beforeEach(() => {
    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: mockLocalStorage,
      writable: true,
    })

    // Mock matchMedia
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: mockMatchMedia,
    })

    // Reset mocks
    vi.clearAllMocks()
    mockLocalStorage.getItem.mockReturnValue(null)
    mockMatchMedia.mockReturnValue({
      matches: false,
      addListener: vi.fn(),
      removeListener: vi.fn(),
    })

    // Reset document class
    document.documentElement.classList.remove('dark-mode')
  })

  afterEach(() => {
    document.documentElement.classList.remove('dark-mode')
  })

  it('should render theme toggle button', () => {
    render(<ThemeToggle />)
    const button = screen.getByRole('button', { name: /switch to/i })
    expect(button).toBeInTheDocument()
  })

  it('should initialize with light mode when no localStorage value', () => {
    mockLocalStorage.getItem.mockReturnValue(null)
    mockMatchMedia.mockReturnValue({
      matches: false,
      addListener: vi.fn(),
      removeListener: vi.fn(),
    })

    render(<ThemeToggle />)
    expect(document.documentElement.classList.contains('dark-mode')).toBe(false)
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith('theme', 'light')
  })

  it('should initialize with dark mode from localStorage', () => {
    mockLocalStorage.getItem.mockReturnValue('dark')

    render(<ThemeToggle />)
    expect(document.documentElement.classList.contains('dark-mode')).toBe(true)
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith('theme', 'dark')
  })

  it('should initialize with light mode from localStorage', () => {
    mockLocalStorage.getItem.mockReturnValue('light')

    render(<ThemeToggle />)
    expect(document.documentElement.classList.contains('dark-mode')).toBe(false)
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith('theme', 'light')
  })

  it('should use system preference when localStorage is empty', () => {
    mockLocalStorage.getItem.mockReturnValue(null)
    mockMatchMedia.mockReturnValue({
      matches: true, // dark mode preferred
      addListener: vi.fn(),
      removeListener: vi.fn(),
    })

    render(<ThemeToggle />)
    expect(document.documentElement.classList.contains('dark-mode')).toBe(true)
  })

  it('should toggle between light and dark mode', async () => {
    const user = userEvent.setup()
    mockLocalStorage.getItem.mockReturnValue('light')

    render(<ThemeToggle />)
    const button = screen.getByRole('button')

    // Initially light mode
    expect(document.documentElement.classList.contains('dark-mode')).toBe(false)

    // Click to toggle to dark
    await user.click(button)
    expect(document.documentElement.classList.contains('dark-mode')).toBe(true)
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith('theme', 'dark')

    // Click to toggle back to light
    await user.click(button)
    expect(document.documentElement.classList.contains('dark-mode')).toBe(false)
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith('theme', 'light')
  })

  it('should handle localStorage errors gracefully', () => {
    mockLocalStorage.getItem.mockImplementation(() => {
      throw new Error('localStorage unavailable')
    })
    mockLocalStorage.setItem.mockImplementation(() => {
      throw new Error('localStorage unavailable')
    })

    // Should not throw
    render(<ThemeToggle />)
    expect(document.documentElement.classList.contains('dark-mode')).toBe(false)
  })

  it('should handle missing matchMedia gracefully', () => {
    mockLocalStorage.getItem.mockReturnValue(null)
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: undefined,
    })

    // Should not throw
    render(<ThemeToggle />)
    expect(document.documentElement.classList.contains('dark-mode')).toBe(false)
  })

  it('should show correct aria-label for light mode', () => {
    mockLocalStorage.getItem.mockReturnValue('light')
    render(<ThemeToggle />)
    const button = screen.getByRole('button', { name: 'Switch to dark mode' })
    expect(button).toBeInTheDocument()
  })

  it('should show correct aria-label for dark mode', () => {
    mockLocalStorage.getItem.mockReturnValue('dark')
    render(<ThemeToggle />)
    const button = screen.getByRole('button', { name: 'Switch to light mode' })
    expect(button).toBeInTheDocument()
  })
})
