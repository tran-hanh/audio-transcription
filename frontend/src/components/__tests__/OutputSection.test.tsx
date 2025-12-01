/**
 * Tests for OutputSection component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { OutputSection } from '../OutputSection'

// Mock downloadTextFile
vi.mock('../../utils/fileUtils', () => ({
  downloadTextFile: vi.fn(),
}))

// Mock clipboard API
const mockWriteText = vi.fn().mockResolvedValue(undefined)
Object.defineProperty(navigator, 'clipboard', {
  value: {
    writeText: mockWriteText,
  },
  writable: true,
  configurable: true,
})

describe('OutputSection', () => {
  const mockOnReset = vi.fn()
  const mockTranscript = 'This is a test transcript.'

  beforeEach(() => {
    vi.clearAllMocks()
    mockWriteText.mockClear()
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

    render(
      <OutputSection
        transcript={mockTranscript}
        originalFileName="test.mp3"
        onReset={mockOnReset}
      />
    )

    const copyButton = screen.getByText(/copy to clipboard/i)
    await user.click(copyButton)

    expect(mockWriteText).toHaveBeenCalledWith(mockTranscript)
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


