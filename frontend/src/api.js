const API_BASE = import.meta.env.VITE_API_URL || '/api';


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

  // tenta json; se não for JSON, pega o text
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
    // monta mensagem completa para debugging (status + possible JSON error + raw text)
    const msg = data?.error || data?.message || (text ? text : `Erro ${res.status}`);
    const err = new Error(msg);
    // adiciona detalhes ao error object para inspeção no catch
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
  
    const isAbsoluteUrl = API_BASE.startsWith('http');
    
    let baseUrl = API_BASE;
    if (isAbsoluteUrl) {
        baseUrl = API_BASE.endsWith('/') ? API_BASE.slice(0, -1) : API_BASE;
    }

    const relativePath = '/auth/google/login'; // Rota no Flask
    
    const url = 
      (isAbsoluteUrl ? baseUrl + relativePath : '/api' + relativePath) +
      (nextPath ? `?next=${encodeURIComponent(nextPath)}` : '');
      
    window.location.href = url;
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

  // animais do usuário
  mine() {
    return apiGet('/animais/mine');
  },

  // detalhe do animal
  get(id) {
    return apiGet(`/animais/${id}`);
  },

  // criar novo
  create(payload) {
    return apiPost('/animais', payload);
  },

  // atualizar
  update(id, payload) {
    return apiPut(`/animais/${id}`, payload);
  },

  // remover
  remove(id) {
    return apiDel(`/animais/${id}`);
  },

  // marcar/desmarcar adotado patch
  adopt(id, { action = 'mark' } = {}) {
    return apiFetch(`/animais/${id}/adopt`, { method: 'PATCH', body: { action } });
  },

  // métricas 
  adoptionMetrics(days = 7) {
    return apiGet(`/animais/metrics/adoptions?days=${days}`);
  },
};

// recomendações
export const recApi = {
  list(n = 12) {
    return apiGet(`/recomendacoes?n=${n}`);
  },
};