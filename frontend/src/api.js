const API_BASE = import.meta.env.VITE_API_URL || '/api';
const API_TOKEN_KEY = 'adopt_me_jwt_token'; // Chave para armazenar o token

// --- Gerenciamento de Token JWT ---

function getToken() {
    return localStorage.getItem(API_TOKEN_KEY);
}

function setToken(token) {
    if (token) {
        // Salva o token
        localStorage.setItem(API_TOKEN_KEY, token);
    } else {
        // Remove o token (logout)
        localStorage.removeItem(API_TOKEN_KEY);
    }
}

// Função auxiliar para processar a resposta do Backend (login/register)
function processJwtResponse(data) {
    if (data.ok && data.access_token) {
        setToken(data.access_token);
        return { ok: true, user: data.user, access_token: data.access_token };
    }
    return data;
}

// --- Funções Auxiliares de Fetch ---

function joinUrl(base, path) {
    if (!base.endsWith('/') && !path.startsWith('/')) return base + '/' + path;
    if (base.endsWith('/') && path.startsWith('/')) return base.slice(0, -1) + path;
    return base + path;
}

async function apiFetch(path, { method = 'GET', body, headers } = {}) {
    const fetchUrl = joinUrl(API_BASE, path);
    const currentToken = getToken();

    const fetchHeaders = {
        'Content-Type': 'application/json',
        ...(headers || {}),
    };
    
    // 💡 CRÍTICO: Adiciona o token JWT no cabeçalho 'Authorization'
    if (currentToken) {
        fetchHeaders['Authorization'] = `Bearer ${currentToken}`;
    }

    const res = await fetch(fetchUrl, {
        method,
        // credentials: 'include' REMOVIDO (não usamos mais cookies de sessão)
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

// Funções de atalho para métodos HTTP
const apiGet = (path, config) => apiFetch(path, { ...config, method: 'GET' });
const apiPost = (path, body, config) => apiFetch(path, { ...config, method: 'POST', body });
const apiPut = (path, body, config) => apiFetch(path, { ...config, method: 'PUT', body });
const apiDel = (path, config) => apiFetch(path, { ...config, method: 'DELETE' });


// --- API de Autenticação (authApi) ---

export const authApi = {
    // Salva o token
    async register(nome, email, senha) {
        const res = await apiPost('/auth/register', { nome, email, senha });
        return processJwtResponse(res);
    },

    // Salva o token
    async login(email, senha) {
        const res = await apiPost('/auth/login', { email, senha });
        return processJwtResponse(res);
    },

    // Limpa o token localmente
    async logout() {
        setToken(null);
        return apiPost('/auth/logout'); 
    },

    async me() {
        // Se não houver token, retorna que não está autenticado imediatamente
        if (!getToken()) {
            return { authenticated: false };
        }
        
        // A apiFetch inclui o Authorization header
        const res = await apiGet('/auth/me');
        return res;
    },
    
    // CRÍTICO para Login com Google
    handleGoogleCallback() {
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');
        
        if (token) {
            setToken(token);
            urlParams.delete('token');
            
            const nextPath = urlParams.get('next') || '/animais';
            urlParams.delete('next');
            
            const newUrl = window.location.pathname + (urlParams.toString() ? `?${urlParams.toString()}` : '');
            
            // Substitui a URL no histórico (limpando o token)
            window.history.replaceState(null, '', newUrl);

            // Redireciona para o `next`
            window.location.href = nextPath;
            
            return true;
        }
        
        return false;
    }
};

// --- Outras APIs ---

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
        return apiPost(`/animais/${id}/adotar`, { action });
    },
};