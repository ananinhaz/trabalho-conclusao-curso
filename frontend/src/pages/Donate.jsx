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
  CircularProgress,
} from '@mui/material'
import UploadFileIcon from '@mui/icons-material/UploadFile';

export default function Donate() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    nome: '',
    especie: 'Cachorro',
    raca: '',
    idade: '',
    porte: '',
    energia: 'Média', 
    bom_com_criancas: 0, 
    descricao: '',
    cidade: '',
    photo_url: '', 
    donor_name: '',
    donor_whatsapp: '',
  })
  const [msg, setMsg] = useState('')
  const [isUploading, setIsUploading] = useState(false)
  const [customEspecie, setCustomEspecie] = useState('')


  //config upload
  const CLOUDINARY_CLOUD_NAME = 'dqytx0v16' 
  const CLOUDINARY_UPLOAD_PRESET = 'Ana_Rocha' 

  const primaryColor = "#6366F1";
  const primaryColorHover = "#4F46E5";
  const cardStyles = {
    borderRadius: "1.25rem",
    boxShadow: "0 15px 45px rgba(15, 23, 42, 0.12)",
  };

  // Função que envia o arquivo para o Cloudinary
  async function handleFileChange(e) {
    const file = e.target.files[0]
    if (!file) return

    setIsUploading(true)
    setMsg('Enviando foto...')

    const formData = new FormData()
    formData.append('file', file)
    formData.append('upload_preset', CLOUDINARY_UPLOAD_PRESET)

    try {
      const res = await fetch(
        `https://api.cloudinary.com/v1_1/${CLOUDINARY_CLOUD_NAME}/image/upload`,
        {
          method: 'POST',
          body: formData,
        }
      )
      const data = await res.json()

      if (data.secure_url) {
        setForm(f => ({ ...f, photo_url: data.secure_url }))
        setMsg('Foto enviada com sucesso!')
      } else {
        throw new Error(data.error.message || 'Erro ao enviar imagem')
      }
    } catch (err) {
      setMsg(err.message)
    } finally {
      setIsUploading(false)
    }
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setMsg('')

    if (isUploading) {
      setMsg("Por favor, aguarde o envio da foto terminar.")
      return
    }
    
    if (!form.photo_url) {
        setMsg("Por favor, adicione uma foto do animal.")
        return
    }

    let finalForm = form

    if (form.especie === 'Outro') {
        if (!customEspecie.trim()) {
            setMsg("Por favor, especifique qual é a espécie do animal no campo 'Qual espécie?'.")
            return
        }
        finalForm = { ...form, especie: customEspecie.trim() }
    }


    try {
      await animaisApi.create(finalForm)
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
        bgcolor: "#F9FAFB"
      }}
    >
      <Paper sx={{ ...cardStyles, p: { xs: 3, sm: 4 }, width: '100%', maxWidth: 720 }}>
        <Typography variant="h5" sx={{ fontWeight: 600, color: "#0f172a", mb: 2 }} gutterBottom>
          Cadastrar animal para adoção
        </Typography>

        <form onSubmit={handleSubmit}>
          <Stack spacing={2}>
            <TextField
              label="Nome do animal"
              value={form.nome}
              onChange={e => setForm(f => ({ ...f, nome: e.target.value }))}
              required
              fullWidth
            />
            
            <TextField
              select
              label="Espécie"
              value={form.especie}
              onChange={e => {
                setForm(f => ({ ...f, especie: e.target.value }))
                // Se  voltar para Cachorro/Gato, limpa o campo customizado
                if (e.target.value !== 'Outro') {
                    setCustomEspecie('');
                }
            }}
              required
              fullWidth
            >
              <MenuItem value="Cachorro">Cachorro</MenuItem>
              <MenuItem value="Gato">Gato</MenuItem>
              <MenuItem value="Outro">Outro</MenuItem>
            </TextField>

            {form.especie === 'Outro' && (
                <TextField
                    label="Qual espécie? (Ex: Coelho, Calopsita)"
                    value={customEspecie}
                    onChange={e => setCustomEspecie(e.target.value)}
                    required 
                    fullWidth
                />
            )}
            
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
              select
              label="Porte"
              value={form.porte}
              onChange={e => setForm(f => ({ ...f, porte: e.target.value }))}
              required
              fullWidth
            >
              <MenuItem value="Pequeno">Pequeno</MenuItem>
              <MenuItem value="Médio">Médio</MenuItem>
              <MenuItem value="Grande">Grande</MenuItem>
            </TextField>

            <TextField
              select
              label="Nível de Energia"
              value={form.energia}
              onChange={e => setForm(f => ({ ...f, energia: e.target.value }))}
              required
              fullWidth
            >
              <MenuItem value="Baixa">Baixa (mais calmo, idoso)</MenuItem>
              <MenuItem value="Média">Média (brincalhão)</MenuItem>
              <MenuItem value="Alta">Alta (muito ativo, esportivo)</MenuItem>
            </TextField>

            <TextField
              select
              label="Bom com Crianças?"
              value={form.bom_com_criancas}
              onChange={e => setForm(f => ({ ...f, bom_com_criancas: parseInt(e.target.value) }))}
              required
              fullWidth
            >
              <MenuItem value={1}>Sim</MenuItem>
              <MenuItem value={0}>Não</MenuItem>
            </TextField>
            
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
            
            {/* upload da foto */}
            <Button
              variant="outlined"
              component="label" 
              fullWidth
              disabled={isUploading}
              startIcon={isUploading ? <CircularProgress size={20} /> : <UploadFileIcon />}
              sx={{ py: 1.2 }}
            >
              {isUploading ? "Enviando Foto..." : "Selecionar Foto do Animal"}
              <input 
                type="file" 
                hidden 
                accept="image/png, image/jpeg"
                onChange={handleFileChange} 
              />
            </Button>
  
            {form.photo_url && !isUploading && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 1, border: '1px dashed #ccc', borderRadius: 2 }}>
                <img src={form.photo_url} alt="Preview" style={{ width: 60, height: 60, borderRadius: '8px', objectFit: 'cover' }} />
                <Typography variant="body2" color="textSecondary">
                  Foto selecionada com sucesso.
                </Typography>
              </Box>
            )}
            
            {/* Campos do Doador */}
            <TextField
              label="Seu Nome"
              value={form.donor_name}
              onChange={e =>
                setForm(f => ({ ...f, donor_name: e.target.value }))
              }
              fullWidth
            />
            <TextField
              label="Seu WhatsApp (somente números com DDD)"
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
              disabled={isUploading} 
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
          <Typography 
            color={msg.includes('sucesso') ? 'green' : 'error'} 
            sx={{ mt: 2 }}
          >
            {msg}
          </Typography>
        )}
      </Paper>
    </Box>
  )
}