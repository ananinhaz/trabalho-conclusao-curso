// src/api.js
const API_BASE = '/api';

async function apiFetch(path, { method = 'GET', body, headers } = {}) {
  const res = await fetch(API_BASE + path, {
    method,
    credentials: 'include',          // <<< importante pro cookie da sessão
    headers: {
      'Content-Type': 'application/json',
      ...(headers || {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = data.error || data.message || `Erro ${res.status}`;
    throw new Error(msg);
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

// -------------------- AUTH --------------------
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
  // 👇 AGORA recebe o next e repassa pro Flask
  loginWithGoogle(nextPath) {
    const url =
      '/api/auth/login/google' +
      (nextPath ? `?next=${encodeURIComponent(nextPath)}` : '');
    window.location.href = url;
  },
};

// -------------------- PERFIL ADOTANTE --------------------
export const perfilApi = {
  get() {
    return apiGet('/perfil_adotante');
  },
  save(payload) {
    return apiPost('/perfil_adotante', payload);
  },
};

// -------------------- ANIMAIS --------------------
export const animaisApi = {
  list(params = {}) {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== '')
    ).toString();
    const suffix = qs ? `?${qs}` : '';
    return apiGet('/animais' + suffix);
  },
  mine() {
    return apiGet('/animais/mine');
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
};

// -------------------- RECOMENDAÇÕES --------------------
export const recApi = {
  list(n = 12) {
    return apiGet(`/recomendacoes?n=${n}`);
  },
};
