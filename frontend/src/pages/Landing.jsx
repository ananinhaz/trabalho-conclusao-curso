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
  Stack,
  IconButton,
  CircularProgress,
} from "@mui/material";
import PetsIcon from "@mui/icons-material/Pets";
import ArrowBackIosIcon from "@mui/icons-material/ArrowBackIos";
import ArrowForwardIosIcon from "@mui/icons-material/ArrowForwardIos";
import FavoriteBorderIcon from "@mui/icons-material/FavoriteBorder";
import ShieldOutlinedIcon from "@mui/icons-material/ShieldOutlined";
import GroupsOutlinedIcon from "@mui/icons-material/GroupsOutlined";
import FavoriteOutlinedIcon from "@mui/icons-material/FavoriteOutlined";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import HomeOutlinedIcon from "@mui/icons-material/HomeOutlined";
import { colors, gradientPrimary, shadows, radii, cardSx, btnGradient, btnOutline } from "../theme";

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

  const primaryColor = colors.primary;
  const primaryColorHover = "#4F46E5";

  const infoCards = [
    {
      icon: <ShieldOutlinedIcon sx={{ fontSize: 28 }} />,
      bg: "#EEF2FF",
      color: colors.primary,
      title: "Adoção consciente",
      text: "Garantir que o animal será acolhido em um ambiente adequado ao seu porte, energia e rotina da família.",
    },
    {
      icon: <CheckCircleOutlineIcon sx={{ fontSize: 28 }} />,
      bg: "#ECFDF5",
      color: colors.success,
      title: "Registro detalhado",
      text: "Quando o processo não considera compatibilidade, aumentam as chances de devolução e frustração.",
    },
    {
      icon: <HomeOutlinedIcon sx={{ fontSize: 28 }} />,
      bg: "#FEF3C7",
      color: colors.gold,
      title: "Família na escolha",
      text: "Cada perfil de adotante é considerado para encontrar o pet que melhor se encaixa no lar.",
    },
    {
      icon: <FavoriteOutlinedIcon sx={{ fontSize: 28 }} />,
      bg: "#F3E8FF",
      color: colors.secondary,
      title: "Amor que transforma",
      text: "Por isso o AdoptMe orienta e recomenda animais com base no seu perfil de adotante.",
    },
  ];

  return (
    <Box sx={{ bgcolor: colors.background, minHeight: "100vh" }}>
      <Paper
        elevation={0}
        component="header"
        sx={{
          bgcolor: colors.card,
          boxShadow: shadows.header,
          py: 1.5,
          px: { xs: 2, md: 6 },
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          position: "sticky",
          top: 0,
          zIndex: 10,
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <Box
            sx={{
              width: 36,
              height: 36,
              borderRadius: "10px",
              background: gradientPrimary,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <PetsIcon sx={{ color: "#fff", fontSize: 20 }} />
          </Box>
          <Typography sx={{ fontSize: "1.35rem", fontWeight: 800, color: colors.text }}>
            AdoptMe
          </Typography>
        </Box>

        <Stack direction="row" spacing={1.5} component="nav">
          <Button
            variant="outlined"
            size="medium"
            startIcon={<FavoriteBorderIcon />}
            onClick={() => navigate("/login?next=/perfil-adotante")}
            sx={{ ...btnOutline, px: 2.5, py: 1 }}
          >
            Quero adotar
          </Button>
          <Button
            variant="contained"
            size="medium"
            startIcon={<PetsIcon />}
            onClick={() => navigate("/login?next=/doar")}
            sx={{ ...btnGradient, px: 2.5, py: 1, height: 'auto' }}
          >
            Quero doar
          </Button>
        </Stack>
      </Paper>

      {/* Hero principal */}
      <Box
        sx={{
          width: "100%",
          maxWidth: 1400,
          mx: "auto",
          px: { xs: 2, md: 4 },
          mt: { xs: 5, md: 8 },
          mb: { xs: 5, md: 7 },
        }}
      >
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: { xs: "1fr", md: "1fr 1.3fr" },
            gap: { xs: 4, md: 6 },
            alignItems: "center",
            width: "100%",
          }}
        >
          <Box sx={{ width: "100%", minWidth: 0 }}>
            <Box
              sx={{
                display: "inline-flex",
                alignItems: "center",
                gap: 0.75,
                bgcolor: "#EEF2FF",
                color: colors.primary,
                px: 2,
                py: 0.75,
                borderRadius: radii.pill,
                fontSize: "0.85rem",
                fontWeight: 600,
                mb: 2.5,
              }}
            >
              <FavoriteBorderIcon sx={{ fontSize: 16 }} />
              Adoção responsável transforma vidas
            </Box>
            <Typography
              variant="h3"
              component="h1"
              sx={{
                fontWeight: 800,
                color: colors.text,
                mb: 2.5,
                lineHeight: 1.15,
                fontSize: { xs: "2.1rem", md: "2.75rem" },
              }}
            >
              Encontre o melhor amigo ou ajude um animal a{" "}
              <Box
                component="span"
                sx={{
                  background: gradientPrimary,
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                encontrar um lar
              </Box>
            </Typography>
            <Typography
              variant="body1"
              sx={{ color: colors.textMuted, mb: 3.5, fontSize: "1.05rem", lineHeight: 1.7, maxWidth: 520 }}
            >
              Encontre o pet ideal ou cadastre um animal para adoção. Nosso sistema usa critérios
              objetivos para recomendar o melhor match, reduzindo devoluções e adoções mal-sucedidas.
            </Typography>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} sx={{ mb: 3 }}>
              <Button
                variant="contained"
                size="large"
                onClick={() => navigate("/login?next=/perfil-adotante")}
                sx={{ ...btnGradient, py: 1.5, px: 4, fontSize: "1rem", height: 52 }}
              >
                Quero adotar
              </Button>
              <Button
                variant="outlined"
                size="large"
                onClick={() => navigate("/login?next=/doar")}
                sx={{ ...btnOutline, py: 1.5, px: 4, fontSize: "1rem", height: 52 }}
              >
                Quero doar
              </Button>
            </Stack>
            <Stack direction="row" spacing={3} flexWrap="wrap" useFlexGap>
              {[
                { icon: <ShieldOutlinedIcon sx={{ fontSize: 18, color: colors.primary }} />, label: "Processo seguro" },
                { icon: <GroupsOutlinedIcon sx={{ fontSize: 18, color: colors.success }} />, label: "Comunidade confiável" },
                { icon: <FavoriteOutlinedIcon sx={{ fontSize: 18, color: colors.secondary }} />, label: "Impacto positivo" },
              ].map((item) => (
                <Stack key={item.label} direction="row" alignItems="center" spacing={0.75}>
                  {item.icon}
                  <Typography sx={{ fontSize: "0.85rem", color: colors.textMuted, fontWeight: 500 }}>
                    {item.label}
                  </Typography>
                </Stack>
              ))}
            </Stack>
          </Box>

          <Box sx={{ width: "100%", minWidth: 0 }}>
            <Box
              sx={{
                position: "relative",
                width: "100%",
                borderRadius: radii.card,
                overflow: "hidden",
                boxShadow: shadows.card,
                minHeight: { xs: 280, md: 500 },
              }}
            >
              {isLoading ? (
                <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: { xs: 280, md: 500 } }}>
                  <CircularProgress sx={{ color: primaryColor }} />
                </Box>
              ) : (
                animais.map((pet, i) => (
                  <Box
                    key={pet.id}
                    sx={{
                      position: i === idx ? "relative" : "absolute",
                      top: 0,
                      left: 0,
                      width: "100%",
                      opacity: i === idx ? 1 : 0,
                      transition: "opacity 0.8s ease-in-out",
                    }}
                  >
                    <Box
                      component="img"
                      src={pet.photo_url || pet.foto}
                      alt={pet.nome}
                      sx={{
                        width: "100%",
                        height: { xs: 280, md: 500 },
                        minHeight: { xs: 280, md: 500 },
                        objectFit: "cover",
                        display: "block",
                      }}
                    />
                    <Box
                      sx={{
                        position: "absolute",
                        bottom: 16,
                        left: 16,
                        right: 16,
                        bgcolor: "rgba(255,255,255,0.95)",
                        backdropFilter: "blur(8px)",
                        borderRadius: "16px",
                        p: 2,
                        boxShadow: shadows.soft,
                      }}
                    >
                      <Typography sx={{ fontWeight: 700, color: colors.text, fontSize: "1.1rem" }}>
                        {pet.nome}
                      </Typography>
                      <Typography sx={{ color: colors.textMuted, fontSize: "0.85rem", mt: 0.25 }}>
                        {pet.especie} em destaque
                      </Typography>
                    </Box>
                  </Box>
                ))
              )}
              {animais.length > 1 && !isLoading && (
                <>
                  <IconButton
                    onClick={handlePrevPet}
                    sx={{
                      position: "absolute",
                      top: "50%",
                      left: 12,
                      transform: "translateY(-50%)",
                      bgcolor: "rgba(255,255,255,0.9)",
                      boxShadow: shadows.soft,
                      "&:hover": { bgcolor: "#fff" },
                    }}
                  >
                    <ArrowBackIosIcon sx={{ fontSize: "1rem", color: colors.text, ml: 0.5 }} />
                  </IconButton>
                  <IconButton
                    onClick={handleNextPet}
                    sx={{
                      position: "absolute",
                      top: "50%",
                      right: 12,
                      transform: "translateY(-50%)",
                      bgcolor: "rgba(255,255,255,0.9)",
                      boxShadow: shadows.soft,
                      "&:hover": { bgcolor: "#fff" },
                    }}
                  >
                    <ArrowForwardIosIcon sx={{ fontSize: "1rem", color: colors.text }} />
                  </IconButton>
                  <Stack
                    direction="row"
                    spacing={0.75}
                    sx={{ position: "absolute", bottom: 90, left: "50%", transform: "translateX(-50%)" }}
                  >
                    {animais.map((pet, i) => (
                      <Box
                        key={pet.id}
                        component="button"
                        onClick={() => setIdx(i)}
                        sx={{
                          width: 8,
                          height: 8,
                          borderRadius: "50%",
                          border: "none",
                          p: 0,
                          bgcolor: i === idx ? colors.primary : "rgba(255,255,255,0.6)",
                          cursor: "pointer",
                          transition: "all 0.2s ease",
                        }}
                      />
                    ))}
                  </Stack>
                </>
              )}
            </Box>
          </Box>
        </Box>
      </Box>

      <Container maxWidth="lg" sx={{ mb: { xs: 4, md: 6 } }}>
        <AdoptionChart />
      </Container>
      <Container maxWidth="lg" sx={{ mb: { xs: 4, md: 6 } }}>
        <MetricsCards />
      </Container>

      {/* Adoção responsável — cards informativos */}
      <Container maxWidth="lg" sx={{ mb: { xs: 5, md: 7 } }}>
        <Box sx={{ textAlign: "center", mb: 4 }}>
          <Typography variant="h4" sx={{ fontWeight: 800, color: colors.text, mb: 1 }}>
            Por que adotar com responsabilidade?
          </Typography>
          <Box sx={{ width: 48, height: 4, bgcolor: colors.gold, borderRadius: 2, mx: "auto" }} />
        </Box>
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: {
              xs: "1fr",
              sm: "repeat(2, minmax(0, 1fr))",
              md: "repeat(4, minmax(0, 1fr))",
            },
            gap: { xs: 2, sm: 2.5, md: 3 },
            width: "100%",
            alignItems: "stretch",
          }}
        >
          {infoCards.map((card) => (
            <Paper
              key={card.title}
              elevation={0}
              sx={{
                ...cardSx,
                p: { xs: 2.5, sm: 3 },
                minHeight: 240,
                height: "100%",
                maxWidth: "100%",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "flex-start",
                textAlign: "center",
                transition: "all 0.2s ease",
                "&:hover": { boxShadow: shadows.hover, transform: "translateY(-4px)" },
              }}
            >
              <Box
                sx={{
                  width: 56,
                  height: 56,
                  borderRadius: "50%",
                  bgcolor: card.bg,
                  color: card.color,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  mb: 2,
                  flexShrink: 0,
                }}
              >
                {card.icon}
              </Box>
              <Typography sx={{ fontWeight: 700, color: colors.text, mb: 1, fontSize: "1rem" }}>
                {card.title}
              </Typography>
              <Typography
                sx={{
                  color: colors.textMuted,
                  fontSize: "0.9rem",
                  lineHeight: 1.6,
                  flexGrow: 1,
                  maxWidth: 280,
                  mx: "auto",
                }}
              >
                {card.text}
              </Typography>
            </Paper>
          ))}
        </Box>
      </Container>

      {/* sobre */}
      <Container maxWidth="md" sx={{ mb: { xs: 5, md: 7 } }}>
        <Paper
          elevation={0}
          sx={{
            ...cardSx,
            p: { xs: 3, md: 5 },
            textAlign: "left",
            borderRadius: "18px",
          }}
        >
          <Typography variant="h5" sx={{ fontWeight: 800, color: colors.text, mb: 2.5, textAlign: "center" }}>
            Sobre o AdoptMe
          </Typography>
          <Typography sx={{ color: colors.textMuted, lineHeight: 1.75, fontSize: "1.05rem", maxWidth: "90%", margin: "0 auto" }}>
            {'🐾 O '}
            <strong>AdoptMe</strong>
            {' é um sistema web que conecta pessoas interessadas em adoção responsável com animais disponíveis para um novo lar.'}
          </Typography>
          <Typography sx={{ color: colors.textMuted, lineHeight: 1.75, fontSize: "1.05rem", maxWidth: "90%", margin: "18px auto 0" }}>
            {'🤝 Em vez de usar um K fixo de forma literal, o AdoptMe transforma o perfil do adotante e os atributos dos animais em vetores numéricos e usa uma medida de '}
            <strong>similaridade vetorial ponderada</strong>
            {' (implementada com utilitários do Scikit-Learn) para rankear os pets mais compatíveis.'}
          </Typography>
          <Typography sx={{ color: colors.textMuted, lineHeight: 1.75, fontSize: "1.05rem", maxWidth: "90%", margin: "18px auto 0" }}>
            {'💜 É um projeto com foco social e acadêmico, desenvolvido com '}
            <strong>React, Flask e PostgreSQL</strong>
            {', containerizada com Docker e hospedada em infraestrutura AWS, com autenticação via Google, trazendo modernidade e responsabilidade ao processo de adoção.'}
          </Typography>
        </Paper>
      </Container>
      <Footer />
    </Box>
  );
}
