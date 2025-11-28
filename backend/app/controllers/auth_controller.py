from __future__ import annotations
import os
import requests
from urllib.parse import urljoin
from flask import Blueprint, url_for, request, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions.db import db
from ..extensions.oauth import oauth

bp = Blueprint("auth", __name__, url_prefix="/auth")

# config: use env vars (em produção defina FRONT_HOME e GOOGLE_CALLBACK)
FRONT_DEFAULT = os.getenv("FRONT_HOME", "http://127.0.0.1:5173/")
GOOGLE_CALLBACK = os.getenv("GOOGLE_CALLBACK", "http://127.0.0.1:5000/auth/google/callback")


def _get_user_by_id(uid: int):
    with db() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT id, nome, email, avatar_url FROM usuarios WHERE id=%s",
            (uid,),
        )
        row = cur.fetchone()
        cur.close()
        return row


def _abs_front_url(target: str) -> str:
    if not target:
        return FRONT_DEFAULT
    if target.startswith("http://") or target.startswith("https://"):
        return target
    return urljoin(FRONT_DEFAULT, target.lstrip("/"))


def _commit_and_redirect(url: str):
    final_url = _abs_front_url(url)
    return (
        f"""<!doctype html><meta charset="utf-8">
<script>
  setTimeout(function(){{ window.location.replace("{final_url}"); }}, 200);
</script>
<p>Autenticado com sucesso. Redirecionando…</p>""",
        200,
        {"Content-Type": "text/html; charset=utf-8"},
    )


def is_postgres_db() -> bool:
    """
    Detecta se o 'db' extension está configurada para Postgres.
    Implementa heurística similar ao resto do projeto.
    """
    try:
        fn = getattr(db, "using_postgres", None)
        if callable(fn):
            return bool(fn())
    except Exception:
        pass
    try:
        return bool(getattr(db, "_using_postgres", False))
    except Exception:
        return False


# cadastro/login
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
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT id FROM usuarios WHERE email=%s", (email,))
            if cur.fetchone():
                cur.close()
                return jsonify(ok=False, error="Email já cadastrado"), 400
            cur.close()

            # Inserção compatível com Postgres (RETURNING) e MySQL (lastrowid)
            if is_postgres_db():
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO usuarios (nome,email,password_hash) VALUES (%s,%s,%s) RETURNING id",
                    (nome, email, generate_password_hash(senha)),
                )
                row = cur.fetchone()
                # row pode ser tuple/list com primeiro elemento id
                if row:
                    try:
                        uid = int(row[0])
                    except Exception:
                        uid = None
                else:
                    uid = None
                cur.close()
            else:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO usuarios (nome,email,password_hash) VALUES (%s,%s,%s)",
                    (nome, email, generate_password_hash(senha)),
                )
                try:
                    uid = int(cur.lastrowid)
                except Exception:
                    uid = None
                cur.close()

            # sanity check
            if not uid:
                # tenta buscar pelo email (por segurança)
                cur = conn.cursor(dictionary=True)
                cur.execute("SELECT id FROM usuarios WHERE email=%s", (email,))
                r = cur.fetchone()
                cur.close()
                if r and r.get("id"):
                    uid = int(r.get("id"))
                else:
                    raise RuntimeError("Não foi possível obter id do novo usuário")
    except Exception as exc:
        print("Erro no DB durante register:", exc)
        return jsonify(ok=False, error="Erro interno"), 500

    session["user_id"] = int(uid)
    session.modified = True
    return jsonify(ok=True, user=_get_user_by_id(uid))


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    senha = data.get("senha") or ""

    if not (email and senha):
        return jsonify(ok=False, error="Credenciais inválidas"), 401

    try:
        with db() as conn:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT id, password_hash FROM usuarios WHERE email=%s", (email,))
            row = cur.fetchone()
            cur.close()
    except Exception as exc:
        print("Erro no DB durante login:", exc)
        return jsonify(ok=False, error="Erro interno"), 500

    if not row or not check_password_hash(row["password_hash"], senha):
        return jsonify(ok=False, error="Credenciais inválidas"), 401

    session["user_id"] = int(row["id"])
    session.modified = True
    return jsonify(ok=True, user=_get_user_by_id(int(row["id"])))


@bp.post("/logout")
def logout():
    session.clear()
    return jsonify(ok=True)


@bp.get("/me")
def me():
    print("SESSION NO /me:", dict(session))
    user_id = session.get("user_id") or (session.get("user") or {}).get("id")
    if not user_id:
        return jsonify({"authenticated": False}), 401

    try:
        with db() as conn:
            with conn.cursor(dictionary=True) as cur:
                cur.execute(
                    "SELECT id, nome, email, avatar_url FROM usuarios WHERE id=%s",
                    (int(user_id),),
                )
                user = cur.fetchone()
    except Exception as exc:
        print("Erro no DB durante /me:", exc)
        session.clear()
        return jsonify({"authenticated": False}), 401

    if not user:
        session.clear()
        return jsonify({"authenticated": False}), 401

    return jsonify({"authenticated": True, "user": user})


# login com o google
@bp.get("/login/google")
def login_google():
    """
    Front chama: /auth/login/google?next=/perfil-adotante
    """
    next_url = request.args.get("next") or ""
    if next_url:
        session["after_login_next"] = next_url
    redirect_uri = GOOGLE_CALLBACK
    print("➡️ redirect_uri que estou mandando pro Google:", redirect_uri)

    return oauth.google.authorize_redirect(
        redirect_uri,
        state=next_url or "no-next",
    )


@bp.get("/google/callback")
def google_callback():
    token = oauth.google.safe_authorize_access_token()
    print("🔍 Google token:", token)
    access_token = token.get("access_token")
    if not access_token:
        return jsonify(ok=False, error="Google não retornou access_token"), 400

    resp = requests.get(
        "https://openidconnect.googleapis.com/v1/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    if resp.status_code != 200:
        return jsonify(ok=False, error=f"Falha ao obter userinfo: {resp.text}"), 400

    info = resp.json()
    sub = info.get("sub")
    email = info.get("email")
    nome = info.get("name") or (email.split("@")[0] if email else "Usuário")
    avatar = info.get("picture")

    if not sub:
        return jsonify(ok=False, error="Google não retornou sub"), 400

    session_next = session.pop("after_login_next", None)
    state_next = request.args.get("state")
    final_next = (
        session_next
        or (state_next if state_next and state_next != "no-next" else None)
        or FRONT_DEFAULT
    )

    try:
        with db() as conn:
            cur = conn.cursor(dictionary=True)

            cur.execute("SELECT id FROM usuarios WHERE google_sub=%s", (sub,))
            u = cur.fetchone()
            if u:
                user_id = int(u["id"])
                session["user_id"] = user_id
                session.modified = True
                cur.close()
                print("✅ login google: achou por google_sub ->", user_id)
                return _commit_and_redirect(final_next)

            if email:
                cur.execute("SELECT id FROM usuarios WHERE email=%s", (email,))
                u = cur.fetchone()
                if u:
                    user_id = int(u["id"])
                    cur.close()
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE usuarios SET google_sub=%s, avatar_url=%s WHERE id=%s",
                        (sub, avatar, user_id),
                    )
                    cur.close()
                    session["user_id"] = user_id
                    session.modified = True
                    print("✅ login google: achou por email e vinculou ->", user_id)
                    return _commit_and_redirect(final_next)

            cur.close()
            cur = conn.cursor()
            # new user (Postgres/MySQL compatible: use RETURNING if available)
            if is_postgres_db():
                cur.execute(
                    "INSERT INTO usuarios (nome,email,google_sub,avatar_url) VALUES (%s,%s,%s,%s) RETURNING id",
                    (nome, email, sub, avatar),
                )
                row = cur.fetchone()
                new_id = int(row[0]) if row else None
                cur.close()
            else:
                cur.execute(
                    "INSERT INTO usuarios (nome,email,google_sub,avatar_url) VALUES (%s,%s,%s,%s)",
                    (nome, email, sub, avatar),
                )
                try:
                    new_id = int(cur.lastrowid)
                except Exception:
                    new_id = None
                cur.close()
    except Exception as exc:
        print("Erro no DB durante google_callback:", exc)
        return jsonify(ok=False, error="Erro interno"), 500

    if not new_id:
        return jsonify(ok=False, error="Falha ao criar usuário"), 500

    session["user_id"] = int(new_id)
    session.modified = True
    print("✅ login google: criou novo usuario ->", new_id)
    return _commit_and_redirect(final_next)
