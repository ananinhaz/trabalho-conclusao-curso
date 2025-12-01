import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import * as api from "../api";

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
      const js = await api.authApi.login(email.trim().toLowerCase(), senha);
      // ...
    } catch (error) {
      console.error("login error", error);
      
      const errorMsg = error instanceof Error 
        ? error.message // Captura a mensagem de erro do mock
        : "Erro desconhecido.";
        
      if (errorMsg.includes("Credenciais inválidas")) {
          setMsg({ type: "error", text: "Email ou senha inválidos." });
      } else {
          setMsg({ type: "error", text: "Erro de rede ao tentar logar." });
      }

    } finally {
      setLoading(false);
    }
  }

  function loginWithGoogle() {
    api.authApi.loginWithGoogle(next);
  }

  function goToRegister() {
    navigate("/auth/register");
  }

  function goToRecover() {

    console.log("Navegar para recuperação de senha.");
  }

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Entrar</h1>

      <form onSubmit={handleSubmit} style={styles.form}>
        <label style={styles.label}>
          E-mail
          <input
            type="email"
            placeholder="seu@exemplo.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={styles.input}
            disabled={loading}
          />
        </label>
        <label style={styles.label}>
          Senha
          <input
            type="password"
            placeholder="••••••••"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            required
            style={styles.input}
            disabled={loading}
          />
        </label>
        <div style={{ marginTop: 10 }}>
          <button
            type="submit"
            style={styles.primaryButton}
            disabled={loading}
          >
            {loading ? "Entrando..." : "Entrar"}
          </button>
        </div>
      </form>

      <hr style={styles.separator} />

      <div style={styles.socialAuth}>
        <button
          onClick={loginWithGoogle}
          style={styles.secondaryButton}
          disabled={loading}
        >
          Entrar com Google
        </button>
        <div style={{ marginTop: 12 }}>
          <span>Não tem conta? </span>
          <button onClick={goToRegister} style={styles.linkButton} disabled={loading}>
            Criar conta
          </button>
        </div>
      </div>

      {msg && (
        <div
          role="alert"
          style={{
            ...styles.alert,
            color: msg.type === "error" ? "#7a1b1b" : "#1b7a1b",
            background: msg.type === "error" ? "#ffffee" : "#eefffe",
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
  secondaryButton: {
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
  separator: {
    margin: "20px 0",
    borderWidth: "1px 0 0 0",
    borderStyle: "solid",
    borderColor: "#eee",
  },
  socialAuth: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  alert: {
    marginTop: 16,
    padding: "10px 12px",
    borderRadius: 6,
  },
};