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

// rota privada
function PrivateRoute({ children }) {
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const [logged, setLogged] = useState(false);

  useEffect(() => {
    let alive = true;
    authApi
      .me()
      .then(() => {
        if (alive) setLogged(true);
      })
      .catch(() => {
        if (alive) setLogged(false);
      })
      .finally(() => {
        if (alive) setLoading(false);
      });

    return () => {
      alive = false;
    };
  }, []);

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
