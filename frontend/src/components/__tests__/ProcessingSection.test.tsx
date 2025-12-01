/**
 * Tests for ProcessingSection component
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ProcessingSection } from '../ProcessingSection'

describe('ProcessingSection', () => {
  it('should render file name', () => {
    render(
      <ProcessingSection fileName="test.mp3" progress={0} message="Uploading..." />
    )

    expect(screen.getByText('test.mp3')).toBeInTheDocument()
  })

  it('should render progress message', () => {
    render(
      <ProcessingSection fileName="test.mp3" progress={50} message="Processing..." />
    )

    expect(screen.getByText('Processing...')).toBeInTheDocument()
  })

  it('should show indeterminate progress bar when progress is 0', () => {
    const { container } = render(
      <ProcessingSection fileName="test.mp3" progress={0} message="Uploading..." />
    )

    const progressBar = container.querySelector('.progress-bar')
    expect(progressBar).toHaveClass('indeterminate')
  })

  it('should show progress bar with percentage when progress > 0', () => {
    const { container } = render(
      <ProcessingSection fileName="test.mp3" progress={75} message="Processing..." />
    )

    const progressBar = container.querySelector('.progress-bar')
    expect(progressBar).not.toHaveClass('indeterminate')

    const progressFill = container.querySelector('.progress-fill')
    expect(progressFill).toHaveStyle({ width: '75%' })
  })
})

