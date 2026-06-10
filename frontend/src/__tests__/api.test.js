import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  apiGet,
  apiPost,
  apiPut,
  apiDel,
  authApi,
  perfilApi,
  animaisApi,
  recApi,
} from '../api'

function mockResponse({ ok = true, status = 200, json, text }) {
  return {
    ok,
    status,
    json: vi.fn().mockImplementation(async () => {
      if (json !== undefined) return json
      throw new Error('not json')
    }),
    text: vi.fn().mockResolvedValue(text ?? ''),
  }
}

describe('api.js', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('apiGet retorna JSON em sucesso', async () => {
    fetch.mockResolvedValue(mockResponse({ json: { ok: true } }))
    const data = await apiGet('/health')
    expect(data).toEqual({ ok: true })
    expect(fetch).toHaveBeenCalledWith(
      '/api/health',
      expect.objectContaining({ method: 'GET' })
    )
  })

  it('apiFetch envia Authorization quando há token', async () => {
    localStorage.setItem('access_token', 'tok123')
    fetch.mockResolvedValue(mockResponse({ json: { id: 1 } }))
    await apiGet('/auth/me')
    const [, opts] = fetch.mock.calls[0]
    expect(opts.headers.Authorization).toBe('Bearer tok123')
  })

  it('apiPost lança erro com mensagem da API', async () => {
    fetch.mockResolvedValue(
      mockResponse({ ok: false, status: 401, json: { error: 'Credenciais inválidas' } })
    )
    await expect(apiPost('/auth/login', { email: 'a', senha: 'b' })).rejects.toThrow(
      'Credenciais inválidas'
    )
  })

  it('apiFetch usa texto quando resposta não é JSON', async () => {
    fetch.mockResolvedValue(
      mockResponse({ ok: false, status: 500, json: undefined, text: 'server down' })
    )
    await expect(apiGet('/broken')).rejects.toThrow('server down')
  })

  it('apiFetch usa mensagem genérica quando json e text falham', async () => {
    fetch.mockResolvedValue({
      ok: false,
      status: 500,
      json: vi.fn().mockRejectedValue(new Error('bad json')),
      text: vi.fn().mockRejectedValue(new Error('bad text')),
    })
    await expect(apiGet('/broken')).rejects.toThrow('Erro 500')
  })

  it('authApi.me chama GET /auth/me', async () => {
    fetch.mockResolvedValue(mockResponse({ json: { user: { id: 1 } } }))
    const data = await authApi.me()
    expect(data.user.id).toBe(1)
    expect(fetch.mock.calls[0][0]).toContain('/auth/me')
  })

  it('authApi.login persiste token e usuário', async () => {
    fetch.mockResolvedValue(
      mockResponse({
        json: { access_token: 'jwt', user: { id: 1, nome: 'Ana' } },
      })
    )
    const data = await authApi.login('a@b.com', 'secret')
    expect(data.access_token).toBe('jwt')
    expect(localStorage.getItem('access_token')).toBe('jwt')
    expect(JSON.parse(localStorage.getItem('user'))).toEqual({ id: 1, nome: 'Ana' })
  })

  it('authApi.register persiste token', async () => {
    fetch.mockResolvedValue(mockResponse({ json: { access_token: 'reg-jwt' } }))
    await authApi.register('Ana', 'a@b.com', 'secret')
    expect(localStorage.getItem('access_token')).toBe('reg-jwt')
  })

  it('authApi.logout limpa storage e chama endpoint', async () => {
    localStorage.setItem('access_token', 'x')
    localStorage.setItem('user', '{}')
    fetch.mockResolvedValue(mockResponse({ json: {} }))
    authApi.logout()
    expect(localStorage.getItem('access_token')).toBeNull()
    expect(localStorage.getItem('user')).toBeNull()
    await vi.waitFor(() => expect(fetch).toHaveBeenCalled())
  })

  it('authApi.logout ignora falha do endpoint', async () => {
    localStorage.setItem('access_token', 'x')
    fetch.mockRejectedValue(new Error('offline'))
    authApi.logout()
    expect(localStorage.getItem('access_token')).toBeNull()
    await vi.waitFor(() => expect(fetch).toHaveBeenCalled())
  })

  it('authApi.loginWithGoogle redireciona para OAuth', () => {
    const original = window.location
    delete window.location
    window.location = { href: '' }
    authApi.loginWithGoogle('/perfil')
    expect(window.location.href).toBe('/api/auth/google?next=%2Fperfil')
    window.location = original
  })

  it('loginWithGoogle acrescenta /api quando VITE_API_URL é base customizada', async () => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8080')
    vi.resetModules()
    const { authApi: customAuth } = await import('../api')
    const original = window.location
    delete window.location
    window.location = { href: '' }
    customAuth.loginWithGoogle('/perfil')
    expect(window.location.href).toBe(
      'http://localhost:8080/api/auth/google?next=%2Fperfil'
    )
    window.location = original
  })

  it('animaisApi cobre CRUD e métricas', async () => {
    fetch
      .mockResolvedValueOnce(mockResponse({ json: [{ id: 1 }] }))
      .mockResolvedValueOnce(mockResponse({ json: [{ id: 2 }] }))
      .mockResolvedValueOnce(mockResponse({ json: { id: 3 } }))
      .mockResolvedValueOnce(mockResponse({ json: { id: 3, nome: 'Novo' } }))
      .mockResolvedValueOnce(mockResponse({ json: { ok: true } }))
      .mockResolvedValueOnce(mockResponse({ json: { ok: true } }))
      .mockResolvedValueOnce(mockResponse({ json: { ok: true } }))
      .mockResolvedValueOnce(mockResponse({ json: [{ day: '2026-01-01', cnt: 2 }] }))

    await animaisApi.list({ especie: 'Gato', vazio: '' })
    await animaisApi.mine()
    await animaisApi.get(3)
    await animaisApi.create({ nome: 'Novo' })
    await animaisApi.update(3, { nome: 'Novo' })
    await animaisApi.remove(3)
    await animaisApi.adopt(3, { action: 'mark' })
    const metrics = await animaisApi.adoptionMetrics(14)

    expect(fetch.mock.calls[0][0]).toContain('/animais?especie=Gato')
    expect(metrics[0].cnt).toBe(2)
  })

  it('perfilApi e recApi fazem GET/POST', async () => {
    fetch
      .mockResolvedValueOnce(mockResponse({ json: { tipo_moradia: 'Casa' } }))
      .mockResolvedValueOnce(mockResponse({ json: { ok: true } }))
      .mockResolvedValueOnce(mockResponse({ json: [{ id: 9 }] }))

    await perfilApi.get()
    await perfilApi.save({ tipo_moradia: 'Casa' })
    const recs = await recApi.list(5)

    expect(recs[0].id).toBe(9)
    expect(fetch.mock.calls[2][0]).toContain('/recomendacoes?n=5')
  })

  it('apiPut e apiDel usam métodos corretos', async () => {
    fetch
      .mockResolvedValueOnce(mockResponse({ json: { ok: true } }))
      .mockResolvedValueOnce(mockResponse({ json: { ok: true } }))
    await apiPut('/x', { a: 1 })
    await apiDel('/x')
    expect(fetch.mock.calls[0][1].method).toBe('PUT')
    expect(fetch.mock.calls[1][1].method).toBe('DELETE')
  })
})
