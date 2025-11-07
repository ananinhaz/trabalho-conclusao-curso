# app/api.py
from __future__ import annotations

from flask import Blueprint, request, jsonify, session
from .extensions.db import db
from math import sqrt

bp_api = Blueprint("api", __name__)

# -------------------------------------------------------------------
# Helpers gerais
# -------------------------------------------------------------------
def _require_auth() -> int | None:
    """Retorna user_id da sessão ou None."""
    uid = session.get("user_id")
    return int(uid) if uid else None


def _row_to_animal(row: dict) -> dict:
    """Normaliza saída de animal para o front."""
    return {
        "id": row.get("id"),
        "nome": row.get("nome"),
        "especie": row.get("especie"),
        "raca": row.get("raca"),
        "idade": row.get("idade"),
        "porte": row.get("porte"),
        "descricao": row.get("descricao"),
        "cidade": row.get("cidade"),
        "photo_url": row.get("photo_url"),
        "donor_name": row.get("donor_name"),
        "donor_whatsapp": row.get("donor_whatsapp"),
        "doador_id": row.get("doador_id"),
        "created_at": row.get("created_at"),
    }


def _json_error(msg: str, code: int = 400):
    return jsonify({"ok": False, "error": msg}), code


# -------------------------------------------------------------------
# Helpers específicos de recomendação (conteúdo + KNN simples com PONDERACÃO)
# -------------------------------------------------------------------

# PESOS: Os pesos são aplicados na ordem dos vetores (10 posições).
# Pesos mais altos são dados a atributos críticos (Moradia e Tempo).
# Vetor de features: [apto, quintal, chacara, tem_criancas, tempo_norm, estilo_calmo, estilo_mod, estilo_ativo, estilo_esport, estilo_pouco_casa]
WEIGHTS = [
    3.0, 3.0, 1.0, 2.0, 2.5,
    1.5, 1.5, 1.5, 1.0, 2.0
]


def _build_user_vector(perfil: dict | None) -> list[float]:
    """
    Converte o perfil do adotante em um vetor numérico (10 elementos).
    Aqui fazemos one-hot simples + alguns números diretos.
    """
    if not perfil:
        return []

    tipo_moradia = (perfil.get("tipo_moradia") or "").lower()
    tem_criancas = int(perfil.get("tem_criancas") or 0)
    tempo = int(perfil.get("tempo_disponivel_horas_semana") or 0)
    estilo = (perfil.get("estilo_vida") or "").lower()

    # one-hot de moradia (3)
    moradia_apto = 1.0 if "aparta" in tipo_moradia else 0.0
    moradia_quintal = 1.0 if "quintal" in tipo_moradia else 0.0
    moradia_chacara = 1.0 if "chácara" in tipo_moradia or "sitio" in tipo_moradia else 0.0

    # one-hot de estilo (5)
    estilo_calmo = 1.0 if "calmo" in estilo else 0.0
    estilo_moderado = 1.0 if "moder" in estilo else 0.0
    estilo_ativo = 1.0 if "ativo" in estilo else 0.0
    estilo_esportivo = 1.0 if "esport" in estilo else 0.0
    estilo_pouco_casa = 1.0 if "pouco" in estilo or "fico pouco" in estilo else 0.0

    # normalização simples do tempo (1)
    tempo_norm = min(tempo, 40) / 40.0  # 0 a 1

    # Vetor final tem 10 elementos (deve corresponder a WEIGHTS)
    return [
        moradia_apto,
        moradia_quintal,
        moradia_chacara,
        float(tem_criancas),
        tempo_norm,
        estilo_calmo,
        estilo_moderado,
        estilo_ativo,
        estilo_esportivo,
        estilo_pouco_casa,
    ]


def _build_animal_vector(row: dict) -> list[float]:
    """
    Converte o animal em vetor numérico (10 elementos) para que a distância
    possa ser calculada contra o vetor do usuário.
    """
    especie = (row.get("especie") or "").lower()
    porte = (row.get("porte") or "").lower()

    # aproximações
    is_gato = 1.0 if "gato" in especie else 0.0
    is_cachorro = 1.0 if "cach" in especie else 0.0

    porte_pequeno = 1.0 if "pequeno" in porte else 0.0
    porte_medio = 1.0 if "medio" in porte or "médio" in porte else 0.0
    porte_grande = 1.0 if "grande" in porte else 0.0

    # mapeamento para o mesmo espaço do usuário: (10 elementos)
    # [apto, quintal, chacara, tem_criancas, tempo_norm, estilo_calmo,
    #  estilo_mod, estilo_ativo, estilo_esport, estilo_pouco]
    return [
        # se é gato, favorece apto; se é cachorro médio/grande, favorece quintal
        is_gato,
        1.0 if is_cachorro and (porte_medio or porte_grande) else 0.0,
        0.0,  # chácara não modelamos a partir do animal
        0.0,  # animal não "tem crianças"
        1.0 if is_gato else 0.5,  # gatos tendem a exigir menos tempo
        1.0 if is_gato else 0.0,  # estilo calmo
        0.5 if is_cachorro and porte_pequeno else 0.2,  # moderado
        1.0 if is_cachorro and (porte_medio or porte_grande) else 0.3,  # ativo
        0.6 if is_cachorro else 0.1,  # esportivo
        0.0,  # pouco em casa não dá pra inferir do pet
    ]

def _euclidean(a: list[float], b: list[float]) -> float:
    """
    Calcula a Distância Euclidiana Ponderada.
    Isso aumenta a penalidade para incompatibilidades em atributos críticos.
    """
    # Garante que os vetores e pesos tenham o mesmo tamanho
    if len(a) != len(b) or len(a) != len(WEIGHTS):
        # Fallback para o cálculo não ponderado se houver erro de tamanho
        return sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
        
    # Cálculo da Distância Euclidiana Ponderada: Raiz quadrada da soma de: Peso * (diferença)²
    weighted_sq_diff = [(w * (x - y) ** 2) for x, y, w in zip(a, b, WEIGHTS)]
    
    return sqrt(sum(weighted_sq_diff))


# -------------------------------------------------------------------
# Perfil do Adotante
# -------------------------------------------------------------------
@bp_api.get("/perfil_adotante")
def get_perfil_adotante():
    uid = _require_auth()
    if not uid:
        return _json_error("unauthenticated", 401)

    with db() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                """
                SELECT usuario_id, tipo_moradia, tem_criancas,
                       tempo_disponivel_horas_semana, estilo_vida, atualizado_em
                FROM perfil_adotante
                WHERE usuario_id = %s
                """,
                (uid,),
            )
            row = cur.fetchone()

    return jsonify({"ok": True, "perfil": row})


@bp_api.post("/perfil_adotante")
def upsert_perfil_adotante():
    uid = _require_auth()
    if not uid:
        return _json_error("unauthenticated", 401)

    data = request.get_json(silent=True) or {}
    tipo_moradia = (data.get("tipo_moradia") or "").strip()
    tem_criancas = int(data.get("tem_criancas") or 0)
    tempo = int(data.get("tempo_disponivel_horas_semana") or 0)
    estilo_vida = (data.get("estilo_vida") or "").strip()

    if len(estilo_vida) > 32:
        return _json_error("estilo_vida muito longo (máx 32)")

    if not tipo_moradia or not estilo_vida:
        return _json_error("Dados obrigatórios ausentes")

    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO perfil_adotante
                    (usuario_id, tipo_moradia, tem_criancas,
                     tempo_disponivel_horas_semana, estilo_vida)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    tipo_moradia = VALUES(tipo_moradia),
                    tem_criancas = VALUES(tem_criancas),
                    tempo_disponivel_horas_semana = VALUES(tempo_disponivel_horas_semana),
                    estilo_vida = VALUES(estilo_vida)
                """,
                (uid, tipo_moradia, tem_criancas, tempo, estilo_vida),
            )

    return jsonify({"ok": True})


# -------------------------------------------------------------------
# Animais – listagem + filtros
# -------------------------------------------------------------------
@bp_api.get("/animais")
def list_animais():
    especie = request.args.get("especie") or ""
    idade = (request.args.get("idade") or "").lower()
    porte = (request.args.get("porte") or "").lower()
    cidade_qs = (request.args.get("cidade") or "").strip().lower()

    where, params = [], []

    if especie:
        where.append("a.especie = %s")
        params.append(especie)
    if idade in ("filhote", "adulto", "idoso"):
        where.append("LOWER(a.idade) LIKE %s")
        params.append(f"%{idade}%")
    if porte in ("pequeno", "medio", "médio", "grande"):
        where.append("LOWER(a.porte) LIKE %s")
        params.append(f"%{porte}%")
    if cidade_qs:
        where.append("LOWER(a.cidade) LIKE %s")
        params.append(f"%{cidade_qs}%")

    sql = """
        SELECT a.id, a.nome, a.especie, a.raca, a.idade, a.porte,
               a.descricao, a.cidade, a.photo_url, a.donor_name, a.donor_whatsapp,
               a.doador_id, a.criado_em AS created_at
        FROM animais a
    """
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY a.criado_em DESC LIMIT 200"

    with db() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall() or []

    return jsonify([_row_to_animal(r) for r in rows])


# -------------------------------------------------------------------
# Animais – criação
# -------------------------------------------------------------------
@bp_api.post("/animais")
def create_animal():
    uid = _require_auth()
    if not uid:
        return _json_error("unauthenticated", 401)

    data = request.get_json(silent=True) or {}
    nome = (data.get("nome") or "").strip()
    especie = (data.get("especie") or "").strip()
    raca = (data.get("raca") or None)
    idade = (data.get("idade") or "").strip()
    porte = (data.get("porte") or None)
    descricao = (data.get("descricao") or "").strip()
    cidade = (data.get("cidade") or "").strip()
    photo_url = (data.get("photo_url") or "").strip()
    donor_name = (data.get("donor_name") or "").strip()
    donor_whatsapp = (data.get("donor_whatsapp") or "").strip()

    if not (nome and especie and descricao and cidade):
        return _json_error("Dados obrigatórios ausentes")

    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO animais
                    (doador_id, nome, especie, raca, idade, porte,
                     descricao, cidade, photo_url, donor_name, donor_whatsapp)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    uid,
                    nome,
                    especie,
                    raca,
                    idade,
                    porte,
                    descricao,
                    cidade,
                    photo_url,
                    donor_name,
                    donor_whatsapp,
                ),
            )
            animal_id = cur.lastrowid
    return jsonify({"ok": True, "id": animal_id})


# -------------------------------------------------------------------
# Animais – detalhe / update / delete / meus
# -------------------------------------------------------------------
@bp_api.get("/animais/<int:aid>")
def get_animal(aid: int):
    with db() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                """
                SELECT id, nome, especie, raca, idade, porte, descricao,
                       cidade, photo_url, donor_name, donor_whatsapp,
                       doador_id, criado_em AS created_at
                FROM animais
                WHERE id=%s
                """,
                (aid,),
            )
            row = cur.fetchone()
    if not row:
        return _json_error("not found", 404)
    return jsonify(_row_to_animal(row))


@bp_api.put("/animais/<int:aid>")
def update_animal(aid: int):
    uid = _require_auth()
    if not uid:
        return _json_error("unauthenticated", 401)

    data = request.get_json(silent=True) or {}
    nome = (data.get("nome") or "").strip()
    especie = (data.get("especie") or "").strip()
    raca = (data.get("raca") or None)
    idade = (data.get("idade") or "").strip()
    porte = (data.get("porte") or None)
    descricao = (data.get("descricao") or "").strip()
    cidade = (data.get("cidade") or "").strip()
    photo_url = (data.get("photo_url") or "").strip()

    if not (nome and especie and descricao and cidade):
        return _json_error("Dados obrigatórios ausentes")

    with db() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT doador_id FROM animais WHERE id=%s", (aid,))
            owner = cur.fetchone()
            if not owner:
                return _json_error("not found", 404)
            if int(owner["doador_id"] or 0) != int(uid):
                return _json_error("forbidden", 403)

            cur.execute(
                """
                UPDATE animais
                    SET nome=%s, especie=%s, raca=%s, idade=%s, porte=%s,
                        descricao=%s, cidade=%s, photo_url=%s
                    WHERE id=%s
                """,
                (
                    nome,
                    especie,
                    raca,
                    idade,
                    porte,
                    descricao,
                    cidade,
                    photo_url,
                    aid,
                ),
            )
    return jsonify({"ok": True})


@bp_api.delete("/animais/<int:aid>")
def delete_animal(aid: int):
    uid = _require_auth()
    if not uid:
        return _json_error("unauthenticated", 401)

    with db() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT doador_id FROM animais WHERE id=%s", (aid,))
            owner = cur.fetchone()
            if not owner:
                return _json_error("not found", 404)
            if int(owner["doador_id"] or 0) != int(uid):
                return _json_error("forbidden", 403)
            cur.execute("DELETE FROM animais WHERE id=%s", (aid,))
    return jsonify({"ok": True})


@bp_api.get("/animais/mine")
def animais_mine():
    uid = _require_auth()
    if not uid:
        return _json_error("unauthenticated", 401)

    with db() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                """
                SELECT id, nome, especie, raca, idade, porte, descricao,
                       cidade, photo_url, donor_name, donor_whatsapp,
                       doador_id, criado_em AS created_at
                FROM animais
                WHERE doador_id = %s
                ORDER BY criado_em DESC
                """,
                (uid,),
            )
            rows = cur.fetchall() or []
    return jsonify([_row_to_animal(r) for r in rows])


# -------------------------------------------------------------------
# Recomendações (conteúdo + KNN simples + fallback)
# -------------------------------------------------------------------
@bp_api.get("/recomendacoes")
def recomendacoes():
    """
    Com login: recomenda com base no perfil (content-based + KNN simples Ponderado).
    Sem login ou sem vetor: devolve últimos anúncios.
    Retorno: {"items":[...], "ids":[...]}
    """
    n = int(request.args.get("n") or 5)
    
    # 1. Tenta obter o ID do usuário da sessão (autenticação real)
    uid = _require_auth()
    
    # 2. Se não estiver logado, verifica 'usuario_id' na query string (para TESTE)
    if not uid:
        test_uid_str = request.args.get("usuario_id")
        if test_uid_str and test_uid_str.isdigit():
            uid = int(test_uid_str) # Usa o ID para rodar a lógica de recomendação.

    def _rows_to_payload(rows, ids):
        return {"items": [_row_to_animal(r) for r in rows], "ids": ids or []}

    # Se ainda não houver UID (nem na sessão, nem na QS) => Fallback 1 (Últimos anúncios)
    if not uid:
        with db() as conn:
            with conn.cursor(dictionary=True) as cur:
                cur.execute(
                    """
                    SELECT id, nome, especie, raca, idade, porte, descricao,
                           cidade, photo_url, donor_name, donor_whatsapp,
                           criado_em AS created_at
                    FROM animais
                    ORDER BY criado_em DESC
                    LIMIT %s
                    """,
                    (n,),
                )
                rows = cur.fetchall() or []
        return jsonify(_rows_to_payload(rows, []))

    # Busca perfil do usuário (KNN START)
    with db() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                """
                SELECT tipo_moradia, tem_criancas,
                       tempo_disponivel_horas_semana, estilo_vida
                FROM perfil_adotante
                WHERE usuario_id = %s
                """,
                (uid,),
            )
            perfil = cur.fetchone()

    user_vec = _build_user_vector(perfil)
    if not user_vec:
        # sem perfil => últimos (Fallback 2, igual ao Fallback 1)
        with db() as conn:
            with conn.cursor(dictionary=True) as cur:
                cur.execute(
                    """
                    SELECT id, nome, especie, raca, idade, porte, descricao,
                           cidade, photo_url, donor_name, donor_whatsapp,
                           criado_em AS created_at
                    FROM animais
                    ORDER BY criado_em DESC
                    LIMIT %s
                    """,
                    (n,),
                )
                rows = cur.fetchall() or []
        return jsonify(_rows_to_payload(rows, []))

    # carrega todos os animais para calcular distância
    with db() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                """
                SELECT id, nome, especie, raca, idade, porte, descricao,
                       cidade, photo_url, donor_name, donor_whatsapp,
                       criado_em AS created_at
                FROM animais
                ORDER BY criado_em DESC
                LIMIT 200
                """
            )
            animais = cur.fetchall() or []

    # calcula distância user-animal e ordena (KNN Ponderado)
    scored: list[tuple[float, dict]] = []
    for r in animais:
        animal_vec = _build_animal_vector(r)
        # a menor distância (dist) = maior similaridade (melhor recomendação)
        dist = _euclidean(user_vec, animal_vec)
        scored.append((dist, r))

    scored.sort(key=lambda x: x[0])
    top_rows = [r for _, r in scored[:n]]
    ids = [r["id"] for r in top_rows]

    return jsonify(_rows_to_payload(top_rows, ids))


# -------------------------------------------------------------------
# Registrar no app
# -------------------------------------------------------------------
def register_blueprints(app):
    app.register_blueprint(bp_api)