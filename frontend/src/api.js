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
        credentials: 'include', // ESSENCIAL para enviar cookies cross-site
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

    // 💡 MUDANÇA 2: Implementação do login com Google via Pop-up
    loginWithGoogle(nextPath) {
        // rota correta no backend: /auth/login/google
        const relativePath = '/auth/login/google';
        const baseNoSlash = API_BASE.endsWith('/') ? API_BASE.slice(0, -1) : API_BASE;
        let target = baseNoSlash + relativePath;

        if (nextPath) target += `?next=${encodeURIComponent(nextPath)}`;

        // 1. Abre o pop-up com a URL do backend
        const loginWindow = window.open(
            target,
            'googleLogin',
            'width=600,height=600,scrollbars=yes,resizable=yes'
        );

        // 2. Cria um intervalo para verificar se a janela foi fechada
        const checkLogin = setInterval(() => {
            if (!loginWindow || loginWindow.closed) {
                clearInterval(checkLogin);
                
                // 3. Ao fechar, recarrega a página de destino (Vercel)
                // Isso força o Frontend a fazer a requisição /auth/me usando o cookie recém-criado.
                if (nextPath) {
                    window.location.href = nextPath;
                } else {
                    window.location.reload();
                }
            }
        }, 500);
    },
};

// ... (Resto do api.js sem alteração)
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