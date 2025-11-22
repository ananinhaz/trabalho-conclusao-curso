import { useEffect, useState, useMemo } from 'react'
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
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline'
import PetsIcon from '@mui/icons-material/Pets'
import CakeIcon from '@mui/icons-material/Cake'
import BoltIcon from '@mui/icons-material/Bolt'
import ChildFriendlyIcon from '@mui/icons-material/ChildFriendly'
import WhatsAppIcon from '@mui/icons-material/WhatsApp'
import EditIcon from '@mui/icons-material/Edit'
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline'
import VolunteerActivismRoundedIcon from '@mui/icons-material/VolunteerActivismRounded'; // Ícone escolhido

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

  const primaryColor = '#6366F1'
  const primaryColorHover = '#4F46E5'
  const forteColor = '#22C55E'
  const adotadoColor = '#D946EF'

  const cardStyles = {
    borderRadius: '0.9rem',
    boxShadow: '0 8px 30px rgba(15, 23, 42, 0.06)',
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
    minHeight: 440,
    transition: 'transform 0.2s, box-shadow 0.2s',
    '&:hover': {
      transform: 'translateY(-4px)',
      boxShadow: '0 18px 40px rgba(15,23,42,0.08)',
    },
  }

  const mainPaperStyles = {
    borderRadius: '1rem',
    boxShadow: '0 10px 30px rgba(15,23,42,0.015)',
    p: { xs: 2, sm: 3 },
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
      .map((r) => byId.get(Number(r.id)))
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
      especies: ['Todas', ...Array.from(especies).sort()],
      portes: ['Todas', ...Array.from(portes).sort()],
      cidades: Array.from(cidades).sort(),
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
      const FRONT_HOST = process.env.REACT_APP_FRONT_HOME || 'http://localhost:5173'
      src = FRONT_HOST.replace(/\/$/, '') + src
    }
    return src
  }

  const avatarSrc = getAvatarSrc()
  const userInitials = user?.nome ? user.nome.split(' ').map((n) => n[0]).join('').toUpperCase().substring(0, 2) : 'U'
  const handleProfileClick = () => (window.location.href = '/perfil')
  
  const AttributeChip = ({ label, icon }) => (
    <Chip
      label={label}
      size="small"
      icon={icon}
      variant="outlined"
      sx={{
        borderRadius: 999,
        fontWeight: 600,
        fontSize: '0.72rem',
        height: 28,
        borderColor: primaryColor,
        color: '#6b7280', 
        background: '#fff',
        '& .MuiChip-icon': {
          color: primaryColor,
          fontSize: 16,
        },
      }}
    />
  )

  function clearFilters() {
    setFilterEspecie('Todas')
    setFilterPorte('Todas')
    setFilterIdadeCat('Todas')
    setFilterCidade('')
  }

  return (
    <Box sx={{ p: { xs: 2, sm: 3 }, bgcolor: '#F9FAFB', minHeight: '100vh', position: 'relative' }}>
      {/* Avatar do user */}
      <Box sx={{ position: 'absolute', top: { xs: 16, sm: 24 }, right: { xs: 16, sm: 24 }, zIndex: 10 }}>
        <IconButton onClick={handleProfileClick} sx={{ p: 0 }}>
          <Avatar sx={{ bgcolor: primaryColor, width: 40, height: 40, fontSize: '0.95rem', boxShadow: '0 2px 6px rgba(0,0,0,0.12)' }} alt={user?.nome || 'Usuário'} src={avatarSrc || undefined} imgProps={{ referrerPolicy: 'no-referrer' }}>
            {userInitials}
          </Avatar>
        </IconButton>
      </Box>

      <Container maxWidth="lg" sx={{ p: 0 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" alignItems={{ xs: 'flex-start', sm: 'center' }} sx={{ mb: 3, gap: 2 }}>
          <Typography variant="h5" sx={{ fontWeight: 600, color: '#0f172a' }}>
            Animais
          </Typography>

          <Stack direction="row" spacing={1} sx={{ mr: { sm: 7 } }}>
            {['all', 'mine', 'recs'].map((tabValue) => (
              <Button
                key={tabValue}
                variant={tab === tabValue ? 'contained' : 'outlined'}
                onClick={() => setTab(tabValue)}
                sx={{
                  borderRadius: '9999px',
                  bgcolor: tab === tabValue ? primaryColor : '#fff',
                  borderColor: primaryColor,
                  color: tab === tabValue ? '#fff' : primaryColor,
                  textTransform: 'none',
                  fontWeight: 500,
                  fontSize: '0.875rem',
                  height: '36px',
                  padding: '0 14px',
                  boxShadow: 'none',
                  '&:hover': { bgcolor: tab === tabValue ? primaryColorHover : '#F4F4FE', borderColor: primaryColorHover },
                  ...(tabValue === 'all' && { display: { xs: 'none', sm: 'flex' } }),
                  
                }}
              >
                {tabValue === 'all' ? 'Todos' : tabValue === 'mine' ? 'Meus anúncios' : 'Recomendados'}
              </Button>
              
            ))}
            <Button
              variant="outlined"
              size="small"
              onClick={() => navigate("/doar")}
              sx={{
                borderRadius: '9999px',
                bgcolor: '#fff',
                borderColor: primaryColor,
                color: primaryColor,
                textTransform: 'none',
                fontWeight: 500,
                fontSize: '0.875rem',
                height: '36px',
                padding: '0 14px',
                boxShadow: 'none',
                '&:hover': { bgcolor: '#F4F4FE', borderColor: primaryColorHover },
                display: { xs: 'none', sm: 'inline-flex' },
              }}
            >
              Quero doar
            </Button>
          </Stack>
        </Stack>

        <Paper sx={{ ...mainPaperStyles }}>
          <Box sx={{ display: 'flex', gap: 1.25, mb: 2, flexWrap: 'wrap', alignItems: 'center' }}>
            <FormControl size="small" sx={{ minWidth: 160, borderRadius: 2 }}>
              <InputLabel id="f-especie-label">Espécie</InputLabel>
              <Select labelId="f-especie-label" value={filterEspecie} label="Espécie" onChange={(e) => setFilterEspecie(e.target.value)} sx={{ borderRadius: '10px', '& .MuiOutlinedInput-notchedOutline': { borderColor: '#E6E8FF' } }}>
                {options.especies.map((sp) => <MenuItem key={sp} value={sp}>{sp}</MenuItem>)}
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 140 }}>
              <InputLabel id="f-idade-label">Idade</InputLabel>
              <Select labelId="f-idade-label" value={filterIdadeCat} label="Idade" onChange={(e) => setFilterIdadeCat(e.target.value)} sx={{ borderRadius: '10px' }}>
                <MenuItem value="Todas">Todas</MenuItem>
                <MenuItem value="Filhote">Filhote</MenuItem>
                <MenuItem value="Adulto">Adulto</MenuItem>
                <MenuItem value="Idoso">Idoso</MenuItem>
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 140 }}>
              <InputLabel id="f-porte-label">Porte</InputLabel>
              <Select labelId="f-porte-label" value={filterPorte} label="Porte" onChange={(e) => setFilterPorte(e.target.value)} sx={{ borderRadius: '10px' }}>
                {options.portes.map((pt) => <MenuItem key={pt} value={pt}>{pt}</MenuItem>)}
              </Select>
            </FormControl>
            <TextField size="small" placeholder="Cidade" value={filterCidade} onChange={(e) => setFilterCidade(e.target.value)} sx={{ minWidth: 180, '& .MuiOutlinedInput-root': { borderRadius: '10px' }, '& .MuiOutlinedInput-notchedOutline': { borderColor: '#E6E8FF' } }} />
            <Button variant="outlined" onClick={clearFilters} sx={{ height: 36, borderRadius: '10px' }}>LIMPAR FILTROS</Button>
          </Box>

          <Grid container spacing={3} justifyContent="center">
            {filteredData.length === 0 && <Typography sx={{ p: 2, color: '#475569' }}>Nenhum resultado.</Typography>}

            {filteredData.map((animal) => {
              const isRecommended = recIdSet.has(Number(animal.id))
              const isMine = Number(animal.doador_id || 0) === Number(user?.id || 0)
              const isAdopted = Boolean(animal.adotado_em)

              // Lógica de selo
              let seloCor = primaryColor
              let seloLabel = 'Recomendado para você'
              const recIndex = recommendedItems.findIndex((item) => Number(item.id) === Number(animal.id))
              const isStronglyRecommended = isRecommended && recIndex === 0 && recommendedItems.length > 0
              if (isStronglyRecommended) {
                seloCor = forteColor
                seloLabel = 'Fortemente Recomendado'
              }

              return (
                <Grid item xs={12} sm={6} md={4} key={animal.id} sx={{ display: 'flex' }}>
                  <Paper
                    sx={{
                      ...cardStyles,
                      flex: 1,
                      maxWidth: 480,
                      margin: '0 auto',
                      display: 'flex',
                      flexDirection: 'column'
                    }}
                  >
                    {/* selo */}
                    {isRecommended && (
                      <Stack direction="row" alignItems="center" justifyContent="center" sx={{ pt: 1.2, mb: 0.6 }}>
                        <CheckCircleOutlineIcon sx={{ color: seloCor, fontSize: '1.1rem', mr: 0.6 }} />
                        <Typography variant="body2" sx={{ color: seloCor, fontWeight: 700, fontSize: '0.82rem' }}>
                          {seloLabel}
                        </Typography>
                      </Stack>
                    )}

                    {/* img+selo adotado*/}
                    <Box sx={{ width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', pt: isRecommended ? 0 : 1.2, position: 'relative' }}>
                      <Box
                        sx={{
                          width: 150,
                          height: 150,
                          backgroundImage: `url('${animal.photo_url || ''}')`,
                          backgroundPosition: 'center',
                          backgroundSize: 'cover',
                          borderRadius: '50%',
                          boxShadow: '0 8px 22px rgba(0,0,0,0.08)',
                          border: '6px solid #fff',
                          mt: -1,
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

                    <Box sx={{ p: 2, pt: 1.2, flexGrow: 1, display: 'flex', flexDirection: 'column', textAlign: 'center' }}>
                      <Typography fontWeight={700} color="#0f172a" sx={{ fontSize: '1.05rem', mb: 0.6 }}>
                        {animal.nome}
                      </Typography>
                      
                      {/* Chips */}
                      <Stack direction="row" spacing={0.6} sx={{ mb: 1, flexWrap: 'wrap', gap: 0.5, justifyContent: 'center', minHeight: 44 }}>
                        <AttributeChip label={animal.especie} icon={<PetsIcon />} />
                        {animal.porte && <AttributeChip label={animal.porte} icon={<PetsIcon />} />}
                        {animal.idade && <AttributeChip label={`${animal.idade} ${Number(animal.idade) > 1 ? 'anos' : 'ano'}`} icon={<CakeIcon />} />}
                        {animal.energia && <AttributeChip label={animal.energia} icon={<BoltIcon />} />}
                        {animal.bom_com_criancas !== null && (
                          <AttributeChip label={animal.bom_com_criancas ? 'Bom com crianças' : 'Não é bom com crianças'} icon={<ChildFriendlyIcon />} />
                        )}
                      </Stack>

                      <Typography variant="body2" color="#64748b" sx={{ fontSize: '0.8rem', mt: 0.5, mb: 0.4 }}>
                        <Stack direction="row" spacing={0.5} alignItems="center" justifyContent="center">
                          <LocationOnIcon sx={{ fontSize: '0.85rem', color: '#94A3B8' }} />
                          <span>{animal.cidade}</span>
                        </Stack>
                      </Typography>

                      <Typography variant="body2" sx={{ mt: 1, color: '#475569', minHeight: 40, fontSize: '0.86rem' }}>
                        {animal.descricao || 'Nenhuma descrição detalhada fornecida.'}
                      </Typography>

                      {/* area de ação */}
                      <Box sx={{ mt: 2, pt: 1, borderTop: '1px solid #f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <Stack direction="row" spacing={0.5} justifyContent="center" alignItems="center">
                          {/* Visitante vê botão de contato se NÃO adotado */}
                          {animal.donor_whatsapp && !isMine && !isAdopted && (
                            <Tooltip title="Falar com doador">
                              <IconButton
                                href={`https://wa.me/${animal.donor_whatsapp}`}
                                target="_blank"
                                size="small"
                                sx={{ color: '#25D366', '&:hover': { bgcolor: 'rgba(37,211,102,0.06)' } }}
                              >
                                <WhatsAppIcon sx={{ fontSize: 25 }} />
                              </IconButton>
                            </Tooltip>
                          )}

                          {isMine && (
                            <>
                              {/* Marcar Adotado / Desmarcar */}
                              <Tooltip title={isAdopted ? "Marcar como disponível" : "Marcar como adotado"}>
                                <IconButton
                                  onClick={() => handleAdoptToggle(animal)}
                                  size="small"
                                  sx={{
                                    mr: 0.6,
                                    transition: 'transform 0.18s ease, color 0.18s ease',
                                    color: isAdopted ? adotadoColor : '#6366F1', 
                                    '&:hover': { 
                                      transform: 'scale(1.12)', 
                                      color: isAdopted ? '#D946EF' : adotadoColor 
                                    },
                                  }}
                                >
                                  <VolunteerActivismRoundedIcon sx={{ fontSize: 28 }} />
                                </IconButton>
                              </Tooltip>

                              <Tooltip title="Editar anúncio">
                                <IconButton onClick={() => handleEdit(animal.id)} size="small" sx={{ color: '#8c8c90ff', '&:hover': { bgcolor: 'rgba(99,102,241,0.06)' } }}>
                                  <EditIcon sx={{ fontSize: 25 }} />
                                </IconButton>
                              </Tooltip>

                              <Tooltip title="Excluir anúncio">
                                <IconButton onClick={() => handleDelete(animal.id)} size="small" sx={{ color: '#EF4444', '&:hover': { bgcolor: 'rgba(239,68,68,0.06)' } }}>
                                  <DeleteOutlineIcon sx={{ fontSize: 25 }} />
                                </IconButton>
                              </Tooltip>
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
