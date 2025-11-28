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

  const res = await fetch(fetchUrl, {
    method,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(headers || {}),
    },
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
  me() {
    return apiGet('/auth/me');
  },
  login(email, senha) {
    return apiPost('/auth/login', { email, senha });
  },
  register(nome, email, senha) {
    return apiPost('/auth/register', { nome, email, senha });
  },
  logout() {
    return apiPost('/auth/logout', {});
  },

  loginWithGoogle(nextPath) {
    // rota correta no backend: /auth/login/google
    const relativePath = '/auth/login/google';
    const isAbsolute = API_BASE.startsWith('http://') || API_BASE.startsWith('https://');

    let target;
    if (isAbsolute) {
      // API_BASE pode já conter '/api' ou o host completo
      const baseNoSlash = API_BASE.endsWith('/') ? API_BASE.slice(0, -1) : API_BASE;
      target = baseNoSlash + relativePath;
    } else {
      // em dev usando proxy /api -> backend; monta com /api prefix
      target = '/api' + relativePath;
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
