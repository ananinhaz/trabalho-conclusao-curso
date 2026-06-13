import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Donate from '../Donate'

describe('Donate (page)', () => {
  it('renderiza título do formulário e botão Anunciar para adoção', () => {
    render(
      <MemoryRouter>
        <Donate />
      </MemoryRouter>
    )

    expect(screen.getByText(/Cadastrar animal para adoção/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Anunciar para Adoção/i })).toBeInTheDocument()
  })
})
