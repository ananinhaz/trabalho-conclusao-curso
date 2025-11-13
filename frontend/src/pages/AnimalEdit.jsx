import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Stack,
  Container,
  CircularProgress,
} from '@mui/material'
import { animaisApi } from '../api'

export default function AnimalEdit() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({
    nome: '',
    especie: '',
    raca: '',
    idade: '',
    porte: '',
    descricao: '',
    cidade: '',
    photo_url: '',
    donor_name: '',
    donor_whatsapp: '',
  })
  const [error, setError] = useState(null)

  useEffect(() => {
    ;(async () => {
      try {
        setLoading(true)
        const res = await animaisApi.get(Number(id))
        setForm({
          nome: res.nome || '',
          especie: res.especie || '',
          raca: res.raca || '',
          idade: res.idade || '',
          porte: res.porte || '',
          descricao: res.descricao || '',
          cidade: res.cidade || '',
          photo_url: res.photo_url || '',
          donor_name: res.donor_name || '',
          donor_whatsapp: res.donor_whatsapp || '',
        })
      } catch (err) {
        console.error(err)
        setError('Falha ao carregar os dados do animal.')
      } finally {
        setLoading(false)
      }
    })()
  }, [id])

  function setField(k, v) {
    setForm(prev => ({ ...prev, [k]: v }))
  }

  async function handleSave(e) {
    e.preventDefault()
    try {
      setSaving(true)
      // validações simples
      if (!form.nome || !form.especie || !form.descricao || !form.cidade) {
        setError('Preencha os campos obrigatórios: nome, espécie, descrição e cidade.')
        setSaving(false)
        return
      }
      // chama a API de update (espera { ok: true } ou equivalente)
      await animaisApi.update(Number(id), form)
      // volta pra listagem ou pro detalhe
      navigate('/animais')
    } catch (err) {
      console.error(err)
      setError('Erro ao salvar. Tente novamente.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <Box sx={{ p: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Editar anúncio
        </Typography>

        {error && (
          <Typography color="error" sx={{ mb: 2 }}>
            {error}
          </Typography>
        )}

        <Box component="form" onSubmit={handleSave}>
          <Stack spacing={2}>
            <TextField label="Nome" value={form.nome} onChange={e => setField('nome', e.target.value)} required fullWidth />
            <TextField label="Especie" value={form.especie} onChange={e => setField('especie', e.target.value)} required fullWidth />
            <TextField label="Raça" value={form.raca} onChange={e => setField('raca', e.target.value)} fullWidth />
            <TextField label="Idade" value={String(form.idade || '')} onChange={e => setField('idade', e.target.value)} fullWidth />
            <TextField label="Porte" value={form.porte} onChange={e => setField('porte', e.target.value)} fullWidth />
            <TextField label="Cidade" value={form.cidade} onChange={e => setField('cidade', e.target.value)} required fullWidth />
            <TextField
              label="Foto (URL)"
              value={form.photo_url}
              onChange={e => setField('photo_url', e.target.value)}
              fullWidth
            />
            <TextField label="Nome do doador" value={form.donor_name} onChange={e => setField('donor_name', e.target.value)} fullWidth />
            <TextField label="WhatsApp do doador" value={form.donor_whatsapp} onChange={e => setField('donor_whatsapp', e.target.value)} fullWidth />
            <TextField
              label="Descrição"
              value={form.descricao}
              onChange={e => setField('descricao', e.target.value)}
              fullWidth
              multiline
              minRows={3}
              required
            />

            <Stack direction="row" spacing={1}>
              <Button type="submit" disabled={saving} variant="contained" sx={{ flex: 1 }}>
                {saving ? 'Salvando...' : 'Salvar'}
              </Button>
              <Button variant="outlined" onClick={() => navigate('/animais')} sx={{ flex: 1 }}>
                Cancelar
              </Button>
            </Stack>
          </Stack>
        </Box>
      </Paper>
    </Container>
  )
}
