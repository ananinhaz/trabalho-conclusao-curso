// src/pages/Login.jsx
import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { authApi } from "../api.js";

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const next = params.get("next") || "/animais";

  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const resp = await authApi.login(email, senha);
      // authApi.login já grava access_token em localStorage
      if (resp && resp.access_token) {
        navigate(next, { replace: true });
      } else {
        // se backend respondeu sem token, mostra mensagem
        setError(resp?.error || "Erro no login. Tente novamente.");
      }
    } catch (err) {
      console.error("Login error:", err);
      setError(err.message || "Erro ao comunicar com a API");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-login">
      <h2>Entrar</h2>
      <form onSubmit={handleSubmit}>
        <label>
          E-mail
          <input
            type="email"
            value={email}
            onChange={(ev) => setEmail(ev.target.value)}
            required
            autoComplete="username"
          />
        </label>

        <label>
          Senha
          <input
            type="password"
            value={senha}
            onChange={(ev) => setSenha(ev.target.value)}
            required
            autoComplete="current-password"
          />
        </label>

        {error && <div style={{ color: "red", marginBottom: 8 }}>{error}</div>}

        <button type="submit" disabled={loading}>
          {loading ? "Entrando..." : "Entrar"}
        </button>
      </form>

      <hr />

      <div>
        <button
          onClick={() => {
            // inicia fluxo google (backend redireciona para FRONT/#token=...)
            authApi.loginWithGoogle(next);
          }}
        >
          Entrar com Google
        </button>
      </div>
    </div>
  );
}
