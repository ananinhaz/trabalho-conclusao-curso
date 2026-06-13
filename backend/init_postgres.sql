CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT,
    google_id TEXT,
    google_sub TEXT,
    avatar_url TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS animais (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER,
    nome TEXT NOT NULL,
    especie TEXT NOT NULL,
    idade INTEGER,
    porte TEXT,
    energia TEXT,
    bom_com_criancas BOOLEAN,
    cidade TEXT,
    city TEXT,
    disponivel BOOLEAN,
    doador_id INTEGER,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    donor_name TEXT,
    donor_whatsapp TEXT,
    photo_url TEXT,
    raca TEXT,
    descricao TEXT,
    status TEXT,
    adotado_em TIMESTAMP
);

CREATE TABLE IF NOT EXISTS perfil_adotante (
    usuario_id INTEGER PRIMARY KEY REFERENCES usuarios(id) ON DELETE CASCADE,
    tipo_moradia TEXT,
    tem_criancas BOOLEAN,
    tempo_disponivel_horas_semana INTEGER,
    estilo_vida TEXT,
    atualizado_em TIMESTAMP
);

CREATE TABLE IF NOT EXISTS adocoes (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    animal_id INTEGER NOT NULL REFERENCES animais(id),
    status TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
