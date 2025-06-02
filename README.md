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

## 🧠 Inteligência Artificial

O sistema conta com um microserviço em Python (Flask) que utiliza machine learning (com Scikit-learn e Pandas) para recomendar animais com base no perfil do usuário.

## 🔧 Tecnologias Utilizadas

### Frontend
- React.js

### Backend
- Node.js
- Express

### Microserviço de IA
- Python
- Flask
- Scikit-learn
- Pandas

### Outros
- OAuth 2.0 (login com Google)
- Figma (protótipos)
- Microsoft Planner (gestão do projeto)
- GitHub (controle de versão)

## 🔒 Segurança

- Autenticação via Google usando OAuth 2.0
- Comunicação via HTTPS
- Proteção contra injeção SQL com uso de boas práticas e prepared statements

## 📂 Estrutura

O sistema segue arquitetura de microserviços:
- Frontend em React
- Backend em Node.js (API REST)
- Microserviço de recomendação em Python (Flask)
