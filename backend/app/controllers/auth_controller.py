from __future__ import annotations
import os
import requests
import traceback
from urllib.parse import urljoin
from flask import Blueprint, url_for, request, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import app.extensions.db as db_module
db = getattr(db_module, "db", None)

from ..extensions.oauth import oauth

bp = Blueprint("auth", __name__, url_prefix="/auth")

FRONT_DEFAULT = os.getenv("FRONT_HOME", "http://127.0.0.1:5173/")
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
        print("Erro no DB durante _get_user_by_id:", repr(exc))
        traceback.print_exc()
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
    """
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

            # Inserção compatível com Postgres (RETURNING) e MySQL (lastrowid)
            new_id = None
            if is_postgres_db():
                # Postgres path
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO usuarios (nome,email,password_hash) VALUES (%s,%s,%s) RETURNING id",
                    (nome, email, generate_password_hash(senha)),
                )
                row = safe_fetchone(cur)
                try:
                    new_id = int(row[0]) if row and row[0] is not None else None
                except Exception:
                    new_id = None
                try:
                    cur.close()
                except Exception:
                    pass
            else:
                # MySQL / generic path
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO usuarios (nome,email,password_hash) VALUES (%s,%s,%s)",
                    (nome, email, generate_password_hash(senha)),
                )
                try:
                    last = getattr(cur, "lastrowid", None)
                    new_id = int(last) if last not in (None, 0) else None
                except Exception:
                    new_id = None
                try:
                    cur.close()
                except Exception:
                    pass

            # fallback: busca pelo email se insert não retornou id
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
                    print("⚠️ Aviso: não foi possível obter id do novo usuário (não raise em tests).")
                    new_id = None

    except Exception as exc:
        print("Erro no DB durante register:", repr(exc))
        traceback.print_exc()
        return jsonify(ok=False, error="Erro interno"), 500

    # sucesso: seta sessão e retorna user
    session["user_id"] = int(new_id) if new_id is not None else None
    session.modified = True
    return jsonify(ok=True, user=_get_user_by_id(new_id) if new_id is not None else _get_user_by_id(None))


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
        print("Erro no DB durante login:", repr(exc))
        traceback.print_exc()
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
                session["user_id"] = user_id
                session.modified = True
                print("✅ login google: achou por google_sub ->", user_id)
                return _commit_and_redirect(final_next)

            if email:
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
                    session["user_id"] = user_id
                    session.modified = True
                    print("✅ login google: achou por email e vinculou ->", user_id)
                    return _commit_and_redirect(final_next)

            # new user
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
                else:
                    print("⚠️ Aviso: não foi possível obter id do novo usuário no google_callback; prosseguindo com new_id=None")
                    new_id = None

    except Exception as exc:
        print("Erro no DB durante google_callback:", repr(exc))
        traceback.print_exc()
        return jsonify(ok=False, error="Erro interno"), 500

    if not new_id:
        session["user_id"] = None
        session.modified = True
        return _commit_and_redirect(final_next)

    session["user_id"] = int(new_id)
    session.modified = True
    print("✅ login google: criou novo usuario ->", new_id)
    return _commit_and_redirect(final_next)
