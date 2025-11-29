from flask import Blueprint, request, jsonify, redirect, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash
from app.extensions.db import db
from app.extensions.oauth import oauth, safe_authorize_access_token

import os

from app.controllers.usuario_controller import User  # <-- seu User real

auth_bp = Blueprint("auth", __name__)

# ---------------------
# REGISTRO
# ---------------------
@auth_bp.post("/auth/register")
def register():
    data = request.get_json()

    if not data.get("email") or not data.get("senha") or not data.get("nome"):
        return jsonify(error="Campos obrigatórios faltando"), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify(error="Email já registrado"), 400

    user = User(
        nome=data["nome"],
        email=data["email"]
    )
    user.set_password(data["senha"])

    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=user.id)
    return jsonify(ok=True, user=user.to_dict(), access_token=token)


# ---------------------
# LOGIN NORMAL
# ---------------------
@auth_bp.post("/auth/login")
def login():
    data = request.get_json()

    user = User.query.filter_by(email=data.get("email")).first()
    if not user or not check_password_hash(user.senha, data.get("senha")):
        return jsonify(error="Credenciais inválidas"), 401

    token = create_access_token(identity=user.id)
    return jsonify(ok=True, user=user.to_dict(), access_token=token)


# ---------------------
# GOOGLE LOGIN
# ---------------------
@auth_bp.get("/auth/login/google")
def google_login():
    redirect_uri = os.environ.get("GOOGLE_CALLBACK")
    return oauth.google.authorize_redirect(redirect_uri)


# ---------------------
# GOOGLE CALLBACK
# ---------------------
@auth_bp.get("/auth/google/callback")
def google_callback():
    token = safe_authorize_access_token()

    if not token:
        return jsonify(error="Falha ao autenticar com o Google"), 400

    user_info = oauth.google.get("userinfo").json()
    email = user_info["email"]

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(
            nome=user_info.get("name", "Usuário Google"),
            email=email
        )
        user.set_password("oauth2-no-password")
        db.session.add(user)
        db.session.commit()

    jwt_token = create_access_token(identity=user.id)

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
    user = User.query.get(uid)

    if not user:
        return jsonify(authenticated=False), 404

    return jsonify(authenticated=True, user=user.to_dict())


# ---------------------
# LOGOUT (frontend apaga token)
# ---------------------
@auth_bp.post("/auth/logout")
def logout():
    return jsonify(ok=True)
