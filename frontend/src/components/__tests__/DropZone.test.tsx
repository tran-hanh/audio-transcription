/**
 * Tests for DropZone component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DropZone } from '../DropZone'

describe('DropZone', () => {
  const mockOnFileSelect = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render drop zone with correct text', () => {
    render(<DropZone onFileSelect={mockOnFileSelect} />)

    expect(screen.getByText('Drag & Drop your audio file here')).toBeInTheDocument()
    expect(screen.getByText('or click to browse files')).toBeInTheDocument()
    expect(screen.getByText('Supports MP3, WAV, M4A (Max 25MB)')).toBeInTheDocument()
  })

  it('should have hidden file input', () => {
    render(<DropZone onFileSelect={mockOnFileSelect} />)

    const fileInput = screen.getByLabelText(/drag & drop/i).querySelector('input[type="file"]')
    expect(fileInput).toBeInTheDocument()
    expect(fileInput).toHaveAttribute('accept', 'audio/*')
  })

  it('should call onFileSelect when file is selected', async () => {
    const user = userEvent.setup()
    render(<DropZone onFileSelect={mockOnFileSelect} />)

    const file = new File(['audio content'], 'test.mp3', { type: 'audio/mpeg' })
    const fileInput = screen.getByLabelText(/drag & drop/i).querySelector('input[type="file"]') as HTMLInputElement

    await user.upload(fileInput, file)

    expect(mockOnFileSelect).toHaveBeenCalledWith(file)
  })

  it('should handle drag and drop', () => {
    render(<DropZone onFileSelect={mockOnFileSelect} />)

    const dropZone = screen.getByLabelText(/drag & drop/i)
    const file = new File(['audio content'], 'test.mp3', { type: 'audio/mpeg' })

    fireEvent.dragOver(dropZone)
    expect(dropZone).toHaveClass('dragover')

    fireEvent.drop(dropZone, {
      dataTransfer: {
        files: [file],
      },
    })

    expect(mockOnFileSelect).toHaveBeenCalledWith(file)
    expect(dropZone).not.toHaveClass('dragover')
  })

  it('should not handle drag events when disabled', () => {
    render(<DropZone onFileSelect={mockOnFileSelect} disabled={true} />)

    const dropZone = screen.getByLabelText(/drag & drop/i)
    const file = new File(['audio content'], 'test.mp3', { type: 'audio/mpeg' })

    fireEvent.dragOver(dropZone)
    expect(dropZone).not.toHaveClass('dragover')

    fireEvent.drop(dropZone, {
      dataTransfer: {
        files: [file],
      },
    })

    expect(mockOnFileSelect).not.toHaveBeenCalled()
  })

  it('should disable file input when disabled prop is true', () => {
    render(<DropZone onFileSelect={mockOnFileSelect} disabled={true} />)

    const fileInput = screen.getByLabelText(/drag & drop/i).querySelector('input[type="file"]') as HTMLInputElement
    expect(fileInput).toBeDisabled()
  })
})


