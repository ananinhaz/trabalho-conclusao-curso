import React from 'react'
import { Box, Container, Grid, Typography, Link, IconButton, Stack } from '@mui/material'
import EmailOutlinedIcon from '@mui/icons-material/EmailOutlined'
import GitHubIcon from '@mui/icons-material/GitHub'
import LinkedInIcon from '@mui/icons-material/LinkedIn'
import PetsIcon from '@mui/icons-material/Pets'
import { colors, shadows, radii } from '../theme'

export default function Footer() {
  const navLinks = [
    { label: 'Início', href: '/' },
    { label: 'Animais', href: '/animais' },
    { label: 'Quero adotar', href: '/login?next=/perfil-adotante' },
    { label: 'Quero doar', href: '/login?next=/doar' },
  ]

  const resourceLinks = [
    { label: 'Sobre o projeto', href: '/' },
    { label: 'Recomendações', href: '/animais' },
  ]

  return (
    <Box component="footer" sx={{ bgcolor: '#EEF2FF', py: 8, mt: 4 }}>
      <Container maxWidth="lg">
        <Grid container spacing={5}>
          <Grid item xs={12} md={4}>
            <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 2 }}>
              <PetsIcon sx={{ color: colors.primary }} />
              <Typography sx={{ fontWeight: 800, fontSize: '1.2rem', color: colors.text }}>
                AdoptMe
              </Typography>
            </Stack>
            <Typography sx={{ color: colors.textMuted, lineHeight: 1.8, fontSize: '0.95rem' }}>
              Plataforma acadêmica voltada para adoção responsável. Facilitamos conexões seguras
              entre pessoas e animais, com recomendações baseadas em compatibilidade real.
            </Typography>
          </Grid>

          <Grid item xs={12} sm={6} md={2}>
            <Typography sx={{ fontWeight: 700, color: colors.text, mb: 2 }}>Navegação</Typography>
            <Stack spacing={1.25}>
              {navLinks.map((link) => (
                <Link
                  key={link.label}
                  href={link.href}
                  underline="hover"
                  sx={{ color: colors.textMuted, fontSize: '0.9rem', '&:hover': { color: colors.primary } }}
                >
                  {link.label}
                </Link>
              ))}
            </Stack>
          </Grid>

          <Grid item xs={12} sm={6} md={2}>
            <Typography sx={{ fontWeight: 700, color: colors.text, mb: 2 }}>Recursos</Typography>
            <Stack spacing={1.25}>
              {resourceLinks.map((link) => (
                <Link
                  key={link.label}
                  href={link.href}
                  underline="hover"
                  sx={{ color: colors.textMuted, fontSize: '0.9rem', '&:hover': { color: colors.primary } }}
                >
                  {link.label}
                </Link>
              ))}
            </Stack>
          </Grid>

          <Grid item xs={12} md={4}>
            <Typography sx={{ fontWeight: 700, color: colors.text, mb: 2 }}>Contato</Typography>
            <Typography sx={{ color: colors.textMuted, fontSize: '0.9rem', mb: 2 }}>
              ana.rocha@catolicasc.edu.br
            </Typography>
            <Stack direction="row" spacing={1.25}>
              {[
                { href: 'mailto:ana.rocha@catolicasc.edu.br', icon: <EmailOutlinedIcon />, color: colors.primary, label: 'Email' },
                { href: 'https://github.com/ananinhaz', icon: <GitHubIcon />, color: '#111', label: 'GitHub' },
                { href: 'https://www.linkedin.com/in/ana-carolina-rocha-739ab61b6', icon: <LinkedInIcon />, color: '#0A66C2', label: 'LinkedIn' },
              ].map((item) => (
                <Link key={item.label} href={item.href} target="_blank" rel="noopener noreferrer" underline="none" aria-label={item.label}>
                  <IconButton
                    sx={{
                      bgcolor: colors.card,
                      boxShadow: shadows.soft,
                      borderRadius: radii.button,
                      width: 44,
                      height: 44,
                      transition: 'all 0.2s ease',
                      '&:hover': { transform: 'translateY(-3px)', boxShadow: shadows.hover },
                    }}
                  >
                    <Box sx={{ color: item.color, display: 'flex' }}>{item.icon}</Box>
                  </IconButton>
                </Link>
              ))}
            </Stack>
          </Grid>
        </Grid>

        <Box sx={{ borderTop: '1px solid rgba(99,102,241,0.12)', mt: 5, pt: 3, textAlign: 'center' }}>
          <Typography sx={{ color: '#9CA3AF', fontSize: '0.9rem' }}>
            © 2025 AdoptMe — Desenvolvido por Ana Carolina Rocha
          </Typography>
        </Box>
      </Container>
    </Box>
  )
}
