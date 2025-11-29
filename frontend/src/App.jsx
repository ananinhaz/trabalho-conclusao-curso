import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";

import Landing from "./pages/Landing.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import AdopterForm from "./pages/AdopterForm.jsx";
import Donate from "./pages/Donate.jsx";
import Animals from "./pages/Animals.jsx";
import AnimalEdit from "./pages/AnimalEdit.jsx";
import Profile from "./pages/Profile.jsx";
import ProfileEdit from "./pages/ProfileEdit";

import { authApi } from "./api.js";

// Hook auxiliar para capturar o token da URL APÓS o login com Google
const useTokenCapture = (setLogged, setLoading) => {
    const location = useLocation();

    useEffect(() => {
        const urlParams = new URLSearchParams(location.search);
        const token = urlParams.get('token');

        if (token) {
            console.log("Token JWT recebido da URL. Armazenando...");
            
            // 1. Armazena o token que veio do Backend
            localStorage.setItem('access_token', token);
            
            // 2. Limpa o token da URL para evitar problemas de segurança e repetição
            urlParams.delete('token');
            const newUrl = location.pathname + (urlParams.toString() ? '?' + urlParams.toString() : '');
            window.history.replaceState(null, '', newUrl);

            // 3. Força a verificação de autenticação (recarregando o estado)
            // Se o token foi capturado, tentamos re-verificar o estado de login
            authApi.me()
                .then(() => {
                    setLogged(true);
                })
                .catch(() => {
                    // Se falhar mesmo com o token (improvável), mantém deslogado
                    setLogged(false);
                })
                .finally(() => {
                    setLoading(false);
                });
        }
    }, [location.search, setLogged, setLoading]); 
};


// Rota privada
function PrivateRoute({ children }) {
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const [logged, setLogged] = useState(false);

  // 💡 NOVO: Captura o token JWT se ele estiver na URL (após login com Google)
  useTokenCapture(setLogged, setLoading);

  useEffect(() => {
    let alive = true;
    
    // Verifica se já há um token no localStorage antes de tentar a API
    if (!localStorage.getItem('access_token')) {
        setLogged(false);
        setLoading(false);
        return;
    }

    authApi
      .me()
      .then(() => {
        if (alive) setLogged(true);
      })
      .catch((err) => {
        if (alive) {
            console.error("Erro na verificação /me:", err);
            // Se falhar (token inválido/expirado), limpa o token local
            localStorage.removeItem('access_token');
            setLogged(false);
        }
      })
      .finally(() => {
        if (alive) setLoading(false);
      });

    return () => {
      alive = false;
    };
    // Adiciona o location.pathname para re-executar se o usuário navegar para uma rota privada.
  }, [location.pathname]); 

  if (loading) return <div>Carregando...</div>;

  if (!logged) {
    return (
      <Navigate
        to={`/login?next=${encodeURIComponent(location.pathname)}`}
        replace
      />
    );
  }

  return children;
}

// Rotas principais
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        path="/perfil-adotante"
        element={
          <PrivateRoute>
            <AdopterForm />
          </PrivateRoute>
        }
      />

      <Route
        path="/doar"
        element={
          <PrivateRoute>
            <Donate />
          </PrivateRoute>
        }
      />

      <Route
        path="/animais"
        element={
          <PrivateRoute>
            <Animals />
          </PrivateRoute>
        }
      />
      <Route
        path="/animais/editar/:id"
        element={
          <PrivateRoute>
            <AnimalEdit />
          </PrivateRoute>
        }
      />
      <Route
  path="/perfil"
  element={
    <PrivateRoute>
      <Profile />
    </PrivateRoute>
  }
/>
<Route path="/perfil/editar" element={<PrivateRoute><ProfileEdit /></PrivateRoute>} />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}