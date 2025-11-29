from flask import Blueprint, jsonify, request
from app.extensions.db import db

bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


@bp.get("")
def list_usuarios():
    rows = db.execute("SELECT id, nome, email FROM usuarios").fetchall()
    return jsonify([dict(r) for r in rows])


@bp.get("/<int:uid>")
def get_usuario(uid):
    row = db.execute(
        "SELECT id, nome, email FROM usuarios WHERE id = %s",
        (uid,)
    ).fetchone()

    if not row:
        return jsonify({"erro": "não encontrado"}), 404

    return jsonify(dict(row)), 200


@bp.post("")
def create_usuario():
    data = request.get_json() or {}

    db.execute(
        "INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, crypt(%s, gen_salt('bf')))",
        (data.get("nome"), data.get("email"), data.get("senha"))
    )
    db.commit()

    return jsonify({"ok": True}), 201


@bp.put("/<int:uid>")
def update_usuario(uid):
    data = request.get_json() or {}

    db.execute(
        "UPDATE usuarios SET nome = %s, email = %s WHERE id = %s",
        (data.get("nome"), data.get("email"), uid)
    )
    db.commit()

    return jsonify({"ok": True}), 200


@bp.delete("/<int:uid>")
def delete_usuario(uid):
    db.execute("DELETE FROM usuarios WHERE id = %s", (uid,))
    db.commit()

    return jsonify({"ok": True}), 200
