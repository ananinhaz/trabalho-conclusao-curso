from __future__ import annotations

from typing import Any, Dict, List, Optional
from ..extensions.db import get_conn  # Certifique-se que essa função existe (retorna conexão mysql.connector)
from ..recommendation.engine import knn_rank


def _carregar_prefs(usuario_id: Optional[int], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Carrega preferências do adotante:
    - Prioriza o registro salvo em perfil_adotante (se usuario_id enviado)
    - Permite sobrescrever/fornecer via querystring para teste rápido
    Campos: tipo_moradia, tem_criancas, tempo_disponivel_horas_semana, estilo_vida
    """
    prefs: Dict[str, Any] = {
        "tipo_moradia": params.get("tipo_moradia"),
        "tem_criancas": int(params.get("tem_criancas")) if params.get("tem_criancas") is not None else None,
        "tempo_disponivel_horas_semana": int(params.get("tempo_disponivel_horas_semana"))
        if params.get("tempo_disponivel_horas_semana")
        else None,
        "estilo_vida": params.get("estilo_vida"),
        # opcional
        "especie_pref": params.get("especie_pref"),
    }

    if usuario_id:
        try:
            conn = get_conn()
            cur = conn.cursor(dictionary=True)
            cur.execute(
                """
                SELECT tipo_moradia, tem_criancas, tempo_disponivel_horas_semana, estilo_vida
                FROM perfil_adotante
                WHERE usuario_id = %s
                """,
                (usuario_id,),
            )
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row:
                for k, v in row.items():
                    if v is not None:
                        prefs[k] = v
        except Exception:
            # mantém params como fallback
            pass

    # Defaults sensatos
    if prefs["tipo_moradia"] is None:
        prefs["tipo_moradia"] = "Apartamento"
    if prefs["tem_criancas"] is None:
        prefs["tem_criancas"] = 0
    if prefs["tempo_disponivel_horas_semana"] is None:
        prefs["tempo_disponivel_horas_semana"] = 7
    if prefs["estilo_vida"] is None:
        prefs["estilo_vida"] = "Moderado"

    return prefs


def _carregar_animais() -> List[dict]:
    """
    Traz os animais com as colunas necessárias para o KNN.
    IMPORTANTE: inclui porte, energia, bom_com_criancas e filtra disponivel=1.
    """
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT id, nome, especie, idade, porte, energia, bom_com_criancas, cidade, disponivel
        FROM animais
        WHERE disponivel = 1
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def recomendar(usuario_id: Optional[int], params: Dict[str, Any], top_n: int = 10) -> List[dict]:
    prefs = _carregar_prefs(usuario_id, params)
    animals = _carregar_animais()
    return knn_rank(animals, prefs, top_n=top_n)
