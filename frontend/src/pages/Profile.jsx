import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Paper,
  Typography,
  Button,
  Stack,
  Container,
  Avatar,
  Divider,
  Grid,
  IconButton,
} from "@mui/material";
import LogoutIcon from "@mui/icons-material/Logout";
import EditIcon from "@mui/icons-material/Edit";
import PeopleIcon from "@mui/icons-material/People";
import PetsIcon from "@mui/icons-material/Pets";
import ArticleIcon from "@mui/icons-material/Article";

import { authApi, animaisApi, perfilApi } from "../api";

export default function Profile() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [mineCount, setMineCount] = useState(0);
  const [hasPerfil, setHasPerfil] = useState(false);
  const [loading, setLoading] = useState(true);

  const initials = (name) =>
    (name || "U")
      .split(" ")
      .map((p) => p[0] || "")
      .join("")
      .toUpperCase()
      .slice(0, 2);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        setLoading(true);
        const me = await authApi.me();
        if (me && me.user) {
          if (!alive) return;
          setUser(me.user);
        } else if (me && me.authenticated && me.user_id) {
          if (!alive) return;
          setUser({ id: me.user_id, nome: "Usuário", email: "" });
        } else if (me && me.user_id) {
          if (!alive) return;
          setUser({ id: me.user_id, nome: "Usuário", email: "" });
        } else {
          if (!alive) return;
          setUser(null);
        }

        // pega os animais para contar
        try {
          const arr = await animaisApi.mine();
          if (!alive) return;
          setMineCount(Array.isArray(arr) ? arr.length : (arr.length || 0));
        } catch {
          // ignora
          if (!alive) return;
          setMineCount(0);
        }

        // perfil adotante
        try {
          const p = await perfilApi.get();
          if (!alive) return;
          setHasPerfil(Boolean(p && p.perfil));
        } catch {
          if (!alive) return;
          setHasPerfil(false);
        }
      } catch (err) {
        // se der erro em me(), deixa user null
        console.debug("profile load:", err);
        if (!alive) return;
        setUser(null);
      } finally {
        if (alive) setLoading(false);
      }
    })();

    return () => {
      alive = false;
    };
  }, []);

  async function handleLogout() {
    try {
      await authApi.logout();
    } catch (err) {
    } finally {
      // manda pro login/landing
      navigate("/");
      window.location.reload(); 
    }
  }

  function gotoEditPerfilAdotante() {
    navigate("/perfil-adotante");
  }
  function gotoMyAds() {
    navigate("/animais");
    setTimeout(() => {
    }, 200);
  }
  function gotoEditAccount() {
    navigate("/perfil/editar");
  }

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "#F8FAFC", py: { xs: 4, md: 6 } }}>
      <Container maxWidth="md">
        <Paper sx={{ p: { xs: 3, md: 4 }, borderRadius: 3, boxShadow: "0 8px 30px rgba(2,6,23,0.06)" }}>
          <Stack direction={{ xs: "column", md: "row" }} spacing={3} alignItems="center">
            {/* Avatar + Info */}
            <Stack direction="row" spacing={2} alignItems="center" sx={{ flex: 1 }}>
              <Avatar
                src={user?.avatar_url || user?.picture || ""}
                alt={user?.nome || "Usuário"}
                sx={{ width: 96, height: 96, fontSize: 32, bgcolor: "#6366F1" }}
              >
                {!user?.avatar_url && initials(user?.nome)}
              </Avatar>

              <Box>
                <Typography variant="h6" sx={{ fontWeight: 700, color: "#0f172a" }}>
                  {user?.nome || "Usuário"}
                </Typography>
                <Typography variant="body2" sx={{ color: "#64748b" }}>
                  {user?.email || "—"}
                </Typography>
                <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
                  <Button
                    variant="outlined"
                    startIcon={<EditIcon />}
                    onClick={gotoEditAccount}
                    sx={{ borderRadius: "999px", textTransform: "none" }}
                  >
                    Editar conta
                  </Button>

                  <Button
                    variant="contained"
                    onClick={gotoEditPerfilAdotante}
                    sx={{
                      borderRadius: "999px",
                      textTransform: "none",
                      bgcolor: "#6366F1",
                      "&:hover": { bgcolor: "#4F46E5" },
                    }}
                  >
                    {hasPerfil ? "Editar perfil de adotante" : "Criar perfil de adotante"}
                  </Button>
                </Stack>
              </Box>
            </Stack>

            <Stack spacing={1} sx={{ alignItems: { xs: "flex-start", md: "flex-end" } }}>
              <IconButton onClick={handleLogout} sx={{ bgcolor: "#fff", borderRadius: 2, boxShadow: "0 4px 12px rgba(2,6,23,0.04)" }}>
                <LogoutIcon />
              </IconButton>
              <Typography variant="caption" color="gray">
                Conectado
              </Typography>
            </Stack>
          </Stack>

          <Divider sx={{ my: 3 }} />

          {/* Stats */}
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={4}>
              <Paper sx={{ p: 2, borderRadius: 2 }}>
                <Stack direction="row" spacing={2} alignItems="center">
                  <PetsIcon sx={{ color: "#6366F1", fontSize: 28 }} />
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 700 }}>
                      {mineCount}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Meus anúncios
                    </Typography>
                  </Box>
                </Stack>
                <Button onClick={gotoMyAds} sx={{ mt: 2, textTransform: "none" }} variant="outlined" fullWidth>
                  Ver anúncios
                </Button>
              </Paper>
            </Grid>

            <Grid item xs={12} sm={6} md={4}>
              <Paper sx={{ p: 2, borderRadius: 2 }}>
                <Stack direction="row" spacing={2} alignItems="center">
                  <PeopleIcon sx={{ color: "#6366F1", fontSize: 28 }} />
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 700 }}>
                      {hasPerfil ? "Sim" : "Não"}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Perfil de adotante
                    </Typography>
                  </Box>
                </Stack>
                <Button onClick={gotoEditPerfilAdotante} sx={{ mt: 2, textTransform: "none" }} variant="outlined" fullWidth>
                  {hasPerfil ? "Editar perfil" : "Criar perfil"}
                </Button>
              </Paper>
            </Grid>

            <Grid item xs={12} sm={12} md={4}>
              <Paper sx={{ p: 2, borderRadius: 2 }}>
                <Stack direction="row" spacing={2} alignItems="center">
                  <ArticleIcon sx={{ color: "#6366F1", fontSize: 28 }} />
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 700 }}>
                      —
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Recomendações recebidas
                    </Typography>
                  </Box>
                </Stack>
                <Button onClick={() => navigate("/animais")} sx={{ mt: 2, textTransform: "none" }} variant="outlined" fullWidth>
                  Ver recomendações
                </Button>
              </Paper>
            </Grid>
          </Grid>
        </Paper>
      </Container>
    </Box>
  );
}
