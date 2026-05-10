"""Compatibility blueprint for recommendation routes.

The canonical implementation lives in app.api.
"""
from flask import Blueprint
from app.api import recomendacoes

bp = Blueprint("recommendation_controller", __name__)
get_recommendations_for_user = recomendacoes
bp.add_url_rule("/recomendacoes", view_func=recomendacoes, methods=["GET"])
