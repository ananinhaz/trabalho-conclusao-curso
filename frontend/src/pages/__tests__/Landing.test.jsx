import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'

vi.mock('../../api', () => ({
  animaisApi: {
    list: vi.fn(() =>
      Promise.resolve([
        {
          id: 1,
          nome: 'Luna',
          especie: 'Gato',
          descricao: 'Gata dócil',
          photo_url: 'https://example.com/luna.jpg',
        },
      ])
    ),
    adoptionMetrics: vi.fn(() => Promise.resolve({ days: [] })),
  },
}))

import Landing from '../Landing'

describe('Landing (page)', () => {
  it('renderiza texto principal da hero e botão Quero adotar', async () => {
    render(
      <MemoryRouter>
        <Landing />
      </MemoryRouter>
    )

    expect(screen.getByText(/encontrar um lar/i)).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getAllByRole('button', { name: /Quero adotar/i }).length).toBeGreaterThan(0)
    })
  })
})
