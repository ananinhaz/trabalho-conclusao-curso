import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Login from '../Login'
import * as api from '../../api' 
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { vi } from 'vitest'

describe('Login (page)', () => {
  afterEach(() => {
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
    // botão de submit (exatamente "Entrar")
    const entrarBtn = screen.getByRole('button', { name: /^Entrar$/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(senhaInput, 'senha123')
    await user.click(entrarBtn)

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('test@example.com', 'senha123')
    })
  })

  test('quando authApi.login falha, mostra um alerta (ou lida com erro)', async () => {
    // mock para rejeitar
    vi.spyOn(api.authApi, 'login').mockRejectedValue(new Error('Credenciais inválidas'))

    // spy no alert ANTES de submeter
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})

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
      expect(alertSpy).toHaveBeenCalled()
    })

    alertSpy.mockRestore()
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

    const googleBtn = screen.getByRole('button', { name: /entrar com google/i })
    await user.click(googleBtn)

    await waitFor(() => {
      expect(mockGoogle).toHaveBeenCalledWith('/perfil-adotante')
    })
  })
})
