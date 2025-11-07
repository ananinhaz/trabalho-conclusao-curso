// src/components/AnimalCard.jsx
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
} from '@mui/material'

export default function AnimalCard({ animal, isMine }) {
  return (
    <Card elevation={2} sx={{ borderRadius: 3, overflow:'hidden' }}>
      <CardContent>
        <Typography variant="h6">{animal.nome}</Typography>
        <Typography variant="body2" color="text.secondary">
          {animal.especie} • {animal.idade} • {animal.cidade}
        </Typography>
        <Typography variant="body2" sx={{ mt: 1 }}>
          {animal.descricao}
        </Typography>
        {isMine && <Chip label="meu" size="small" sx={{ mt: 1 }} />}
      </CardContent>
      <CardActions>
        {animal.donor_whatsapp && (
          <Button
            size="small"
            href={`https://wa.me/${animal.donor_whatsapp}`}
            target="_blank"
          >
            Falar com doador
          </Button>
        )}
      </CardActions>
    </Card>
  )
}
