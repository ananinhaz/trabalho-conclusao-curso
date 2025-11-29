from __future__ import annotations
import os
import requests
import traceback
from urllib.parse import urljoin
from flask import Blueprint, url_for, request, jsonify, redirect
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity 
from werkzeug.security import generate_password_hash, check_password_hash
import app.extensions.db as db_module
db = getattr(db_module, "db", None)

from ..extensions.oauth import oauth

bp = Blueprint("auth", __name__, url_prefix="/auth")

FRONT_DEFAULT = os.getenv("FRONT_HOME", "http://127.0.0.1:5173/").rstrip('/')
GOOGLE_CALLBACK = os.getenv("GOOGLE_CALLBACK", "http://127.0.0.1:5000/auth/google/callback")


def safe_fetchone(cur):
    """Wrapper resiliente para cur.fetchone() que converte StopIteration -> None."""
    try:
        return cur.fetchone()
    except StopIteration:
        return None
    except Exception:
        try:
            return cur.fetchone()
        except Exception:
            return None


def is_postgres_db():
    """Verifica se a conexão é PostgreSQL."""
    db_url = os.getenv("DATABASE_URL", "")
    return db_url.startswith("postgresql") or db_url.startswith("postgres")


def _get_user_by_id(uid: int):
    """Busca dados básicos de um usuário pelo ID."""
    try:
        with db() as conn:
            try:
                with conn.cursor(dictionary=True) as cur:
                    cur.execute(
                        "SELECT id, nome, email, avatar_url FROM usuarios WHERE id=%s",
                        (uid,)
                    )
                    user_data = safe_fetchone(cur)
                    return user_data
            except Exception:
                return None
    except Exception as exc:
        print(f"Erro ao buscar usuário {uid}: {repr(exc)}")
        traceback.print_exc()
        return None

def _abs_front_url(path: str) -> str:
    """Retorna uma URL absoluta para o frontend."""
    return urljoin(FRONT_DEFAULT.rstrip('/') + '/', path.lstrip('/'))

def _commit_and_redirect(url: str):
    """Redireciona para a URL e retorna uma resposta Flask."""
    return redirect(url)


# ----------------------------------------------------------------------
# Rotas de Autenticação Manual (JWT)
# ----------------------------------------------------------------------

# Cadastro
@bp.post("/register")
def register():
    data = request.json
    nome = data.get("nome")
    email = data.get("email")
    senha = data.get("senha")
    
    if not all([nome, email, senha]):
        return jsonify(ok=False, error="Nome, email e senha são obrigatórios"), 400

    new_id = None
    try:
        with db() as conn:
            # 1. Checa se o email já existe
            try:
                with conn.cursor(dictionary=True) as cur:
                    cur.execute("SELECT id FROM usuarios WHERE email=%s", (email,))
                    if safe_fetchone(cur):
                        return jsonify(ok=False, error="E-mail já cadastrado"), 409
            except:
                pass 

            # 2. Insere
            password_hash = generate_password_hash(senha)
            cur = conn.cursor()
            
            if is_postgres_db():
                cur.execute(
                    "INSERT INTO usuarios (nome, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                    (nome, email, password_hash)
                )
                row = safe_fetchone(cur)
                new_id = int(row[0]) if row and row[0] is not None else None
            else:
                cur.execute(
                    "INSERT INTO usuarios (nome, email, password_hash) VALUES (%s, %s, %s)",
                    (nome, email, password_hash)
                )
                new_id = int(getattr(cur, "lastrowid", None))

            try:
                cur.close()
            except Exception:
                pass
    except Exception as exc:
        print("Erro no DB durante register:", repr(exc))
        traceback.print_exc()
        return jsonify(ok=False, error="Erro interno ao cadastrar"), 500


    if not new_id:
        return jsonify(ok=False, error="Erro ao cadastrar usuário"), 500

    user_data = _get_user_by_id(int(new_id))

    if not user_data:
        return jsonify(ok=False, error="Cadastro bem-sucedido, mas erro ao buscar dados do usuário"), 500
        
    # CRIAÇÃO DO TOKEN JWT
    access_token = create_access_token(identity=int(new_id))
    
    return jsonify(
        ok=True, 
        user=user_data, 
        access_token=access_token # Retorna o token para o frontend
    ), 200 


# Login (email/senha)
@bp.post("/login")
def login():
    data = request.json
    email = data.get("email")
    senha = data.get("senha")
    
    if not all([email, senha]):
        return jsonify(ok=False, error="Email e senha são obrigatórios"), 400

    row = None
    try:
        with db() as conn:
            try:
                with conn.cursor(dictionary=True) as cur:
                    cur.execute(
                        "SELECT id, password_hash FROM usuarios WHERE email=%s",
                        (email,),
                    )
                    row = safe_fetchone(cur)
            except Exception:
                pass 
    except Exception as exc:
        print("Erro no DB durante login:", repr(exc))
        traceback.print_exc()
        return jsonify(ok=False, error="Erro interno ao buscar usuário"), 500

    if not row or not check_password_hash(row["password_hash"], senha):
        return jsonify(ok=False, error="Credenciais inválidas"), 401

    user_id = int(row["id"])
    
    user_data = _get_user_by_id(user_id)
    
    if not user_data:
        return jsonify(ok=False, error="Login bem-sucedido, mas erro ao buscar dados do usuário"), 500

    # CRIAÇÃO DO TOKEN JWT
    access_token = create_access_token(identity=user_id)
    
    return jsonify(
        ok=True, 
        user=user_data, 
        access_token=access_token # Retorna o token para o frontend
    ), 200 


# Logout (apenas notifica o frontend para apagar o token localmente)
@bp.post("/logout")
def logout():
    return jsonify(ok=True)


# Me (Protegido por JWT)
@bp.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity() # Pega o ID do usuário a partir do token
    user_data = _get_user_by_id(user_id)

    if not user_data:
        return jsonify(ok=False, error="Usuário não encontrado"), 404
        
    return jsonify(
        authenticated=True,
        user=user_data,
        user_id=user_id
    ), 200


# ----------------------------------------------------------------------
# Rotas de Autenticação Social (Google - Redireciona com JWT)
# ----------------------------------------------------------------------

@bp.get("/google/login")
def google_login():
    next_url = request.args.get('next', _abs_front_url('/animais'))
    
    return oauth.google.authorize_redirect(
        redirect_uri=GOOGLE_CALLBACK,
        state={"next": next_url}
    )


@bp.get("/google/callback")
def google_callback():
    final_next = _abs_front_url('/animais')
    
    try:
        token = oauth.google.authorize_access_token()
    except Exception as exc:
        print("Erro ao obter token do Google:", repr(exc))
        traceback.print_exc()
        return _commit_and_redirect(f"{final_next}?error=google_token_failed")

    # Extrai o estado, se houver
    state = request.args.get('state')
    if state:
        try:
            import json
            state_data = json.loads(state)
            final_next = state_data.get('next', final_next)
        except:
            print(f"Aviso: Estado de callback inválido: {state}")

    # Obtém as informações do usuário do Google
    user_info_response = requests.get('https://www.googleapis.com/oauth2/v3/userinfo', 
                                      headers={'Authorization': f'Bearer {token["access_token"]}'})
    user_info_response.raise_for_status()
    user_info = user_info_response.json()
    
    email = user_info.get("email")
    nome = user_info.get("name")
    avatar_url = user_info.get("picture")

    if not email:
        return _commit_and_redirect(f"{final_next}?error=email_nao_recebido")

    # Tenta encontrar o usuário no DB
    row = None
    try:
        with db() as conn:
            try:
                with conn.cursor(dictionary=True) as cur:
                    cur.execute("SELECT id, nome, avatar_url FROM usuarios WHERE email=%s", (email,))
                    row = safe_fetchone(cur)
            except Exception:
                pass 
    except Exception as exc:
        print("Erro no DB durante google_callback (busca):", repr(exc))
        traceback.print_exc()
        return _commit_and_redirect(f"{final_next}?error=db_search_failed")


    new_id = None
    if row:
        new_id = int(row["id"])
        # Atualiza nome e avatar caso tenha mudado
        try:
            with db() as conn:
                cur = conn.cursor()
                cur.execute(
                    "UPDATE usuarios SET nome=%s, avatar_url=%s WHERE id=%s",
                    (nome, avatar_url, new_id)
                )
                try:
                    cur.close()
                except Exception:
                    pass
        except Exception:
            pass
    else:
        # Usuário não encontrado, cria um novo
        try:
            with db() as conn:
                password_hash = generate_password_hash("") 
                cur = conn.cursor()
                
                if is_postgres_db():
                    cur.execute(
                        "INSERT INTO usuarios (nome, email, password_hash, avatar_url) VALUES (%s, %s, %s, %s) RETURNING id",
                        (nome, email, password_hash, avatar_url)
                    )
                    row = safe_fetchone(cur)
                    new_id = int(row[0]) if row and row[0] is not None else None
                else:
                    cur.execute(
                        "INSERT INTO usuarios (nome, email, password_hash, avatar_url) VALUES (%s, %s, %s, %s)",
                        (nome, email, password_hash, avatar_url)
                    )
                    new_id = int(getattr(cur, "lastrowid", None))

                try:
                    cur.close()
                except Exception:
                    pass
                
        except Exception as exc:
            print("Erro no DB durante google_callback (insert):", repr(exc))
            traceback.print_exc()
            return _commit_and_redirect(f"{final_next}?error=db_insert_failed")

    if not new_id:
        return _commit_and_redirect(f"{final_next}?error=login_failed")

    # CRIAÇÃO DO TOKEN JWT
    access_token = create_access_token(identity=int(new_id))
    
    # CRÍTICO: Redireciona para o frontend passando o token JWT na URL
    return _commit_and_redirect(f"{final_next}?token={access_token}&next={final_next}")