// src/App.jsx
import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";

import Landing from "./pages/Landing.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import AdopterForm from "./pages/AdopterForm.jsx";
import Donate from "./pages/Donate.jsx";
import Animals from "./pages/Animals.jsx";
// se não tiver Home, pode tirar
// import Home from "./pages/Home.jsx";

import { authApi } from "./api.js";

// guarda a rota e só libera depois de checar o backend
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

  // 👇 isso aqui impede o “pisca e volta”
  if (loading) {
    return <div>Carregando...</div>;
  }

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

export default function App() {
  return (
    <Routes>
      {/* públicas */}
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* protegidas */}
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

      {/* se tiver home:
      <Route
        path="/home"
        element={
          <PrivateRoute>
            <Home />
          </PrivateRoute>
        }
      /> */}

      {/* fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
