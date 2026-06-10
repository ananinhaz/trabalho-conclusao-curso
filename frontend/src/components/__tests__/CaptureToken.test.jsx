import { render, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import CaptureToken from '../CaptureToken'

const mockNavigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

const VALID_JWT = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIn0.abc'

describe('CaptureToken', () => {
  beforeEach(() => {
    localStorage.clear()
    mockNavigate.mockReset()
    window.history.replaceState = vi.fn()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('não faz nada quando não há hash', () => {
    window.location.hash = ''
    render(
      <MemoryRouter>
        <CaptureToken />
      </MemoryRouter>
    )
    expect(localStorage.getItem('access_token')).toBeNull()
    expect(mockNavigate).not.toHaveBeenCalled()
  })

  it('grava JWT válido, limpa hash e navega', async () => {
    window.location.hash = `#token=${VALID_JWT}&next=/perfil`
    render(
      <MemoryRouter>
        <CaptureToken />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(localStorage.getItem('access_token')).toBe(VALID_JWT)
      expect(mockNavigate).toHaveBeenCalledWith('/perfil')
      expect(window.history.replaceState).toHaveBeenCalled()
    })
  })

  it('ignora token inválido', async () => {
    window.location.hash = '#token=not-a-jwt&next=/animais'
    render(
      <MemoryRouter>
        <CaptureToken />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(localStorage.getItem('access_token')).toBeNull()
      expect(mockNavigate).not.toHaveBeenCalled()
    })
  })
})
