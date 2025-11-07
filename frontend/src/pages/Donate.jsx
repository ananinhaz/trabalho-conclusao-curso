// src/pages/Donate.jsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { animaisApi } from '../api'
import {
  Box,
  Paper,
  Typography,
  TextField,
  MenuItem,
  Button,
  Stack,
  Container,
} from '@mui/material'

export default function Donate() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    nome: '',
    especie: 'Cachorro',
    raca: '',
    idade: '',
    porte: '',
    descricao: '',
    cidade: '',
    photo_url: '',
    donor_name: '',
    donor_whatsapp: '',
  })
  const [msg, setMsg] = useState('')

  // Cores e Estilos Comuns
  const primaryColor = "#6366F1"; // Azul/Roxo do AdoptMe
  const primaryColorHover = "#4F46E5";
  const cardStyles = {
    borderRadius: "1.25rem",
    boxShadow: "0 15px 45px rgba(15, 23, 42, 0.12)",
  };


  async function handleSubmit(e) {
    e.preventDefault()
    setMsg('')
    try {
      await animaisApi.create(form)
      // depois de doar → lista de animais
      navigate('/animais', { replace: true })
    } catch (err) {
      setMsg(err.message || 'Erro ao cadastrar animal')
    }
  }

  return (
    <Box 
      sx={{ 
        p: { xs: 2, sm: 3 }, 
        display: 'flex', 
        justifyContent: 'center',
        minHeight: "100vh",
        bgcolor: "#F9FAFB" // Fundo claro como na Landing
      }}
    >
      <Paper sx={{ ...cardStyles, p: { xs: 3, sm: 4 }, width: '100%', maxWidth: 720 }}>
        <Typography variant="h5" sx={{ fontWeight: 600, color: "#0f172a", mb: 2 }} gutterBottom>
          Cadastrar animal para adoção
        </Typography>

        <form onSubmit={handleSubmit}>
          <Stack spacing={2}>
            <TextField
              label="Nome"
              value={form.nome}
              onChange={e => setForm(f => ({ ...f, nome: e.target.value }))}
              required
              fullWidth
            />
            <TextField
              select
              label="Espécie"
              value={form.especie}
              onChange={e => setForm(f => ({ ...f, especie: e.target.value }))}
              required
              fullWidth
            >
              <MenuItem value="Cachorro">Cachorro</MenuItem>
              <MenuItem value="Gato">Gato</MenuItem>
              <MenuItem value="Outro">Outro</MenuItem>
            </TextField>
            <TextField
              label="Raça (opcional)"
              value={form.raca}
              onChange={e => setForm(f => ({ ...f, raca: e.target.value }))}
              fullWidth
            />
            <TextField
              label="Idade (em anos)"
              value={form.idade}
              onChange={e => setForm(f => ({ ...f, idade: e.target.value }))}
              type="number"
              fullWidth
            />
            <TextField
              label="Porte (Ex: Pequeno, Médio, Grande)"
              value={form.porte}
              onChange={e => setForm(f => ({ ...f, porte: e.target.value }))}
              fullWidth
            />
            <TextField
              label="Descrição"
              multiline
              rows={3}
              value={form.descricao}
              onChange={e =>
                setForm(f => ({ ...f, descricao: e.target.value }))
              }
              required
              fullWidth
            />
            <TextField
              label="Cidade (Ex: São Paulo - SP)"
              value={form.cidade}
              onChange={e => setForm(f => ({ ...f, cidade: e.target.value }))}
              required
              fullWidth
            />
            <TextField
              label="URL da foto"
              value={form.photo_url}
              onChange={e =>
                setForm(f => ({ ...f, photo_url: e.target.value }))
              }
              fullWidth
            />
            <TextField
              label="Nome do doador"
              value={form.donor_name}
              onChange={e =>
                setForm(f => ({ ...f, donor_name: e.target.value }))
              }
              fullWidth
            />
            <TextField
              label="WhatsApp do doador (somente números com DDD)"
              value={form.donor_whatsapp}
              onChange={e =>
                setForm(f => ({ ...f, donor_whatsapp: e.target.value }))
              }
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
              Anunciar para Adoção
            </Button>
          </Stack>
        </form>

        {msg && (
          <Typography color="error" sx={{ mt: 2 }}>
            {msg}
          </Typography>
        )}
      </Paper>
    </Box>
  )
}