import { useEffect, useState, useMemo } from "react";
import PropTypes from "prop-types";
import { Box, Grid, Paper, Typography, CircularProgress, LinearProgress } from "@mui/material";
import PetsIcon from "@mui/icons-material/Pets";
import FavoriteBorderIcon from "@mui/icons-material/FavoriteBorder";
import ChildFriendlyIcon from "@mui/icons-material/ChildFriendly";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import { animaisApi } from "../api";
import { colors, shadows, radii, cardSx } from "../theme";

function StatCard({ title, value, hint, icon, iconBg, iconColor }) {
  return (
    <Paper
      elevation={0}
      sx={{
        ...cardSx,
        p: 3,
        minHeight: 120,
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        transition: "all 0.2s ease",
        "&:hover": { boxShadow: shadows.hover, transform: "translateY(-2px)" },
      }}
    >
      <Box sx={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <Box>
          <Typography sx={{ fontSize: 13, color: colors.textMuted, fontWeight: 600 }}>{title}</Typography>
          <Typography sx={{ fontSize: 32, fontWeight: 800, color: colors.text, mt: 0.75, lineHeight: 1 }}>
            {value}
          </Typography>
        </Box>
        <Box
          sx={{
            width: 48,
            height: 48,
            borderRadius: "50%",
            bgcolor: iconBg,
            color: iconColor,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          {icon}
        </Box>
      </Box>
      {hint && <Typography sx={{ fontSize: 12, color: "#9CA3AF", mt: 1.5 }}>{hint}</Typography>}
    </Paper>
  );
}

StatCard.propTypes = {
  title: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  hint: PropTypes.string,
  icon: PropTypes.node.isRequired,
  iconBg: PropTypes.string.isRequired,
  iconColor: PropTypes.string.isRequired,
};

export default function MetricsCards() {
  const [loading, setLoading] = useState(true);
  const [animals, setAnimals] = useState([]);

  useEffect(() => {
    let mounted = true;

    (async () => {
      try {
        const resp = await animaisApi.list();
        let rows = [];
        if (Array.isArray(resp)) rows = resp;
        else if (resp && Array.isArray(resp.items)) rows = resp.items;
        else if (resp && Array.isArray(resp.animais)) rows = resp.animais;
        else if (resp && Array.isArray(resp.animals)) rows = resp.animals;

        if (mounted) setAnimals(rows.slice(0, 200));
      } catch (e) {
        console.error("Erro buscando animais para métricas:", e);
        if (mounted) setAnimals([]);
      } finally {
        if (mounted) setLoading(false);
      }
    })();

    return () => {
      mounted = false;
    };
  }, []);

  const totals = useMemo(() => {
    const total = animals.length;
    const adopted = animals.filter((a) => Boolean(a.adotado_em)).length;
    const available = total - adopted;

    const bySpecies = {};
    animals.forEach((a) => {
      const s = ((a.especie || "Desconhecido") + "").toLowerCase();
      bySpecies[s] = (bySpecies[s] || 0) + 1;
    });

    const goodWithKids = animals.filter((a) => a.bom_com_criancas === 1 || a.bom_com_criancas === true).length;

    return { total, adopted, available, bySpecies, goodWithKids };
  }, [animals]);

  if (loading) {
    return (
      <Paper elevation={0} sx={{ ...cardSx, p: 4, mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 2, fontWeight: 800, color: colors.text }}>
          Visão rápida
        </Typography>
        <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
          <CircularProgress sx={{ color: colors.primary }} />
        </Box>
      </Paper>
    );
  }

  return (
    <Paper elevation={0} sx={{ ...cardSx, p: { xs: 3, md: 4 }, mb: 3, borderRadius: radii.card }}>
      <Typography variant="h6" sx={{ mb: 3, fontWeight: 800, color: colors.text }}>
        Visão rápida
      </Typography>
      <Grid container spacing={2.5}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total de anúncios"
            value={totals.total}
            hint="Últimos registros carregados"
            icon={<PetsIcon />}
            iconBg="#EEF2FF"
            iconColor={colors.primary}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Disponíveis"
            value={totals.available}
            hint={`${totals.adopted} ${totals.adopted === 1 ? "já adotado" : "já adotados"}`}
            icon={<TrendingUpIcon />}
            iconBg="#ECFDF5"
            iconColor={colors.success}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Bom com crianças"
            value={totals.goodWithKids}
            hint="Anúncios marcados como OK com crianças"
            icon={<ChildFriendlyIcon />}
            iconBg="#FEF3C7"
            iconColor={colors.gold}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Adoções"
            value={totals.adopted}
            hint="Animais com status adotado"
            icon={<FavoriteBorderIcon />}
            iconBg="#F3E8FF"
            iconColor={colors.secondary}
          />
        </Grid>

        <Grid item xs={12}>
          <Box sx={{ mt: 1, p: 2.5, bgcolor: colors.background, borderRadius: radii.input }}>
            <Typography sx={{ fontSize: 13, color: colors.textMuted, mb: 2, fontWeight: 600 }}>
              Distribuição por espécies
            </Typography>
            <Box sx={{ display: "flex", gap: 2, alignItems: "flex-start", flexWrap: "wrap" }}>
              {Object.entries(totals.bySpecies).length === 0 ? (
                <Typography sx={{ color: "#9CA3AF" }}>Sem dados</Typography>
              ) : (
                Object.entries(totals.bySpecies).map(([sp, cnt]) => {
                  const pct = totals.total > 0 ? Math.round((cnt / totals.total) * 100) : 0;
                  return (
                    <Box key={sp} sx={{ minWidth: 160, flex: "1 1 160px" }}>
                      <Typography sx={{ fontSize: 12, color: colors.text, fontWeight: 600, textTransform: "capitalize" }}>
                        {sp}
                      </Typography>
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mt: 0.75 }}>
                        <Box sx={{ flex: 1 }}>
                          <LinearProgress
                            variant="determinate"
                            value={pct}
                            sx={{
                              height: 8,
                              borderRadius: 4,
                              backgroundColor: "#EEF2FF",
                              "& .MuiLinearProgress-bar": {
                                background: "linear-gradient(90deg, #6366F1, #8B5CF6)",
                                borderRadius: 4,
                              },
                            }}
                          />
                        </Box>
                        <Typography sx={{ fontSize: 12, color: colors.textMuted, minWidth: 36, textAlign: "right" }}>
                          {pct}%
                        </Typography>
                      </Box>
                    </Box>
                  );
                })
              )}
            </Box>
          </Box>
        </Grid>
      </Grid>
    </Paper>
  );
}
