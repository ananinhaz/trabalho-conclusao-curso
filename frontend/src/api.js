const API_BASE = import.meta.env.VITE_API_URL || '/api';

// --- Funções Auxiliares de Fetch ---

function joinUrl(base, path) {
    if (!base.endsWith('/') && !path.startsWith('/')) return base + '/' + path;
    if (base.endsWith('/') && path.startsWith('/')) return base.slice(0, -1) + path;
    return base + path;
}

/**
 * Função genérica para chamadas de API.
 * Usa credentials: 'include' para garantir que os cookies JWT (HTTP-Only) sejam enviados.
 */
async function apiFetch(path, { method = 'GET', body, headers } = {}) {
    const fetchUrl = joinUrl(API_BASE, path);

    const fetchHeaders = {
        'Content-Type': 'application/json',
        ...(headers || {}),
    };
    
    // 💡 CRÍTICO: 'include' é ESSENCIAL para que o navegador envie o Cookie HTTP-Only
    const res = await fetch(fetchUrl, {
        method,
        credentials: 'include', 
        headers: fetchHeaders,
        body: body ? JSON.stringify(body) : undefined,
    });

    let data = {};
    let text = '';
    // Tenta ler o JSON; se falhar, tenta ler o texto para melhor feedback de erro
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
        // Lança um erro se a resposta HTTP não for 2xx
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
    // Estas chamadas agora dependem do Backend definir o Cookie HTTP-Only na resposta
    async register(nome, email, senha) {
        // A resposta define o cookie de autenticação
        return apiPost('/auth/register', { nome, email, senha });
    },

    async login(email, senha) {
        // A resposta define o cookie de autenticação
        return apiPost('/auth/login', { email, senha });
    },

    // A rota de logout fará com que o Backend remova o cookie de sessão
    async logout() {
        return apiPost('/auth/logout'); 
    },

    async me() {
        // O Cookie é enviado automaticamente aqui; se for válido, a rota retorna os dados do usuário
        // Se o Cookie for inválido/expirado, apiGet lançará um erro 401 que será tratado no seu hook useAuth
        return apiGet('/auth/me');
    },
    
    /**
     * Lida com o redirecionamento após o login via Google.
     * O Backend já definiu o Cookie JWT, então só precisamos limpar a URL e redirecionar.
     */
    handleGoogleCallback() {
        const urlParams = new URLSearchParams(window.location.search);
        
        // O Render não retorna mais 'token' na URL, o token é definido via Cookie.
        // O Backend pode ter enviado o destino em 'next'
        const nextPath = urlParams.get('next') || '/animais';
        urlParams.delete('next');
        
        // Limpa quaisquer parâmetros de erro ou temporários (como 'token' antigo) da URL
        const newUrl = window.location.pathname + (urlParams.toString() ? `?${urlParams.toString()}` : '');
        window.history.replaceState(null, '', newUrl);

        // O usuário já está autenticado (o cookie foi definido no redirecionamento do Backend)
        // Redireciona para a página de destino
        window.location.href = nextPath;
        
        return true; 
    }
};

// --- Outras APIs ---

export const perfilApi = {
    get() {
        // Requer Cookie JWT
        return apiGet('/perfil_adotante');
    },
    save(payload) {
        // Requer Cookie JWT
        return apiPost('/perfil_adotante', payload);
    },
};

export const animaisApi = {
    list(params = {}) {
        const qs = new URLSearchParams(
            Object.entries(params).filter(([, v]) => v !== undefined && v !== '')
        ).toString();
        const suffix = qs ? `?${qs}` : '';
        // Requer Cookie JWT (se estiver autenticado)
        return apiGet(`/animais${suffix}`);
    },
    mine() {
        // Requer Cookie JWT
        return apiGet('/animais/mine');
    },
    get(id) {
        // Requer Cookie JWT (se estiver autenticado)
        return apiGet(`/animais/${id}`);
    },
    create(payload) {
        // Requer Cookie JWT
        return apiPost('/animais', payload);
    },
    update(id, payload) {
        // Requer Cookie JWT
        return apiPut(`/animais/${id}`, payload);
    },
    remove(id) {
        // Requer Cookie JWT
        return apiDel(`/animais/${id}`);
    },
    adopt(id, { action = 'mark' } = {}) {
        // Requer Cookie JWT
        return apiPost(`/animais/${id}/adotar`, { action });
    },
};