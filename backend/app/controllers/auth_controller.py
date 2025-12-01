# backend/app/controllers/auth_controller.py
from __future__ import annotations
import os
from urllib.parse import urljoin

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

# Importa o oauth (deve ser inicializado em create_app via init_oauth)
from app.extensions.oauth import oauth

bp = Blueprint("auth", __name__, url_prefix="")  # registrado em /api/auth pelo create_app

# Defaults (FRONT_HOME / GOOGLE_CALLBACK podem ser configurados via env)
FRONT_DEFAULT = os.getenv("FRONT_HOME", "http://127.0.0.1:5173/")
GOOGLE_CALLBACK_ENV = (os.getenv("GOOGLE_CALLBACK") or os.getenv("GOOGLE_REDIRECT_URI") or "").strip() or None


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


def _make_token_for_user_id(user_id):
    """
    Garantir que o 'identity' passado para create_access_token seja string (sub precisa ser string).
    Retorna o token criado.
    """
    if user_id is None:
        # não deveria acontecer, mas tratar
        current_app.logger.warning("_make_token_for_user_id called with None")
        identity = None
    else:
        # forçar string
        identity = str(user_id)
    token = create_access_token(identity=identity)
    current_app.logger.debug("_make_token_for_user_id: created token for identity=%s", identity)
    return token


# ---------- REGISTER ----------
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

            pw_hash = generate_password_hash(senha)
            new_id = None

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

    user = _get_user_by_id(new_id) if new_id else None
    # criar token garantindo identity como string
    token = _make_token_for_user_id(user["id"] if user else None)
    return jsonify(ok=True, user=user, access_token=token), 201


# ---------- LOGIN ----------
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
    token = _make_token_for_user_id(int(row["id"]))
    return jsonify(ok=True, user=user, access_token=token)


# ---------- ME ----------
@bp.get("/me")
@jwt_required()
def me():
    try:
        uid = get_jwt_identity()
        # get_jwt_identity() retorna a string que foi colocada em sub — converter ao usar no DB
        try:
            uid_int = int(uid) if uid is not None else None
        except Exception:
            current_app.logger.warning("me: jwt identity is not integer-convertible: %r", uid)
            return jsonify({"authenticated": False}), 401

        user = _get_user_by_id(uid_int)
        if not user:
            return jsonify({"authenticated": False}), 401
        return jsonify({"authenticated": True, "user": user})
    except Exception as exc:
        current_app.logger.exception("Erro no /me: %s", exc)
        return jsonify({"authenticated": False}), 401


# ---------- GOOGLE OAUTH: START FLOW ----------
@bp.get("/google")
def google_login():
    """
    Inicia o fluxo OAuth com o Google.
    Verifica pré-condições (provider registrado, envs presentes) antes do redirect.
    """
    try:
        # provider registrado?
        if not getattr(oauth, "google", None):
            current_app.logger.error("google_login: provider 'google' não registrado (init_oauth não rodou ou faltam envs).")
            return jsonify(ok=False, error="OAuth provider not available"), 500

        # envs mínimas
        if not os.getenv("GOOGLE_CLIENT_ID") or not os.getenv("GOOGLE_CLIENT_SECRET"):
            current_app.logger.error("google_login: GOOGLE_CLIENT_ID/SECRET ausentes.")
            return jsonify(ok=False, error="OAuth not configured (missing client id/secret)"), 500

        next_path = request.args.get("next") or request.args.get("state") or "/"
        try:
            session["after_login_next"] = next_path
        except Exception:
            # normalmente por falta de secret_key; já resolvemos isso no create_app
            current_app.logger.debug("google_login: falha ao gravar session (verifique app.secret_key).")

        # callback: usar env se definido, senão gerar dinamicamente
        callback = GOOGLE_CALLBACK_ENV or url_for(".google_callback", _external=True)
        current_app.logger.info("google_login: iniciando redirect; callback=%s next=%s", callback, next_path)

        return oauth.google.authorize_redirect(redirect_uri=callback, state=next_path)
    except Exception as exc:
        current_app.logger.exception("Erro iniciando oauth google: %s", exc)
        return jsonify(ok=False, error="OAuth init failed"), 500


# ---------- GOOGLE OAUTH CALLBACK ----------
# dentro de auth_controller.py: substituir google_callback pelo código abaixo

@bp.get("/google/callback")
def google_callback():
    current_app.logger.info("google_callback: called; request.args keys=%s session keys=%s",
                            list(request.args.keys()), list(session.keys()))
    try:
        # usa safe_authorize_access_token (pode ser o authlib normal ou nosso fallback)
        if getattr(getattr(oauth, "google", None), "safe_authorize_access_token", None):
            token_resp = oauth.google.safe_authorize_access_token()
        else:
            token_resp = oauth.google.authorize_access_token()

        # token_resp pode ser dict (fallback manual) ou object retornado por authlib
        try:
            if isinstance(token_resp, dict):
                current_app.logger.info("google_callback: token_resp keys=%s", list(token_resp.keys()))
            else:
                current_app.logger.info("google_callback: token obtained (authlib object).")
        except Exception:
            current_app.logger.debug("google_callback: não consegui inspecionar token_resp safely.")

        # obter userinfo: primeiro tenta via client.get('userinfo'), se não funcionar
        userinfo = None
        try:
            # authlib client will use metadata userinfo endpoint
            resp = oauth.google.get("userinfo")
            userinfo = resp.json()
        except Exception as e:
            current_app.logger.warning("google_callback: oauth.google.get('userinfo') falhou: %s", e)
            # fallback: use explicit endpoint if available (token_resp may include it as _userinfo_endpoint)
            userinfo_endpoint = None
            try:
                # token_resp pode ser dict com _userinfo_endpoint (nossa fallback)
                if isinstance(token_resp, dict):
                    userinfo_endpoint = token_resp.get("_userinfo_endpoint")
            except Exception:
                userinfo_endpoint = None
            # fallback to known google endpoint
            if not userinfo_endpoint:
                userinfo_endpoint = "https://openidconnect.googleapis.com/v1/userinfo"
            # request userinfo with access token
            access_token = token_resp.get("access_token") if isinstance(token_resp, dict) else token_resp.get("access_token")
            headers = {"Authorization": f"Bearer {access_token}"}
            r = requests.get(userinfo_endpoint, headers=headers, timeout=10)
            r.raise_for_status()
            userinfo = r.json()

        current_app.logger.info("google_callback: got userinfo email=%s", userinfo.get("email"))
    except Exception as exc:
        current_app.logger.exception("Google oauth error (callback): %s", exc)
        return jsonify(ok=False, error="OAuth failure"), 400

    # ... (restante do seu código que cria/atualiza usuário e gera token permanece igual)


    email = userinfo.get("email")
    name = userinfo.get("name") or (email.split("@")[0] if email else "Usuário")
    avatar = userinfo.get("picture")
    sub = userinfo.get("sub")

    if not sub:
        return jsonify(ok=False, error="Google não retornou sub"), 400

    # busca/cria usuário
    user_id = None
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
            else:
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
                        cur3 = conn.cursor()
                        cur3.execute(
                            "UPDATE usuarios SET google_sub=%s, avatar_url=%s WHERE id=%s",
                            (sub, avatar, user_id),
                        )
                        try:
                            cur3.close()
                        except Exception:
                            pass

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
    # garantir que token identity seja string
    jwt_token = _make_token_for_user_id(user_id)

    FRONT = current_app.config.get("FRONT_HOME", FRONT_DEFAULT).rstrip("/")
    # priorizar state (query) -> session -> default
    next_path = request.args.get("state") or session.pop("after_login_next", None) or "/"

    redirect_url = f"{FRONT}/#token={jwt_token}&next={next_path}"
    current_app.logger.info("Google-login redirect (truncated): %s", redirect_url[:200])
    return redirect(redirect_url)
