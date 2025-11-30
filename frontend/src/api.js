// src/api.js  (SUBSTITUA pelo conteúdo abaixo)
const API_BASE = import.meta.env.VITE_API_URL || '/api';

function joinUrl(base, path) {
  if (!base.endsWith('/') && !path.startsWith('/')) return base + '/' + path;
  if (base.endsWith('/') && path.startsWith('/')) return base.slice(0, -1) + path;
  return base + path;
}

async function apiFetch(path, { method = 'GET', body, headers } = {}) {
  const fetchUrl = API_BASE.endsWith('/') && path.startsWith('/')
    ? API_BASE.slice(0, -1) + path
    : API_BASE + path;

  // add Authorization header from localStorage (JWT)
  const token = localStorage.getItem('access_token');

  const finalHeaders = {
    'Content-Type': 'application/json',
    ...(headers || {}),
  };
  if (token) finalHeaders['Authorization'] = `Bearer ${token}`;

  const res = await fetch(fetchUrl, {
    method,
    // JWT in header -> we DO NOT use credentials include
    headers: finalHeaders,
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
    err.httpStatus = res.status;
    err.httpData = data;
    err.httpText = text;
    throw err;
  }
  return data;
}

export function apiGet(path) {
  return apiFetch(path);
}
export function apiPost(path, body) {
  return apiFetch(path, { method: 'POST', body });
}
export function apiPut(path, body) {
  return apiFetch(path, { method: 'PUT', body });
}
export function apiDel(path) {
  return apiFetch(path, { method: 'DELETE' });
}

// auth
export const authApi = {
  async me() {
    return apiGet('/auth/me');
  },
  // login: saves token if backend returns access_token
  async login(email, senha) {
    const data = await apiPost('/auth/login', { email, senha });
    if (data && data.access_token) {
      localStorage.setItem('access_token', data.access_token);
      if (data.user) localStorage.setItem('user', JSON.stringify(data.user));
    }
    return data;
  },
  async register(nome, email, senha) {
    const data = await apiPost('/auth/register', { nome, email, senha });
    if (data && data.access_token) {
      localStorage.setItem('access_token', data.access_token);
      if (data.user) localStorage.setItem('user', JSON.stringify(data.user));
    }
    return data;
  },
  logout() {
    // clear local session token (backend logout optional)
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    // if your backend still wants a logout endpoint you can call it:
    try {
      apiPost('/auth/logout', {}); // fire-and-forget
    } catch (e) {
      // ignore
    }
  },

  loginWithGoogle(nextPath) {
    // inicia o fluxo OAuth no backend; backend vai redirecionar para FRONT/#token=...
    // API_BASE pode ser '/api' (dev proxy) ou absolute URL
    const relativePath = '/auth/google';
    const isAbsolute = API_BASE.startsWith('http://') || API_BASE.startsWith('https://');

    let target;
    if (isAbsolute) {
      const baseNoSlash = API_BASE.endsWith('/') ? API_BASE.slice(0, -1) : API_BASE;
      target = baseNoSlash + relativePath;
    } else {
      // quando API_BASE é '/api' no dev, queremos '/api/auth/google'
      const baseNoSlash = API_BASE.endsWith('/') ? API_BASE.slice(0, -1) : API_BASE;
      target = baseNoSlash + relativePath;
    }

    if (nextPath) target += `?next=${encodeURIComponent(nextPath)}`;
    window.location.href = target;
  },
};

// perfil adotante
export const perfilApi = {
  get() {
    return apiGet('/perfil_adotante');
  },
  save(payload) {
    return apiPost('/perfil_adotante', payload);
  },
};

export const animaisApi = {
  list(params = {}) {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== '')
    ).toString();
    const suffix = qs ? `?${qs}` : '';
    return apiGet(`/animais${suffix}`);
  },
  mine() {
    return apiGet('/animais/mine');
  },
  get(id) {
    return apiGet(`/animais/${id}`);
  },
  create(payload) {
    return apiPost('/animais', payload);
  },
  update(id, payload) {
    return apiPut(`/animais/${id}`, payload);
  },
  remove(id) {
    return apiDel(`/animais/${id}`);
  },
  adopt(id, { action = 'mark' } = {}) {
    return apiFetch(`/animais/${id}/adopt`, { method: 'PATCH', body: { action } });
  },
  adoptionMetrics(days = 7) {
    return apiGet(`/animais/metrics/adoptions?days=${days}`);
  },
};

export const recApi = {
  list(n = 12) {
    return apiGet(`/recomendacoes?n=${n}`);
  },
};
