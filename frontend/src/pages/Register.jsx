// src/pages/Register.jsx
import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { authApi } from "../api.js";

export default function Register() {
  const navigate = useNavigate();
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const next = params.get("next") || "/animais";

  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (!nome || !email || !senha) {
      setError("Preencha todos os campos.");
      return;
    }
    setLoading(true);
    try {
      const resp = await authApi.register(nome, email, senha);
      // authApi.register já salva access_token em localStorage (se retornado)
      if (resp && resp.access_token) {
        navigate(next, { replace: true });
      } else {
        setError(resp?.error || "Erro ao registrar. Tente novamente.");
      }
    } catch (err) {
      console.error("Register error:", err);
      setError(err.message || "Erro ao comunicar com a API");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-register">
      <h2>Cadastrar</h2>
      <form onSubmit={handleSubmit}>
        <label>
          Nome
          <input
            type="text"
            value={nome}
            onChange={(ev) => setNome(ev.target.value)}
            required
            autoComplete="name"
          />
        </label>

        <label>
          E-mail
          <input
            type="email"
            value={email}
            onChange={(ev) => setEmail(ev.target.value)}
            required
            autoComplete="email"
          />
        </label>

        <label>
          Senha
          <input
            type="password"
            value={senha}
            onChange={(ev) => setSenha(ev.target.value)}
            required
            autoComplete="new-password"
          />
        </label>

        {error && <div style={{ color: "red", marginBottom: 8 }}>{error}</div>}

        <button type="submit" disabled={loading}>
          {loading ? "Cadastrando..." : "Cadastrar"}
        </button>
      </form>

      <hr />

      <div>
        <button
          onClick={() => {
            authApi.loginWithGoogle(next);
          }}
        >
          Cadastrar com Google
        </button>
      </div>
    </div>
  );
}
