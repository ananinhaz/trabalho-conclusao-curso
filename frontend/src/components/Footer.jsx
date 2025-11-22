import React from 'react'
import { Box, Container, Grid, Typography, Link, IconButton, Stack } from '@mui/material'
import EmailOutlinedIcon from '@mui/icons-material/EmailOutlined'
import GitHubIcon from '@mui/icons-material/GitHub'
import LinkedInIcon from '@mui/icons-material/LinkedIn'

export default function Footer() {
  const primary = '#6366F1'

  return (
    <Box component="footer" sx={{ bgcolor: '#F4F6FF', py: 8, mt: 8 }}>
      <Container maxWidth="lg">
        <Grid container spacing={4} alignItems="flex-start">
          <Grid item xs={12} md={7}>
            <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
              AdoptMe
            </Typography>

            <Typography sx={{ color: '#475569', maxWidth: 720, lineHeight: 1.8 }}>
              Plataforma acadêmica voltada para adoção responsável. Nosso propósito é
              facilitar conexões seguras entre pessoas e animais, com recomendações
              baseadas em compatibilidade real de perfil e necessidades.
            </Typography>

            <Typography sx={{ color: '#9CA3AF', mt: 4, fontSize: '0.95rem' }}>
              © 2025 AdoptMe — Desenvolvido por Ana Carolina Rocha
            </Typography>
          </Grid>
          <Grid
            item
            xs={12}
            md={5}
            sx={{
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              alignItems: { xs: 'flex-start', md: 'flex-end' },
              pr: { md: 4 },
            }}
          >
            <Box sx={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: { xs: 'flex-start', md: 'flex-end' } }}>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
                Contato
              </Typography>
              <Box sx={{ width: '100%', display: 'flex', justifyContent: { xs: 'flex-start', md: 'flex-end' } }}>
                <Stack
                  direction="row"
                  spacing={1.25}
                  sx={{
                    mt: 1,
                    ml: { md: 4 },
                  }}
                >
                  <Link href="mailto:ana.rocha@catolicasc.edu.br" underline="none" aria-label="Enviar email">
                    <IconButton
                      size="large"
                      title="Enviar email"
                      sx={{
                        bgcolor: '#fff',
                        boxShadow: '0 6px 18px rgba(15,23,42,0.04)',
                        borderRadius: 2,
                        width: 48,
                        height: 48,
                        '&:hover': { transform: 'translateY(-3px)', boxShadow: '0 10px 28px rgba(15,23,42,0.06)' },
                      }}
                    >
                      <EmailOutlinedIcon sx={{ color: primary }} />
                    </IconButton>
                  </Link>

                  <Link href="https://github.com/ananinhaz" target="_blank" rel="noopener noreferrer" underline="none" aria-label="GitHub">
                    <IconButton
                      size="large"
                      title="GitHub"
                      sx={{
                        bgcolor: '#fff',
                        boxShadow: '0 6px 18px rgba(15,23,42,0.04)',
                        borderRadius: 2,
                        width: 48,
                        height: 48,
                        '&:hover': { transform: 'translateY(-3px)', boxShadow: '0 10px 28px rgba(15,23,42,0.06)' },
                      }}
                    >
                      <GitHubIcon sx={{ color: '#111' }} />
                    </IconButton>
                  </Link>

                  <Link href="https://www.linkedin.com/in/ana-carolina-rocha-739ab61b6" target="_blank" rel="noopener noreferrer" underline="none" aria-label="LinkedIn">
                    <IconButton
                      size="large"
                      title="LinkedIn"
                      sx={{
                        bgcolor: '#fff',
                        boxShadow: '0 6px 18px rgba(15,23,42,0.04)',
                        borderRadius: 2,
                        width: 48,
                        height: 48,
                        '&:hover': { transform: 'translateY(-3px)', boxShadow: '0 10px 28px rgba(15,23,42,0.06)' },
                      }}
                    >
                      <LinkedInIcon sx={{ color: '#0A66C2' }} />
                    </IconButton>
                  </Link>
                </Stack>
              </Box>
            </Box>
          </Grid>
        </Grid>
      </Container>
    </Box>
  )
}
