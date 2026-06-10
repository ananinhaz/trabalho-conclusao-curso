import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import Animals from '../Animals'
import * as api from '../../api'

const baseAnimals = [
  { id: 1, nome: 'Rex', especie: 'Cachorro', porte: 'Médio', cidade: 'SP', idade: '2' },
  { id: 2, nome: 'Luna', especie: 'Gato', porte: 'Pequeno', cidade: 'Curitiba', idade: '3' },
]

describe('Animals (page)', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  test('exibe filtros derivados dos animais retornados pela API', async () => {
    vi.spyOn(api.animaisApi, 'list').mockResolvedValue(baseAnimals)
    vi.spyOn(api.animaisApi, 'mine').mockResolvedValue([])
    vi.spyOn(api.recApi, 'list').mockResolvedValue({ items: [], ids: [] })

    const user = userEvent.setup()

    render(
      <MemoryRouter>
        <Animals user={{ id: 1, nome: 'Ana' }} />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Animais')).toBeInTheDocument()
    })

    await user.click(screen.getByLabelText(/espécie/i))

    expect(await screen.findByRole('option', { name: 'Cachorro' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Gato' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Todas' })).toBeInTheDocument()
  })
})
