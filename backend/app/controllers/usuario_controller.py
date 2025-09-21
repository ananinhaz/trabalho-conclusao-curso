from flask import Blueprint, jsonify, request
from ..services import usuario_service as svc

bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")

@bp.get("")
def list_usuarios():
    return jsonify(svc.listar())

@bp.get("/<int:uid>")
def get_usuario(uid):
    row = svc.obter(uid)
    return (jsonify(row), 200) if row else (jsonify({"erro": "não encontrado"}), 404)

@bp.post("")
def create_usuario():
    data = request.get_json() or {}
    novo = svc.criar(data)
    return jsonify(novo), 201

@bp.put("/<int:uid>")
def update_usuario(uid):
    data = request.get_json() or {}
    ok = svc.atualizar(uid, data)
    return (jsonify({"ok": True}), 200) if ok else (jsonify({"erro": "não encontrado"}), 404)

@bp.delete("/<int:uid>")
def delete_usuario(uid):
    ok = svc.remover(uid)
    return (jsonify({"ok": True}), 200) if ok else (jsonify({"erro": "não encontrado"}), 404)
