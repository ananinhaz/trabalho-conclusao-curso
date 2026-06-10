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

  it('apiGet não envia Authorization quando não há token', async () => {
    fetch.mockResolvedValue(mockResponse({ json: {} }))
    await apiGet('/health')
    const [, opts] = fetch.mock.calls[0]
    expect(opts.headers.Authorization).toBeUndefined()
  })

  it('apiGet normaliza URL quando VITE_API_URL termina com barra', async () => {
    vi.stubEnv('VITE_API_URL', '/api/')
    vi.resetModules()
    const { apiGet: get } = await import('../api')
    fetch.mockResolvedValue(mockResponse({ json: { ok: true } }))
    await get('/health')
    expect(fetch.mock.calls[0][0]).toBe('/api/health')
  })

  it('apiDel não envia body na requisição', async () => {
    fetch.mockResolvedValue(mockResponse({ json: { ok: true } }))
    await apiDel('/recurso')
    const [, opts] = fetch.mock.calls[0]
    expect(opts.body).toBeUndefined()
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

  it('apiFetch usa campo message quando error ausente', async () => {
    fetch.mockResolvedValue(
      mockResponse({ ok: false, status: 400, json: { message: 'Pedido inválido' } })
    )
    await expect(apiGet('/broken')).rejects.toThrow('Pedido inválido')
  })

  it('apiFetch usa Erro status quando json falha e text é vazio', async () => {
    fetch.mockResolvedValue(
      mockResponse({ ok: false, status: 422, json: undefined, text: '' })
    )
    await expect(apiGet('/broken')).rejects.toThrow('Erro 422')
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

  it('authApi.login não persiste storage quando access_token ausente', async () => {
    fetch.mockResolvedValue(mockResponse({ json: { ok: true } }))
    await authApi.login('a@b.com', 'secret')
    expect(localStorage.getItem('access_token')).toBeNull()
    expect(localStorage.getItem('user')).toBeNull()
  })

  it('authApi.login persiste token sem usuário quando user ausente', async () => {
    fetch.mockResolvedValue(mockResponse({ json: { access_token: 'jwt-only' } }))
    await authApi.login('a@b.com', 'secret')
    expect(localStorage.getItem('access_token')).toBe('jwt-only')
    expect(localStorage.getItem('user')).toBeNull()
  })

  it('authApi.register persiste token', async () => {
    fetch.mockResolvedValue(mockResponse({ json: { access_token: 'reg-jwt' } }))
    await authApi.register('Ana', 'a@b.com', 'secret')
    expect(localStorage.getItem('access_token')).toBe('reg-jwt')
  })

  it('authApi.register persiste usuário quando retornado', async () => {
    fetch.mockResolvedValue(
      mockResponse({ json: { access_token: 'reg-jwt', user: { id: 2, nome: 'Bob' } } })
    )
    await authApi.register('Bob', 'b@b.com', 'secret')
    expect(JSON.parse(localStorage.getItem('user'))).toEqual({ id: 2, nome: 'Bob' })
  })

  it('authApi.register não persiste storage quando access_token ausente', async () => {
    fetch.mockResolvedValue(mockResponse({ json: { ok: true } }))
    await authApi.register('Ana', 'a@b.com', 'secret')
    expect(localStorage.getItem('access_token')).toBeNull()
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

  it('loginWithGoogle sem next omite query string', () => {
    const original = window.location
    delete window.location
    window.location = { href: '' }
    authApi.loginWithGoogle()
    expect(window.location.href).toBe('/api/auth/google')
    window.location = original
  })

  it('loginWithGoogle não duplica /api quando VITE_API_URL já é /api', async () => {
    vi.stubEnv('VITE_API_URL', '/api')
    vi.resetModules()
    const { authApi: customAuth } = await import('../api')
    const original = window.location
    delete window.location
    window.location = { href: '' }
    customAuth.loginWithGoogle('/dest')
    expect(window.location.href).toBe('/api/auth/google?next=%2Fdest')
    window.location = original
  })

  it('loginWithGoogle normaliza VITE_API_URL que termina com /api/', async () => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8080/api/')
    vi.resetModules()
    const { authApi: customAuth } = await import('../api')
    const original = window.location
    delete window.location
    window.location = { href: '' }
    customAuth.loginWithGoogle('/go')
    expect(window.location.href).toBe(
      'http://localhost:8080/api/auth/google?next=%2Fgo'
    )
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

  it('animaisApi.list sem parâmetros não adiciona query string', async () => {
    fetch.mockResolvedValue(mockResponse({ json: [] }))
    await animaisApi.list()
    expect(fetch.mock.calls[0][0]).toBe('/api/animais')
  })

  it('animaisApi.list ignora parâmetros vazios ou undefined', async () => {
    fetch.mockResolvedValue(mockResponse({ json: [] }))
    await animaisApi.list({ especie: '', porte: undefined })
    expect(fetch.mock.calls[0][0]).toBe('/api/animais')
  })

  it('recApi.list usa n padrão 12', async () => {
    fetch.mockResolvedValue(mockResponse({ json: [] }))
    await recApi.list()
    expect(fetch.mock.calls[0][0]).toContain('/recomendacoes?n=12')
  })

  it('animaisApi.adopt usa action padrão mark', async () => {
    fetch.mockResolvedValue(mockResponse({ json: { ok: true } }))
    await animaisApi.adopt(5)
    const [, opts] = fetch.mock.calls[0]
    expect(JSON.parse(opts.body)).toEqual({ action: 'mark' })
    expect(opts.method).toBe('PATCH')
  })

  it('animaisApi.adoptionMetrics usa days padrão 7', async () => {
    fetch.mockResolvedValue(mockResponse({ json: [] }))
    await animaisApi.adoptionMetrics()
    expect(fetch.mock.calls[0][0]).toContain('days=7')
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
