// frontend/src/api.js
// Ajuste: unificamos a chave do token para 'access_token' e incluímos handler para callback Google

const API_BASE = import.meta.env.VITE_API_URL || '/api';

// --- UNIFICADO: chave usada no localStorage (padronizamos para 'access_token') ---
const API_TOKEN_KEY = 'access_token'; // <- importante: deve bater com o que o App.jsx grava

// --- Gerenciamento de Token JWT ---
export function getToken() {
  return localStorage.getItem(API_TOKEN_KEY);
}

export function setToken(token) {
  if (token) {
    localStorage.setItem(API_TOKEN_KEY, token);
  } else {
    localStorage.removeItem(API_TOKEN_KEY);
  }
}

// Função para processar resposta de login/register que retorna access_token
function processJwtResponse(data) {
  if (data && data.ok && data.access_token) {
    setToken(data.access_token);
    return { ok: true, user: data.user, access_token: data.access_token };
  }
  return data;
}

// --- util de construção de URLs ---
function joinUrl(base, path) {
  if (!base.endsWith('/') && !path.startsWith('/')) return base + '/' + path;
  if (base.endsWith('/') && path.startsWith('/')) return base.slice(0, -1) + path;
  return base + path;
}

// --- fetch wrapper que injeta Authorization quando há token ---
async function apiFetch(path, { method = 'GET', body, headers } = {}) {
  const fetchUrl = joinUrl(API_BASE, path);
  const currentToken = getToken();

  const fetchHeaders = {
    'Content-Type': 'application/json',
    ...(headers || {}),
  };

  if (currentToken) {
    fetchHeaders['Authorization'] = `Bearer ${currentToken}`;
  }

  const res = await fetch(fetchUrl, {
    method,
    headers: fetchHeaders,
    body: body ? JSON.stringify(body) : undefined,
  });

  let data = {};
  let text = '';
  try {
    data = await res.json();
  } catch (e) {
    try {
      text = await res.text();
    } catch (e2) {
      text = '';
    }
  }

  if (!res.ok) {
    const msg = data?.error || data?.message || (text ? text : `Erro ${res.status}`);
    const err = new Error(msg);
    err.status = res.status;
    throw err;
  }

  return data;
}

// atalhos HTTP
export const apiGet = (path, config) => apiFetch(path, { ...config, method: 'GET' });
export const apiPost = (path, body, config) => apiFetch(path, { ...config, method: 'POST', body });
export const apiPut = (path, body, config) => apiFetch(path, { ...config, method: 'PUT', body });
export const apiDel = (path, config) => apiFetch(path, { ...config, method: 'DELETE' });

// --- Auth API ---
export const authApi = {
  async register(nome, email, senha) {
    const res = await apiPost('/auth/register', { nome, email, senha });
    return processJwtResponse(res);
  },

  async login(email, senha) {
    const res = await apiPost('/auth/login', { email, senha });
    return processJwtResponse(res);
  },

  async logout() {
    setToken(null);
    try { await apiPost('/auth/logout'); } catch(e){ /* ignore */ }
    return;
  },

  async me() {
    if (!getToken()) {
      return { authenticated: false };
    }
    const res = await apiGet('/auth/me');
    return res;
  },

  // Handler para o callback do Google: captura ?token=... da URL, armazena e redireciona
  handleGoogleCallback() {
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const token = urlParams.get('token');

      if (token) {
        setToken(token);
        urlParams.delete('token');

        const nextPath = urlParams.get('next') || '/animais';
        urlParams.delete('next');

        const newUrl = window.location.pathname + (urlParams.toString() ? `?${urlParams.toString()}` : '');

        // Limpa token da URL
        window.history.replaceState(null, '', newUrl);

        // Redireciona para o caminho desejado
        window.location.href = nextPath;

        return true;
      }
    } catch (e) {
      console.error('handleGoogleCallback error', e);
    }
    return false;
  },
};

// --- Outras APIs (exemplos) ---
export const perfilApi = {
  get() { return apiGet('/perfil_adotante'); },
  save(payload) { return apiPost('/perfil_adotante', payload); },
};

export const animaisApi = {
  list(params = {}) {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== '')
    ).toString();
    const suffix = qs ? `?${qs}` : '';
    return apiGet(`/animais${suffix}`);
  },
  mine() { return apiGet('/animais/mine'); },
  get(id) { return apiGet(`/animais/${id}`); },
  create(payload) { return apiPost('/animais', payload); },
  update(id, payload) { return apiPut(`/animais/${id}`, payload); },
  remove(id) { return apiDel(`/animais/${id}`); },
  adopt(id, { action = 'mark' } = {}) { return apiPost(`/animais/${id}/adotar`, { action }); },
};
