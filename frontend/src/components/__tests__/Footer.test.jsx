import { render, screen } from '@testing-library/react'
import Footer from '../Footer'

describe('Footer', () => {
  it('renderiza AdoptMe e seção Contato', () => {
    render(<Footer />)

    expect(screen.getAllByText(/AdoptMe/i).length).toBeGreaterThan(0)
    expect(screen.getByText(/Contato/i)).toBeInTheDocument()
  })
})
