# TCC - Adopt.me

Este repositório armazena o desenvolvimento completo do Trabalho de Conclusão de Curso (TCC).

## Informações iniciais

- **Tema:** Adopt.me
- **Autor:** Ana Carolina Rocha
- **Orientador:** Diogo Vinícius Winck
- **Instituição:** Católica de Santa Catarina
- **Curso:** Engenharia de Software

# 🐾 Adopt.me

Adopt.me é um sistema web inteligente de adoção de animais. O projeto utiliza **Inteligência Artificial** (KNN Ponderado) para recomendar animais com base no perfil do adotante, promovendo adoções mais conscientes e compatíveis.

## 📌 Objetivo

Facilitar o processo de adoção de animais, conectando adotantes e doadores por meio de uma plataforma personalizada e intuitiva, e **reduzindo a taxa de adoções mal-sucedidas** através da afinidade técnica.

## 🚀 Funcionalidades Chave

- **Sistema de Recomendação por IA:** Implementação customizada do algoritmo **K-Nearest Neighbors Ponderado (KNN)**, que calcula a afinidade por **Distância Euclidiana**.
- **Perfil do Adotante:** Formulário para coletar dados de estilo de vida (moradia, rotina, etc.) que alimentam o motor de IA.
- **Autenticação Segura:** Cadastro e login de usuários com suporte a **Google OAuth 2.0** e **JWT**.
- **Gerenciamento de Anúncios:** CRUD completo para anúncios de animais por doadores.
- **Interface:** Aplicação Single Page Application (SPA) com cards e selo visual de "Recomendado".
- **Filtros de Busca:** Opções de filtragem por espécie, idade, porte e localização.

## 🐾 Visão Geral

Adopt.me é um sistema web completo, com frontend em **React/Material UI**, backend em **API REST Flask** e banco de dados **PostgreSQL 16**. A aplicação é **containerizada com Docker** e hospedada em **AWS EC2**, com **Nginx** como reverse proxy e **HTTPS** via **Let's Encrypt**.

---

## 🧱 Stack e Arquitetura

| Camada | Tecnologia |
|--------|------------|
| Frontend | React, Vite, Material UI |
| Backend | Flask (Python), Gunicorn |
| Banco de dados | PostgreSQL 16 (container Docker) |
| Orquestração | Docker Compose |
| Hospedagem | AWS EC2 (Ubuntu) |
| Proxy / HTTPS | Nginx + Let's Encrypt |
| CI/CD | GitHub Actions |
| Autenticação | JWT + Google OAuth 2.0 |

### Containers em produção

| Container | Função |
|-----------|--------|
| `tcc_nginx` | Reverse proxy (portas 80/443) |
| `tcc_frontend` | Build React servido por `serve` |
| `tcc_backend` | API Flask via Gunicorn |
| `tcc_db` | PostgreSQL 16 (volume `postgres_data`) |

Conexão interna do backend ao banco:

```
postgresql://postgres:postgres@db:5432/adoptme
```

### Backend (Flask, Python)

- **Motor de IA:** KNN Ponderado em Python com Scikit-Learn (distância euclidiana ponderada).
- **API REST:** Blueprints para autenticação (`/api/auth`) e recursos (`/api`).
- **Segurança:** Prepared statements via psycopg2 e autenticação JWT no header `Authorization`.

### Banco de Dados (PostgreSQL 16)

- Schema `adoptme` com tabelas `usuarios`, `animais` e `perfil_adotante`.
- Dados persistidos no volume Docker `postgres_data`.
- Inicialização via `backend/init_postgres.sql`.

### Frontend (React / Material UI)

- SPA que consome a API REST.
- Principais páginas: `Animals.jsx`, `Donate.jsx`, `AdopterForm.jsx`, `Landing.jsx`.

---

## Desenvolvimento local

### Pré-requisitos

- Docker e Docker Compose **ou**
- Python 3.11+ e Node.js 18+ (desenvolvimento sem Docker)

### Opção 1 — Docker Compose (recomendado, igual à produção)

Na raiz do projeto:

```bash
docker compose up -d --build
```

- Frontend: http://localhost:5173 (ou via Nginx, conforme `docker-compose.yml`)
- Backend: http://localhost:5000
- PostgreSQL: container `tcc_db` (rede interna Docker)

Configure um arquivo `.env` na raiz com variáveis como `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` e `GOOGLE_REDIRECT_URI` quando necessário.

### Opção 2 — Backend e frontend separados

**Backend:**

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\Activate.ps1
# Linux/macOS:
# source venv/bin/activate
pip install -r requirements.txt
# Defina DATABASE_URL apontando para um PostgreSQL acessível
flask run
# Backend em http://127.0.0.1:5000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
# Frontend em http://127.0.0.1:5173
```

---

## Deploy em produção (AWS EC2)

A aplicação roda em instância **EC2 Ubuntu** com **Docker Compose**:

1. Clonar o repositório em `~/trabalho-conclusao-curso`
2. Configurar `.env` na EC2 (credenciais Google OAuth — **não versionar**)
3. Certificados HTTPS em `certbot/` (Let's Encrypt)
4. `docker compose up -d --build`

O domínio **adoptme.com.br** é servido via **Nginx** (`tcc_nginx`), que encaminha:

- `/` → frontend
- `/api` → backend

Deploy automatizado via **GitHub Actions** (workflow `deploy.yml`), disparado após o CI na branch `main`.

---

## Testes e cobertura

**Backend:**

```bash
cd backend
. venv\Scripts\Activate.ps1   # ou source venv/bin/activate
pytest --cov=app --cov-report=xml --cov-report=term
# coverage.xml em backend/coverage.xml
```

**Frontend:**

```bash
cd frontend
npm run test:coverage
# lcov.info em frontend/coverage/lcov.info
```

**SonarCloud:** Os relatórios `backend/coverage.xml` e `frontend/coverage/lcov.info` são usados pelo workflow de CI.
