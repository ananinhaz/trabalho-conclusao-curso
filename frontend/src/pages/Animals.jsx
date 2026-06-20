import { useEffect, useState, useMemo } from 'react'
import PropTypes from 'prop-types'
import { useNavigate } from 'react-router-dom'
import { animaisApi, recApi, authApi } from '../api'
import {
  Box,
  Paper,
  Typography,
  Button,
  Stack,
  Chip,
  Grid,
  Container,
  IconButton,
  Avatar,
  Tooltip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
} from '@mui/material'

import LocationOnIcon from '@mui/icons-material/LocationOn'
import PetsIcon from '@mui/icons-material/Pets'
import CakeIcon from '@mui/icons-material/Cake'
import BoltIcon from '@mui/icons-material/Bolt'
import ChildFriendlyIcon from '@mui/icons-material/ChildFriendly'
import EditIcon from '@mui/icons-material/Edit'
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline'
import VolunteerActivismRoundedIcon from '@mui/icons-material/VolunteerActivismRounded'
import FavoriteBorderIcon from '@mui/icons-material/FavoriteBorder'
import FilterListOffIcon from '@mui/icons-material/FilterListOff'
import { colors, gradientPrimary, shadows, radii, cardSx, btnGradient, btnEdit, btnDelete, btnOutline, inputSx } from '../theme'

const localeSort = (a, b) => a.localeCompare(b, 'pt', { sensitivity: 'base' })

function getCompatibilityBadge(score) {
  if (score == null) return null

  if (score < 30) return null

  if (score >= 85) {
    return {
      label: '⭐ Excelente compatibilidade',
      bgcolor: colors.goldBg,
      color: colors.goldText,
    }
  }

  if (score >= 70) {
    return {
      label: '✅ Boa compatibilidade',
      bgcolor: '#EEF2FF',
      color: colors.primary,
    }
  }

  if (score >= 50) {
    return {
      label: '🐾 Compatibilidade intermediária',
      bgcolor: '#FFF8E1',
      color: '#B45309',
    }
  }

  return {
    label: '🔎 Requer mais atenção',
    bgcolor: '#F3F4F6',
    color: colors.textMuted,
  }
}


export default function Animals({ user: userProp }) {
  const navigate = useNavigate()
  const [all, setAll] = useState([])
  const [mine, setMine] = useState([])
  const [recs, setRecs] = useState({ items: [], ids: [] })
  const [tab, setTab] = useState('all')
  const [user, setUser] = useState(userProp || null)

  // filtros 
  const [filterEspecie, setFilterEspecie] = useState('Todas')
  const [filterIdadeCat, setFilterIdadeCat] = useState('Todas')
  const [filterPorte, setFilterPorte] = useState('Todas')
  const [filterCidade, setFilterCidade] = useState('')

  const primaryColor = colors.primary
  const primaryColorHover = '#4F46E5'
  const adotadoColor = '#8B5CF6'

  const cardStyles = {
    ...cardSx,
    borderRadius: '20px',
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
    minHeight: 480,
    transition: 'all 0.2s ease',
    '&:hover': {
      transform: 'translateY(-4px)',
      boxShadow: shadows.hover,
    },
  }

  const mainPaperStyles = {
    ...cardSx,
    borderRadius: radii.card,
    p: { xs: 2.5, sm: 3.5 },
  }

  useEffect(() => {
    ;(async () => {
      const [a, m, r] = await Promise.all([animaisApi.list(), animaisApi.mine(), recApi.list(6)])
      setRecs({
        items: r.items || [],
        ids: r.ids || [],
      })
      setAll(a || [])
      setMine(m || [])
    })()
  }, [])

  useEffect(() => {
    setUser(userProp || null)
  }, [userProp])

  // fallback dev: /auth/me
  useEffect(() => {
    if (!user) {
      ;(async () => {
        try {
          if (authApi && authApi.me) {
            const me = await authApi.me()
            if (me && me.user) {
              setUser(me.user)
            } else if (me && me.authenticated && me.user_id) {
              setUser({ id: me.user_id, nome: 'Usuário' })
            }
          }
        } catch (err) {}
      })()
    }
  }, [user])

  const recommendedItems = recs.items || []
  const recIdSet = new Set(
    (recommendedItems.length > 0 ? recommendedItems.map((it) => Number(it.id)) : (recs.ids || []).map((n) => Number(n))).filter(
      (v) => !Number.isNaN(v)
    )
  )

  const baseData = tab === 'mine' ? mine : tab === 'recs' ? recommendedItems : all || []
  const orderedBaseData = useMemo(() => {
    const data = baseData || []
    if (tab !== 'all') return data

    const byId = new Map(data.map((d) => [Number(d.id), d]))

    // pega os recomendados que existem em todos na ordem de recommendedItems
    const recsInAll = (recommendedItems || [])
      .map((r) => {
        const base = byId.get(Number(r.id))
        return base ? { ...base, compatibility_score: r.compatibility_score } : null
      })
      .filter(Boolean)

    const others = data.filter((d) => !recIdSet.has(Number(d.id)))

    return [...recsInAll, ...others]
  }, [baseData, tab, recommendedItems, recIdSet])

  function getAgeCategory(raw) {
    if (!raw && raw !== 0) return 'Adulto'
    const s = String(raw).toLowerCase()
    if (s.includes('filh') || s.includes('filhote')) return 'Filhote'
    if (s.includes('idos') || s.includes('idoso')) return 'Idoso'
    const n = Number(s)
    if (!Number.isNaN(n)) {
      if (n <= 1) return 'Filhote'
      if (n >= 8) return 'Idoso'
      return 'Adulto'
    }
    return 'Adulto'
  }

  const options = useMemo(() => {
    const especies = new Set()
    const portes = new Set()
    const cidades = new Set()
    ;(all || []).forEach((a) => {
      if (a?.especie) especies.add(String(a.especie))
      if (a?.porte) portes.add(String(a.porte))
      if (a?.cidade) cidades.add(String(a.cidade))
    })
    return {
      especies: ['Todas', ...Array.from(especies).sort(localeSort)],
      portes: ['Todas', ...Array.from(portes).sort(localeSort)],
      cidades: Array.from(cidades).sort(localeSort),
    }
  }, [all])

  const filteredData = useMemo(() => {
    return (orderedBaseData || []).filter((animal) => {
      if (filterEspecie && filterEspecie !== 'Todas' && (!animal.especie || String(animal.especie) !== filterEspecie)) return false
      if (filterPorte && filterPorte !== 'Todas' && (!animal.porte || String(animal.porte) !== filterPorte)) return false
      if (filterCidade && filterCidade.trim() !== '' && !String(animal.cidade || '').toLowerCase().includes(filterCidade.trim().toLowerCase())) return false
      if (filterIdadeCat && filterIdadeCat !== 'Todas' && getAgeCategory(animal.idade) !== filterIdadeCat) return false
      return true
    })
  }, [orderedBaseData, filterEspecie, filterPorte, filterCidade, filterIdadeCat])

  async function handleDelete(id) {
    if (!window.confirm('Excluir anúncio?')) return
    await animaisApi.remove(id)
    setAll((prev) => prev.filter((x) => x.id !== id))
    setMine((prev) => prev.filter((x) => x.id !== id))
    setRecs((prev) => ({ ...prev, items: (prev.items || []).filter((x) => x.id !== id) }))
  }

  function handleEdit(id) {
    navigate(`/animais/editar/${id}`)
  }

  async function handleAdoptToggle(animal) {
    try {
      const isMine = Number(animal.doador_id || 0) === Number(user?.id || 0)
      if (!isMine) {
        alert('Apenas o responsável pelo anúncio pode marcar como adotado.')
        return
      }
      const already = Boolean(animal.adotado_em)
      const action = already ? 'undo' : 'mark'
      const confirmMsg = already ? 'Deseja marcar este animal como disponível novamente?' : 'Confirma marcar este animal como ADOTADO? Parabéns! 🎉'
      if (!window.confirm(confirmMsg)) return

      const resp = await animaisApi.adopt(animal.id, { action })
      const updated = (resp && resp.animal) ? resp.animal : null

      if (updated) {
        setAll((prev) => prev.map((a) => (Number(a.id) === Number(updated.id) ? updated : a)))
        setMine((prev) => prev.map((a) => (Number(a.id) === Number(updated.id) ? updated : a)))
        setRecs((prev) => ({
          ...prev,
          items: (prev.items || []).map((a) => (Number(a.id) === Number(updated.id) ? updated : a)),
        }))
      } else {
        // Fallback local se a API não retornar o objeto atualizado completo
        const localUpdated = { ...animal, adotado_em: action === 'mark' ? new Date().toISOString().slice(0, 10) : null }
        setAll((prev) => prev.map((a) => (Number(a.id) === Number(localUpdated.id) ? localUpdated : a)))
        setMine((prev) => prev.map((a) => (Number(a.id) === Number(localUpdated.id) ? localUpdated : a)))
        setRecs((prev) => ({
          ...prev,
          items: (prev.items || []).map((a) => (Number(a.id) === Number(localUpdated.id) ? localUpdated : a)),
        }))
      }
    } catch (err) {
      console.error('Erro ao marcar adotado:', err)
      alert('Erro ao atualizar o status de adoção.')
    }
  }

  const getAvatarSrc = () => {
    const candidates = [user?.avatar_url, user?.photo_url, user?.avatar, user?.picture, user?.photo, user?.profile_image]
    let src = candidates.find(Boolean) || ''
    if (src && src.startsWith('/')) {
      const FRONT_HOST = import.meta.env.VITE_FRONT_HOME || window.location.origin
      src = FRONT_HOST.replace(/\/$/, '') + src
    }
    return src
  }

  const avatarSrc = getAvatarSrc()
  const userInitials = user?.nome ? user.nome.split(' ').map((n) => n[0]).join('').toUpperCase().substring(0, 2) : 'U'
  const handleProfileClick = () => (window.location.href = '/perfil')
  
  function AttributeChip({ label, icon }) {
    return (
    <Chip
      label={label}
      size="small"
      icon={icon}
      variant="outlined"
      sx={{
        borderRadius: radii.pill,
        fontWeight: 600,
        fontSize: '0.72rem',
        height: 28,
        borderColor: '#E2E8F0',
        color: colors.textMuted,
        background: colors.card,
        '& .MuiChip-icon': {
          color: colors.primary,
          fontSize: 16,
        },
      }}
    />
    )
  }

  AttributeChip.propTypes = {
    label: PropTypes.string.isRequired,
    icon: PropTypes.element.isRequired,
  }

  function clearFilters() {
    setFilterEspecie('Todas')
    setFilterPorte('Todas')
    setFilterIdadeCat('Todas')
    setFilterCidade('')
  }

  return (
    <Box sx={{ p: { xs: 2, sm: 3 }, bgcolor: colors.background, minHeight: '100vh', position: 'relative' }}>
      <Box sx={{ position: 'absolute', top: { xs: 16, sm: 24 }, right: { xs: 16, sm: 24 }, zIndex: 10 }}>
        <IconButton
          onClick={handleProfileClick}
          sx={{
            p: 0,
            transition: 'all 0.2s ease',
            '&:hover': { transform: 'scale(1.05)' },
          }}
        >
          <Avatar
            sx={{
              bgcolor: colors.primary,
              width: 44,
              height: 44,
              fontSize: '0.95rem',
              boxShadow: shadows.soft,
              border: '2px solid #fff',
            }}
            alt={user?.nome || 'Usuário'}
            src={avatarSrc || undefined}
            imgProps={{ referrerPolicy: 'no-referrer' }}
          >
            {userInitials}
          </Avatar>
        </IconButton>
      </Box>

      <Container maxWidth="lg" sx={{ p: 0 }}>
        <Box sx={{ mb: 3.5, pr: { sm: 7 } }}>
          <Typography variant="h4" sx={{ fontWeight: 800, color: colors.text, fontSize: { xs: '1.6rem', md: '2rem' } }}>
            Animais para adoção
          </Typography>
          <Typography sx={{ color: colors.textMuted, mt: 0.5, fontSize: '0.95rem' }}>
            Encontre seu novo melhor amigo ou gerencie seus anúncios
          </Typography>
        </Box>

        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          justifyContent="space-between"
          alignItems={{ xs: 'flex-start', sm: 'center' }}
          sx={{ mb: 3, gap: 2, mr: { sm: 7 } }}
        >
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            {['all', 'mine', 'recs'].map((tabValue) => (
              <Button
                key={tabValue}
                variant={tab === tabValue ? 'contained' : 'outlined'}
                onClick={() => setTab(tabValue)}
                sx={{
                  borderRadius: radii.pill,
                  bgcolor: tab === tabValue ? undefined : colors.card,
                  background: tab === tabValue ? gradientPrimary : undefined,
                  borderColor: colors.primary,
                  color: tab === tabValue ? '#fff' : colors.primary,
                  textTransform: 'none',
                  fontWeight: 600,
                  fontSize: '0.875rem',
                  height: 40,
                  px: 2,
                  boxShadow: 'none',
                  transition: 'all 0.2s ease',
                  '&:hover': {
                    bgcolor: tab === tabValue ? undefined : '#EEF2FF',
                    background: tab === tabValue ? 'linear-gradient(90deg, #4F46E5, #7C3AED)' : undefined,
                    borderColor: primaryColorHover,
                  },
                  ...(tabValue === 'all' && { display: { xs: 'none', sm: 'flex' } }),
                }}
              >
                {tabValue === 'all' ? 'Todos' : tabValue === 'mine' ? 'Meus anúncios' : 'Recomendados'}
              </Button>
            ))}
            <Button
              variant="outlined"
              onClick={() => navigate('/doar')}
              sx={{
                ...btnOutline,
                height: 40,
                px: 2,
                display: { xs: 'none', sm: 'inline-flex' },
              }}
            >
              Quero doar
            </Button>
          </Stack>
        </Stack>

        <Paper sx={{ ...mainPaperStyles, mb: 3 }}>
          <Box
            sx={{
              display: 'flex',
              gap: 1.5,
              mb: 3,
              flexWrap: 'wrap',
              alignItems: 'center',
              p: 2,
              bgcolor: colors.background,
              borderRadius: radii.input,
            }}
          >
            <FormControl size="small" sx={{ minWidth: 160, ...inputSx }}>
              <InputLabel id="f-especie-label">Espécie</InputLabel>
              <Select labelId="f-especie-label" value={filterEspecie} label="Espécie" onChange={(e) => setFilterEspecie(e.target.value)}>
                {options.especies.map((sp) => <MenuItem key={sp} value={sp}>{sp}</MenuItem>)}
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 140, ...inputSx }}>
              <InputLabel id="f-idade-label">Idade</InputLabel>
              <Select labelId="f-idade-label" value={filterIdadeCat} label="Idade" onChange={(e) => setFilterIdadeCat(e.target.value)}>
                <MenuItem value="Todas">Todas</MenuItem>
                <MenuItem value="Filhote">Filhote</MenuItem>
                <MenuItem value="Adulto">Adulto</MenuItem>
                <MenuItem value="Idoso">Idoso</MenuItem>
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 140, ...inputSx }}>
              <InputLabel id="f-porte-label">Porte</InputLabel>
              <Select labelId="f-porte-label" value={filterPorte} label="Porte" onChange={(e) => setFilterPorte(e.target.value)}>
                {options.portes.map((pt) => <MenuItem key={pt} value={pt}>{pt}</MenuItem>)}
              </Select>
            </FormControl>
            <TextField
              size="small"
              placeholder="Cidade"
              value={filterCidade}
              onChange={(e) => setFilterCidade(e.target.value)}
              sx={{ minWidth: 200, ...inputSx }}
            />
            <Button
              variant="outlined"
              onClick={clearFilters}
              startIcon={<FilterListOffIcon />}
              sx={{
                height: 40,
                borderRadius: radii.button,
                textTransform: 'none',
                fontWeight: 600,
                borderColor: colors.border,
                color: colors.textMuted,
                '&:hover': { borderColor: colors.primary, color: colors.primary },
              }}
            >
              LIMPAR FILTROS
            </Button>
          </Box>

          <Grid container spacing={3} justifyContent="center">
            {filteredData.length === 0 && (
              <Typography sx={{ p: 3, color: colors.textMuted, width: '100%', textAlign: 'center' }}>
                Nenhum resultado.
              </Typography>
            )}

            {filteredData.map((animal) => {
              const isMine = Number(animal.doador_id || 0) === Number(user?.id || 0)
              const isAdopted = Boolean(animal.adotado_em)

              const compatScore = animal.compatibility_score
              const compatBadge = getCompatibilityBadge(compatScore)
              const showCompatBadge = compatBadge

              return (
                <Grid item xs={12} sm={6} md={4} key={animal.id} sx={{ display: 'flex' }}>
                  <Paper sx={{ ...cardStyles, flex: 1, maxWidth: 480, margin: '0 auto' }}>
                    {showCompatBadge && (
                      <Box sx={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        pt: 1.5,
                        pb: 0.5,
                        gap: 0.25,
                      }}>
                        <Box
                          sx={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            bgcolor: compatBadge.bgcolor,
                            color: compatBadge.color,
                            px: 1.5,
                            py: 0.5,
                            borderRadius: '8px',
                            fontSize: '0.78rem',
                            fontWeight: 700,
                          }}
                        >
                          {compatBadge.label}
                        </Box>

                        <Typography
                          variant="caption"
                          sx={{
                            fontWeight: 700,
                            color: compatBadge.color,
                          }}
                        >
                          {compatScore}% compatível
                        </Typography>
                      </Box>
                    )}

                    <Box sx={{ width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', pt: showCompatBadge ? 0.5 : 1.5, position: 'relative' }}>
                      <Box
                        sx={{
                          width: 160,
                          height: 160,
                          backgroundImage: `url('${animal.photo_url || ''}')`,
                          backgroundPosition: 'center',
                          backgroundSize: 'cover',
                          borderRadius: '50%',
                          boxShadow: shadows.card,
                          border: '5px solid #fff',
                          position: 'relative',
                        }}
                      />
                      
                      {/* selo sobre a foto */}
                      {isAdopted && (
                        <Box sx={{
                          position: 'absolute',
                          top: '50%',
                          left: '50%',
                          transform: 'translate(-50%, -50%)',
                          bgcolor: 'rgba(255,255,255,0.85)', 
                          borderRadius: '20px',
                          px: 1.5,
                          py: 0.5,
                          display: 'flex',
                          alignItems: 'center',
                          boxShadow: '0 4px 10px rgba(0,0,0,0.1)',
                          zIndex: 5
                        }}>
                          <VolunteerActivismRoundedIcon sx={{ color: adotadoColor, fontSize: 20, mr: 0.5 }} />
                          <Typography variant="caption" sx={{ fontWeight: 800, color: adotadoColor, letterSpacing: 0.5 }}>
                            ADOTADO
                          </Typography>
                        </Box>
                      )}
                    </Box>

                    <Box sx={{ p: 2.5, pt: 1.5, flexGrow: 1, display: 'flex', flexDirection: 'column', textAlign: 'center' }}>
                      <Typography fontWeight={800} color={colors.text} sx={{ fontSize: '1.15rem', mb: 0.75 }}>
                        {animal.nome}
                      </Typography>
                      <Stack direction="row" spacing={0.6} sx={{ mb: 1, flexWrap: 'wrap', gap: 0.5, justifyContent: 'center', minHeight: 44 }}>
                        <AttributeChip label={animal.especie} icon={<PetsIcon />} />
                        {animal.porte && <AttributeChip label={animal.porte} icon={<PetsIcon />} />}
                        {animal.idade && <AttributeChip label={`${animal.idade} ${Number(animal.idade) > 1 ? 'anos' : 'ano'}`} icon={<CakeIcon />} />}
                        {animal.energia && <AttributeChip label={animal.energia} icon={<BoltIcon />} />}
                        {animal.bom_com_criancas !== null && (
                          <AttributeChip label={animal.bom_com_criancas ? 'Bom com crianças' : 'Não é bom com crianças'} icon={<ChildFriendlyIcon />} />
                        )}
                      </Stack>

                      <Typography variant="body2" color={colors.textMuted} sx={{ fontSize: '0.82rem', mt: 0.5, mb: 0.5 }}>
                        <Stack direction="row" spacing={0.5} alignItems="center" justifyContent="center">
                          <LocationOnIcon sx={{ fontSize: '0.9rem', color: '#94A3B8' }} />
                          <span>{animal.cidade}</span>
                        </Stack>
                      </Typography>

                      <Typography variant="body2" sx={{ mt: 1, color: colors.textMuted, minHeight: 40, fontSize: '0.86rem', lineHeight: 1.5 }}>
                        {animal.descricao || 'Nenhuma descrição detalhada fornecida.'}
                      </Typography>

                      <Box sx={{ mt: 'auto', pt: 2, borderTop: '1px solid #F1F5F9' }}>
                        <Stack direction="row" spacing={1} justifyContent="center" alignItems="center" flexWrap="wrap" useFlexGap>
                          {animal.donor_whatsapp && !isMine && !isAdopted && (
                            <Button
                              component="a"
                              href={`https://wa.me/${animal.donor_whatsapp}`}
                              target="_blank"
                              startIcon={<FavoriteBorderIcon />}
                              sx={{ ...btnGradient, flex: { xs: '1 1 100%', sm: '0 1 auto' }, minWidth: 140 }}
                            >
                              Adotar / Interesse
                            </Button>
                          )}

                          {isMine && (
                            <>
                              <Tooltip title={isAdopted ? 'Marcar como disponível' : 'Marcar como adotado'}>
                                <Button
                                  onClick={() => handleAdoptToggle(animal)}
                                  startIcon={<VolunteerActivismRoundedIcon />}
                                  sx={{
                                    ...btnGradient,
                                    background: isAdopted ? 'linear-gradient(90deg, #8B5CF6, #A78BFA)' : gradientPrimary,
                                    minWidth: 120,
                                  }}
                                >
                                  {isAdopted ? 'Disponível' : 'Adotado 🎉'}
                                </Button>
                              </Tooltip>

                              <Button
                                onClick={() => handleEdit(animal.id)}
                                startIcon={<EditIcon />}
                                sx={{ ...btnEdit, minWidth: 100 }}
                              >
                                Editar
                              </Button>

                              <Button
                                onClick={() => handleDelete(animal.id)}
                                startIcon={<DeleteOutlineIcon />}
                                sx={{ ...btnDelete, minWidth: 100 }}
                              >
                                Excluir
                              </Button>
                            </>
                          )}
                        </Stack>
                      </Box>
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

Animals.propTypes = {
  user: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    nome: PropTypes.string,
    avatar_url: PropTypes.string,
    photo_url: PropTypes.string,
    avatar: PropTypes.string,
    picture: PropTypes.string,
    photo: PropTypes.string,
    profile_image: PropTypes.string,
    doador_id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  }),
}
