"""Legacy user-controller shim.

Current API exposes auth/user functionality through app.controllers.auth_controller
and app.api routes. This module keeps import compatibility for older code.
"""
from flask import Blueprint, jsonify

bp = Blueprint("usuario_controller", __name__)


def list_usuarios():
    return jsonify({"ok": False, "error": "not_implemented"}), 404


def get_usuario_by_id(user_id: int):
    return jsonify({"ok": False, "error": "not_implemented", "id": user_id}), 404


def update_usuario(user_id: int, *_args, **_kwargs):
    return jsonify({"ok": False, "error": "not_implemented", "id": user_id}), 404
