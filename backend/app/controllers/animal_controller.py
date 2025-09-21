from flask import Blueprint, jsonify, request
from ..services import animal_service as svc

bp = Blueprint("animais", __name__, url_prefix="/animais")

@bp.get("")
def list_animais():
    return jsonify(svc.listar())

@bp.get("/<int:aid>")
def get_animal(aid):
    row = svc.obter(aid)
    return (jsonify(row), 200) if row else (jsonify({"erro": "não encontrado"}), 404)

@bp.post("")
def create_animal():
    data = request.get_json() or {}
    novo = svc.criar(data)
    return jsonify(novo), 201

@bp.put("/<int:aid>")
def update_animal(aid):
    data = request.get_json() or {}
    ok = svc.atualizar(aid, data)
    return (jsonify({"ok": True}), 200) if ok else (jsonify({"erro": "não encontrado"}), 404)

@bp.delete("/<int:aid>")
def delete_animal(aid):
    ok = svc.remover(aid)
    return (jsonify({"ok": True}), 200) if ok else (jsonify({"erro": "não encontrado"}), 404)
