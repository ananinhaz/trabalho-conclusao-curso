# backend/app/controllers/auth_controller.py
from __future__ import annotations
import os
import traceback
from urllib.parse import urljoin
from flask import Blueprint, url_for, request, jsonify, current_app, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

import app.extensions.db as db_module
db = getattr(db_module, "db", None)

from ..extensions.oauth import oauth

bp = Blueprint("auth", __name__, url_prefix="")  # we'll mount to /api/auth in create_app()

FRONT_DEFAULT = os.getenv("FRONT_HOME", "http://127.0.0.1:5173/")
GOOGLE_CALLBACK = os.getenv("GOOGLE_CALLBACK", "http://127.0.0.1:5000/api/auth/google/callback")


def safe_fetchone(cur):
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
        current_app.logger.exception("Erro no DB durante _get_user_by_id: %s", exc)
        return None


def _abs_front_url(target: str) -> str:
    if not target:
        return FRONT_DEFAULT
    if target.startswith("http://") or target.startswith("https://"):
        return target
    return urljoin(FRONT_DEFAULT, target.lstrip("/"))


def _commit_and_redirect(url: str):
    final_url = _abs_front_url(url)
    final_url = final_url.replace("localhost:5173", "127.0.0.1:5173")
    # For JWT flow we will redirect with fragment token, but keep simple HTML fallback
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


# ---------- REGISTRATION (returns JWT) ----------
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
            try:
                with conn.cursor(dictionary=True) as cur:
                    cur.execute("SELECT id FROM usuarios WHERE email=%s", (email,))
                    found = safe_fetchone(cur)
            except TypeError:
                cur = conn.cursor()
                cur.execute("SELECT id FROM usuarios WHERE email=%s", (email,))
                found = safe_fetchone(cur)
                try:
                    cur.close()
                except Exception:
                    pass

            if found:
                return jsonify(ok=False, error="Email já cadastrado"), 400

            new_id = None
            pw_hash = generate_password_hash(senha)

            if is_postgres_db():
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO usuarios (nome,email,password_hash) VALUES (%s,%s,%s) RETURNING id",
                    (nome, email, pw_hash),
                )
                row = safe_fetchone(cur)
                new_id = int(row[0]) if row and row[0] is not None else None
                try:
                    cur.close()
                except Exception:
                    pass
            else:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO usuarios (nome,email,password_hash) VALUES (%s,%s,%s)",
                    (nome, email, pw_hash),
                )
                try:
                    new_id = int(getattr(cur, "lastrowid", None))
                except Exception:
                    new_id = None
                try:
                    cur.close()
                except Exception:
                    pass

            # fallback: select by email to get id
            if not new_id:
                try:
                    cur2 = conn.cursor(dictionary=True)
                    cur2.execute("SELECT id FROM usuarios WHERE email=%s", (email,))
                    r = safe_fetchone(cur2)
                except Exception:
                    r = None
                finally:
                    try:
                        cur2.close()
                    except Exception:
                        pass

                if r and r.get("id"):
                    new_id = int(r.get("id"))
                else:
                    current_app.logger.warning("Could not determine new user id after insert.")

    except Exception as exc:
        current_app.logger.exception("Erro no DB durante register: %s", exc)
        return jsonify(ok=False, error="Erro interno"), 500

    # Success -> return JWT and user payload
    user = _get_user_by_id(new_id) if new_id else None
    token = create_access_token(identity=user["id"] if user else None)
    return jsonify(ok=True, user=user, access_token=token), 201


# ---------- LOGIN (returns JWT) ----------
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
                try:
                    cur.close()
                except Exception:
                    pass
    except Exception as exc:
        current_app.logger.exception("Erro no DB durante login: %s", exc)
        return jsonify(ok=False, error="Erro interno"), 500

    if not row or not check_password_hash(row["password_hash"], senha):
        return jsonify(ok=False, error="Credenciais inválidas"), 401

    user = _get_user_by_id(int(row["id"]))
    token = create_access_token(identity=int(row["id"]))
    return jsonify(ok=True, user=user, access_token=token)


# ---------- ME (protected by JWT) ----------
@bp.get("/me")
@jwt_required()
def me():
    try:
        uid = get_jwt_identity()
        user = _get_user_by_id(int(uid))
        if not user:
            return jsonify({"authenticated": False}), 401
        return jsonify({"authenticated": True, "user": user})
    except Exception as exc:
        current_app.logger.exception("Erro no /me: %s", exc)
        return jsonify({"authenticated": False}), 401


# ---------- GOOGLE OAUTH CALLBACK -> return token in fragment ----------
@bp.get("/google/callback")
def google_callback():
    try:
        token_resp = oauth.google.authorize_access_token()
        userinfo = oauth.google.get("userinfo").json()
    except Exception as exc:
        current_app.logger.exception("Google oauth error: %s", exc)
        return jsonify(ok=False, error="OAuth failure"), 400

    email = userinfo.get("email")
    name = userinfo.get("name") or (email.split("@")[0] if email else "Usuário")
    avatar = userinfo.get("picture")
    sub = userinfo.get("sub")

    if not sub:
        return jsonify(ok=False, error="Google não retornou sub"), 400

    # existing logic: find by google_sub or by email, else create
    try:
        with db() as conn:
            # check google_sub
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
            else:
                # try find by email
                user_id = None
                if email:
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
                        user_id = int(r2.get("id"))
                        # bind google_sub
                        cur3 = conn.cursor()
                        cur3.execute(
                            "UPDATE usuarios SET google_sub=%s, avatar_url=%s WHERE id=%s",
                            (sub, avatar, user_id),
                        )
                        try:
                            cur3.close()
                        except Exception:
                            pass

                # create new user if still None
                if not user_id:
                    cur4 = conn.cursor()
                    if is_postgres_db():
                        cur4.execute(
                            "INSERT INTO usuarios (nome,email,google_sub,avatar_url) VALUES (%s,%s,%s,%s) RETURNING id",
                            (name, email, sub, avatar),
                        )
                        r = safe_fetchone(cur4)
                        user_id = int(r[0]) if r else None
                    else:
                        cur4.execute(
                            "INSERT INTO usuarios (nome,email,google_sub,avatar_url) VALUES (%s,%s,%s,%s)",
                            (name, email, sub, avatar),
                        )
                        user_id = int(getattr(cur4, "lastrowid", None)) if getattr(cur4, "lastrowid", None) else None
                    try:
                        cur4.close()
                    except Exception:
                        pass

    except Exception as exc:
        current_app.logger.exception("Erro DB no google_callback: %s", exc)
        return jsonify(ok=False, error="Erro interno"), 500

    user = _get_user_by_id(user_id) if user_id else None
    jwt_token = create_access_token(identity=user_id)
    FRONT = current_app.config.get("FRONT_HOME", FRONT_DEFAULT).rstrip("/")
    next_path = request.args.get("state") or session.pop("after_login_next", None) or "/"
    # redirect with fragment so front can capture
    redirect_url = f"{FRONT}/#token={jwt_token}&next={next_path}"
    current_app.logger.info("Google-login redirect (truncated): %s", redirect_url[:200])
    return redirect(redirect_url)
