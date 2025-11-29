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
// 🚨 ESTE HOOK NÃO É MAIS NECESSÁRIO! A lógica de Cookie HTTP-Only torna o token invisível ao JS.
// O 'api.js' corrigido já lida com o redirecionamento após o Google Callback.
// O AuthState será verificado pelo 'authApi.me()' logo abaixo.
// const useTokenCapture = (setLogged, setLoading) => { ... }


// Rota privada
function PrivateRoute({ children }) {
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const [logged, setLogged] = useState(false);

  // 🚨 REMOVIDO: useTokenCapture (pois o token está no Cookie HTTP-Only)

  useEffect(() => {
    let alive = true;
    
    // Com Cookie HTTP-Only, o único jeito de saber se o usuário está logado
    // é perguntando ao Backend via 'authApi.me()', que envia o Cookie automaticamente.
    authApi
      .me()
      .then(() => {
        if (alive) setLogged(true);
      })
      .catch((err) => {
        if (alive) {
            // O erro (status 401) significa que o Cookie não existe ou expirou/é inválido.
            // 🚨 REMOVIDO: localStorage.removeItem('access_token');
            console.error("Erro na verificação /me (Sessão inválida/expirada):", err);
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