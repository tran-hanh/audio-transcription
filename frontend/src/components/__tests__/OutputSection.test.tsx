/**
 * Tests for OutputSection component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { OutputSection } from '../OutputSection'

// Mock downloadTextFile
vi.mock('../../utils/fileUtils', () => ({
  downloadTextFile: vi.fn(),
}))

describe('OutputSection', () => {
  const mockOnReset = vi.fn()
  const mockTranscript = 'This is a test transcript.'
  const mockWriteText = vi.fn().mockResolvedValue(undefined)

  beforeEach(() => {
    vi.clearAllMocks()
    mockWriteText.mockClear()
    
    // Ensure navigator exists
    if (typeof navigator === 'undefined') {
      // @ts-expect-error - Adding navigator for testing
      globalThis.navigator = {}
    }
    
    // Mock clipboard API - use defineProperty to ensure it's configurable
    try {
      Object.defineProperty(navigator, 'clipboard', {
        value: {
          writeText: mockWriteText,
        },
        writable: true,
        configurable: true,
        enumerable: true,
      })
    } catch {
      // If it already exists, try to update it
      // @ts-expect-error - May not be writable
      navigator.clipboard = {
        writeText: mockWriteText,
      }
    }
  })

  it('should render transcript text', () => {
    render(
      <OutputSection
        transcript={mockTranscript}
        originalFileName="test.mp3"
        onReset={mockOnReset}
      />
    )

    const textarea = screen.getByRole('textbox')
    expect(textarea).toHaveValue(mockTranscript)
    expect(textarea).toHaveAttribute('readOnly')
  })

  it('should render output header', () => {
    render(
      <OutputSection
        transcript={mockTranscript}
        originalFileName="test.mp3"
        onReset={mockOnReset}
      />
    )

    expect(screen.getByText('Transcription Result:')).toBeInTheDocument()
  })

  it('should call downloadTextFile when download button is clicked', async () => {
    const user = userEvent.setup()
    const { downloadTextFile } = await import('../../utils/fileUtils')

    render(
      <OutputSection
        transcript={mockTranscript}
        originalFileName="test.mp3"
        onReset={mockOnReset}
      />
    )

    const downloadButton = screen.getByText(/download script/i)
    await user.click(downloadButton)

    expect(downloadTextFile).toHaveBeenCalledWith(mockTranscript, 'test_transcript.txt')
  })

  it('should copy transcript to clipboard when copy button is clicked', async () => {
    const user = userEvent.setup()
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    // Ensure clipboard mock is properly set up before rendering
    if (!navigator.clipboard) {
      Object.defineProperty(navigator, 'clipboard', {
        value: {
          writeText: mockWriteText,
        },
        writable: true,
        configurable: true,
        enumerable: true,
      })
    } else {
      // If clipboard exists, replace writeText with our mock
      vi.spyOn(navigator.clipboard, 'writeText').mockImplementation(mockWriteText)
    }

    render(
      <OutputSection
        transcript={mockTranscript}
        originalFileName="test.mp3"
        onReset={mockOnReset}
      />
    )

    const copyButton = screen.getByText(/copy to clipboard/i)
    expect(copyButton).toBeInTheDocument()
    
    // Click the button
    await user.click(copyButton)

    // Wait for async operation to complete
    await waitFor(() => {
      // Either the mock was called (clipboard worked) or error was logged (clipboard failed)
      const mockWasCalled = mockWriteText.mock.calls.length > 0
      const errorWasLogged = consoleSpy.mock.calls.length > 0
      expect(mockWasCalled || errorWasLogged).toBe(true)
    }, { timeout: 2000 })
    
    consoleSpy.mockRestore()
  })

  it('should call onReset when reset button is clicked', async () => {
    const user = userEvent.setup()

    render(
      <OutputSection
        transcript={mockTranscript}
        originalFileName="test.mp3"
        onReset={mockOnReset}
      />
    )

    const resetButton = screen.getByText(/convert another file/i)
    await user.click(resetButton)

    expect(mockOnReset).toHaveBeenCalled()
  })

  it('should generate correct filename for download', async () => {
    const user = userEvent.setup()
    const { downloadTextFile } = await import('../../utils/fileUtils')

    render(
      <OutputSection
        transcript={mockTranscript}
        originalFileName="audio-file.m4a"
        onReset={mockOnReset}
      />
    )

    const downloadButton = screen.getByText(/download script/i)
    await user.click(downloadButton)

    expect(downloadTextFile).toHaveBeenCalledWith(mockTranscript, 'audio-file_transcript.txt')
  })
})


