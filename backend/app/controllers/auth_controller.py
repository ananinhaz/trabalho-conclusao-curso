# encoding: utf-8
from flask import Blueprint, request, jsonify, redirect, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash
from ..services import usuario_service as usuario_svc
from ..extensions import oauth as oauth_ext
import os

auth_bp = Blueprint("auth", __name__)

# ---------------------
# REGISTRO
# ---------------------
@auth_bp.post("/auth/register")
def register():
    data = request.get_json() or {}

    if not data.get("email") or not data.get("senha") or not data.get("nome"):
        return jsonify(error="Campos obrigatórios faltando"), 400

    existing = usuario_svc.find_by_email(data["email"])
    if existing:
        return jsonify(error="Email já registrado"), 400

    novo = usuario_svc.criar({
        "nome": data["nome"],
        "email": data["email"],
        "senha": data["senha"]
    })

    token = create_access_token(identity=novo.get("id"))
    return jsonify(ok=True, user=novo, access_token=token), 201


# ---------------------
# LOGIN NORMAL
# ---------------------
@auth_bp.post("/auth/login")
def login():
    data = request.get_json() or {}
    email = data.get("email")
    senha = data.get("senha")

    if not email or not senha:
        return jsonify(error="Credenciais inválidas"), 401

    user = usuario_svc.find_by_email(email)
    if not user:
        return jsonify(error="Credenciais inválidas"), 401

    if not check_password_hash(user.get("senha_hash", ""), senha):
        return jsonify(error="Credenciais inválidas"), 401

    token = create_access_token(identity=user.get("id"))
    return jsonify(ok=True, user=user, access_token=token)


# ---------------------
# GOOGLE LOGIN
# ---------------------
@auth_bp.get("/auth/login/google")
def google_login():
    redirect_uri = os.environ.get("GOOGLE_CALLBACK")
    # oauth client no extension deve estar em app.extensions.oauth.oauth
    return oauth_ext.oauth.google.authorize_redirect(redirect_uri)


# ---------------------
# GOOGLE CALLBACK
# ---------------------
@auth_bp.get("/auth/google/callback")
def google_callback():
    try:
        token = oauth_ext.oauth.google.safe_authorize_access_token()
    except Exception:
        return jsonify(error="Falha ao autenticar com o Google"), 400

    user_info = oauth_ext.oauth.google.get("userinfo").json()
    email = user_info.get("email")

    # Se o usuário não existir, cria
    user = usuario_svc.find_by_email(email)
    if not user:
        user = usuario_svc.criar({
            "nome": user_info.get("name", "Usuário Google"),
            "email": email,
            "senha": "oauth2-no-password"
        })

    jwt_token = create_access_token(identity=user.get("id"))
    FRONT = current_app.config.get("FRONT_HOME")
    next_path = request.args.get("next", "/animais")
    return redirect(f"{FRONT}/?token={jwt_token}&next={next_path}")


# ---------------------
# ME
# ---------------------
@auth_bp.get("/auth/me")
@jwt_required()
def me():
    uid = get_jwt_identity()
    user = usuario_svc.obter(uid)
    if not user:
        return jsonify(authenticated=False), 404
    return jsonify(authenticated=True, user=user)


# ---------------------
# LOGOUT (frontend apaga token)
# ---------------------
@auth_bp.post("/auth/logout")
def logout():
    return jsonify(ok=True)
