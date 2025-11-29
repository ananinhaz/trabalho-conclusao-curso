from flask import Blueprint, jsonify, request
from app.extensions.db import db
from app.api import User  # <-- sua classe real de usuário

bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


@bp.get("")
def list_usuarios():
    usuarios = User.query.all()
    return jsonify([u.to_dict() for u in usuarios])


@bp.get("/<int:uid>")
def get_usuario(uid):
    user = User.query.get(uid)
    if not user:
        return jsonify({"erro": "não encontrado"}), 404
    return jsonify(user.to_dict()), 200


@bp.post("")
def create_usuario():
    data = request.get_json() or {}

    user = User(
        nome=data.get("nome"),
        email=data.get("email")
    )
    user.set_password(data.get("senha"))

    db.session.add(user)
    db.session.commit()

    return jsonify(user.to_dict()), 201


@bp.put("/<int:uid>")
def update_usuario(uid):
    user = User.query.get(uid)
    if not user:
        return jsonify({"erro": "não encontrado"}), 404

    data = request.get_json() or {}

    user.nome = data.get("nome", user.nome)
    user.email = data.get("email", user.email)

    if "senha" in data:
        user.set_password(data["senha"])

    db.session.commit()
    return jsonify({"ok": True}), 200


@bp.delete("/<int:uid>")
def delete_usuario(uid):
    user = User.query.get(uid)
    if not user:
        return jsonify({"erro": "não encontrado"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"ok": True}), 200
