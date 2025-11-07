// src/pages/AdopterForm.jsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { perfilApi } from "../api";
import {
  Box,
  Paper,
  Typography,
  TextField,
  MenuItem,
  Button,
  Stack,
  Divider,
  InputAdornment,
} from "@mui/material";
import PetsIcon from "@mui/icons-material/Pets";
import HomeIcon from "@mui/icons-material/Home";
import ChildCareIcon from "@mui/icons-material/ChildCare";
import AccessTimeIcon from "@mui/icons-material/AccessTime";
import FavoriteBorderIcon from "@mui/icons-material/FavoriteBorder";
// Nenhum import novo necessário

export default function AdopterForm() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    tipo_moradia: "",
    tem_criancas: 0,
    tempo_disponivel_horas_semana: 0,
    estilo_vida: "",
  });
  const [msg, setMsg] = useState("");

  // ... (lógica useEffect e handleSubmit idêntica) ...

  useEffect(() => {
    (async () => {
      try {
        const r = await perfilApi.get();
        if (r.ok && r.perfil) {
          setForm({
            tipo_moradia: r.perfil.tipo_moradia || "",
            tem_criancas: r.perfil.tem_criancas ?? 0,
            tempo_disponivel_horas_semana:
              r.perfil.tempo_disponivel_horas_semana ?? 0,
            estilo_vida: r.perfil.estilo_vida || "",
          });
        }
      } catch {
        // ignora
      }
    })();
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setMsg("");
    try {
      await perfilApi.save(form);
      navigate("/animais", { replace: true });
    } catch (err) {
      setMsg(err.message || "Erro ao salvar");
    }
  }

  const primaryColor = "#6366F1";
  const primaryColorHover = "#4F46E5";

  return (
    <Box
      sx={{
        minHeight: "100vh",
        bgcolor: "#F9FAFB",
      }}
    >
      {/* ... (Header idêntico) ... */}
      <Box
        sx={{
          height: 62,
          bgcolor: "#fff",
          borderBottom: "1px solid rgba(15,23,42,0.05)",
          display: "flex",
          alignItems: "center",
          px: { xs: 2, md: 6 },
          gap: 1,
        }}
      >
        <PetsIcon sx={{ color: primaryColor }} />
        <Typography sx={{ fontWeight: 600, color: "#0f172a" }}>
          <Box component="span" sx={{ color: primaryColor, fontWeight: 700 }}>
            AdoptMe
          </Box>{" "}
          • Perfil do adotante
        </Typography>
      </Box>

      <Box
        sx={{
          maxWidth: 820, // Mantém a largura máxima do card
          mx: "auto",
          mt: 4,
          px: { xs: 2, md: 0 },
          pb: 6,
        }}
      >
        <Paper
          elevation={0}
          sx={{
            borderRadius: "1.25rem",
            bgcolor: "#fff",
            border: "1px solid rgba(15,23,42,0.03)",
            boxShadow: "0 20px 50px rgba(15,23,42,0.03)",
            p: { xs: 2.5, md: 3 }, // Padding interno do Paper reduzido
          }}
        >
          {/* --- CABEÇALHO COMPACTO --- */}
          <Box sx={{ textAlign: "center", mb: 2 }}>
            <Box
              sx={{
                width: 44, // Ícone menor
                height: 44, // Ícone menor
                bgcolor: "#EEF2FF",
                borderRadius: "50%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                mx: "auto",
                mb: 1.5,
              }}
            >
              <PetsIcon sx={{ color: primaryColor, fontSize: "1.6rem" }} />
            </Box>
            
            <Typography
              variant="h6" // Mantido como h6, mas fonte pode ser ajustada
              sx={{ fontWeight: 600, color: "#1f2937", mb: 0.5, fontSize: "1.1rem" }} // Fonte menor
            >
              Para indicarmos o melhor pet, precisamos te conhecer 🙂
            </Typography>
            <Typography sx={{ color: "#6b7280", fontSize: "0.8rem" }}>
              Leva menos de 1 minuto. Depois disso já mostramos os animais
              compatíveis.
            </Typography>
          </Box>

          <Divider sx={{ my: 2 }} />

          {/* --- FORMULÁRIO COMPACTO --- */}
          <form onSubmit={handleSubmit}>
            <Stack spacing={1.5}> {/* Espaçamento entre campos reduzido */}
              <TextField
                size="small" // <-- A MÁGICA ACONTECE AQUI
                select
                label="Tipo de moradia"
                value={form.tipo_moradia}
                onChange={(e) =>
                  setForm((f) => ({ ...f, tipo_moradia: e.target.value }))
                }
                required
                fullWidth
                variant="filled"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <HomeIcon sx={{ color: "#6b7280", fontSize: '1.25rem' }} />
                    </InputAdornment>
                  ),
                  disableUnderline: true,
                  sx: { borderRadius: "0.9rem", bgcolor: "#f3f4f6" },
                }}
              >
                <MenuItem value="Apartamento">Apartamento</MenuItem>
                <MenuItem value="Casa com quintal">Casa com quintal</MenuItem>
                <MenuItem value="Casa sem quintal">Casa sem quintal</MenuItem>
                <MenuItem value="Chácara/Sítio">Chácara / sítio</MenuItem>
              </TextField>

              <TextField
                size="small" // <-- A MÁGICA ACONTECE AQUI
                select
                label="Tem crianças em casa?"
                value={form.tem_criancas}
                onChange={(e) =>
                  setForm((f) => ({
                    ...f,
                    tem_criancas: Number(e.target.value),
                  }))
                }
                fullWidth
                variant="filled"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <ChildCareIcon sx={{ color: "#6b7280", fontSize: '1.25rem' }} />
                    </InputAdornment>
                  ),
                  disableUnderline: true,
                  sx: { borderRadius: "0.9rem", bgcolor: "#f3f4f6" },
                }}
              >
                <MenuItem value={0}>Não</MenuItem>
                <MenuItem value={1}>Sim</MenuItem>
              </TextField>

              <TextField
                size="small" // <-- A MÁGICA ACONTECE AQUI
                label="Tempo disponível (horas/semana)"
                type="number"
                value={form.tempo_disponivel_horas_semana}
                onChange={(e) =>
                  setForm((f) => ({
                    ...f,
                    tempo_disponivel_horas_semana: Number(e.target.value),
                  }))
                }
                required
                fullWidth
                variant="filled"
                helperText="Inclua tempo para passeios, brincadeiras e cuidados."
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <AccessTimeIcon sx={{ color: "#6b7280", fontSize: '1.25rem' }} />
                    </InputAdornment>
                  ),
                  disableUnderline: true,
                  sx: { borderRadius: "0.9rem", bgcolor: "#f3f4f6" },
                }}
                // Estilizando o HelperText para ser menor
                FormHelperTextProps={{
                  sx: { mt: 0.25, fontSize: "0.7rem", lineHeight: 1.2 }
                }}
              />

              <TextField
                size="small" // <-- A MÁGICA ACONTECE AQUI
                select
                label="Estilo de vida"
                value={form.estilo_vida}
                onChange={(e) =>
                  setForm((f) => ({ ...f, estilo_vida: e.target.value }))
                }
                required
                fullWidth
                variant="filled"
                helperText="Assim indicamos pets mais calmos ou mais ativos."
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <FavoriteBorderIcon sx={{ color: "#6b7280", fontSize: '1.25rem' }} />
                    </InputAdornment>
                  ),
                  disableUnderline: true,
                  sx: { borderRadius: "0.9rem", bgcolor: "#f3f4f6" },
                }}
                FormHelperTextProps={{
                  sx: { mt: 0.25, fontSize: "0.7rem", lineHeight: 1.2 }
                }}
              >
                <MenuItem value="Calmo">Calmo</MenuItem>
                <MenuItem value="Moderado">Moderado</MenuItem>
                <MenuItem value="Ativo">Ativo</MenuItem>
                <MenuItem value="Esportivo">Esportivo</MenuItem>
                <MenuItem value="Fico pouco em casa">
                  Fico pouco em casa
                </MenuItem>
              </TextField>

              {/* --- BOTÃO COMPACTO --- */}
              <Button
                type="submit"
                size="large" // Mantém large para ser fácil de clicar, mas ajusta padding
                variant="contained"
                startIcon={<FavoriteBorderIcon />}
                sx={{
                  mt: 2,
                  py: 0.8, // Padding vertical reduzido
                  borderRadius: "9999px",
                  textTransform: "none",
                  fontWeight: 600,
                  fontSize: "0.9rem", // Fonte do botão menor
                  bgcolor: primaryColor,
                  color: "#fff",
                  boxShadow: "none",
                  "&:hover": {
                    bgcolor: primaryColorHover,
                    boxShadow: "0 4px 14px rgba(0,0,0,0.08)",
                  },
                }}
              >
                Salvar perfil e ver animais
              </Button>
            </Stack>
          </form>

          {msg && (
            <Typography color="error" sx={{ mt: 2, textAlign: "center", fontSize: "0.85rem" }}>
              {msg}
            </Typography>
          )}
        </Paper>
      </Box>
    </Box>
  );
}