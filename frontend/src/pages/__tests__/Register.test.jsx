import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Register from '../Register'
import * as api from '../../api'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { vi } from 'vitest'

describe('Register (page)', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  test('submit com sucesso chama authApi.register e redireciona', async () => {
    const mockRegister = vi
      .spyOn(api.authApi, 'register')
      .mockResolvedValue({ access_token: 'tok', user: { id: 1 } })

    const user = userEvent.setup()

    render(
      <MemoryRouter initialEntries={['/auth/register?next=/animais']}>
        <Routes>
          <Route path="/auth/register" element={<Register />} />
          <Route path="/animais" element={<div>Animais page</div>} />
        </Routes>
      </MemoryRouter>
    )

    await user.type(screen.getByLabelText(/nome/i), 'Ana')
    await user.type(screen.getByLabelText(/e-?mail/i), 'ana@exemplo.com')
    await user.type(screen.getByLabelText(/senha/i), 'senha123')
    await user.click(screen.getByRole('button', { name: /^Criar conta$/i }))

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith('Ana', 'ana@exemplo.com', 'senha123')
    })
  })

  test('campos vazios mostram erro de validação', async () => {
    render(
      <MemoryRouter initialEntries={['/auth/register']}>
        <Routes>
          <Route path="/auth/register" element={<Register />} />
        </Routes>
      </MemoryRouter>
    )

    fireEvent.submit(screen.getByRole('button', { name: /^Criar conta$/i }).closest('form'))

    expect(await screen.findByText('Preencha todos os campos.')).toBeInTheDocument()
  })

  test('register sem access_token mostra erro da API', async () => {
    vi.spyOn(api.authApi, 'register').mockResolvedValue({ error: 'Email já existe' })

    const user = userEvent.setup()

    render(
      <MemoryRouter initialEntries={['/auth/register']}>
        <Routes>
          <Route path="/auth/register" element={<Register />} />
        </Routes>
      </MemoryRouter>
    )

    await user.type(screen.getByLabelText(/nome/i), 'Ana')
    await user.type(screen.getByLabelText(/e-?mail/i), 'dup@exemplo.com')
    await user.type(screen.getByLabelText(/senha/i), 'senha123')
    await user.click(screen.getByRole('button', { name: /^Criar conta$/i }))

    await waitFor(() => {
      expect(screen.getByText('Email já existe')).toBeInTheDocument()
    })
  })

  test('quando register falha mostra mensagem de erro', async () => {
    vi.spyOn(api.authApi, 'register').mockRejectedValue(new Error('Email já cadastrado'))

    const user = userEvent.setup()

    render(
      <MemoryRouter initialEntries={['/auth/register']}>
        <Routes>
          <Route path="/auth/register" element={<Register />} />
        </Routes>
      </MemoryRouter>
    )

    await user.type(screen.getByLabelText(/nome/i), 'Ana')
    await user.type(screen.getByLabelText(/e-?mail/i), 'dup@exemplo.com')
    await user.type(screen.getByLabelText(/senha/i), 'senha123')
    await user.click(screen.getByRole('button', { name: /^Criar conta$/i }))

    await waitFor(() => {
      expect(screen.getByText('Email já cadastrado')).toBeInTheDocument()
    })
  })

  test('botão Google chama loginWithGoogle com next', async () => {
    const mockGoogle = vi.spyOn(api.authApi, 'loginWithGoogle').mockImplementation(() => {})
    const user = userEvent.setup()

    render(
      <MemoryRouter initialEntries={['/auth/register?next=/perfil']}>
        <Routes>
          <Route path="/auth/register" element={<Register />} />
        </Routes>
      </MemoryRouter>
    )

    await user.click(screen.getByRole('button', { name: /Cadastrar com Google/i }))

    await waitFor(() => {
      expect(mockGoogle).toHaveBeenCalledWith('/perfil')
    })
  })
})
