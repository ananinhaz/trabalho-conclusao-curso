# backend/app/controllers/auth_controller.py
from __future__ import annotations
import os
from urllib.parse import urljoin
import requests

from flask import (
    Blueprint,
    url_for,
    request,
    jsonify,
    current_app,
    redirect,
    session,
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

import app.extensions.db as db_module
db = getattr(db_module, "db", None)

# oauth provider inicializado via init_oauth
from app.extensions.oauth import oauth


bp = Blueprint("auth", __name__, url_prefix="")

FRONT_DEFAULT = os.getenv("FRONT_HOME", "http://127.0.0.1:5173").rstrip("/")
GOOGLE_CALLBACK_ENV = os.getenv("GOOGLE_CALLBACK") or os.getenv("GOOGLE_REDIRECT_URI")


# --------------- HELPERS -----------------

def safe_fetchone(cur):
    try:
        return cur.fetchone()
    except Exception:
        return None


def _get_user_by_id(uid: int):
    if not uid:
        return None
    try:
        with db() as conn:
            try:
                with conn.cursor(dictionary=True) as cur:
                    cur.execute("SELECT id, nome, email, avatar_url FROM usuarios WHERE id=%s", (uid,))
                    return safe_fetchone(cur)
            except TypeError:
                cur = conn.cursor()
                cur.execute("SELECT id, nome, email, avatar_url FROM usuarios WHERE id=%s", (uid,))
                row = safe_fetchone(cur)
                cur.close()
                return row
    except Exception as exc:
        current_app.logger.exception("DB error _get_user_by_id: %s", exc)
        return None


def _make_token(uid):
    return create_access_token(identity=str(uid) if uid else None)


def is_postgres_db() -> bool:
    try:
        return bool(db_module.using_postgres())
    except Exception:
        return False


# --------------- REGISTER -----------------

@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    nome = (data.get("nome") or "").strip()
    email = (data.get("email") or "").strip().lower()
    senha = data.get("senha") or ""

    if not (nome and email and senha):
        return jsonify(ok=False, error="Dados obrigatórios"), 400

    try:
        with db() as conn:
            # verificar se email já existe
            try:
                with conn.cursor(dictionary=True) as cur:
                    cur.execute("SELECT id FROM usuarios WHERE email=%s", (email,))
                    if safe_fetchone(cur):
                        return jsonify(ok=False, error="Email já cadastrado"), 400
            except TypeError:
                cur = conn.cursor()
                cur.execute("SELECT id FROM usuarios WHERE email=%s", (email,))
                if safe_fetchone(cur):
                    return jsonify(ok=False, error="Email já cadastrado"), 400

            pw_hash = generate_password_hash(senha)

            # inserir
            if is_postgres_db():
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO usuarios (nome,email,password_hash) VALUES (%s,%s,%s) RETURNING id",
                    (nome, email, pw_hash),
                )
                row = safe_fetchone(cur)
                user_id = int(row[0]) if row else None
            else:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO usuarios (nome,email,password_hash) VALUES (%s,%s,%s)",
                    (nome, email, pw_hash),
                )
                user_id = int(getattr(cur, "lastrowid", None))

    except Exception as exc:
        current_app.logger.exception("DB error register: %s", exc)
        return jsonify(ok=False, error="Erro interno"), 500

    user = _get_user_by_id(user_id)
    token = _make_token(user_id)
    return jsonify(ok=True, user=user, access_token=token), 201


# --------------- LOGIN -----------------

@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    senha = data.get("senha") or ""

    if not (email and senha):
        return jsonify(ok=False, error="Credenciais inválidas"), 401

    try:
        with db() as conn:
            try:
                with conn.cursor(dictionary=True) as cur:
                    cur.execute("SELECT id, password_hash FROM usuarios WHERE email=%s", (email,))
                    row = safe_fetchone(cur)
            except TypeError:
                cur = conn.cursor()
                cur.execute("SELECT id, password_hash FROM usuarios WHERE email=%s", (email,))
                row = safe_fetchone(cur)

    except Exception as exc:
        current_app.logger.exception("DB error login: %s", exc)
        return jsonify(ok=False, error="Erro interno"), 500

    if not row or not check_password_hash(row["password_hash"], senha):
        return jsonify(ok=False, error="Credenciais inválidas"), 401

    user = _get_user_by_id(int(row["id"]))
    token = _make_token(int(row["id"]))
    return jsonify(ok=True, user=user, access_token=token)


# --------------- ME -----------------

@bp.get("/me")
@jwt_required()
def me():
    try:
        uid = int(get_jwt_identity())
        user = _get_user_by_id(uid)
        if not user:
            return jsonify(authenticated=False), 401
        return jsonify(authenticated=True, user=user)
    except Exception:
        return jsonify(authenticated=False), 401


# ---------------------------------------
#           GOOGLE OAUTH
# ---------------------------------------

@bp.get("/google")
def google_login():
    if not getattr(oauth, "google", None):
        return jsonify(ok=False, error="Google OAuth não configurado"), 500

    if not os.getenv("GOOGLE_CLIENT_ID"):
        return jsonify(ok=False, error="Missing GOOGLE_CLIENT_ID"), 500

    next_path = request.args.get("next") or "/"
    session["after_login_next"] = next_path

    callback_url = GOOGLE_CALLBACK_ENV or url_for(".google_callback", _external=True)

    return oauth.google.authorize_redirect(
        redirect_uri=callback_url,
        state=next_path,
    )


@bp.get("/google/callback")
def google_callback():
    try:
        # tenta fluxo padrão ou safe fallback da extensão
        if hasattr(oauth.google, "safe_authorize_access_token"):
            token = oauth.google.safe_authorize_access_token()
        else:
            token = oauth.google.authorize_access_token()

        access_token = token.get("access_token")
        if not access_token:
            raise Exception("No access_token in token response")

        # userinfo correto
        resp = requests.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        resp.raise_for_status()
        userinfo = resp.json()

        email = userinfo.get("email")
        sub = userinfo.get("sub")
        name = userinfo.get("name") or (email.split("@")[0] if email else "Usuário")
        avatar = userinfo.get("picture")

        if not email or not sub:
            return jsonify(ok=False, error="Google não retornou email/sub"), 400

        # BUSCAR/CRIAR usuário no DB
        with db() as conn:
            # procurar por google_sub
            cur = conn.cursor()
            cur.execute("SELECT id FROM usuarios WHERE google_sub=%s", (sub,))
            r = safe_fetchone(cur)

            if r:
                user_id = int(r[0])
            else:
                # procurar por email
                cur.execute("SELECT id FROM usuarios WHERE email=%s", (email,))
                r2 = safe_fetchone(cur)
                if r2:
                    user_id = int(r2[0])
                    cur.execute(
                        "UPDATE usuarios SET google_sub=%s, avatar_url=%s WHERE id=%s",
                        (sub, avatar, user_id),
                    )
                else:
                    # criar novo
                    if is_postgres_db():
                        cur.execute(
                            "INSERT INTO usuarios (nome,email,google_sub,avatar_url) VALUES (%s,%s,%s,%s) RETURNING id",
                            (name, email, sub, avatar),
                        )
                        row = safe_fetchone(cur)
                        user_id = int(row[0])
                    else:
                        cur.execute(
                            "INSERT INTO usuarios (nome,email,google_sub,avatar_url) VALUES (%s,%s,%s,%s)",
                            (name, email, sub, avatar),
                        )
                        user_id = int(getattr(cur, "lastrowid", None))

        # gerar token
        jwt_token = _make_token(user_id)

        # construir redirect
        FRONT = current_app.config.get("FRONT_HOME", FRONT_DEFAULT)
        next_path = request.args.get("state") or session.pop("after_login_next", "/")

        return redirect(f"{FRONT}/#token={jwt_token}&next={next_path}")

    except Exception as exc:
        current_app.logger.exception("Google OAuth error: %s", exc)
        return jsonify(ok=False, error="OAuth failure"), 400
