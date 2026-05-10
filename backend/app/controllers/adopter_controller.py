"""Compatibility blueprint for adopter profile routes.

The canonical implementation lives in app.api.
"""
from flask import Blueprint
from app.api import get_perfil_adotante, upsert_perfil_adotante

bp = Blueprint("adopter_controller", __name__)
bp.add_url_rule("/perfil_adotante", view_func=get_perfil_adotante, methods=["GET"])
bp.add_url_rule("/perfil_adotante", view_func=upsert_perfil_adotante, methods=["POST", "OPTIONS"])
