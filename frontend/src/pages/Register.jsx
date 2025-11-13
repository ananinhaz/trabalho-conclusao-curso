import { useState } from "react";
import {
  Alert,
  Box,
  Button,
  Container,
  Paper,
  TextField,
  Typography,
} from "@mui/material";
import { useNavigate, useLocation } from "react-router-dom";
import { authApi } from "../api";

export default function Register() {
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [msg, setMsg] = useState("");
  const [ok, setOk] = useState(false);

  const navigate = useNavigate();
  const location = useLocation();
  
  // Cores e Estilos Comuns
  const primaryColor = "#6366F1"; 
  const primaryColorHover = "#4F46E5";
  const cardStyles = {
    borderRadius: "1.25rem",
    boxShadow: "0 15px 45px rgba(15, 23, 42, 0.12)",
  };

  // pega o ?next=/perfil-adotante (ou /doar)
  const params = new URLSearchParams(location.search);
  const next = params.get("next") || "/animais";

  async function onSubmit(e) {
    e.preventDefault();
    setMsg("");
    setOk(false);

    try {
      // 1) cria o usuário
      await authApi.register(nome.trim(), email.trim(), senha);

      // 2) faz login automático
      await authApi.login(email.trim(), senha);

      setOk(true);

      // 3) vai para o fluxo que o usuário queria
      navigate(next, { replace: true });
    } catch (err) {
      setMsg(err.message || "Falha no cadastro");
    }
  }

  return (
    <Box
      sx={{
        minHeight: "100vh",
        background:
          "linear-gradient(135deg, #eff6ff 0%, #ffffff 40%, #eef2ff 100%)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        p: 3,
      }}
    >
      <Container maxWidth="sm">
        <Paper elevation={3} sx={{ ...cardStyles, p: 4 }}>
          <Typography variant="h5" sx={{ fontWeight: 600, color: "#0f172a", mb: 2 }} gutterBottom>
            Criar conta
          </Typography>
          <Box
            component="form"
            onSubmit={onSubmit}
            sx={{ display: "grid", gap: 2, mt: 1 }}
          >
            <TextField
              label="Nome"
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              required
              fullWidth
            />
            <TextField
              label="E-mail"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              fullWidth
            />
            <TextField
              label="Senha"
              type="password"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              required
              fullWidth
            />
            <Button
              type="submit"
              variant="contained"
              fullWidth
              sx={{
                background: primaryColor,
                py: 1.2,
                borderRadius: "0.5rem",
                textTransform: "none",
                fontWeight: 600,
                "&:hover": { background: primaryColorHover },
                mt: 1,
                boxShadow: 'none'
              }}
            >
              Cadastrar
            </Button>
          </Box>

          {msg && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {msg}
            </Alert>
          )}
          {ok && (
            <Alert severity="success" sx={{ mt: 2 }}>
              Conta criada! Redirecionando…
            </Alert>
          )}

          <Typography sx={{ mt: 3, fontSize: "0.8rem", color: "#475569", textAlign: "center" }}>
            Já tem conta?{" "}
            <Button
              onClick={() =>
                navigate(`/login?next=${encodeURIComponent(next)}`)
              }
              size="small"
              sx={{ color: primaryColor, textTransform: 'none', fontWeight: 600 }}
            >
              Entrar
            </Button>
          </Typography>
        </Paper>
      </Container>
    </Box>
  );
}