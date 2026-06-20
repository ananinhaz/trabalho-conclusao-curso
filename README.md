# AdoptMe — Trabalho de Conclusão de Curso

Repositório do sistema web **AdoptMe**, desenvolvido como Trabalho de Conclusão de Curso (TCC).

## Informações acadêmicas

| Campo | Valor |
|-------|-------|
| Tema | AdoptMe — plataforma de adoção de animais |
| Autora | Ana Carolina Rocha |
| Orientador | Diogo Vinícius Winck |
| Instituição | Católica de Santa Catarina |
| Curso | Engenharia de Software |

---

## O que o sistema faz

O AdoptMe conecta **adotantes** e **doadores** de animais por meio de uma aplicação web. Usuários autenticados podem:

- cadastrar-se e entrar com e-mail/senha ou **Google OAuth 2.0**;
- preencher um **perfil de adotante** (tipo de moradia, presença de crianças, tempo disponível, estilo de vida);
- publicar, editar e remover anúncios de animais;
- listar animais com filtros (espécie, idade, porte, cidade);
- receber **recomendações ordenadas** com base no perfil do adotante;
- marcar animais como adotados;
- visualizar métricas de adoções.

A recomendação **não substitui** a decisão do adotante: o sistema calcula uma proximidade numérica entre perfil e animal e exibe um **percentual de compatibilidade** na interface.

---

## Stack tecnológica (estado atual do repositório)

| Camada | Tecnologia |
|--------|------------|
| Frontend | React 18, Vite 5, Material UI 7, React Router 7 |
| Backend | Python 3.11, Flask 3, Gunicorn |
| Banco em produção | PostgreSQL 16 (container Docker) |
| Acesso a dados | SQL parametrizado via `psycopg2` (Postgres), com suporte a SQLite (testes locais) e MySQL (fallback legado em `db.py` e serviço MySQL no CI) |
| Cálculo de distância | NumPy + **scikit-learn** (`sklearn.metrics.pairwise_distances`) |
| Autenticação | JWT (`Flask-JWT-Extended`, `PyJWT`) + Google OAuth (`Authlib`) |
| Containerização | Docker, Docker Compose |
| Produção | AWS EC2, Nginx, Let's Encrypt, GitHub Container Registry (GHCR) |
| CI/CD | GitHub Actions (testes + SonarCloud + deploy) |

---

## Arquitetura

### Visão geral

```
[Browser] → [Nginx :443] → /     → [frontend :5173]  (React estático via serve)
                         → /api  → [backend :5000]   (Flask/Gunicorn)
                                    ↓
                              [PostgreSQL :5432]
```

Em **desenvolvimento local** com `docker-compose.yml`, Nginx não é utilizado: frontend (`5173`) e backend (`5000`) expõem portas diretamente.

### Backend (`backend/`)

- Aplicação Flask criada em `app/__init__.py` (`create_app()`).
- Rotas de autenticação: `app/controllers/auth_controller.py`, prefixo `/api/auth`.
- Rotas de negócio: `app/api.py`, prefixo `/api`.
- Conexão com banco: `app/extensions/db.py` — pool Postgres (`ThreadedConnectionPool`), SQLite em memória/arquivo para testes, ou MySQL se `DATABASE_URL` não estiver definida e variáveis `DB_*` estiverem configuradas.
- OAuth Google: `app/extensions/oauth.py`.
- Schema Postgres inicial: `backend/init_postgres.sql`.
- Servidor WSGI: `gunicorn` (ver `backend/Dockerfile` e `wsgi.py`).

**Principais endpoints (`/api`):**

| Método | Rota | Descrição |
|--------|------|-----------|
| GET/POST | `/perfil_adotante` | Consulta e upsert do perfil |
| GET/POST/PUT/DELETE | `/animais`, `/animais/<id>` | CRUD de animais |
| GET | `/animais/mine` | Anúncios do usuário logado |
| PATCH | `/animais/<id>/adopt` | Marcar/desmarcar adoção |
| GET | `/recomendacoes?n=` | Recomendações (ver seção abaixo) |
| GET | `/animais/metrics/adoptions` | Métricas de adoções |

**Autenticação (`/api/auth`):** registro, login, `/me`, fluxo Google (`/google`, `/google/callback`). O backend aceita identidade via sessão Flask, header `Authorization: Bearer <JWT>` ou token legado numérico.

### Frontend (`frontend/`)

- SPA React servida pelo Vite em desenvolvimento e por `serve` (build estático) em produção.
- URL da API configurada em tempo de build via `VITE_API_URL`.
- Páginas principais: `Landing`, `Login`, `Register`, `AdopterForm`, `Donate`, `Animals`, `Profile`.
- A página `Animals.jsx` exibe badges de compatibilidade quando o campo `compatibility_score` está presente na resposta de `/api/recomendacoes`.

### Banco de dados

**Produção e Docker local:** PostgreSQL 16, banco `adoptme`, tabelas principais:

- `usuarios` — contas (senha hash e/ou `google_sub`)
- `animais` — anúncios
- `perfil_adotante` — perfil do adotante (1:1 com usuário)
- `adocoes` — registros de adoção

**Testes automatizados locais:** `backend/tests/conftest.py` configura SQLite (`DATABASE_URL=sqlite:///test.db`).

**CI (GitHub Actions):** o workflow `ci-sonar.yml` sobe um serviço **MySQL 8.0** e executa os testes backend contra ele. Isso é ambiente de CI; **não** é o banco de produção.

---

## Sistema de recomendação

A rota ativa é **`GET /api/recomendacoes`**, implementada em `backend/app/api.py`.  
O módulo `backend/app/recommendation/engine.py` contém uma implementação alternativa com `sklearn.neighbors.NearestNeighbors`, mas **não é chamada** por essa rota HTTP.

### Quando há recomendação personalizada

Condições: usuário autenticado **e** perfil de adotante preenchido.

1. **Vetorização manual** — perfil e animal viram vetores numéricos de 4 dimensões:
   - `_build_user_vector(perfil)` — moradia, crianças, tempo normalizado (0–20 h → 0–1), estilo de vida.
   - `_build_animal_vector(animal)` — porte/espécie, compatibilidade com crianças, demanda de tempo, nível de atividade inferido.

2. **Distância ponderada** — calculada com:

   ```python
   sklearn.metrics.pairwise_distances(
       user_vec, X_animals,
       metric='minkowski', p=2, w=VEC_WEIGHTS
   )
   ```

   Pesos atuais (`VEC_WEIGHTS`): `[2.0, 1.5, 3.0, 2.0]` (moradia, crianças, tempo, estilo).

   Com `p=2` e pesos `w`, trata-se de **distância euclidiana ponderada** entre vetores. O scikit-learn é usado aqui como **biblioteca de cálculo numérico**; não há treinamento de modelo, ajuste de hiperparâmetros nem pipeline de machine learning.

3. **Ranking** — todos os animais disponíveis entram no cálculo (sem filtros rígidos de exclusão). Ordenação pela **distância crescente** (menor distância = maior proximidade).

4. **Score percentual** — para cada animal:

   ```
   max_distance = sqrt(soma(VEC_WEIGHTS))
   compatibility_score = max(0, 100 × (1 − distância / max_distance))
   ```

   Valor arredondado com uma casa decimal, retornado no JSON como `compatibility_score`.

5. **Resposta** — retorna os `n` primeiros (padrão `n=6`):

   ```json
   { "items": [ { "id": 1, "nome": "...", "compatibility_score": 78.5, ... } ], "ids": [1, ...] }
   ```

### Fallbacks (sem personalização)

- Usuário **não autenticado** → últimos `n` animais por `criado_em DESC`, sem `compatibility_score`.
- Usuário autenticado **sem perfil** → mesmo fallback cronológico.

### Interface (frontend)

Quando `compatibility_score` está presente, `Animals.jsx` exibe badge e percentual. Faixas atuais no código:

| Score | Texto exibido |
|-------|---------------|
| ≥ 85 | ⭐ Excelente compatibilidade |
| ≥ 70 | ✅ Boa compatibilidade |
| ≥ 50 | 🐾 Compatibilidade intermediária |
| ≥ 30 | 🔎 Requer mais atenção |
| < 30 | sem badge |

---

## Docker

### Desenvolvimento local — `docker-compose.yml`

| Serviço | Imagem / build | Portas |
|---------|----------------|--------|
| `tcc_db` | `postgres:16` | 5432 |
| `tcc_backend` | build `./backend` | 5000 |
| `tcc_frontend` | build `./frontend` (`VITE_API_URL=http://localhost:5000/api`) | 5173 |

Volume persistente: `postgres_data`.

```bash
docker compose up -d --build
```

### Produção (EC2) — `docker-compose.prod.yml`

| Serviço | Origem |
|---------|--------|
| `tcc_db` | `postgres:16` |
| `tcc_backend` | `ghcr.io/ananinhaz/adoptme-backend:latest` |
| `tcc_frontend` | `ghcr.io/ananinhaz/adoptme-frontend:latest` |
| `tcc_nginx` | `nginx:alpine` (proxy reverso, portas 80/443) |

Certificados TLS: volume `./certbot/conf` montado no Nginx. Configuração: `nginx/nginx.conf` (HTTP → HTTPS, `/api` → backend, `/` → frontend).

A EC2 **não executa build** de backend/frontend — apenas `docker pull` das imagens publicadas no GHCR.

---

## Deploy e CI/CD

### CI — `.github/workflows/ci-sonar.yml`

Disparado em push/PR na branch `main`:

1. Sobe MySQL 8.0 como serviço e cria schema de teste.
2. Executa testes backend (`pytest` + cobertura → `backend/coverage.xml`).
3. Executa testes frontend (`vitest` + cobertura → `frontend/coverage/lcov.info`).
4. Envia análise ao **SonarCloud**.

### CD — `.github/workflows/deploy.yml`

Disparado após CI bem-sucedido na `main` ou manualmente (`workflow_dispatch`):

1. **Job `build-and-push`:** build das imagens Docker de backend e frontend; push para GHCR com tags `:latest` e `:<commit-sha>`. Frontend buildado com `VITE_API_URL=https://adoptme.com.br/api`.
2. **Job `deploy`:** SSH na EC2 (`~/trabalho-conclusao-curso`), login no GHCR, execução de `scripts/deploy-ec2.sh`.

### Script de deploy — `scripts/deploy-ec2.sh`

- Atualiza código via `git pull` (preserva `.env` e `certbot/` locais).
- Preserva `nginx/nginx.conf` customizado da EC2.
- `docker pull` das imagens GHCR.
- `docker compose -f docker-compose.prod.yml up -d` — banco, backend, frontend; Nginx recriado somente se `nginx.conf` mudou.
- Aguarda healthcheck do Postgres antes de subir o backend.

**Secrets necessários no GitHub:** `EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY`, `GHCR_TOKEN` (PAT com `read:packages` para pull na EC2), `SONAR_TOKEN`, `SONAR_ORG`, `SONAR_PROJECTKEY`.

**Domínio de produção:** `adoptme.com.br`

---

## Desenvolvimento local (sem Docker)

### Pré-requisitos

- Python 3.11+
- Node.js 18+

### Backend

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\Activate.ps1
# Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
```

Configure variáveis de ambiente (arquivo `.env` na raiz ou em `backend/`), por exemplo:

- `DATABASE_URL=postgresql://postgres:postgres@localhost:5432/adoptme` (Postgres local), ou
- `DATABASE_URL=sqlite:///./test.db` + `python init_sqlite_schema.py` (SQLite)

Variáveis OAuth (opcionais para login Google): `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`, `FRONT_HOME`.

```bash
flask run
# http://127.0.0.1:5000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# http://127.0.0.1:5173
```

Defina `VITE_API_URL=http://127.0.0.1:5000/api` se necessário (`.env` no frontend ou variável de ambiente).

---

## Testes

**Backend:**

```bash
cd backend
pytest --cov=app --cov-report=xml --cov-report=term
```

**Frontend:**

```bash
cd frontend
npm run test:coverage
```

Relatórios de cobertura consumidos pelo SonarCloud no CI.

---

## Estrutura de diretórios (resumo)

```
├── backend/
│   ├── app/
│   │   ├── api.py                 # rotas REST + recomendação ativa
│   │   ├── controllers/           # auth, recommendation (wrapper)
│   │   ├── extensions/            # db, oauth
│   │   └── recommendation/        # engine legado (não usado pela rota /recomendacoes)
│   ├── init_postgres.sql
│   ├── Dockerfile
│   └── tests/
├── frontend/
│   ├── src/pages/                 # telas React
│   ├── Dockerfile
│   └── vitest.config.js
├── docker-compose.yml             # dev local
├── docker-compose.prod.yml        # produção EC2
├── nginx/nginx.conf
├── scripts/deploy-ec2.sh
└── .github/workflows/
    ├── ci-sonar.yml
    └── deploy.yml
```

---

## Dependências Python relevantes (`backend/requirements.txt`)

Flask, Gunicorn, NumPy, pandas, scikit-learn, psycopg2-binary, mysql-connector-python, PyJWT, Flask-JWT-Extended, Authlib, flask-cors, python-dotenv, requests.

O **pandas** e parte do **scikit-learn** são usados principalmente no módulo legado `recommendation/engine.py`. A rota `/api/recomendacoes` utiliza **NumPy** e `sklearn.metrics.pairwise_distances`.
