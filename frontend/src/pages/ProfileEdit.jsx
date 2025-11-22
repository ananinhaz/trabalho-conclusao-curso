import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Container, Paper, Typography, TextField, Button, Stack } from "@mui/material";
import { authApi } from "../api";

export default function ProfileEdit() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ nome: "", email: "", avatar_url: "" });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const me = await authApi.me();
        if (me && me.user) {
          setForm({
            nome: me.user.nome || "",
            email: me.user.email || "",
            avatar_url: me.user.avatar_url || "",
          });
        } else if (me && me.user_id) {
          setForm({ nome: "", email: "", avatar_url: "" });
        }
      } catch (err) {}
      setLoading(false);
    })();
  }, []);

  function setField(k, v) {
    setForm((p) => ({ ...p, [k]: v }));
  }

  async function handleSave(e) {
    e.preventDefault();
    navigate("/perfil");
  }

  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>Editar conta</Typography>
        <form onSubmit={handleSave}>
          <Stack spacing={2}>
            <TextField label="Nome" value={form.nome} onChange={(e) => setField("nome", e.target.value)} fullWidth />
            <TextField label="Email" value={form.email} onChange={(e) => setField("email", e.target.value)} fullWidth />
            <TextField label="Avatar (URL)" value={form.avatar_url} onChange={(e) => setField("avatar_url", e.target.value)} fullWidth />
            <Stack direction="row" spacing={1}>
              <Button type="submit" variant="contained" sx={{ flex: 1 }}>Salvar</Button>
              <Button variant="outlined" sx={{ flex: 1 }} onClick={() => navigate("/perfil")}>Cancelar</Button>
            </Stack>
          </Stack>
        </form>
      </Paper>
    </Container>
  );
}
