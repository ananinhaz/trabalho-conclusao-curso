// src/pages/Home.jsx
import { useNavigate } from 'react-router-dom';

export default function Home() {
  const navigate = useNavigate();

  return (
    <div style={{ maxWidth: 640, margin: '60px auto', fontFamily: 'system-ui' }}>
      <h1>AdoptMe</h1>
      <p>Conectando pessoas e animais com responsabilidade.</p>
      <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
        {/* fluxo de adoção */}
        <button onClick={() => navigate('/login?next=/adopter-form')}>
          Quero adotar
        </button>
        {/* fluxo de doação */}
        <button onClick={() => navigate('/login?next=/donate')}>
          Quero doar
        </button>
      </div>
    </div>
  );
}
