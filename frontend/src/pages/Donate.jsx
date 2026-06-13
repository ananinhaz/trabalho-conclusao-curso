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
  CircularProgress,
} from '@mui/material'
import PetsIcon from '@mui/icons-material/Pets';
import CloudUploadOutlinedIcon from '@mui/icons-material/CloudUploadOutlined';
import { colors, radii, cardSx, btnGradient, inputSx } from '../theme';

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

  const fieldSx = { ...inputSx, '& .MuiInputBase-root': { borderRadius: radii.input } };

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
    <Box sx={{ p: { xs: 2, sm: 3 }, display: 'flex', justifyContent: 'center', minHeight: '100vh', bgcolor: colors.background }}>
      <Paper sx={{ ...cardSx, p: { xs: 3, sm: 5 }, width: '100%', maxWidth: 760, borderRadius: radii.card }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 3, gap: 2 }}>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 800, color: colors.text, mb: 0.75, fontSize: { xs: '1.5rem', md: '1.75rem' } }}>
              Cadastrar animal para adoção
            </Typography>
            <Typography sx={{ color: colors.textMuted, fontSize: '0.95rem' }}>
              Preencha as informações do animal e seus dados de contato
            </Typography>
          </Box>
          <Box sx={{ width: 56, height: 56, borderRadius: '16px', bgcolor: colors.primary, display: { xs: 'none', sm: 'flex' }, alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <PetsIcon sx={{ color: '#fff', fontSize: 28 }} />
          </Box>
        </Box>

        <form onSubmit={handleSubmit}>
          <Stack spacing={2.5}>
            <Typography sx={{ fontWeight: 700, color: colors.text, fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: 1 }}>
              <PetsIcon sx={{ color: colors.primary, fontSize: 20 }} />
              Informações do animal
            </Typography>

            <TextField label="Nome do animal" value={form.nome} onChange={e => setForm(f => ({ ...f, nome: e.target.value }))} required fullWidth sx={fieldSx} />
            
            <TextField select label="Espécie" value={form.especie} onChange={e => { setForm(f => ({ ...f, especie: e.target.value })); if (e.target.value !== 'Outro') { setCustomEspecie(''); } }} required fullWidth sx={fieldSx}>
              <MenuItem value="Cachorro">Cachorro</MenuItem>
              <MenuItem value="Gato">Gato</MenuItem>
              <MenuItem value="Outro">Outro</MenuItem>
            </TextField>

            {form.especie === 'Outro' && (
              <TextField label="Qual espécie? (Ex: Coelho, Calopsita)" value={customEspecie} onChange={e => setCustomEspecie(e.target.value)} required fullWidth sx={fieldSx} />
            )}

            <TextField label="Raça (opcional)" value={form.raca} onChange={e => setForm(f => ({ ...f, raca: e.target.value }))} fullWidth sx={fieldSx} />
            <TextField label="Idade (em anos)" value={form.idade} onChange={e => setForm(f => ({ ...f, idade: e.target.value }))} type="number" fullWidth sx={fieldSx} />
            <TextField select label="Porte" value={form.porte} onChange={e => setForm(f => ({ ...f, porte: e.target.value }))} required fullWidth sx={fieldSx}>
              <MenuItem value="Pequeno">Pequeno</MenuItem>
              <MenuItem value="Médio">Médio</MenuItem>
              <MenuItem value="Grande">Grande</MenuItem>
            </TextField>
            <TextField select label="Nível de Energia" value={form.energia} onChange={e => setForm(f => ({ ...f, energia: e.target.value }))} required fullWidth sx={fieldSx}>
              <MenuItem value="Baixa">Baixa (mais calmo, idoso)</MenuItem>
              <MenuItem value="Média">Média (brincalhão)</MenuItem>
              <MenuItem value="Alta">Alta (muito ativo, esportivo)</MenuItem>
            </TextField>
            <TextField select label="Bom com Crianças?" value={String(form.bom_com_criancas ?? 0)} onChange={e => setForm(f => ({ ...f, bom_com_criancas: Number(e.target.value) }))} required fullWidth sx={fieldSx}>
              <MenuItem value="1">Sim</MenuItem>
              <MenuItem value="0">Não</MenuItem>
            </TextField>
            <TextField label="Descrição" multiline rows={4} value={form.descricao} onChange={e => setForm(f => ({ ...f, descricao: e.target.value }))} required fullWidth sx={fieldSx} />
            <TextField label="Cidade (Ex: São Paulo - SP)" value={form.cidade} onChange={e => setForm(f => ({ ...f, cidade: e.target.value }))} required fullWidth sx={fieldSx} />

            <Box
              component="label"
              sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 1,
                p: 4,
                border: `2px dashed ${colors.border}`,
                borderRadius: radii.input,
                bgcolor: colors.background,
                cursor: isUploading ? 'wait' : 'pointer',
                transition: 'all 0.2s ease',
                '&:hover': { borderColor: colors.primary, bgcolor: '#EEF2FF' },
              }}
            >
              {isUploading ? <CircularProgress size={28} sx={{ color: colors.primary }} /> : <CloudUploadOutlinedIcon sx={{ fontSize: 40, color: colors.primary }} />}
              <Typography sx={{ fontWeight: 600, color: colors.text }}>
                {isUploading ? 'Enviando Foto...' : 'Selecionar Foto do Animal'}
              </Typography>
              <Typography sx={{ fontSize: '0.8rem', color: colors.textMuted }}>PNG ou JPEG</Typography>
              <input type="file" hidden accept="image/png, image/jpeg" onChange={handleFileChange} disabled={isUploading} />
            </Box>

            {form.photo_url && !isUploading && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2, border: `1px solid ${colors.border}`, borderRadius: radii.input, bgcolor: colors.background }}>
                <img src={form.photo_url} alt="Preview" style={{ width: 80, height: 80, borderRadius: '12px', objectFit: 'cover' }} />
                <Typography variant="body2" sx={{ color: colors.success, fontWeight: 600 }}>
                  Foto selecionada com sucesso.
                </Typography>
              </Box>
            )}

            <Typography sx={{ fontWeight: 700, color: colors.text, fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: 1, pt: 1 }}>
              Seus dados de contato
            </Typography>
            <TextField label="Seu Nome" value={form.donor_name} onChange={e => setForm(f => ({ ...f, donor_name: e.target.value }))} fullWidth sx={fieldSx} />
            <TextField label="Seu WhatsApp (somente números com DDD)" value={form.donor_whatsapp} onChange={e => setForm(f => ({ ...f, donor_whatsapp: e.target.value }))} fullWidth sx={fieldSx} />

            <Button type="submit" variant="contained" fullWidth disabled={isUploading} startIcon={<PetsIcon />} sx={{ ...btnGradient, py: 1.5, mt: 1, fontSize: '1rem', height: 52 }}>
              Anunciar para Adoção
            </Button>
          </Stack>
        </form>

        {msg && (
          <Typography color={msg.includes('sucesso') ? colors.success : 'error'} sx={{ mt: 2, fontWeight: 500 }}>
            {msg}
          </Typography>
        )}
      </Paper>
    </Box>
  )
}