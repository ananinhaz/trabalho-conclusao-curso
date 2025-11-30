# encoding: utf-8
from flask import Blueprint, request, jsonify
from ..services import animal_service as svc

# nome do blueprint: animais_bp (IMPORTANTE para app.__init__.py)
animais_bp = Blueprint("animais", __name__)

# lista animais (GET /animais)
@animais_bp.get("/animais")
def list_animais():
    try:
        rs = svc.listar(limit=200)
        return jsonify(rs)
    except Exception as e:
        return jsonify({"ok": False, "error": "internal", "message": str(e)}), 500

# get /animais/<id>
@animais_bp.get("/animais/<int:aid>")
def get_animal(aid: int):
    try:
        row = svc.obter(aid)
        if not row:
            return jsonify({"erro": "not found"}), 404
        return jsonify(row)
    except Exception as e:
        return jsonify({"ok": False, "error": "internal", "message": str(e)}), 500

# criar animal (POST /animais) -- espera JSON
@animais_bp.post("/animais")
def create_animal():
    try:
        data = request.get_json(silent=True) or {}
        # o serviço cria e retorna id (ou dict)
        # aqui não fazemos autenticação - supomos que o controller original lida com ela
        result = svc.criar(data, doador_id=data.get("doador_id"))
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"ok": False, "error": "internal", "message": str(e)}), 500

# atualizar animal (PUT /animais/<id>)
@animais_bp.put("/animais/<int:aid>")
def update_animal(aid: int):
    try:
        data = request.get_json(silent=True) or {}
        ok = svc.atualizar(aid, data)
        if ok:
            return jsonify({"ok": True})
        return jsonify({"erro": "not found"}), 404
    except Exception as e:
        return jsonify({"ok": False, "error": "internal", "message": str(e)}), 500

# deletar animal (DELETE /animais/<id>)
@animais_bp.delete("/animais/<int:aid>")
def delete_animal(aid: int):
    try:
        ok = svc.remover(aid)
        if ok:
            return jsonify({"ok": True})
        return jsonify({"erro": "not found"}), 404
    except Exception as e:
        return jsonify({"ok": False, "error": "internal", "message": str(e)}), 500
