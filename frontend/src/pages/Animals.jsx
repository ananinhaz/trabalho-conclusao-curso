// src/pages/Animals.jsx
import { useEffect, useState } from 'react'
import { animaisApi, recApi } from '../api'
import {
  Box,
  Paper,
  Typography,
  Button,
  Stack,
  Chip,
  Grid,
  Container,
} from '@mui/material'
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline'

export default function Animals({ user }) {
  const [all, setAll] = useState([])
  const [mine, setMine] = useState([])
  const [recs, setRecs] = useState({ items: [], ids: [] })
  const [tab, setTab] = useState('all')

  // Cores e Estilos Comuns
  const primaryColor = "#6366F1"; // Azul/Roxo do AdoptMe
  const primaryColorHover = "#4F46E5";
  const cardStyles = {
    // Estilo de card refinado: bordas arredondadas e sombra suave
    borderRadius: "1.25rem",
    boxShadow: "0 15px 45px rgba(15, 23, 42, 0.05)",
    overflow: 'hidden',
    transition: 'transform 0.2s, box-shadow 0.2s',
    '&:hover': {
      transform: 'translateY(-3px)',
      boxShadow: "0 20px 60px rgba(15, 23, 42, 0.1)",
    }
  };
  const mainPaperStyles = {
    borderRadius: "1.25rem",
    boxShadow: "0 20px 50px rgba(15,23,42,0.03)",
  };


  useEffect(() => {
    ;(async () => {
      const [a, m, r] = await Promise.all([
        animaisApi.list(),
        animaisApi.mine(),
        recApi.list(12),
      ])
      setAll(a || [])
      setMine(m || [])
      setRecs(r || { items: [], ids: [] })
    })()
  }, [])

  const recIdSet = new Set(recs.ids || [])

  const data =
    tab === 'mine' ? mine : tab === 'recs' ? recs.items || [] : all || []

  async function handleDelete(id) {
    if (!window.confirm('Excluir anúncio?')) return
    await animaisApi.remove(id)
    setAll(prev => prev.filter(x => x.id !== id))
    setMine(prev => prev.filter(x => x.id !== id))
    setRecs(prev => ({
      ...prev,
      items: (prev.items || []).filter(x => x.id !== id),
      ids: (prev.ids || []).filter(x => x !== id),
    }))
  }

  return (
    <Box sx={{ p: { xs: 2, sm: 3 }, bgcolor: "#F9FAFB", minHeight: "100vh" }}>
      <Container maxWidth="lg" sx={{ p: 0 }}>
        <Paper sx={{ ...mainPaperStyles, p: { xs: 2, sm: 3 } }}>
          <Stack
            direction={{ xs: 'column', sm: 'row' }}
            justifyContent="space-between"
            alignItems={{ xs: 'flex-start', sm: 'center' }}
            sx={{ mb: 3, gap: 2 }}
          >
            <Typography variant="h5" sx={{ fontWeight: 600, color: "#0f172a" }}>
              Animais
            </Typography>
            {/* Botões de Filtro com estilo Pílula */}
            <Stack direction="row" spacing={1}>
              <Button
                variant={tab === 'all' ? 'contained' : 'outlined'}
                onClick={() => setTab('all')}
                sx={{ 
                  borderRadius: "9999px",
                  bgcolor: tab === 'all' ? primaryColor : '#fff',
                  borderColor: primaryColor,
                  color: tab === 'all' ? '#fff' : primaryColor,
                  textTransform: 'none',
                  fontWeight: 600,
                  boxShadow: 'none',
                  '&:hover': {
                    bgcolor: tab === 'all' ? primaryColorHover : '#F4F4FE',
                    borderColor: primaryColorHover,
                  }
                }}
              >
                Todos
              </Button>
              <Button
                variant={tab === 'mine' ? 'contained' : 'outlined'}
                onClick={() => setTab('mine')}
                sx={{ 
                  borderRadius: "9999px",
                  bgcolor: tab === 'mine' ? primaryColor : '#fff',
                  borderColor: primaryColor,
                  color: tab === 'mine' ? '#fff' : primaryColor,
                  textTransform: 'none',
                  fontWeight: 600,
                  boxShadow: 'none',
                  '&:hover': {
                    bgcolor: tab === 'mine' ? primaryColorHover : '#F4F4FE',
                    borderColor: primaryColorHover,
                  }
                }}
              >
                Meus anúncios
              </Button>
              <Button
                variant={tab === 'recs' ? 'contained' : 'outlined'}
                onClick={() => setTab('recs')}
                sx={{ 
                  borderRadius: "9999px",
                  bgcolor: tab === 'recs' ? primaryColor : '#fff',
                  borderColor: primaryColor,
                  color: tab === 'recs' ? '#fff' : primaryColor,
                  textTransform: 'none',
                  fontWeight: 600,
                  boxShadow: 'none',
                  '&:hover': {
                    bgcolor: tab === 'recs' ? primaryColorHover : '#F4F4FE',
                    borderColor: primaryColorHover,
                  }
                }}
              >
                Recomendados
              </Button>
            </Stack>
          </Stack>

          <Grid container spacing={3}>
            {data.length === 0 && (
              <Typography sx={{ p: 2, color: "#475569" }}>
                Nenhum resultado.
              </Typography>
            )}

            {data.map(animal => {
              // 1. Verifica se o ID do animal está na lista de IDs recomendados.
              const isRecommended = recIdSet.has(animal.id)

              // 2. CORREÇÃO: Define a condição para mostrar o chip.
              // Ele deve aparecer se for recomendado E se NÃO estivermos na aba 'recs'.
              const showRecommendedChip = isRecommended && tab !== 'recs'
              
              const isMine = animal.doador_id === user?.id

              return (
                <Grid item xs={12} sm={6} md={4} key={animal.id}>
                  <Paper sx={{ ...cardStyles, position: 'relative' }}>
                    
                    {/* Imagem do Animal */}
                    <Box
                      sx={{
                        height: 150,
                        background: `#f1f5f9 url('${animal.photo_url || ''}') center/cover no-repeat`,
                        position: 'relative',
                        // Aplicar border-radius na parte superior da imagem
                        borderTopLeftRadius: "1.25rem",
                        borderTopRightRadius: "1.25rem",
                      }}
                    >
                      {/* Tag "Recomendado" Refinada: renderiza apenas se showRecommendedChip for true */}
                      {showRecommendedChip && (
                        <Chip
                          label="Recomendado"
                          size="small"
                          icon={<CheckCircleOutlineIcon sx={{ color: '#fff !important' }} />}
                          sx={{ 
                            position: 'absolute', 
                            top: 10, 
                            left: 10,
                            bgcolor: primaryColor, // Usando a cor primária
                            color: '#fff',
                            fontWeight: 600,
                            fontSize: '0.75rem',
                            height: '24px',
                            paddingLeft: '6px',
                          }}
                        />
                      )}
                    </Box>

                    {/* Conteúdo do Card */}
                    <Box sx={{ p: 2 }}>
                      <Typography fontWeight={600} color="#0f172a" sx={{ fontSize: '1.15rem' }}>
                        {animal.nome}
                      </Typography>
                      <Typography variant="body2" color="#64748b" sx={{ fontSize: '0.85rem' }}>
                        {animal.especie} • {animal.idade} • {animal.cidade}
                      </Typography>
                      <Typography variant="body2" sx={{ mt: 1, color: "#475569", minHeight: 40 }}>
                        {animal.descricao}
                      </Typography>

                      <Stack direction="row" spacing={1} sx={{ mt: 2, pt: 1, borderTop: '1px solid #f1f5f9' }}>
                        {animal.donor_whatsapp && (
                          <Button
                            size="small"
                            variant="outlined"
                            href={`https://wa.me/${animal.donor_whatsapp}`}
                            target="_blank"
                            sx={{
                                borderRadius: "9999px",
                                textTransform: "none",
                                fontWeight: 600,
                                borderColor: primaryColor,
                                color: primaryColor,
                                '&:hover': {
                                  borderColor: primaryColorHover,
                                  bgcolor: '#F4F4FE'
                                }
                              }}
                          >
                            Falar com doador
                          </Button>
                        )}
                        {isMine && (
                          <>
                            {/* editar você faz depois */}
                            <Button
                              size="small"
                              color="error"
                              onClick={() => handleDelete(animal.id)}
                              sx={{
                                borderRadius: "9999px",
                                textTransform: "none",
                                fontWeight: 600,
                              }}
                            >
                              Excluir
                            </Button>
                          </>
                        )}
                      </Stack>
                    </Box>
                  </Paper>
                </Grid>
              )
            })}
          </Grid>
        </Paper>
      </Container>
    </Box>
  )
}