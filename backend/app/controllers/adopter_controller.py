from __future__ import annotations
from flask import Blueprint, request, jsonify, session
from flask_cors import cross_origin
from ..extensions.db import get_conn

bp = Blueprint("adopter", __name__)

ALLOWED_ORIGINS = [
    "http://127.0.0.1:8080",
    "http://localhost:8080",
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]

@bp.route("/perfil_adotante", methods=["POST", "OPTIONS"])
@cross_origin(
    origins=ALLOWED_ORIGINS,
    supports_credentials=True,
    allow_headers=["Content-Type"],
    methods=["POST", "OPTIONS"],
    max_age=600,
)
def save_adopter_profile():
    if request.method == "OPTIONS":
        return ("", 204)
    uid = session.get("user_id")
    if not uid:
        return jsonify({"error": "unauthenticated"}), 401

    data = request.get_json(silent=True) or {}
    tipo_moradia = (data.get("tipo_moradia") or "").strip()
    tem_criancas = int(data.get("tem_criancas") or 0)
    tempo = int(data.get("tempo_disponivel_horas_semana") or 0)
    estilo = (data.get("estilo_vida") or "").strip()

    if not (tipo_moradia and estilo):
        return jsonify({"error": "Campos obrigatórios ausentes"}), 400

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO perfil_adotante
          (user_id, tipo_moradia, tem_criancas, tempo_disponivel_horas_semana, estilo_vida)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
          tipo_moradia = VALUES(tipo_moradia),
          tem_criancas = VALUES(tem_criancas),
          tempo_disponivel_horas_semana = VALUES(tempo_disponivel_horas_semana),
          estilo_vida = VALUES(estilo_vida)
        """,
        (uid, tipo_moradia, tem_criancas, tempo, estilo),
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"ok": True})
