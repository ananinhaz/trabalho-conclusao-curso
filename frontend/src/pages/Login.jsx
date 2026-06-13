import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Stack,
  Divider,
  Alert,
} from "@mui/material";
import GoogleIcon from "@mui/icons-material/Google";
import * as api from "../api";
import { colors, shadows, cardSx, btnGradient, btnOutline, inputSx, radii } from "../theme";

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
      await api.authApi.login(email.trim().toLowerCase(), senha);
      navigate(next, { replace: true });
    } catch (error) {
      console.error("login error", error);

      const errorMsg = error instanceof Error
        ? error.message
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
    const qs = next && next !== "/" ? `?next=${encodeURIComponent(next)}` : "";
    navigate(`/register${qs}`);
  }

  function goToRecover() {
    console.log("Navegar para recuperação de senha.");
  }

  const fieldSx = {
    ...inputSx,
    "& .MuiInputBase-root": {
      borderRadius: radii.input,
      bgcolor: colors.background,
    },
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        bgcolor: colors.background,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        px: 2,
        py: 4,
      }}
    >
      <Paper
        elevation={0}
        sx={{
          ...cardSx,
          width: "100%",
          maxWidth: 500,
          borderRadius: "24px",
          boxShadow: shadows.card,
          p: { xs: 3, sm: 4 },
        }}
      >
        <Box sx={{ textAlign: "center", mb: 3 }}>
          <Typography
            variant="h4"
            component="h1"
            sx={{ fontWeight: 800, color: colors.text, mb: 1, fontSize: { xs: "1.75rem", sm: "2rem" } }}
          >
            Entrar
          </Typography>
          <Typography sx={{ color: colors.textMuted, fontSize: "0.95rem", lineHeight: 1.6 }}>
            Acesse sua conta para continuar ajudando animais a encontrarem um lar.
          </Typography>
        </Box>

        <Box component="form" onSubmit={handleSubmit}>
          <Stack spacing={2.5}>
            <TextField
              label="E-mail"
              type="email"
              placeholder="seu@exemplo.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              fullWidth
              disabled={loading}
              autoComplete="email"
              sx={fieldSx}
            />
            <TextField
              label="Senha"
              type="password"
              placeholder="••••••••"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              required
              fullWidth
              disabled={loading}
              autoComplete="current-password"
              sx={fieldSx}
            />

            <Button
              type="submit"
              variant="contained"
              fullWidth
              disabled={loading}
              sx={{ ...btnGradient, height: 48, fontSize: "1rem", mt: 0.5 }}
            >
              {loading ? "Entrando..." : "Entrar"}
            </Button>
          </Stack>
        </Box>

        <Divider sx={{ my: 3 }}>
          <Typography sx={{ color: colors.textMuted, fontSize: "0.85rem", fontWeight: 600, px: 1 }}>
            OU
          </Typography>
        </Divider>

        <Button
          variant="outlined"
          fullWidth
          onClick={loginWithGoogle}
          disabled={loading}
          startIcon={<GoogleIcon />}
          sx={{ ...btnOutline, height: 48, borderRadius: radii.button }}
        >
          Entrar com Google
        </Button>

        <Typography sx={{ textAlign: "center", mt: 3, color: colors.textMuted, fontSize: "0.9rem" }}>
          Não tem conta?{" "}
          <Button
            onClick={goToRegister}
            disabled={loading}
            sx={{
              textTransform: "none",
              fontWeight: 600,
              color: colors.primary,
              p: 0,
              minWidth: 0,
              verticalAlign: "baseline",
              "&:hover": { bgcolor: "transparent", textDecoration: "underline" },
            }}
          >
            Criar conta
          </Button>
        </Typography>

        {msg && (
          <Alert
            role="alert"
            severity={msg.type === "error" ? "error" : "success"}
            sx={{ mt: 2.5, borderRadius: radii.input }}
          >
            {msg.text}
          </Alert>
        )}
      </Paper>
    </Box>
  );
}
