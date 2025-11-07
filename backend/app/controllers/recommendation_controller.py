from flask import Blueprint, request, jsonify
from ..services.recommendation_service import recomendar

bp = Blueprint("recomendacao", __name__, url_prefix="/recomendacoes")

@bp.get("")
def get_recomendacoes():
    usuario_id = request.args.get("usuario_id", type=int)
    top_n = request.args.get("n", default=10, type=int)
    params = {
        "especie_pref": request.args.get("especie_pref"),
        "idade_min": request.args.get("idade_min"),
        "idade_max": request.args.get("idade_max"),
        "porte": request.args.get("porte"),
        "cidade": request.args.get("cidade"),
    }
    recs = recomendar(usuario_id, params, top_n=top_n)
    return jsonify(recs), 200
