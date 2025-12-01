// src/pages/Login.jsx
import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const initialNext = params.get("next") || "/perfil-adotante";

  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [next, setNext] = useState(initialNext);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState(null);

  useEffect(() => setNext(initialNext), [initialNext]);

  async function handleSubmit(e) {
    e.preventDefault();
    setMsg(null);
    if (!email || !senha) {
      setMsg({ type: "error", text: "Preencha email e senha." });
      return;
    }
    setLoading(true);

    try {
      const API = import.meta.env.VITE_API_URL || "";
      const url = API.replace(/\/$/, "") + "/auth/login";

      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim().toLowerCase(), senha }),
      });

      const js = await res.json().catch(() => null);

      if (!res.ok || !js) {
        const errText = js && js.error ? js.error : `Erro ${res.status}`;
        setMsg({ type: "error", text: `Falha ao logar: ${errText}` });
        setLoading(false);
        return;
      }

      if (js.ok && js.access_token) {
        localStorage.setItem("access_token", js.access_token);
        setMsg({ type: "success", text: "Login realizado. Redirecionando..." });
        setTimeout(() => {
          window.location.href = next || "/perfil-adotante";
        }, 400);
      } else {
        setMsg({ type: "error", text: js.error || "Resposta inesperada do servidor." });
      }
    } catch (err) {
      console.error("login error", err);
      setMsg({ type: "error", text: "Erro de rede ao tentar logar." });
    } finally {
      setLoading(false);
    }
  }

  function goToRegister() {
    const target = `/register?next=${encodeURIComponent(next || "/perfil-adotante")}`;
    navigate(target);
  }

  function loginWithGoogle() {
    const API = import.meta.env.VITE_API_URL || "";
    window.location.href = API.replace(/\/$/, "") + "/auth/google?next=" + encodeURIComponent(next || "/perfil-adotante");
  }

  return (


    <div style={styles.container}>
      <h1 style={styles.title}>Entrar</h1>

      <form onSubmit={handleSubmit} style={styles.form}>
        <label style={styles.label}>
          E-mail
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={styles.input}
            placeholder="seu@exemplo.com"
            required
          />
        </label>

        <label style={styles.label}>
          Senha
          <input
            type="password"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            style={styles.input}
            placeholder="••••••••"
            required
          />
        </label>

        <div style={{ marginTop: 10 }}>
          <button type="submit" disabled={loading} style={styles.primaryButton}>
            {loading ? "Entrando..." : "Entrar"}
          </button>
        </div>
      </form>

      <hr style={styles.hr} />

      <div style={styles.actions}>
        <button onClick={loginWithGoogle} style={styles.ghostButton}>
          Entrar com Google
        </button>

        <div style={{ marginTop: 12 }}>
          <span>Não tem conta? </span>
          <button onClick={goToRegister} style={styles.linkButton}>
            Criar conta
          </button>
        </div>
      </div>

      {msg && (
        <div
          role="alert"
          style={{
            marginTop: 16,
            padding: "10px 12px",
            borderRadius: 6,
            color: msg.type === "error" ? "#7a1b1b" : "#084d07",
            background: msg.type === "error" ? "#fee" : "#eefbe9",
            border: `1px solid ${msg.type === "error" ? "#f5c2c2" : "#cde8c9"}`,
          }}
        >
          {msg.text}
        </div>
      )}
    </div>
  );
}

const styles = {
  container: {
    maxWidth: 760,
    margin: "24px auto",
    padding: 18,
    fontFamily: "Inter, Roboto, Arial, sans-serif",
  },
  title: {
    margin: "0 0 12px 0",
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: 10,
  },
  label: {
    display: "flex",
    flexDirection: "column",
    fontSize: 14,
  },
  input: {
    marginTop: 6,
    padding: "8px 10px",
    fontSize: 14,
    borderRadius: 6,
    border: "1px solid #ccc",
    width: "100%",
    boxSizing: "border-box",
  },
  primaryButton: {
    padding: "8px 14px",
    borderRadius: 6,
    border: "none",
    background: "#6b5cff",
    color: "#fff",
    cursor: "pointer",
    fontSize: 14,
  },
  ghostButton: {
    padding: "8px 14px",
    borderRadius: 6,
    border: "1px solid #6b5cff",
    background: "#fff",
    color: "#6b5cff",
    cursor: "pointer",
    fontSize: 14,
  },
  linkButton: {
    marginLeft: 6,
    background: "none",
    border: "none",
    color: "#6b5cff",
    textDecoration: "underline",
    cursor: "pointer",
    fontSize: 14,
  },
  hr: {
    margin: "20px 0",
    border: "none",
    borderTop: "1px solid #eee",
  },
  actions: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
};
