/** Constantes visuais — somente UI, sem lógica de negócio */
export const colors = {
  primary: '#6366F1',
  secondary: '#8B5CF6',
  background: '#F8FAFC',
  card: '#FFFFFF',
  text: '#0F172A',
  textMuted: '#64748B',
  gold: '#F59E0B',
  goldBg: '#FEF3C7',
  goldText: '#B45309',
  success: '#10B981',
  border: '#E2E8F0',
};

export const gradientPrimary = 'linear-gradient(90deg, #6366F1 0%, #8B5CF6 100%)';

export const shadows = {
  soft: '0 4px 24px rgba(15, 23, 42, 0.06)',
  card: '0 8px 32px rgba(15, 23, 42, 0.08)',
  header: '0 2px 16px rgba(15, 23, 42, 0.06)',
  hover: '0 12px 40px rgba(15, 23, 42, 0.12)',
};

export const radii = {
  card: '20px',
  input: '14px',
  button: '12px',
  pill: '9999px',
};

export const cardSx = {
  borderRadius: radii.card,
  bgcolor: colors.card,
  boxShadow: shadows.soft,
  border: '1px solid rgba(15, 23, 42, 0.04)',
  transition: 'all 0.2s ease',
};

export const btnGradient = {
  background: gradientPrimary,
  color: '#fff',
  borderRadius: radii.button,
  height: 42,
  fontWeight: 600,
  textTransform: 'none',
  boxShadow: 'none',
  transition: 'all 0.2s ease',
  '&:hover': {
    background: 'linear-gradient(90deg, #4F46E5 0%, #7C3AED 100%)',
    boxShadow: '0 6px 20px rgba(99, 102, 241, 0.35)',
  },
};

export const btnOutline = {
  borderRadius: radii.pill,
  textTransform: 'none',
  fontWeight: 600,
  borderColor: colors.primary,
  color: colors.primary,
  transition: 'all 0.2s ease',
  '&:hover': {
    borderColor: '#4F46E5',
    bgcolor: '#EEF2FF',
  },
};

export const btnEdit = {
  background: '#fff',
  border: '1px solid #D1D5DB',
  color: '#374151',
  borderRadius: radii.button,
  height: 42,
  fontWeight: 600,
  textTransform: 'none',
  transition: 'all 0.2s ease',
  '&:hover': { bgcolor: '#F9FAFB', borderColor: '#9CA3AF' },
};

export const btnDelete = {
  background: '#FEF2F2',
  border: '1px solid #FCA5A5',
  color: '#DC2626',
  borderRadius: radii.button,
  height: 42,
  fontWeight: 600,
  textTransform: 'none',
  transition: 'all 0.2s ease',
  '&:hover': { bgcolor: '#FEE2E2', borderColor: '#F87171' },
};

export const inputSx = {
  '& .MuiOutlinedInput-root': {
    borderRadius: radii.input,
    bgcolor: '#fff',
    transition: 'all 0.2s ease',
    '& fieldset': { borderColor: colors.border },
    '&:hover fieldset': { borderColor: colors.primary },
    '&.Mui-focused fieldset': { borderColor: colors.primary },
  },
};
