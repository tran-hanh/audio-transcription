/**
 * Tests for ErrorAlert component
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ErrorAlert } from '../ErrorAlert'

describe('ErrorAlert', () => {
  it('should render error message', () => {
    render(<ErrorAlert message="Test error message" />)

    expect(screen.getByText('Test error message')).toBeInTheDocument()
    expect(screen.getByText('⚠️')).toBeInTheDocument()
  })

  it('should not render when message is empty', () => {
    const { container } = render(<ErrorAlert message="" />)
    expect(container.firstChild).toBeNull()
  })

  it('should have correct styling classes', () => {
    render(<ErrorAlert message="Error" />)

    const alert = screen.getByText('Error').closest('.error-alert')
    expect(alert).toBeInTheDocument()
  })
})

