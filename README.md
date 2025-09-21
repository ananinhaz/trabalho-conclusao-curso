# TCC - Adopt.me

Este repositório será utilizado para armazenar o desenvolvimento do Trabalho de Conclusão de Curso (TCC).

## Informações iniciais

- **Tema:** Adopt.me
- **Autor:** Ana Carolina Rocha
- **Orientador:** Diogo Vinícius Winck
- **Instituição:** Católica de Santa Catarina
- **Curso:** Engenharia de Software

# 🐾 Adopt.me

Adopt.me é um sistema web inteligente de adoção de animais. O projeto utiliza inteligência artificial para recomendar animais com base no perfil do adotante, promovendo adoções mais conscientes e compatíveis.

## 📌 Objetivo

Facilitar o processo de adoção de animais, conectando adotantes e doadores por meio de uma plataforma personalizada e intuitiva.

## 🚀 Funcionalidades

- Cadastro e login de usuários (incluindo autenticação via Google)
- Cadastro de animais para adoção
- Filtros de busca por espécie, idade, porte e localização
- Sistema de recomendação inteligente usando IA
- Interface com cards informativos dos animais
- Edição e exclusão de cadastros
- Indicação de animais recomendados com selo visual

## 🐾 Visão Geral

**AdoptMe** é um sistema web para adoção de animais. Nesta entrega o foco é **backend + banco de dados** com uma **API REST em Flask** e **MySQL**. Há também um **frontend demo** (página estática) para demonstrar o consumo da API.

> Próximas etapas previstas: autenticação via Google (OAuth 2.0) e motor de recomendação (KNN/Scikit-learn).

---

## 🧱 Arquitetura

- **Backend (Flask, Python)**
  - Padrão **MVC leve + camadas** (Controllers → Services → Repositories).
  - **Pool de conexões** MySQL (`mysql.connector.pooling`).
  - **Validação** com **Pydantic** (ex.: `EmailStr`).
  - **CORS** habilitado para o frontend demo.
  - Rotas de **health-check** e **CRUD** básico de `usuarios` e `animais`.

- **Banco de Dados (MySQL 8.x)**
  - Schema `adoptme` com tabelas `usuarios` e `animais`.

- **Frontend (demo)**
  - Página estática simples (`frontend/index.html`) que consome a API via `fetch`.


