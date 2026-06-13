import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'

vi.mock('../../api', () => ({
  perfilApi: {
    get: vi.fn(() => Promise.resolve({ ok: false })),
  },
}))

import AdopterForm from '../AdopterForm'

describe('AdopterForm (page)', () => {
  it('renderiza título e botão Salvar perfil e ver animais', () => {
    render(
      <MemoryRouter>
        <AdopterForm />
      </MemoryRouter>
    )

    expect(screen.getByRole('heading', { name: /Perfil do adotante/i })).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /Salvar perfil e ver animais/i })
    ).toBeInTheDocument()
  })
})
