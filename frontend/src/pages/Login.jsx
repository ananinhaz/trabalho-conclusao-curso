import { useLocation, useNavigate } from "react-router-dom";
import { authApi } from "../api";
import {
  Box,
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Stack,
  Divider,
} from "@mui/material"; 

export default function Login() {
  const location = useLocation();
  const navigate = useNavigate();

  // Cores e Estilos Comuns a
  const primaryColor = "#6366F1"; 
  const primaryColorHover = "#4F46E5";
  const cardStyles = {
    borderRadius: "1.25rem",
    boxShadow: "0 15px 45px rgba(15, 23, 42, 0.12)",
  };

  // pega o ?next=/perfil-adotante
  const params = new URLSearchParams(location.search);
  const next = params.get("next") || "/animais";

    async function handleSubmit(e) {
    e.preventDefault();

    const formData = new FormData(e.currentTarget);
    const email = (formData.get("email") || "").toString().trim();
    const senha = (formData.get("senha") || "").toString().trim();

    if (!email || !senha) {
      alert("Preencha e-mail e senha.");
      return;
    }

    try {
      await authApi.login(email, senha);
      navigate(next, { replace: true });
    } catch (err) {
      alert(err.message || "Erro ao fazer login");
    }
  }

  function handleGoogle() {
    authApi.loginWithGoogle(next);
  }

  function handleRegister() {
    navigate(`/register?next=${encodeURIComponent(next)}`);
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
      <Paper sx={{ ...cardStyles, width: "100%", maxWidth: "420px", p: { xs: 3, sm: 4 } }}>
        <Typography variant="h5" sx={{ fontWeight: 600, color: "#0f172a", mb: 0.5 }}>
          Entrar
        </Typography>
        <Typography sx={{ color: "#64748b", fontSize: "0.85rem", mb: 2 }}>
          Acesse sua conta para adotar ou cadastrar um animal.
        </Typography>

        {/* botão google */}
        <Button
          onClick={handleGoogle}
          variant="outlined"
          sx={{
            width: "100%",
            borderColor: '#e2e8f0',
            color: '#0f172a',
            borderRadius: "0.6rem",
            py: 1,
            textTransform: 'none',
            '&:hover': {
                borderColor: '#cbd5e1'
            }
          }}
          startIcon={
            <Box component="span" sx={{ width: "1.5rem", height: "1.5rem", display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <svg
                    style={{ width: "1.4rem", height: "1.4rem" }}
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 48 48"
                >
                <path
                    fill="#FFC107"
                    d="M43.6 20.5H42V20H24v8h11.3C33.7 31.6 29.3 35 24 35 16.8 35 11 29.2 11 22S16.8 9 24 9c3.1 0 5.9 1.1 8.1 2.9l5.7-5.7C33.5 3.4 28.9 2 24 2 12.3 2 3 11.3 3 23s9.3 21 21 21c10.5 0 19.5-7.6 19.5-21 0-1.3-.1-2.2-.3-3.5z"
                />
                <path
                    fill="#FF3D00"
                    d="M6.3 14.7l6.6 4.8C14.4 16 18.8 13 24 13c3.1 0 5.9 1.1 8.1 2.9l5.7-5.7C33.5 3.4 28.9 2 24 2 16 2 9 6.5 6.3 14.7z"
                />
                <path
                    fill="#4CAF50"
                    d="M24 44c5.2 0 9.9-1.7 13.6-4.7l-6.3-5.3C29.2 35.2 26.7 36 24 36 18.7 36 14.3 32.7 12.7 28l-6.6 5.1C9 40.9 15.9 44 24 44z"
                />
                <path
                    fill="#1976D2"
                    d="M43.6 20.5H42V20H24v8h11.3c-.6 2.6-2.1 4.6-4.3 6l6.3 5.3C35.1 40.3 39 37 41.1 32.6c1.2-2.5 1.9-5.6 1.9-8.6 0-1.3-.1-2.2-.4-3.5z"
                />
                </svg>
            </Box>
          }
        >
          Entrar com Google
        </Button>

        <Divider sx={{ my: 2 }}>
            <Typography variant="caption" sx={{ color: "#94a3b8", textTransform: 'uppercase' }}>
                ou
            </Typography>
        </Divider>

        {/* formulário padrão */}
        <Box component="form" onSubmit={handleSubmit} sx={{ width: "100%" }}>
          <TextField
            name="email"
            label="E-mail"
            type="email"
            fullWidth
            margin="dense"
            size="small"
            sx={{ mb: 1.5 }}
          />
          <TextField
            name="senha"
            label="Senha"
            type="password"
            fullWidth
            margin="dense"
            size="small"
            sx={{ mb: 2 }}
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
              boxShadow: 'none'
            }}
          >
            Entrar
          </Button>
        </Box>

        <Typography sx={{ mt: 2, fontSize: "0.8rem", color: "#475569", textAlign: "center" }}>
          Não tem conta?{" "}
          <Button onClick={handleRegister} size="small" sx={{ color: primaryColor, textTransform: 'none', fontWeight: 600 }}>
            Cadastre-se
          </Button>
        </Typography>
      </Paper>
    </Box>
  );
}