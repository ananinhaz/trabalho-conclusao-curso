import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { vi, beforeEach } from 'vitest'

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
        {
          id: 2,
          nome: 'Thor',
          especie: 'Cachorro',
          descricao: 'Cão energético',
          photo_url: 'https://example.com/thor.jpg',
        },
      ])
    ),
    adoptionMetrics: vi.fn(() => Promise.resolve({ days: [] })),
  },
}))

vi.mock('@nivo/line', () => ({
  ResponsiveLine: () => <div data-testid="adoption-chart-mock" />,
}))

import Landing from '../Landing'
import * as api from '../../api'

const defaultAnimals = [
  {
    id: 1,
    nome: 'Luna',
    especie: 'Gato',
    descricao: 'Gata dócil',
    photo_url: 'https://example.com/luna.jpg',
  },
  {
    id: 2,
    nome: 'Thor',
    especie: 'Cachorro',
    descricao: 'Cão energético',
    photo_url: 'https://example.com/thor.jpg',
  },
]

describe('Landing (page)', () => {
  beforeEach(() => {
    api.animaisApi.list.mockReset()
    api.animaisApi.list.mockImplementation(() => Promise.resolve(defaultAnimals))
    api.animaisApi.adoptionMetrics.mockReset()
    api.animaisApi.adoptionMetrics.mockImplementation(() => Promise.resolve({ days: [] }))
  })

  it('navega para login ao clicar em Quero adotar', async () => {
    const user = userEvent.setup()

    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<div>Tela de login</div>} />
        </Routes>
      </MemoryRouter>
    )

    expect(screen.getByText(/encontrar um lar/i)).toBeInTheDocument()

    const adotarButtons = await screen.findAllByRole('button', { name: /Quero adotar/i })
    await user.click(adotarButtons[0])

    await waitFor(() => {
      expect(screen.getByText(/Tela de login/i)).toBeInTheDocument()
    })
  })

  it('navega para login ao clicar em Quero doar', async () => {
    const user = userEvent.setup()

    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<div>Tela de login</div>} />
        </Routes>
      </MemoryRouter>
    )

    const doarButtons = await screen.findAllByRole('button', { name: /Quero doar/i })
    await user.click(doarButtons[0])

    await waitFor(() => {
      expect(screen.getByText(/Tela de login/i)).toBeInTheDocument()
    })
  })

  it('renderiza carrossel com primeiro pet e navega para o próximo', async () => {
    const user = userEvent.setup()

    const { container } = render(
      <MemoryRouter>
        <Landing />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Luna/i)).toBeInTheDocument()
      expect(screen.getByText(/Gato em destaque/i)).toBeInTheDocument()
    })

    const hero = container.querySelector('img[alt="Luna"]')?.closest('div')?.parentElement?.parentElement
    const heroSection = container.querySelector('img[alt="Luna"]')?.closest('[class*="MuiBox"]')?.parentElement
    const iconButtons = container.querySelectorAll('.MuiIconButton-root')
    expect(iconButtons.length).toBeGreaterThanOrEqual(2)

    await user.click(iconButtons[1])

    await waitFor(() => {
      expect(screen.getByText(/Thor/i)).toBeInTheDocument()
      expect(screen.getByText(/Cachorro em destaque/i)).toBeInTheDocument()
    })

    await user.click(iconButtons[0])

    await waitFor(() => {
      expect(screen.getByText(/Luna/i)).toBeInTheDocument()
    })
  })

  it('exibe seção informativa após carregar dados', async () => {
    render(
      <MemoryRouter>
        <Landing />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Por que adotar com responsabilidade/i)).toBeInTheDocument()
      expect(screen.getByText(/Adoção consciente/i)).toBeInTheDocument()
    })
  })

  it('navega carrossel pelos indicadores (dots)', async () => {
    const user = userEvent.setup()

    render(
      <MemoryRouter>
        <Landing />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Luna/i)).toBeInTheDocument()
      expect(screen.getByText(/Gato em destaque/i)).toBeInTheDocument()
    })

    const dotButtons = (await screen.findAllByRole('button')).filter(
      (btn) => !btn.textContent?.trim() && !btn.className.includes('MuiIconButton')
    )
    expect(dotButtons.length).toBeGreaterThanOrEqual(2)

    await user.click(dotButtons[1])

    await waitFor(() => {
      expect(screen.getByText(/Cachorro em destaque/i)).toBeInTheDocument()
    })
  })

  it('usa fallback estático quando API retorna lista vazia', async () => {
    api.animaisApi.list.mockImplementation(() => Promise.resolve([]))

    render(
      <MemoryRouter>
        <Landing />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Mascote/i)).toBeInTheDocument()
      expect(screen.getByText(/Cachorro em destaque/i)).toBeInTheDocument()
    })
  })

  it('usa fallback quando API falha', async () => {
    api.animaisApi.list.mockImplementation(() => Promise.reject(new Error('offline')))

    render(
      <MemoryRouter>
        <Landing />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Mascote/i)).toBeInTheDocument()
    })
  })
})
