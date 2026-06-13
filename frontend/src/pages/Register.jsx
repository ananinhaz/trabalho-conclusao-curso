import { useState } from "react";
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
import { authApi } from "../api.js";
import { colors, shadows, cardSx, btnGradient, btnOutline, inputSx, radii } from "../theme";

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

  function goToLogin() {
    const qs = next && next !== "/" ? `?next=${encodeURIComponent(next)}` : "";
    navigate(`/login${qs}`);
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
            Criar conta
          </Typography>
          <Typography sx={{ color: colors.textMuted, fontSize: "0.95rem", lineHeight: 1.6 }}>
            Cadastre-se e comece a usar a plataforma AdoptMe.
          </Typography>
        </Box>

        <Box component="form" onSubmit={handleSubmit}>
          <Stack spacing={2.5}>
            <TextField
              label="Nome"
              type="text"
              value={nome}
              onChange={(ev) => setNome(ev.target.value)}
              required
              fullWidth
              disabled={loading}
              autoComplete="name"
              sx={fieldSx}
            />
            <TextField
              label="E-mail"
              type="email"
              value={email}
              onChange={(ev) => setEmail(ev.target.value)}
              required
              fullWidth
              disabled={loading}
              autoComplete="email"
              sx={fieldSx}
            />
            <TextField
              label="Senha"
              type="password"
              value={senha}
              onChange={(ev) => setSenha(ev.target.value)}
              required
              fullWidth
              disabled={loading}
              autoComplete="new-password"
              sx={fieldSx}
            />

            {error && (
              <Alert severity="error" sx={{ borderRadius: radii.input }}>
                {error}
              </Alert>
            )}

            <Button
              type="submit"
              variant="contained"
              fullWidth
              disabled={loading}
              sx={{ ...btnGradient, height: 48, fontSize: "1rem", mt: 0.5 }}
            >
              {loading ? "Criando conta..." : "Criar conta"}
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
          onClick={() => authApi.loginWithGoogle(next)}
          disabled={loading}
          startIcon={<GoogleIcon />}
          sx={{ ...btnOutline, height: 48, borderRadius: radii.button }}
        >
          Cadastrar com Google
        </Button>

        <Typography sx={{ textAlign: "center", mt: 3, color: colors.textMuted, fontSize: "0.9rem" }}>
          Já possui conta?{" "}
          <Button
            onClick={goToLogin}
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
            Entrar
          </Button>
        </Typography>
      </Paper>
    </Box>
  );
}
