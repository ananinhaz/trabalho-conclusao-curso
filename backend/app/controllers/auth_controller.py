from __future__ import annotations
import os
import requests
import traceback
from urllib.parse import urljoin
# 💡 IMPORTANTE: 'redirect' deve estar aqui!
# 💡 NOVO: Importar módulos JWT
from flask import Blueprint, url_for, request, session, jsonify, redirect
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity 
from werkzeug.security import generate_password_hash, check_password_hash
import app.extensions.db as db_module
db = getattr(db_module, "db", None)

from ..extensions.oauth import oauth

bp = Blueprint("auth", __name__, url_prefix="/auth")

FRONT_DEFAULT = os.getenv("FRONT_HOME", "http://127.0.0.1:5173/")
GOOGLE_CALLBACK = os.getenv("GOOGLE_CALLBACK", "http://127.0.0.1:5000/auth/google/callback")


# ... (funções auxiliares: safe_fetchone, _get_user_by_id, is_postgres_db - MANTER) ...


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


def _get_user_by_id(uid: int):
    # ... (MANTER: lógica de busca no banco de dados) ...
    try:
        with db() as conn:
            try:
                with conn.cursor(dictionary=True) as cur:
                    cur.execute(
                        "SELECT id, nome, email, avatar_url FROM usuarios WHERE id=%s",
                        (uid,),
                    )
                    row = safe_fetchone(cur)
            except TypeError:
                cur = conn.cursor()
                cur.execute(
                    "SELECT id, nome, email, avatar_url FROM usuarios WHERE id=%s",
                    (uid,),
                )
                row = safe_fetchone(cur)
                try:
                    cur.close()
                except Exception:
                    pass
            return row
    except Exception as exc:
        print("Erro no DB durante _get_user_by_id:", repr(exc))
        traceback.print_exc()
        return None


def _abs_front_url(target: str) -> str:
    if not target:
        return FRONT_DEFAULT
    if target.startswith("http://") or target.startswith("https://"):
        return target
    return urljoin(FRONT_DEFAULT, target.lstrip("/"))


# 💡 FUNÇÃO DE REDIRECIONAMENTO (MANTER)
def _commit_and_redirect(url: str):
    """
    Substitui o redirecionamento baseado em JS/HTML por um redirecionamento HTTP 302
    usando flask.redirect.
    """
    final_url = _abs_front_url(url)
    final_url = final_url.replace("localhost:5173", "127.0.0.1:5173")
    return redirect(final_url)


def is_postgres_db() -> bool:
    # ... (MANTER: lógica de detecção de DB) ...
    try:
        fn = getattr(db_module, "using_postgres", None)
        if callable(fn):
            return bool(fn())
    except Exception:
        pass
    try:
        return bool(getattr(db_module, "_using_postgres", False))
    except Exception:
        return False


# cadastro
@bp.post("/register")
def register():
    # ... (MANTER: validação, busca por email e inserção no DB) ...

    # 💡 MUDANÇA: Substituir session pelo JWT
    if not new_id:
        return jsonify(ok=False, error="Erro ao cadastrar usuário"), 500

    # ❌ REMOVER: session["user_id"] = int(new_id) if new_id is not None else None
    # ❌ REMOVER: session.modified = True

    access_token = create_access_token(identity=int(new_id))
    
    return jsonify(
        ok=True, 
        user=_get_user_by_id(int(new_id)),
        access_token=access_token # 💡 Retorna o token
    )


# login (email/senha)
@bp.post("/login")
def login():
    # ... (MANTER: busca no DB, validação de senha) ...

    if not row or not check_password_hash(row["password_hash"], senha):
        return jsonify(ok=False, error="Credenciais inválidas"), 401

    user_id = int(row["id"])

    # ❌ REMOVER: session["user_id"] = user_id
    # ❌ REMOVER: session.modified = True

    # 💡 MUDANÇA: Cria e retorna o token JWT
    access_token = create_access_token(identity=user_id)
    
    return jsonify(
        ok=True, 
        user=_get_user_by_id(user_id),
        access_token=access_token # 💡 Retorna o token
    )


# logout
@bp.post("/logout")
def logout():
    # ❌ REMOVER: session.clear()
    # O logout agora é feito limpando o token no frontend (LocalStorage)
    return jsonify(ok=True)


# me
@bp.get("/me")
@jwt_required() # 💡 MUDANÇA: Protege a rota com JWT
def me():
    # ❌ REMOVER: print("SESSION NO /me:", dict(session))
    
    # 💡 MUDANÇA: Pega o ID do usuário do token JWT
    user_id = get_jwt_identity() 
    
    # ❌ REMOVER: user_id = session.get("user_id") or (session.get("user") or {}).get("id")
    
    if not user_id:
        return jsonify({"authenticated": False}), 401 

    # ... (MANTER: lógica de busca no DB) ...
    try:
        with db() as conn:
            try:
                with conn.cursor(dictionary=True) as cur:
                    cur.execute(
                        "SELECT id, nome, email, avatar_url FROM usuarios WHERE id=%s",
                        (int(user_id),),
                    )
                    user = safe_fetchone(cur)
            except TypeError:
                cur = conn.cursor()
                cur.execute(
                    "SELECT id, nome, email, avatar_url FROM usuarios WHERE id=%s",
                    (int(user_id),),
                )
                user = safe_fetchone(cur)
                try:
                    cur.close()
                except Exception:
                    pass
    except Exception as exc:
        print("Erro no DB durante /me:", repr(exc))
        traceback.print_exc()
        # ❌ REMOVER: session.clear()
        return jsonify({"authenticated": False}), 401

    if not user:
        # ❌ REMOVER: session.clear()
        return jsonify({"authenticated": False}), 401

    return jsonify({"authenticated": True, "user": user})


# login com o google
@bp.get("/login/google")
def login_google():
    """
    Front chama: /auth/login/google?next=/perfil-adotante
    """
    next_url = request.args.get("next") or ""
    # ❌ REMOVER: if next_url: session["after_login_next"] = next_url
    
    redirect_uri = GOOGLE_CALLBACK
    print("➡️ redirect_uri que estou mandando pro Google:", redirect_uri)

    # 💡 MUDANÇA: Passar o 'next' como parte do 'state'
    state_payload = next_url if next_url else "no-next"

    return oauth.google.authorize_redirect(
        redirect_uri,
        state=state_payload,
    )


@bp.get("/google/callback")
def google_callback():
    # ... (MANTER: Obter token do Google e userinfo) ...
    token = oauth.google.safe_authorize_access_token()
    print("🔍 Google token:", token)
    access_token = token.get("access_token")
    if not access_token:
        return _commit_and_redirect("/login")

    resp = requests.get(
        "https://openidconnect.googleapis.com/v1/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    if resp.status_code != 200:
        return _commit_and_redirect("/login")

    info = resp.json()
    sub = info.get("sub")
    email = info.get("email")
    nome = info.get("name") or (email.split("@")[0] if email else "Usuário")
    avatar = info.get("picture")

    if not sub:
        return _commit_and_redirect("/login")

    # ❌ REMOVER: session_next = session.pop("after_login_next", None)
    
    # 💡 MUDANÇA: Pega o 'next' do parâmetro 'state'
    state_next = request.args.get("state")
    final_next_path = (
        state_next 
        if state_next and state_next != "no-next" else "/perfil-adotante"
    )

    # ... (MANTER: Lógica de busca e criação de usuário no DB) ...
    user_id = None
    try:
        with db() as conn:
            # 1. Tenta achar por google_sub
            # ... (código para u, user_id)
            try:
                with conn.cursor(dictionary=True) as cur:
                    cur.execute("SELECT id FROM usuarios WHERE google_sub=%s", (sub,))
                    u = safe_fetchone(cur)
            except TypeError:
                cur = conn.cursor()
                cur.execute("SELECT id FROM usuarios WHERE google_sub=%s", (sub,))
                u = safe_fetchone(cur)
                try:
                    cur.close()
                except Exception:
                    pass

            if u:
                user_id = int(u["id"])
                print("✅ login google: achou por google_sub ->", user_id)
            
            # 2. Tenta achar por email e vincular
            elif email:
                try:
                    with conn.cursor(dictionary=True) as cur:
                        cur.execute("SELECT id FROM usuarios WHERE email=%s", (email,))
                        u = safe_fetchone(cur)
                except TypeError:
                    cur = conn.cursor()
                    cur.execute("SELECT id FROM usuarios WHERE email=%s", (email,))
                    u = safe_fetchone(cur)
                    try:
                        cur.close()
                    except Exception:
                        pass

                if u:
                    user_id = int(u["id"])
                    # update vinculo
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE usuarios SET google_sub=%s, avatar_url=%s WHERE id=%s",
                        (sub, avatar, user_id),
                    )
                    try:
                        cur.close()
                    except Exception:
                        pass
                    print("✅ login google: achou por email e vinculou ->", user_id)
            
            # 3. Novo usuário
            if not user_id:
                cur = conn.cursor()
                if is_postgres_db():
                    cur.execute(
                        "INSERT INTO usuarios (nome,email,google_sub,avatar_url) VALUES (%s,%s,%s,%s) RETURNING id",
                        (nome, email, sub, avatar),
                    )
                    row = safe_fetchone(cur)
                    new_id = int(row[0]) if row else None
                else:
                    cur.execute(
                        "INSERT INTO usuarios (nome,email,google_sub,avatar_url) VALUES (%s,%s,%s,%s)",
                        (nome, email, sub, avatar),
                    )
                    try:
                        new_id = int(getattr(cur, "lastrowid", None))
                    except Exception:
                        new_id = None

                try:
                    cur.close()
                except Exception:
                    pass
                
                # Fallback para obter new_id
                if not new_id:
                    try:
                        cur2 = conn.cursor(dictionary=True)
                        cur2.execute("SELECT id FROM usuarios WHERE email=%s", (email,))
                        r2 = safe_fetchone(cur2)
                    except Exception:
                        r2 = None
                    finally:
                        try:
                            cur2.close()
                        except Exception:
                            pass

                    if r2 and r2.get("id"):
                        new_id = int(r2.get("id"))

                if new_id:
                    user_id = new_id
                    print("✅ login google: criou novo usuario ->", user_id)

    except Exception as exc:
        print("Erro no DB durante google_callback:", repr(exc))
        traceback.print_exc()
        return _commit_and_redirect("/login")


    # 💡 MUDANÇA CRÍTICA: Geração do JWT e Redirecionamento com Token na URL
    if user_id:
        access_token = create_access_token(identity=user_id)
        
        # ❌ REMOVER: session["user_id"] = int(user_id) ; session.modified = True

        # Redireciona para o frontend, adicionando o token na URL
        final_redirect_url = _abs_front_url(final_next_path)
        
        # ⚠️ MUDANÇA: Adiciona o token na URL antes de redirecionar
        # Se já houver query string, usa '&', senão usa '?'
        sep = '&' if '?' in final_redirect_url else '?'
        final_redirect_url += f"{sep}token={access_token}"
        
        return redirect(final_redirect_url, code=302)
    
    # Falha de login/cadastro
    return _commit_and_redirect("/login")