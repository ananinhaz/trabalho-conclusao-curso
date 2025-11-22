import { useEffect, useState, useMemo } from "react";
import { Box, Grid, Paper, Typography, CircularProgress, LinearProgress } from "@mui/material";
import { animaisApi } from "../api";

function StatCard({ title, value, hint }) {
  return (
    <Paper
      elevation={0}
      sx={{
        p: 2.25,
        borderRadius: 2,
        minHeight: 96,
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
      }}
    >
      <Box>
        <Typography sx={{ fontSize: 12, color: "#6B7280", fontWeight: 600 }}>{title}</Typography>
        <Typography sx={{ fontSize: 20, fontWeight: 700, color: "#0f172a", mt: 1 }}>{value}</Typography>
      </Box>
      {hint && <Typography sx={{ fontSize: 12, color: "#9CA3AF" }}>{hint}</Typography>}
    </Paper>
  );
}

export default function MetricsCards() {
  const [loading, setLoading] = useState(true);
  const [animals, setAnimals] = useState([]);

  useEffect(() => {
    let mounted = true;

    (async () => {
      // busca animais para métricas 
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

  // totals calculados localmente 
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
      <Paper
        elevation={0}
        sx={{ borderRadius: "1rem", p: 3, boxShadow: "0 10px 30px rgba(0,0,0,0.03)", mb: 3, mt: 4 }}
      >
        <Typography variant="h6" sx={{ mb: 2, fontWeight: 700 }}>
          Visão rápida
        </Typography>
        <Box sx={{ display: "flex", gap: 2 }}>
          <Box sx={{ flex: 1, minHeight: 80, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <CircularProgress />
          </Box>
        </Box>
      </Paper>
    );
  }

  return (
    <Paper elevation={0} sx={{ borderRadius: "1rem", p: 3, boxShadow: "0 10px 30px rgba(0,0,0,0.03)", mb: 3, mt: 6 }}>
      <Typography variant="h6" sx={{ mb: 2, fontWeight: 700 }}>
        Visão rápida
      </Typography>
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard title="Total de anúncios" value={totals.total} hint="Últimos registros carregados" />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Disponíveis"
            value={totals.available}
            hint={`${totals.adopted} ${totals.adopted === 1 ? "já adotado" : "já adotados"}`}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard title="Bom com crianças" value={totals.goodWithKids} hint="Anúncios marcados como OK com crianças" />
        </Grid>

        {/* Distribuição por espécies */}
        <Grid item xs={12}>
          <Box sx={{ mt: 1 }}>
            <Typography sx={{ fontSize: 13, color: "#6B7280", mb: 1, fontWeight: 600 }}>Distribuição por espécies</Typography>
            <Box sx={{ display: "flex", gap: 2, alignItems: "flex-start", flexWrap: "wrap" }}>
              {Object.entries(totals.bySpecies).length === 0 ? (
                <Typography sx={{ color: "#9CA3AF" }}>Sem dados</Typography>
              ) : (
                Object.entries(totals.bySpecies).map(([sp, cnt]) => {
                  const pct = totals.total > 0 ? Math.round((cnt / totals.total) * 100) : 0;
                  return (
                    <Box key={sp} sx={{ minWidth: 160, flex: "1 1 160px" }}>
                      <Typography
                        sx={{
                          fontSize: 12,
                          color: "#374151",
                          fontWeight: 600,
                          textTransform: "capitalize",
                        }}
                      >
                        {sp}
                      </Typography>
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mt: 0.5 }}>
                        <Box sx={{ flex: 1 }}>
                          <LinearProgress
                            variant="determinate"
                            value={pct}
                            sx={{
                              height: 8,
                              borderRadius: 2,
                              backgroundColor: "#EEF2FF",
                              "& .MuiLinearProgress-bar": { backgroundColor: "#6366F1" },
                            }}
                          />
                        </Box>
                        <Typography sx={{ fontSize: 12, color: "#6B7280", minWidth: 36, textAlign: "right" }}>
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
