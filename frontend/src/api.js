const API_BASE = import.meta.env.VITE_API_URL || '/api';

function joinUrl(base, path) {
    if (!base.endsWith('/') && !path.startsWith('/')) return base + '/' + path;
    if (base.endsWith('/') && path.startsWith('/')) return base.slice(0, -1) + path;
    return base + path;
}

async function apiFetch(path, { method = 'GET', body, headers } = {}) {
    // 💡 NOVO: Pega o token do LocalStorage
    const token = localStorage.getItem('access_token');

    const fetchUrl = API_BASE.endsWith('/') && path.startsWith('/')
        ? API_BASE.slice(0, -1) + path
        : API_BASE + path;

    const res = await fetch(fetchUrl, {
        method,
        // ❌ REMOVER: credentials: 'include', 
        
        headers: {
            'Content-Type': 'application/json',
            ...(headers || {}),
            // 💡 CRÍTICO: Envia o token de acesso no formato Bearer (se existir)
            ...(token && { 'Authorization': `Bearer ${token}` }), 
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

    // 💡 NOVO: Adiciona a verificação de 401 para forçar o logout (token expirado)
    if (res.status === 401 && path !== '/auth/login' && path !== '/auth/me') { 
         authApi.forceLogout();
    }

    if (!res.ok) {
        const msg = data?.error || data?.message || (text ? text : `Erro ${res.status}`);
        const err = new Error(msg);
        err.httpStatus = res.status;
        err.httpData = data;
        err.httpText = text;
        throw err;
    }
    
    // 💡 MUDANÇA: Para login e register, o body agora contém o token
    if (path === '/auth/login' || path === '/auth/register') {
        if (data.access_token) {
            localStorage.setItem('access_token', data.access_token);
        }
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
        // A lógica de armazenamento de token foi movida para apiFetch, mas 
        // a função ainda pode retornar o 'user' para manter a interface consistente.
        return apiPost('/auth/login', { email, senha }).then(data => data.user);
    },
    register(nome, email, senha) {
        // A lógica de armazenamento de token foi movida para apiFetch.
        return apiPost('/auth/register', { nome, email, senha }).then(data => data.user);
    },
    logout() {
        // 💡 MUDANÇA: Logout limpa o token no cliente
        localStorage.removeItem('access_token');
        // Chama o endpoint do backend (que agora é no-op, mas mantém o padrão)
        return apiPost('/auth/logout', {}); 
    },
    
    // 💡 NOVO: Função de logout forçado (se o token expirar, por exemplo)
    forceLogout() {
        localStorage.removeItem('access_token');
        // Opcional: Redireciona para o login
        window.location.href = '/login'; 
    },


    loginWithGoogle(nextPath) {
        // 💡 MUDANÇA: Retorna ao redirecionamento, removendo o pop-up
        const relativePath = '/auth/login/google';
        const isAbsolute = API_BASE.startsWith('http://') || API_BASE.startsWith('https://');

        let target;
        if (isAbsolute) {
            const baseNoSlash = API_BASE.endsWith('/') ? API_BASE.slice(0, -1) : API_BASE;
            target = baseNoSlash + relativePath;
        } else {
            target = '/api' + relativePath;
        }

        if (nextPath) target += `?next=${encodeURIComponent(nextPath)}`;

        // 💡 CRÍTICO: Redireciona na mesma janela
        window.location.href = target;
    },
};

// ... (Resto do api.js sem alteração)
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