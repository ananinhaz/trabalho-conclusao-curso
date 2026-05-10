"""Compatibility blueprint for animal routes.

The canonical implementation lives in app.api.
This module keeps backward-compatible symbols for imports/tests.
"""
from flask import Blueprint
from app.api import list_animais, create_animal, get_animal as get_animal_by_id, update_animal, delete_animal

bp = Blueprint("animal_controller", __name__)
bp.add_url_rule("/animais", view_func=list_animais, methods=["GET"])
bp.add_url_rule("/animais", view_func=create_animal, methods=["POST"])
bp.add_url_rule("/animais/<int:aid>", view_func=get_animal_by_id, methods=["GET"])
bp.add_url_rule("/animais/<int:aid>", view_func=update_animal, methods=["PUT", "PATCH"])
bp.add_url_rule("/animais/<int:aid>", view_func=delete_animal, methods=["DELETE"])
