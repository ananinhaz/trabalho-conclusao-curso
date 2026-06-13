import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { vi, beforeEach } from 'vitest'

const mockGet = vi.fn()
const mockSave = vi.fn()

vi.mock('../../api', () => ({
  perfilApi: {
    get: (...args) => mockGet(...args),
    save: (...args) => mockSave(...args),
  },
}))

import AdopterForm from '../AdopterForm'

describe('AdopterForm (page)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockGet.mockResolvedValue({
      ok: true,
      perfil: {
        tipo_moradia: 'Apartamento',
        tem_criancas: 0,
        tempo_disponivel_horas_semana: 5,
        estilo_vida: 'Calmo',
      },
    })
    mockSave.mockResolvedValue({ ok: true })
  })

  it('carrega perfil existente e permite editar campos', async () => {
    render(
      <MemoryRouter>
        <AdopterForm />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(mockGet).toHaveBeenCalled()
    })

    expect(screen.getByLabelText(/Tipo de moradia/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Tempo disponível/i)).toHaveValue(5)
  })

  it('altera selects, tempo disponível e submete o formulário', async () => {
    const user = userEvent.setup()

    render(
      <MemoryRouter>
        <Routes>
          <Route path="/" element={<AdopterForm />} />
          <Route path="/animais" element={<div>Lista de animais</div>} />
        </Routes>
      </MemoryRouter>
    )

    await waitFor(() => expect(mockGet).toHaveBeenCalled())

    await user.click(screen.getByLabelText(/Tipo de moradia/i))
    await user.click(screen.getByRole('option', { name: 'Casa com quintal' }))

    await user.click(screen.getByLabelText(/Tem crianças em casa/i))
    await user.click(screen.getByRole('option', { name: 'Sim' }))

    await user.clear(screen.getByLabelText(/Tempo disponível/i))
    await user.type(screen.getByLabelText(/Tempo disponível/i), '20')

    await user.click(screen.getByLabelText(/Estilo de vida/i))
    await user.click(screen.getByRole('option', { name: 'Ativo' }))

    await user.click(screen.getByRole('button', { name: /Salvar perfil e ver animais/i }))

    await waitFor(() => {
      expect(mockSave).toHaveBeenCalledWith({
        tipo_moradia: 'Casa com quintal',
        tem_criancas: 1,
        tempo_disponivel_horas_semana: 20,
        estilo_vida: 'Ativo',
      })
      expect(screen.getByText(/Lista de animais/i)).toBeInTheDocument()
    })
  }, 10000)

  it('exibe erro quando save falha', async () => {
    mockSave.mockRejectedValueOnce(new Error('Falha ao salvar'))
    const user = userEvent.setup()

    render(
      <MemoryRouter>
        <AdopterForm />
      </MemoryRouter>
    )

    await waitFor(() => expect(mockGet).toHaveBeenCalled())

    await user.click(screen.getByLabelText(/Tipo de moradia/i))
    await user.click(screen.getByRole('option', { name: 'Apartamento' }))
    await user.click(screen.getByLabelText(/Estilo de vida/i))
    await user.click(screen.getByRole('option', { name: 'Moderado' }))
    await user.clear(screen.getByLabelText(/Tempo disponível/i))
    await user.type(screen.getByLabelText(/Tempo disponível/i), '10')

    await user.click(screen.getByRole('button', { name: /Salvar perfil e ver animais/i }))

    expect(await screen.findByText(/Falha ao salvar/i)).toBeInTheDocument()
  })

  it('ignora erro ao carregar perfil inexistente', async () => {
    mockGet.mockRejectedValueOnce(new Error('sem perfil'))

    render(
      <MemoryRouter>
        <AdopterForm />
      </MemoryRouter>
    )

    await waitFor(() => expect(mockGet).toHaveBeenCalled())
    expect(screen.getByRole('button', { name: /Salvar perfil e ver animais/i })).toBeInTheDocument()
  })

  it('exibe mensagem genérica quando save falha sem mensagem', async () => {
    mockSave.mockRejectedValueOnce({})
    const user = userEvent.setup()

    render(
      <MemoryRouter>
        <AdopterForm />
      </MemoryRouter>
    )

    await waitFor(() => expect(mockGet).toHaveBeenCalled())

    await user.click(screen.getByLabelText(/Tipo de moradia/i))
    await user.click(screen.getByRole('option', { name: 'Apartamento' }))
    await user.click(screen.getByLabelText(/Estilo de vida/i))
    await user.click(screen.getByRole('option', { name: 'Moderado' }))
    await user.clear(screen.getByLabelText(/Tempo disponível/i))
    await user.type(screen.getByLabelText(/Tempo disponível/i), '8')

    await user.click(screen.getByRole('button', { name: /Salvar perfil e ver animais/i }))

    expect(await screen.findByText(/Erro ao salvar/i)).toBeInTheDocument()
  })
})
