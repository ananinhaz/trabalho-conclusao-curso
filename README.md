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
- **Autenticação Segura:** Cadastro e login de usuários com suporte a **Google OAuth 2.0**.
- **Gerenciamento de Anúncios:** CRUD (Cadastro, Leitura, Atualização e Exclusão) completo para anúncios de animais por doadores.
- **Interface:** Aplicação Single Page Application (SPA) com cards e selo visual de "Recomendado".
- **Filtros de Busca:** Opções de filtragem por espécie, idade, porte e localização.

## 🐾 Visão Geral

Adopt.me é um sistema web completo, com o frontend desenvolvido em **React/Material UI** e o backend em **API REST Flask** e **PostgreSQL**. O foco principal desta entrega é a operação total da aplicação, validando o motor de recomendação como o principal diferencial técnico do TCC.

---

## 🧱 Arquitetura Técnica

O sistema segue uma arquitetura modularizada em três camadas, garantindo escalabilidade e separação de responsabilidades.

- **Backend (Flask, Python)**
  - **Motor de IA:** Lógica de negócio do KNN Ponderado implementada diretamente em Python, gerenciando a vetorização de dados e o cálculo de similaridade.
  - **API REST:** Estrutura organizada com **Blueprints** (`auth.py` e `api.py`) para gerenciar as rotas de autenticação, perfis e CRUD de animais.
  - **Segurança:** Uso de **Pydantic** para validação de dados e `prepared statements` no acesso ao MySQL para mitigar Injeção SQL.
  - **Conexão:** Utiliza **Pool de Conexões** MySQL (`mysql.connector.pooling`) para otimizar o desempenho.

- **Banco de Dados (MySQL 8.x)**
  - Schema `adoptme` com as tabelas cruciais `usuarios`, `animais` e `perfil_adotante`.

- **Frontend (React / Material UI)**
  - Aplicação Single Page Application (SPA) que consome a API REST.
  - Principais componentes incluem a página de listagem (`Animals.jsx`), o formulário de doação (`Donate.jsx`) e o formulário de perfil do adotante (`AdopterForm.jsx`).

---

## Desenvolvimento local

### Pré-requisitos
- Python 3.10+
- Node.js 18+
- (Opcional) MySQL, se não usar SQLite

### 1. Configurar variáveis de ambiente
```bash
cp .env.example .env
# Edite .env: para dev local com SQLite use DATABASE_URL=sqlite:///./backend/dev.db
```

### 2. Rodar o backend
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\Activate.ps1
# Linux/macOS:
# source venv/bin/activate
pip install -r requirements.txt
# Com .env com DATABASE_URL=sqlite:///./dev.db (caminho relativo a backend/)
# Criar tabelas SQLite (uma vez):
python init_sqlite_schema.py
flask run
# ou: python -m flask run
# Backend em http://127.0.0.1:5000
```

### 3. Rodar o frontend
```bash
cd frontend
npm install
npm run dev
# Frontend em http://127.0.0.1:5173
```

### 4. Testes e cobertura

**Backend (SQLite nos testes):**
```bash
cd backend
# Certifique-se de que .env tem DATABASE_URL=sqlite:///... ou deixe o conftest definir
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

**Sonar:** Os relatórios `backend/coverage.xml` e `frontend/coverage/lcov.info` são usados pelo SonarCloud no CI.
