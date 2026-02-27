/**
 * Tests for DropZone component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
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
    expect(screen.getByText('Supports MP3, WAV, M4A (Max 1GB)')).toBeInTheDocument()
  })

  it('should have hidden file input', () => {
    const { container } = render(<DropZone onFileSelect={mockOnFileSelect} />)

    const fileInput = container.querySelector('input[type="file"]')
    expect(fileInput).toBeTruthy()
    expect(fileInput).toHaveAttribute('accept', 'audio/*')
  })

  it('should call onFileSelect when file is selected', async () => {
    const { container } = render(<DropZone onFileSelect={mockOnFileSelect} />)

    const file = new File(['audio content'], 'test.mp3', { type: 'audio/mpeg' })
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement
    expect(fileInput).toBeTruthy()

    // Simulate file selection
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      writable: false,
    })
    fireEvent.change(fileInput)

    expect(mockOnFileSelect).toHaveBeenCalledWith(file)
  })

  it('should handle drag and drop', () => {
    const { container } = render(<DropZone onFileSelect={mockOnFileSelect} />)

    const dropZone = container.querySelector('label.drop-zone') as HTMLElement
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
    const { container } = render(<DropZone onFileSelect={mockOnFileSelect} disabled={true} />)

    const dropZone = container.querySelector('label.drop-zone') as HTMLElement
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
    const { container } = render(<DropZone onFileSelect={mockOnFileSelect} disabled={true} />)

    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement
    expect(fileInput).toBeTruthy()
    expect(fileInput).toBeDisabled()
  })

  it('should handle drag leave', () => {
    const { container } = render(<DropZone onFileSelect={mockOnFileSelect} />)

    const dropZone = container.querySelector('label.drop-zone') as HTMLElement

    fireEvent.dragOver(dropZone)
    expect(dropZone).toHaveClass('dragover')

    fireEvent.dragLeave(dropZone)
    expect(dropZone).not.toHaveClass('dragover')
  })

  it('should handle keyboard Enter key', () => {
    const { container } = render(<DropZone onFileSelect={mockOnFileSelect} />)

    const dropZone = container.querySelector('label.drop-zone') as HTMLElement
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement
    const clickSpy = vi.spyOn(fileInput, 'click')

    fireEvent.keyDown(dropZone, { key: 'Enter' })
    expect(clickSpy).toHaveBeenCalled()
  })

  it('should handle keyboard Space key', () => {
    const { container } = render(<DropZone onFileSelect={mockOnFileSelect} />)

    const dropZone = container.querySelector('label.drop-zone') as HTMLElement
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement
    const clickSpy = vi.spyOn(fileInput, 'click')

    fireEvent.keyDown(dropZone, { key: ' ' })
    expect(clickSpy).toHaveBeenCalled()
  })

  it('should not handle keyboard events when disabled', () => {
    const { container } = render(<DropZone onFileSelect={mockOnFileSelect} disabled={true} />)

    const dropZone = container.querySelector('label.drop-zone') as HTMLElement
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement
    const clickSpy = vi.spyOn(fileInput, 'click')

    fireEvent.keyDown(dropZone, { key: 'Enter' })
    expect(clickSpy).not.toHaveBeenCalled()
  })

  it('should display file info when selectedFile is provided', () => {
    const selectedFile = new File(['test'], 'audio.mp3', { type: 'audio/mpeg' })
    render(<DropZone onFileSelect={mockOnFileSelect} selectedFile={selectedFile} />)

    expect(screen.getByText('Selected File')).toBeInTheDocument()
    expect(screen.getByText('Name:')).toBeInTheDocument()
    expect(screen.getByText('Size:')).toBeInTheDocument()
    expect(screen.getByText('Type:')).toBeInTheDocument()
    expect(screen.getByText('audio.mp3')).toBeInTheDocument()
  })

  it('should display file type from file.type when available', () => {
    const selectedFile = new File(['test'], 'audio.mp3', { type: 'audio/mpeg' })
    render(<DropZone onFileSelect={mockOnFileSelect} selectedFile={selectedFile} />)

    expect(screen.getByText('audio/mpeg')).toBeInTheDocument()
  })

  it('should display file type from extension when type is missing', () => {
    const selectedFile = new File(['test'], 'audio.wav', { type: '' })
    render(<DropZone onFileSelect={mockOnFileSelect} selectedFile={selectedFile} />)

    expect(screen.getByText('WAV')).toBeInTheDocument()
  })

  it('should handle drop without file', () => {
    const { container } = render(<DropZone onFileSelect={mockOnFileSelect} />)

    const dropZone = container.querySelector('label.drop-zone') as HTMLElement

    fireEvent.drop(dropZone, {
      dataTransfer: {
        files: [],
      },
    })

    expect(mockOnFileSelect).not.toHaveBeenCalled()
  })
})


