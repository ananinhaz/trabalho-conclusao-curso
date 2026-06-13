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
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import LockOutlinedIcon from "@mui/icons-material/LockOutlined";
import { colors, gradientPrimary, shadows, radii, cardSx, btnGradient, inputSx } from "../theme";

export default function AdopterForm() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    tipo_moradia: "",
    tem_criancas: 0,
    tempo_disponivel_horas_semana: 0,
    estilo_vida: "",
  });
  const [msg, setMsg] = useState("");


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

  const fieldSx = {
    ...inputSx,
    '& .MuiInputBase-root': {
      borderRadius: radii.input,
      bgcolor: colors.background,
    },
  };

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: colors.background }}>
      <Box
        sx={{
          height: 68,
          bgcolor: colors.card,
          boxShadow: shadows.header,
          display: "flex",
          alignItems: "center",
          px: { xs: 2, md: 6 },
          gap: 1,
        }}
      >
        <Box sx={{ width: 36, height: 36, borderRadius: "10px", background: gradientPrimary, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <PetsIcon sx={{ color: "#fff", fontSize: 20 }} />
        </Box>
        <Typography sx={{ fontWeight: 700, color: colors.text }}>
          <Box component="span" sx={{ color: colors.primary, fontWeight: 800 }}>AdoptMe</Box>
          {" "}• Perfil do adotante
        </Typography>
      </Box>

      <Box sx={{ maxWidth: 720, mx: "auto", mt: { xs: 3, md: 5 }, px: { xs: 2, md: 0 }, pb: 6 }}>
        <Paper elevation={0} sx={{ ...cardSx, p: { xs: 3, md: 4 }, borderRadius: radii.card }}>
          <Box sx={{ textAlign: "center", mb: 3 }}>
            <Box sx={{ width: 56, height: 56, bgcolor: "#EEF2FF", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", mx: "auto", mb: 2 }}>
              <PetsIcon sx={{ color: colors.primary, fontSize: "1.8rem" }} />
            </Box>
            <Typography variant="h5" sx={{ fontWeight: 800, color: colors.text, mb: 0.75 }}>
              Perfil do adotante
            </Typography>
            <Typography sx={{ color: colors.textMuted, fontSize: "0.9rem" }}>
              Leva menos de 1 minuto. Depois disso já mostramos os animais compatíveis.
            </Typography>
          </Box>

          <Box sx={{ bgcolor: colors.goldBg, color: colors.goldText, borderRadius: radii.input, p: 2, mb: 3, display: "flex", gap: 1.5, alignItems: "flex-start" }}>
            <AutoAwesomeIcon sx={{ fontSize: 22, mt: 0.25 }} />
            <Box>
              <Typography sx={{ fontWeight: 700, fontSize: "0.9rem", mb: 0.25 }}>Recomendação inteligente</Typography>
              <Typography sx={{ fontSize: "0.82rem", lineHeight: 1.5 }}>
                Suas respostas alimentam o algoritmo de compatibilidade para encontrar o pet ideal.
              </Typography>
            </Box>
          </Box>

          <Divider sx={{ my: 2.5, borderColor: "#F1F5F9" }} />

          <form onSubmit={handleSubmit}>
            <Stack spacing={2}>
              <TextField size="medium" select label="Tipo de moradia" value={form.tipo_moradia} onChange={(e) => setForm((f) => ({ ...f, tipo_moradia: e.target.value }))} required fullWidth sx={fieldSx} InputProps={{ startAdornment: (<InputAdornment position="start"><HomeIcon sx={{ color: colors.primary, fontSize: '1.25rem' }} /></InputAdornment>) }}>
                <MenuItem value="Apartamento">Apartamento</MenuItem>
                <MenuItem value="Casa com quintal">Casa com quintal</MenuItem>
                <MenuItem value="Casa sem quintal">Casa sem quintal</MenuItem>
                <MenuItem value="Chácara/Sítio">Chácara / sítio</MenuItem>
              </TextField>

              <TextField size="medium" select label="Tem crianças em casa?" value={form.tem_criancas} onChange={(e) => setForm((f) => ({ ...f, tem_criancas: Number(e.target.value) }))} fullWidth sx={fieldSx} InputProps={{ startAdornment: (<InputAdornment position="start"><ChildCareIcon sx={{ color: colors.primary, fontSize: '1.25rem' }} /></InputAdornment>) }}>
                <MenuItem value={0}>Não</MenuItem>
                <MenuItem value={1}>Sim</MenuItem>
              </TextField>

              <TextField size="medium" label="Tempo disponível (horas/semana)" type="number" value={form.tempo_disponivel_horas_semana} onChange={(e) => setForm((f) => ({ ...f, tempo_disponivel_horas_semana: Number(e.target.value) }))} required fullWidth sx={fieldSx} helperText="Inclua tempo para passeios, brincadeiras e cuidados." InputProps={{ startAdornment: (<InputAdornment position="start"><AccessTimeIcon sx={{ color: colors.primary, fontSize: '1.25rem' }} /></InputAdornment>) }} />

              <TextField size="medium" select label="Estilo de vida" value={form.estilo_vida} onChange={(e) => setForm((f) => ({ ...f, estilo_vida: e.target.value }))} required fullWidth sx={fieldSx} helperText="Assim indicamos pets mais calmos ou mais ativos." InputProps={{ startAdornment: (<InputAdornment position="start"><FavoriteBorderIcon sx={{ color: colors.primary, fontSize: '1.25rem' }} /></InputAdornment>) }}>
                <MenuItem value="Calmo">Calmo</MenuItem>
                <MenuItem value="Moderado">Moderado</MenuItem>
                <MenuItem value="Ativo">Ativo</MenuItem>
                <MenuItem value="Esportivo">Esportivo</MenuItem>
                <MenuItem value="Fico pouco em casa">Fico pouco em casa</MenuItem>
              </TextField>

              <Box sx={{ bgcolor: '#F5F3FF', borderRadius: radii.input, p: 2, mt: 1 }}>
                <Typography sx={{ fontWeight: 700, fontSize: '0.85rem', color: colors.text, mb: 1 }}>O que consideramos na recomendação</Typography>
                <Stack direction="row" flexWrap="wrap" gap={0.75}>
                  {['Porte do animal', 'Rotina da família', 'Energia', 'Moradia', 'Crianças'].map((tag) => (
                    <Box key={tag} sx={{ bgcolor: colors.card, border: `1px solid ${colors.border}`, borderRadius: radii.pill, px: 1.5, py: 0.4, fontSize: '0.75rem', color: colors.textMuted, fontWeight: 500 }}>
                      {tag}
                    </Box>
                  ))}
                </Stack>
              </Box>

              <Button type="submit" size="large" variant="contained" startIcon={<FavoriteBorderIcon />} sx={{ ...btnGradient, mt: 2, py: 1.5, fontSize: '1rem', height: 52 }}>
                Salvar perfil e ver animais
              </Button>

              <Stack direction="row" alignItems="center" justifyContent="center" spacing={0.75} sx={{ mt: 1 }}>
                <LockOutlinedIcon sx={{ fontSize: 16, color: colors.textMuted }} />
                <Typography sx={{ fontSize: '0.78rem', color: colors.textMuted }}>
                  Suas informações são seguras e utilizadas apenas para recomendações.
                </Typography>
              </Stack>
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