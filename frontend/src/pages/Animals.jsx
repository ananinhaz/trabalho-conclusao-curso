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
import LocationOnIcon from '@mui/icons-material/LocationOn'; // Importado para ícone de cidade

export default function Animals({ user }) {
  const [all, setAll] = useState([])
  const [mine, setMine] = useState([])
  const [recs, setRecs] = useState({ items: [], ids: [] })
  const [tab, setTab] = useState('all')

  const primaryColor = '#6366F1'
  const primaryColorHover = '#4F46E5'
  const forteColor = '#22C55E' 
  const menosColor = '#F97316' 

  const cardStyles = {
    borderRadius: '1.25rem',
    boxShadow: '0 15px 45px rgba(15, 23, 42, 0.05)',
    overflow: 'hidden',
    transition: 'transform 0.2s, box-shadow 0.2s',
    '&:hover': {
      transform: 'translateY(-3px)',
      boxShadow: '0 20px 60px rgba(15, 23, 42, 0.1)',
    },
  }
  const mainPaperStyles = {
    borderRadius: '1.25rem',
    boxShadow: '0 20px 50px rgba(15,23,42,0.03)',
  }

  useEffect(() => {
    ;(async () => {
      // Chamamos apenas os 4 melhores. Ajuste este número '4' se quiser mostrar mais ou menos.
      const [a, m, r] = await Promise.all([
        animaisApi.list(),
        animaisApi.mine(),
        recApi.list(4), // Recomendação limitada a 4
      ])

      setRecs({
        items: r.items || [],
        ids: r.ids || [], 
      })

      setAll(a || [])
      setMine(m || [])

      console.log('IA mandou esses IDs:', r.ids)
    })()
  }, [])

  // lista que a aba "recomendados" vai mostrar
  const recommendedItems = recs.items || []

  // 👇 só esses ids aqui terão selo
  const recIdSet = new Set((recs.ids || []).map(n => Number(n)))

  // qual lista mostrar
  const data =
    tab === 'mine'
      ? mine
      : tab === 'recs'
      ? recommendedItems
      : all || []

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
    <Box sx={{ p: { xs: 2, sm: 3 }, bgcolor: '#F9FAFB', minHeight: '100vh' }}>
      <Container maxWidth="lg" sx={{ p: 0 }}>
        <Paper sx={{ ...mainPaperStyles, p: { xs: 2, sm: 3 } }}>
          <Stack
            direction={{ xs: 'column', sm: 'row' }}
            justifyContent="space-between"
            alignItems={{ xs: 'flex-start', sm: 'center' }}
            sx={{ mb: 3, gap: 2 }}
          >
            <Typography variant="h5" sx={{ fontWeight: 600, color: '#0f172a' }}>
              Animais
            </Typography>
            <Stack direction="row" spacing={1}>
              <Button
                variant={tab === 'all' ? 'contained' : 'outlined'}
                onClick={() => setTab('all')}
                sx={{
                  borderRadius: '9999px',
                  bgcolor: tab === 'all' ? primaryColor : '#fff',
                  borderColor: primaryColor,
                  color: tab === 'all' ? '#fff' : primaryColor,
                  textTransform: 'none',
                  fontWeight: 600,
                  boxShadow: 'none',
                  '&:hover': {
                    bgcolor: tab === 'all' ? primaryColorHover : '#F4F4FE',
                    borderColor: primaryColorHover,
                  },
                }}
              >
                Todos
              </Button>
              <Button
                variant={tab === 'mine' ? 'contained' : 'outlined'}
                onClick={() => setTab('mine')}
                sx={{
                  borderRadius: '9999px',
                  bgcolor: tab === 'mine' ? primaryColor : '#fff',
                  borderColor: primaryColor,
                  color: tab === 'mine' ? '#fff' : primaryColor,
                  textTransform: 'none',
                  fontWeight: 600,
                  boxShadow: 'none',
                  '&:hover': {
                    bgcolor: tab === 'mine' ? primaryColorHover : '#F4F4FE',
                    borderColor: primaryColorHover,
                  },
                }}
              >
                Meus anúncios
              </Button>
              <Button
                variant={tab === 'recs' ? 'contained' : 'outlined'}
                onClick={() => setTab('recs')}
                sx={{
                  borderRadius: '9999px',
                  bgcolor: tab === 'recs' ? primaryColor : '#fff',
                  borderColor: primaryColor,
                  color: tab === 'recs' ? '#fff' : primaryColor,
                  textTransform: 'none',
                  fontWeight: 600,
                  boxShadow: 'none',
                  '&:hover': {
                    bgcolor: tab === 'recs' ? primaryColorHover : '#F4F4FE',
                    borderColor: primaryColorHover,
                  },
                }}
              >
                Recomendados
              </Button>
            </Stack>
          </Stack>

          <Grid container spacing={3}>
            {data.length === 0 && (
              <Typography sx={{ p: 2, color: '#475569' }}>
                Nenhum resultado.
              </Typography>
            )}

            {data.map(animal => {
              const isRecommended = recIdSet.has(Number(animal.id))
              const showRecommendedChip = isRecommended && tab !== 'recs'
              const isMine = animal.doador_id === user?.id

              let chipLabel = 'Recomendado'
              let chipColor = primaryColor
              let chipIcon = (
                <CheckCircleOutlineIcon sx={{ color: '#fff !important' }} />
              )

              if (isRecommended) {
                const recIndex = recommendedItems.findIndex(
                  item => item.id === animal.id
                )
                const isFirst = recIndex === 0 && recommendedItems.length > 0
                const isLast =
                  recIndex === recommendedItems.length - 1 &&
                  recommendedItems.length > 1

                if (isFirst) {
                  chipLabel = 'Fortemente Recomendado'
                  chipColor = forteColor
                  chipIcon = null
                } else if (isLast) {
                  chipLabel = 'Menos Recomendado'
                  chipColor = menosColor
                  chipIcon = null
                }
              }

              return (
                <Grid item xs={12} sm={6} md={4} key={animal.id}>
                  <Paper sx={{ ...cardStyles, position: 'relative' }}>
                    <Box
                      sx={{
                        height: 150,
                        background: `#f1f5f9 url('${
                          animal.photo_url || ''
                        }) center/cover no-repeat`,
                        position: 'relative',
                        borderTopLeftRadius: '1.25rem',
                        borderTopRightRadius: '1.25rem',
                      }}
                    >
                      {showRecommendedChip && (
                        <Chip
                          label={chipLabel}
                          size="small"
                          icon={chipIcon}
                          sx={{
                            position: 'absolute',
                            top: 10,
                            left: 10,
                            bgcolor: chipColor,
                            color: '#fff',
                            fontWeight: 600,
                            fontSize: '0.75rem',
                            height: '24px',
                            paddingLeft: chipIcon ? '6px' : '10px',
                            paddingRight: '10px',
                          }}
                        />
                      )}
                    </Box>

                    <Box sx={{ p: 2 }}>
                      <Typography
                        fontWeight={600}
                        color="#0f172a"
                        sx={{ fontSize: '1.15rem' }}
                      >
                        {animal.nome}
                      </Typography>
                      
                      {/* ✅ INFORMAÇÕES DETALHADAS COM CHIPS */}
                      <Stack direction="row" spacing={1} sx={{ mt: 0.5, mb: 1 }}>
                        <Chip 
                          label={animal.especie} 
                          size="small" 
                          color="primary" 
                          variant="outlined" 
                        />
                        {animal.porte && <Chip 
                          label={animal.porte} 
                          size="small" 
                          color="default" 
                          variant="filled"
                        />}
                        {animal.idade && <Chip 
                          label={animal.idade} 
                          size="small" 
                          color="default" 
                          variant="outlined" 
                        />}
                        {animal.raca && <Chip 
                          label={animal.raca} 
                          size="small" 
                          color="default" 
                          variant="outlined" 
                        />}
                      </Stack>
                      
                      <Typography
                        variant="body2"
                        color="#64748b"
                        sx={{ fontSize: '0.85rem' }}
                      >
                        <Stack direction="row" spacing={0.5} alignItems="center">
                            <LocationOnIcon sx={{ fontSize: '1rem' }} />
                            <span>{animal.cidade}</span>
                        </Stack>
                      </Typography>
                      
                      <Typography
                        variant="body2"
                        sx={{ mt: 1, color: '#475569', minHeight: 40 }}
                      >
                        {animal.descricao || 'Nenhuma descrição detalhada fornecida.'}
                      </Typography>

                      <Stack
                        direction="row"
                        spacing={1}
                        sx={{
                          mt: 2,
                          pt: 1,
                          borderTop: '1px solid #f1f5f9',
                        }}
                      >
                        {animal.donor_whatsapp && (
                          <Button
                            size="small"
                            variant="outlined"
                            href={`https://wa.me/${animal.donor_whatsapp}`}
                            target="_blank"
                            sx={{
                              borderRadius: '9999px',
                              textTransform: 'none',
                              fontWeight: 600,
                              borderColor: primaryColor,
                              color: primaryColor,
                              '&:hover': {
                                borderColor: primaryColorHover,
                                bgcolor: '#F4F4FE',
                              },
                            }}
                          >
                            Falar com doador
                          </Button>
                        )}
                        {isMine && (
                          <Button
                            size="small"
                            color="error"
                            onClick={() => handleDelete(animal.id)}
                            sx={{
                              borderRadius: '9999px',
                              textTransform: 'none',
                              fontWeight: 600,
                            }}
                          >
                            Excluir
                          </Button>
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