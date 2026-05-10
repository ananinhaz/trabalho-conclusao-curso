#!/usr/bin/env python3
"""
Cria o schema SQLite para desenvolvimento local.
Execute uma vez: python init_sqlite_schema.py
Requer DATABASE_URL=sqlite:///./dev.db (ou caminho desejado) em .env
"""
import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("DATABASE_URL", "")
if not url or "sqlite" not in url.lower():
    print("Defina DATABASE_URL=sqlite:///./dev.db em .env")
    exit(1)
path = url.replace("sqlite:///", "").split("?")[0]
path = path.replace("/", os.sep)
db_dir = Path(path).parent
db_dir.mkdir(parents=True, exist_ok=True)

con = sqlite3.connect(path)
cur = con.cursor()
cur.executescript("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT, email TEXT UNIQUE, password_hash TEXT,
    google_sub TEXT, avatar_url TEXT
);
CREATE TABLE IF NOT EXISTS animais (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT, especie TEXT, raca TEXT, idade TEXT, porte TEXT,
    descricao TEXT, cidade TEXT, photo_url TEXT, donor_name TEXT, donor_whatsapp TEXT,
    doador_id INTEGER, criado_em TEXT, adotado_em TEXT, energia TEXT, bom_com_criancas INTEGER
);
CREATE TABLE IF NOT EXISTS perfil_adotante (
    usuario_id INTEGER PRIMARY KEY,
    tipo_moradia TEXT, tem_criancas INTEGER,
    tempo_disponivel_horas_semana INTEGER, estilo_vida TEXT
);
""")
con.commit()
con.close()
print(f"Schema criado em {path}")
