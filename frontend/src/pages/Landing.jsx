// src/pages/Landing.jsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Container,
  Paper,
  Typography,
  Button,
  Grid,
  Stack,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
} from "@mui/material";
import PetsIcon from "@mui/icons-material/Pets";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import ArrowBackIosIcon from "@mui/icons-material/ArrowBackIos";
import ArrowForwardIosIcon from "@mui/icons-material/ArrowForwardIos";

// MOCK DE DADOS ORIGINAIS DOS ANIMAIS (MANTIDO)
const animaisMock = [
  {
    id: 1,
    nome: "Luna",
    especie: "Gato",
    descricao: "Filhote dócil, se dá bem com crianças.",
    foto: "https://placekitten.com/500/260",
  },
  {
    id: 2,
    nome: "Thor",
    especie: "Cachorro",
    descricao: "Porte médio, muito carinhoso.",
    foto: "https://images.dog.ceo/breeds/hound-blood/n02088466_9625.jpg",
  },
  {
    id: 3,
    nome: "Maya",
    especie: "Cachorro",
    descricao: "Ideal para apartamento.",
    foto: "https://images.dog.ceo/breeds/spaniel-cocker/n02102318_8705.jpg",
  },
  {
    id: 4,
    nome: "Simba",
    especie: "Gato",
    descricao: "Calmo, castrado.",
    foto: "https://placekitten.com/501/260",
  },
];


export default function Landing() {
  const navigate = useNavigate();

  const [idx, setIdx] = useState(0);
  
  // LÓGICA DO CARROSSEL AUTOMÁTICO (MANTIDA)
  useEffect(() => {
    const t = setInterval(() => {
      setIdx((prev) => (prev + 1) % animaisMock.length);
    }, 4500); 
    return () => clearInterval(t);
  }, [animaisMock.length]);

  // Função para avançar/voltar no carrossel manualmente
  const handlePrevPet = () => {
    setIdx((prev) => (prev - 1 + animaisMock.length) % animaisMock.length);
  };

  const handleNextPet = () => {
    setIdx((prev) => (prev + 1) % animaisMock.length);
  };

  // Cores da nossa identidade visual (MANTIDAS)
  const primaryColor = "#6366F1";
  const primaryColorHover = "#4F46E5";

  // Estilo de card padrão (MANTIDO)
  const cardStyles = {
    borderRadius: "1.25rem",
    bgcolor: "#fff",
    border: "1px solid rgba(15,23,42,0.03)",
    boxShadow: "0 20px 50px rgba(15,23,42,0.03)",
  };

  return (
    <Box sx={{ bgcolor: "#F9FAFB", minHeight: "100vh" }}>
      
      {/* 1. TOPO / HEADER (MANTIDO) */}
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

      {/* 2. CARROSSEL HORIZONTAL COM CONTEÚDO DO PET E NOVA FRASE */}
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
          {/* Loop pelos animais para animação de fade */}
          {animaisMock.map((pet, i) => (
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
              {/* Parte da Imagem (Lado Esquerdo, 40%) */}
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
                <img src={pet.foto} alt={pet.nome} />
              </Box>

              {/* Parte do Texto e Frase (Lado Direito, 60% ou 100% em mobile) */}
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
                
                {/* *** ALTERAÇÃO AQUI: FRASE BONITA NO LUGAR DOS BOTÕES *** */}
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

          {/* Setas de Navegação (MANTIDAS) */}
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

          {/* Bolinhas de navegação (MANTIDAS) */}
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
            {animaisMock.map((pet, i) => (
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
        </Paper>
      </Container>


      {/* 3. HERO PRINCIPAL (MANTIDO) */}
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


      {/* 4. ADOÇÃO RESPONSÁVEL (MANTIDO) */}
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

      {/* 5. SOBRE O ADOPTME (MANTIDO) */}
      <Container maxWidth="lg" sx={{ mb: { xs: 4, md: 6 } }}>
        <Grid container spacing={4} alignItems="stretch">
          
          <Grid item xs={12} md={7}>
            <Typography variant="h5" sx={{ fontWeight: 600, color: "#1f2937", mb: 1.5 }}>
              Sobre o AdoptMe
            </Typography>
            <Typography sx={{ color: "#475569", mb: 1 }}>
              O AdoptMe é um sistema web de adoção de animais que centraliza, em
              um único ambiente, o cadastro de adotantes e de doadores.
            </Typography>
            <Typography sx={{ color: "#475569", mb: 1 }}>
              Ele utiliza uma lógica de recomendação simples (K-NN) para aproximar
              o perfil do adotante ao animal mais adequado, considerando moradia,
              presença de crianças, tempo disponível e estilo de vida.
            </Typography>
            <Typography sx={{ color: "#475569" }}>
              É um projeto com foco social e acadêmico, desenvolvido em React no
              frontend, Flask no backend e MySQL como banco de dados, com
              autenticação via Google e filtros de busca.
            </Typography>
          </Grid>

          <Grid item xs={12} md={5}>
            <Paper
              elevation={0}
              sx={{
                ...cardStyles,
                bgcolor: "#EEF2FF",
                p: { xs: 2.5, md: 3 },
                height: "100%"
              }}
            >
              <Typography variant="h6" sx={{ fontWeight: 600, color: "#1f2937", mb: 1.5 }}>
                Resumo rápido
              </Typography>
              <List dense sx={{ p: 0 }}>
                {[
                  "Sistema unificado para adotar e doar",
                  "Recomendações por afinidade de perfil",
                  "React + Flask + MySQL",
                  "IA simples com KNN (scikit-learn)",
                  "Autenticação pelo Google",
                  "Interface responsiva",
                ].map((text) => (
                  <ListItem key={text} sx={{ p: 0, mb: 0.5 }}>
                    <ListItemIcon sx={{ minWidth: 32 }}>
                      <CheckCircleOutlineIcon sx={{ color: primaryColor, fontSize: "1.2rem" }} />
                    </ListItemIcon>
                    <ListItemText
                      primary={text}
                      primaryTypographyProps={{ color: "#475569", fontSize: '0.9rem' }}
                    />
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}