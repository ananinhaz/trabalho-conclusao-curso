import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { animaisApi } from '../api'; 
import AdoptionChart from "../components/AdoptionChart";
import Footer from '../components/Footer';
import MetricsCards from '../components/MetricsCards';

import {
  Box,
  Container,
  Paper,
  Typography,
  Button,
  Grid,
  Stack,
  IconButton,
  CircularProgress,
} from "@mui/material";
import PetsIcon from "@mui/icons-material/Pets";
import ArrowBackIosIcon from "@mui/icons-material/ArrowBackIos";
import ArrowForwardIosIcon from "@mui/icons-material/ArrowForwardIos";

export default function Landing() {
  const navigate = useNavigate();

  const [animais, setAnimais] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [idx, setIdx] = useState(0);

  useEffect(() => {
    async function fetchAnimais() {
      try {
        const response = await animaisApi.list(); 
        
        let fetchedAnimais = [];

        if (Array.isArray(response)) {
            fetchedAnimais = response.slice(0, 10);
        } else if (response && Array.isArray(response.animais)) {
            fetchedAnimais = response.animais.slice(0, 10);
        } else {
            console.warn("A resposta da API não está no formato de array ou { animais: array }.", response);
        }

        // Se não houver animais reais, usa um fallback estático
        if (fetchedAnimais.length === 0) {
            console.warn("API retornou 0 animais, usando fallback estático no carrossel.");
            setAnimais([{
                id: 'fallback',
                nome: "Mascote",
                especie: "Cachorro",
                descricao: "Adote um amigo, mude uma vida. Clique em 'Quero adotar'.",
                // Garante que há uma imagem de fallback para evitar erros
                photo_url: "https://images.dog.ceo/breeds/retriever-golden/n02099601_5654.jpg", 
            }]);
        } else {
            // se houver dados, eles serão carregados
            setAnimais(fetchedAnimais);
        }

      } catch (error) {
        console.error("Erro ao carregar animais para o carrossel. Verifique se o backend está rodando e se a rota /api/animais está acessível.", error);
        // Fallback em caso de erro de conexão
        setAnimais([{
            id: 'fallback-error',
            nome: "Mascote",
            especie: "Cachorro",
            descricao: "O AdoptMe está carregando... Adote um amigo!",
            photo_url: "https://images.dog.ceo/breeds/retriever-golden/n02099601_5654.jpg",
        }]);
      } finally {
        setIsLoading(false);
      }
    }
    fetchAnimais();
  }, []); 

  // carrossel
  useEffect(() => {
    if (animais.length > 0) {
      const t = setInterval(() => {
        setIdx((prev) => (prev + 1) % animais.length);
      }, 4500); 
      return () => clearInterval(t);
    }
  }, [animais.length]);

  //Função para avançar/voltar no carrossel manualmente
  const handlePrevPet = () => {
    setIdx((prev) => (prev - 1 + animais.length) % animais.length);
  };

  const handleNextPet = () => {
    setIdx((prev) => (prev + 1) % animais.length);
  };

  const primaryColor = "#6366F1";
  const primaryColorHover = "#4F46E5";

  const cardStyles = {
    borderRadius: "1.25rem",
    bgcolor: "#fff",
    border: "1px solid rgba(15,23,42,0.03)",
    boxShadow: "0 20px 50px rgba(15,23,42,0.03)",
  };

  return (
    <Box sx={{ bgcolor: "#F9FAFB", minHeight: "100vh" }}>
      <Paper
        elevation={0}
        component="header"
        sx={{
          bgcolor: "#fff",
          borderBottom: "1px solid rgba(15,23,42,0.05)",
          py: 1,
          px: { xs: 2, md: 4 },
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          position: "sticky",
          top: 0,
          zIndex: 10,
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
          <PetsIcon sx={{ color: primaryColor }} />
          <Typography
            sx={{
              fontSize: "1.3rem",
              fontWeight: 700,
              color: primaryColor,
            }}
          >
            AdoptMe
          </Typography>
        </Box>

        <Stack direction="row" spacing={1} component="nav">
          <Button
            variant="outlined"
            size="small"
            onClick={() => navigate("/login?next=/perfil-adotante")}
            sx={{
              borderRadius: "9999px",
              textTransform: "none",
              fontWeight: 600,
              borderColor: primaryColor,
              color: primaryColor,
              "&:hover": {
                borderColor: primaryColorHover,
                bgcolor: "#F4F4FE"
              }
            }}
          >
            Quero adotar
          </Button>
          <Button
            variant="contained"
            size="small"
            onClick={() => navigate("/login?next=/doar")}
            sx={{
              borderRadius: "9999px",
              textTransform: "none",
              fontWeight: 600,
              bgcolor: primaryColor,
              "&:hover": { bgcolor: primaryColorHover },
              boxShadow: "none"
            }}
          >
            Quero doar
          </Button>
        </Stack>
      </Paper>

      {/*  carrossel com conteudo dos animais */}
      <Container maxWidth="lg" sx={{ mt: { xs: 4, md: 6 }, mb: { xs: 4, md: 6 } }}>
        <Paper
          elevation={0}
          sx={{
            ...cardStyles,
            overflow: "hidden",
            position: "relative",
            p: 0,
            minHeight: { xs: '300px', md: '280px' }, 
            bgcolor: '#FFF', 
          }}
        >
          {/*mostrar o loading ou o carrossel */}
          {isLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', minHeight: { xs: '300px', md: '280px' } }}>
              <CircularProgress sx={{ color: primaryColor }} />
            </Box>
          ) : (
            <>
              {/* Loop pelos animais */}
              {animais.map((pet, i) => (
                <Box
                  key={pet.id}
                  sx={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    width: "100%",
                    height: "100%",
                    display: "flex", 
                    alignItems: "stretch", 
                    opacity: i === idx ? 1 : 0, 
                    transition: "opacity 0.8s ease-in-out",
                    bgcolor: '#fff', 
                  }}
                >
                  {/* Imagem animais */}
                  <Box
                    sx={{
                      flex: { xs: 1, md: 0.4 }, 
                      height: "100%",
                      bgcolor: '#eee', 
                      display: { xs: 'none', md: 'block' }, 
                      "& img": {
                        width: "100%",
                        height: "100%",
                        objectFit: "cover",
                        objectPosition: "center",
                      },
                    }}
                  >
                    <img 
                      src={pet.photo_url || pet.foto} 
                      alt={pet.nome} 
                    />
                  </Box>

                  <Box sx={{
                    flex: { xs: 1, md: 0.6 }, 
                    p: { xs: 3, md: 4 },
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center', 
                    textAlign: { xs: 'center', md: 'left' },
                  }}>
                    <Typography
                      variant="h6"
                      component="span"
                      sx={{
                        fontWeight: 600,
                        color: primaryColor,
                        fontSize: '1rem',
                        mb: 0.5,
                      }}
                    >
                      {pet.especie} em destaque
                    </Typography>
                    <Typography
                      variant="h4"
                      component="h2"
                      sx={{
                        fontWeight: 700,
                        mb: 1.5,
                        color: '#1f2937',
                        fontSize: { xs: '2rem', md: '2.5rem' },
                        lineHeight: 1.1,
                      }}
                    >
                      {pet.nome}
                    </Typography>
                    <Typography
                      variant="body1"
                      sx={{
                        mb: 3,
                        color: '#475569',
                        fontSize: { xs: '0.95rem', md: '1.05rem' },
                      }}
                    >
                      {pet.descricao}
                    </Typography>
                    
                    <Typography
                        variant="h6"
                        sx={{
                          fontWeight: 500,
                          color: primaryColorHover,
                          fontStyle: 'italic',
                          mt: 1,
                          fontSize: { xs: '1rem', md: '1.1rem' },
                        }}
                    >
                      "O próximo capítulo de uma vida começa com você."
                    </Typography>
                    
                  </Box>
                </Box>
              ))}

              {/* Setas de Navegação */}
              {animais.length > 1 && (
                <>
                  <IconButton
                    onClick={handlePrevPet}
                    sx={{
                      position: "absolute",
                      top: "50%",
                      left: { xs: 10, md: 20 },
                      transform: "translateY(-50%)",
                      bgcolor: "rgba(255,255,255,0.7)",
                      "&:hover": { bgcolor: "rgba(255,255,255,0.9)" },
                      zIndex: 2,
                    }}
                  >
                    <ArrowBackIosIcon sx={{ fontSize: { xs: '1rem', md: '1.2rem' }, color: "#333" }} />
                  </IconButton>
                  <IconButton
                    onClick={handleNextPet}
                    sx={{
                      position: "absolute",
                      top: "50%",
                      right: { xs: 10, md: 20 },
                      transform: "translateY(-50%)",
                      bgcolor: "rgba(255,255,255,0.7)",
                      "&:hover": { bgcolor: "rgba(255,255,255,0.9)" },
                      zIndex: 2,
                    }}
                  >
                    <ArrowForwardIosIcon sx={{ fontSize: { xs: '1rem', md: '1.2rem' }, color: "#333" }} />
                  </IconButton>
                </>
              )}

              {/* Bolinhas de navegação */}
              {animais.length > 1 && (
                <Stack
                  direction="row"
                  spacing={0.75}
                  sx={{
                    position: "absolute",
                    bottom: "1rem",
                    left: "50%",
                    transform: "translateX(-50%)",
                    zIndex: 2,
                  }}
                >
                  {animais.map((pet, i) => (
                    <Box
                      key={pet.id}
                      component="button"
                      onClick={() => setIdx(i)}
                      sx={{
                        width: "10px",
                        height: "10px",
                        borderRadius: "50%",
                        border: "none",
                        p: 0,
                        bgcolor: i === idx ? primaryColor : "rgba(0,0,0,0.2)", 
                        cursor: "pointer",
                        transition: "background-color 0.3s ease",
                        "&:hover": {
                          bgcolor: i === idx ? primaryColorHover : "rgba(0,0,0,0.4)",
                        },
                      }}
                    />
                  ))}
                </Stack>
              )}
            </>
          )}
        </Paper>
      </Container>

      {/* Hero principal  */}
      <Container maxWidth="lg" sx={{ mb: { xs: 4, md: 6 } }}>
        <Grid container spacing={5} alignItems="center">
          <Grid item xs={12}>
            <Typography
              variant="h3"
              component="h1"
              sx={{
                fontWeight: 700,
                color: "#0f172a",
                mb: 2,
                lineHeight: 1.2,
                fontSize: { xs: '2rem', md: '2.8rem' },
                textAlign: 'center'
              }}
            >
              Conectando pessoas e animais com responsabilidade.
            </Typography>
            <Typography
              variant="body1"
              sx={{ color: "#475569", mb: 3, fontSize: "1.05rem", textAlign: 'center', maxWidth: 800, mx: 'auto' }}
            >
              Encontre o pet ideal ou cadastre um animal para adoção. Nosso
              sistema usa critérios objetivos para recomendar o melhor match,
              reduzindo devoluções e adoções mal-sucedidas.
            </Typography>
            <Stack direction="row" spacing={1.5} justifyContent="center">
              <Button
                variant="contained"
                size="large"
                onClick={() => navigate("/login?next=/perfil-adotante")}
                sx={{
                  borderRadius: "9999px",
                  textTransform: "none",
                  fontWeight: 600,
                  bgcolor: primaryColor,
                  "&:hover": { bgcolor: primaryColorHover },
                  py: 1.2,
                  px: 3,
                  boxShadow: "none"
                }}
              >
                Quero adotar
              </Button>
              <Button
                variant="outlined"
                size="large"
                onClick={() => navigate("/login?next=/doar")}
                sx={{
                  borderRadius: "9999px",
                  textTransform: "none",
                  fontWeight: 600,
                  borderColor: primaryColor,
                  color: primaryColor,
                  "&:hover": {
                    borderColor: primaryColorHover,
                    bgcolor: "#F4F4FE"
                  },
                  py: 1.2,
                  px: 3,
                }}
              >
                Quero doar
              </Button>
            </Stack>
          </Grid>
        </Grid>
      </Container>

      <Container maxWidth="lg" sx={{ mb: { xs: 4, md: 6 } }}>
        <AdoptionChart />
      </Container>
      <Container maxWidth="lg" sx={{ mb: { xs: 4, md: 6 } }}>
        <MetricsCards />
      </Container>

      {/* Adoção responsavel*/}
      <Container maxWidth="lg" sx={{ mb: { xs: 4, md: 6 } }}>
        <Paper
          elevation={0}
          sx={{ ...cardStyles, p: { xs: 2.5, md: 4 }, textAlign: 'center' }}
        >
          <Typography variant="h5" sx={{ fontWeight: 600, color: "#1f2937", mb: 1.5 }}>
            Por que adoção responsável?
          </Typography>
          <Typography sx={{ color: "#475569", mb: 1, maxWidth: "800px", mx: "auto" }}>
            A adoção não é apenas “pegar um pet”. É garantir que o animal será
            acolhido em um ambiente adequado ao seu porte, energia e rotina da
            família.
          </Typography>
          <Typography sx={{ color: "#475569", mb: 1, maxWidth: "800px", mx: "auto" }}>
            Quando o processo não considera isso, aumentam as chances de
            devolução, estresse do animal e frustração de quem adotou.
          </Typography>
          <Typography sx={{ color: "#475569", maxWidth: "800px", mx: "auto", fontWeight: 500 }}>
            Por isso o AdoptMe orienta e recomenda animais com base no seu perfil.
          </Typography>
        </Paper>
      </Container>

      {/* sobre */}
      <Box
        sx={{
          maxWidth: "900px",
          margin: "60px auto",
          padding: "36px 48px",
          background: "white",
          borderRadius: "22px",
          boxShadow: "0 8px 24px rgba(0,0,0,0.06)",
          textAlign: "left",
        }}
      >
        <Typography
          variant="h5"
          sx={{
            fontWeight: 700,
            color: "#1f2937",
            mb: 2,
            textAlign: "center",
          }}
        >
          Sobre o AdoptMe
        </Typography>

        <Typography
          variant="body1"
          sx={{
            color: "#4b5563",
            lineHeight: 1.65,
            fontSize: "1.05rem",
            maxWidth: "90%",
            margin: "0 auto",
          }}
        >
          🐾 O <strong>AdoptMe</strong> é um sistema web que conecta pessoas interessadas
          em adoção responsável com animais disponíveis para um novo lar.
        </Typography>

        <Typography
          variant="body1"
          sx={{
            color: "#4b5563",
            lineHeight: 1.65,
            fontSize: "1.05rem",
            maxWidth: "90%",
            margin: "18px auto 0",
          }}
        >
          🤝 Em vez de usar um K fixo de forma literal, o AdoptMe transforma o perfil do
          adotante e os atributos dos animais em vetores numéricos e usa uma medida
          de <strong>similaridade vetorial ponderada</strong> (implementada com utilitários do
          Scikit-Learn) para rankear os pets mais compatíveis. Essa abordagem permite
          priorizar características importantes e gerar recomendações personalizadas.
        </Typography>

        <Typography
          variant="body1"
          sx={{
            color: "#4b5563",
            lineHeight: 1.65,
            fontSize: "1.05rem",
            maxWidth: "90%",
            margin: "18px auto 0",
          }}
        >
          💜 É um projeto com foco social e acadêmico, desenvolvido com
          <strong> React, Flask e MySQL</strong>, com autenticação via Google,
          trazendo modernidade e responsabilidade ao processo de adoção.
        </Typography>
      </Box>
      <Footer />
    </Box>
  );
}
