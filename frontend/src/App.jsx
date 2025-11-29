// frontend/src/App.jsx
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
    // 1) tenta delegar para o handler central
    const handled = authApi.handleGoogleCallback();
    if (handled) {
      // O handler redireciona automaticamente para "next", então aqui normalmente não chega.
      return;
    }

    // 2) fallback — caso o token esteja na URL mas handler falhou (por algum motivo)
    const urlParams = new URLSearchParams(location.search);
    const token = urlParams.get('token');

    if (token) {
      console.log("Token JWT recebido da URL (fallback). Armazenando...");
      localStorage.setItem('access_token', token);
      urlParams.delete('token');
      const newUrl = location.pathname + (urlParams.toString() ? '?' + urlParams.toString() : '');
      window.history.replaceState(null, '', newUrl);

      authApi.me()
        .then(() => setLogged(true))
        .catch(() => setLogged(false))
        .finally(() => setLoading(false));
    }
  }, [location.search, setLogged, setLoading]);
};

// Rota privada
function PrivateRoute({ children }) {
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const [logged, setLogged] = useState(false);

  // tenta capturar token (se veio do Google)
  useTokenCapture(setLogged, setLoading);

  useEffect(() => {
    let alive = true;

    // Verifica token local primeiro
    if (!localStorage.getItem('access_token')) {
      setLogged(false);
      setLoading(false);
      return;
    }

    authApi.me()
      .then(() => { if (alive) setLogged(true); })
      .catch((err) => {
        if (alive) {
          console.error("Erro na verificação /me:", err);
          localStorage.removeItem('access_token');
          setLogged(false);
        }
      })
      .finally(() => { if (alive) setLoading(false); });

    return () => { alive = false; };
  }, [location.pathname]);

  if (loading) return <div>Carregando.</div>;

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
      <Route path="/perfil-adotante" element={<PrivateRoute><AdopterForm /></PrivateRoute>} />
      <Route path="/doar" element={<PrivateRoute><Donate /></PrivateRoute>} />
      <Route path="/animais" element={<PrivateRoute><Animals /></PrivateRoute>} />
      <Route path="/animais/editar/:id" element={<PrivateRoute><AnimalEdit /></PrivateRoute>} />
      <Route path="/perfil" element={<PrivateRoute><Profile /></PrivateRoute>} />
      <Route path="/perfil/editar" element={<PrivateRoute><ProfileEdit /></PrivateRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
