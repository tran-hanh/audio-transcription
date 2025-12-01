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
    } catch (e) {
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

    // Ensure clipboard mock is accessible
    expect(navigator.clipboard).toBeDefined()
    expect(navigator.clipboard.writeText).toBe(mockWriteText)

    render(
      <OutputSection
        transcript={mockTranscript}
        originalFileName="test.mp3"
        onReset={mockOnReset}
      />
    )

    const copyButton = screen.getByText(/copy to clipboard/i)
    
    // Click the button
    await user.click(copyButton)

    // Wait for async clipboard operation to complete
    await waitFor(() => {
      expect(mockWriteText).toHaveBeenCalledWith(mockTranscript)
    }, { timeout: 2000 })
    
    // Also verify it was called exactly once
    expect(mockWriteText).toHaveBeenCalledTimes(1)
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


