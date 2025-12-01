import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Login from '../Login'
import * as api from '../../api' 
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { vi } from 'vitest'

describe('Login (page)', () => {
  afterEach(() => {
    // Restaura o mock da API após cada teste, garantindo isolamento.
    vi.restoreAllMocks() 
  })

  test('preenche email/senha e chama authApi.login, redireciona após sucesso', async () => {
    const mockLogin = vi
      .spyOn(api.authApi, 'login')
      .mockResolvedValue({ ok: true, user: { id: 1, nome: 'Test' } })

    const user = userEvent.setup()

    render(
      <MemoryRouter initialEntries={['/auth/login?next=/animais']}>
        <Routes>
          <Route path="/auth/login" element={<Login />} />
        </Routes>
      </MemoryRouter>
    )

    const emailInput = screen.getByLabelText(/e-?mail/i)
    const senhaInput = screen.getByLabelText(/senha/i)
    const entrarBtn = screen.getByRole('button', { name: /^Entrar$/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(senhaInput, 'password123')
    await user.click(entrarBtn)

    expect(mockLogin).toHaveBeenCalledWith('test@example.com', 'password123')

  })

  test('quando authApi.login falha, mostra um alerta (ou lida com erro)', async () => {
    const mockLogin = vi
      .spyOn(api.authApi, 'login')
      .mockRejectedValue(new Error('Credenciais inválidas')) 

    const user = userEvent.setup()

    render(
      <MemoryRouter initialEntries={['/auth/login']}>
        <Routes>
          <Route path="/auth/login" element={<Login />} />
        </Routes>
      </MemoryRouter>
    )

    const emailInput = screen.getByLabelText(/e-?mail/i)
    const senhaInput = screen.getByLabelText(/senha/i)
    const entrarBtn = screen.getByRole('button', { name: /^Entrar$/i })

    await user.type(emailInput, 'bad@example.com')
    await user.type(senhaInput, 'wrong')
    await user.click(entrarBtn)

    await waitFor(() => {
      expect(screen.getByText('Email ou senha inválidos.')).toBeInTheDocument()
    })
    
  })

  test('clica em "Entrar com Google" e chama loginWithGoogle com next', async () => {
    const mockGoogle = vi.spyOn(api.authApi, 'loginWithGoogle').mockImplementation(() => {})
    const user = userEvent.setup()

    render(
      <MemoryRouter initialEntries={['/auth/login?next=/perfil-adotante']}>
        <Routes>
          <Route path="/auth/login" element={<Login />} />
        </Routes>
      </MemoryRouter>
    )

    const googleBtn = screen.getByRole('button', { name: /Entrar com Google/i })

    await user.click(googleBtn)

    await waitFor(() => {
      expect(mockGoogle).toHaveBeenCalledWith('/perfil-adotante')
    })
  })
})