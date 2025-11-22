from __future__ import annotations
from flask import Blueprint, request, jsonify, session
from .extensions.db import db
import numpy as np
from sklearn.metrics.pairwise import pairwise_distances 
from datetime import datetime, timedelta

bp_api = Blueprint("api", __name__)

# pesos da IA
VEC_WEIGHTS = np.array([
    1.0,  # [0] Porte/Moradia (V0)
    1.0,  # [1] Crianças/Temperamento (V1)
    5.0,  # [2] Tempo/Necessidade de Tempo (V2) - ponderado alto
    1.0   # [3] Estilo de Vida/Atividade (V3)
]) 

def _build_user_vector(perfil: dict) -> list[float]:
    """Cria um vetor numérico de 4 dimensões a partir do perfil do adotante."""
    tm = (perfil.get("tipo_moradia") or "").lower()
    tem_criancas = int(perfil.get("tem_criancas") or 0)
    tempo = int(perfil.get("tempo_disponivel_horas_semana") or 0)
    estilo = (perfil.get("estilo_vida") or "").lower()

    if "aparta" in tm:
        tm_vec = 0.0
    elif "quintal" in tm or "casa" in tm:
        tm_vec = 1.0
    else:
        tm_vec = 0.5
    
    tempo_norm = min(tempo, 20) / 20.0 

    if "ativo" in estilo or "esport" in estilo:
        estilo_vec = 1.0
    elif "tranq" in estilo or "calmo" in estilo:
        estilo_vec = 0.0
    else:
        estilo_vec = 0.5

    return [tm_vec, float(tem_criancas), tempo_norm, estilo_vec]


def _build_animal_vector(a: dict) -> list[float]:
    """Cria um vetor numérico de 4 dimensões a partir dos atributos do animal."""
    especie = str(a.get("especie") or "").lower()
    porte = str(a.get("porte") or "").lower()
    
    age_value = str(a.get("idade") or "0")
    
    determined_idade = "desconhecido"
    try:
        age_num = float(age_value.split()[0].replace(',', '.')) 
        
        if age_num <= 1:
            determined_idade = "filhote"
        elif age_num <= 7:
            determined_idade = "adulto"
        else:
            determined_idade = "idoso"
            
    except (ValueError, IndexError):
        determined_idade = age_value.lower() 

    idade = determined_idade

    if especie == "gato" or porte == "pequeno":
        v0 = 0.0
    elif porte == "medio":
        v0 = 0.5
    else: 
        v0 = 1.0

    if idade == "idoso":
        v1 = 0.0
    elif idade == "adulto":
        v1 = 0.5
    else:
        v1 = 1.0 

    if especie == "gato":
        v2 = 0.0
    elif idade == "filhote" or especie == "cachorro":
        v2 = 1.0
    else: 
        v2 = 0.5

    if especie == "cachorro" or idade == "filhote":
        v3 = 1.0
    else: 
        v3 = 0.0
        
    return [v0, v1, v2, v3]

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
        "energia": row.get("energia"),
        "bom_com_criancas": row.get("bom_com_criancas"),
        "adotado_em": row.get("adotado_em"),
    }


def _json_error(msg: str, code: int = 400):
    return jsonify({"ok": False, "error": msg}), code


def _rows_to_payload(rows, ids):
    return {"items": [_row_to_animal(r) for r in rows], "ids": ids or []}

# Perfil do Adotante
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

# Animais CRUD e Listagem
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
    if porte in ("pequeno", "medio", "grande"):
        where.append("LOWER(a.porte) LIKE %s")
        params.append(f"%{porte}%")
    if cidade_qs:
        where.append("LOWER(a.cidade) LIKE %s")
        params.append(f"%{cidade_qs}%")

    sql = """
        SELECT a.id, a.nome, a.especie, a.raca, a.idade, a.porte,
               a.descricao, a.cidade, a.photo_url, a.donor_name, a.donor_whatsapp,
               a.doador_id, a.criado_em AS created_at,
               a.energia, a.bom_com_criancas,
               a.adotado_em
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
    energia = (data.get("energia") or None)
    bom_com_criancas = (data.get("bom_com_criancas") or 0)

    if not (nome and especie and descricao and cidade):
        return _json_error("Dados obrigatórios ausentes")

    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO animais
                    (doador_id, nome, especie, raca, idade, porte,
                     descricao, cidade, photo_url, donor_name, donor_whatsapp,
                     energia, bom_com_criancas)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    uid, nome, especie, raca, idade, porte, descricao, 
                    cidade, photo_url, donor_name, donor_whatsapp,
                    energia, bom_com_criancas
                ),
            )
            animal_id = cur.lastrowid
    return jsonify({"ok": True, "id": animal_id})


@bp_api.get("/animais/<int:aid>")
def get_animal(aid: int):
    with db() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                """
                SELECT id, nome, especie, raca, idade, porte, descricao,
                       cidade, photo_url, donor_name, donor_whatsapp,
                       doador_id, criado_em AS created_at,
                       energia, bom_com_criancas, adotado_em
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
    
    adotado_em = data.get("adotado_em")
    
    nome = (data.get("nome") or "").strip()
    especie = (data.get("especie") or "").strip()
    raca = (data.get("raca") or None)
    idade = (data.get("idade") or "").strip()
    porte = (data.get("porte") or None)
    descricao = (data.get("descricao") or "").strip()
    cidade = (data.get("cidade") or "").strip()
    photo_url = (data.get("photo_url") or "").strip()
    energia = (data.get("energia") or None)
    bom_com_criancas = (data.get("bom_com_criancas") or 0)

    # Lógica de segurança para não apagar dados se o front mandar vazio
    with db() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT * FROM animais WHERE id=%s", (aid,))
            owner = cur.fetchone()
            if not owner:
                return _json_error("not found", 404)
            if int(owner["doador_id"] or 0) != int(uid):
                return _json_error("forbidden", 403)
            
            # Se campos vierem vazios, mantem os antigos
            if not nome: nome = owner['nome']
            if not especie: especie = owner['especie']
            if not descricao: descricao = owner['descricao']
            if not cidade: cidade = owner['cidade']
            if not photo_url: photo_url = owner['photo_url']
            if 'adotado_em' not in data: adotado_em = owner['adotado_em'] # Mantém status anterior se não vier

            cur.execute(
                """
                UPDATE animais
                   SET nome=%s, especie=%s, raca=%s, idade=%s, porte=%s,
                       descricao=%s, cidade=%s, photo_url=%s,
                       energia=%s, bom_com_criancas=%s, adotado_em=%s
                 WHERE id=%s
                """,
                (
                    nome, especie, raca, idade, porte,
                    descricao, cidade, photo_url,
                    energia, bom_com_criancas, adotado_em,
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
                       doador_id, criado_em AS created_at,
                       energia, bom_com_criancas, adotado_em
                  FROM animais
                 WHERE doador_id = %s
                 ORDER BY criado_em DESC
                """,
                (uid,),
            )
            rows = cur.fetchall() or []
    return jsonify([_row_to_animal(r) for r in rows])

# rota de recomendação
@bp_api.get("/recomendacoes")
def recomendacoes():
    n = int(request.args.get("n") or 6)
    uid = _require_auth()

    # Lógica de fallback
    if not uid:
        with db() as conn:
            with conn.cursor(dictionary=True) as cur:
                cur.execute(
                    """
                    SELECT id, nome, especie, raca, idade, porte, descricao,
                           cidade, photo_url, donor_name, donor_whatsapp,
                           criado_em AS created_at,
                           energia, bom_com_criancas, adotado_em
                      FROM animais
                     ORDER BY criado_em DESC
                     LIMIT %s
                    """,
                    (n,),
                )
                rows = cur.fetchall() or []
        return jsonify(_rows_to_payload(rows, []))

    # Busca perfil
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

    if not perfil:
        # Lógica de fallback para sem perfil
        with db() as conn:
            with conn.cursor(dictionary=True) as cur:
                cur.execute(
                    """
                    SELECT id, nome, especie, raca, idade, porte, descricao,
                           cidade, photo_url, donor_name, donor_whatsapp,
                           criado_em AS created_at,
                           energia, bom_com_criancas, adotado_em
                      FROM animais
                     ORDER BY criado_em DESC
                     LIMIT %s
                    """,
                    (n,),
                )
                rows = cur.fetchall() or []
        return jsonify(_rows_to_payload(rows, []))

    # Tem perfil -> pega todos os animais
    with db() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                """
                SELECT id, nome, especie, raca, idade, porte, descricao,
                       cidade, photo_url, donor_name, donor_whatsapp,
                       criado_em AS created_at,
                       energia, bom_com_criancas, adotado_em
                  FROM animais
                """
            )
            animals = cur.fetchall() or []

    # regras duras (filtros)
    tm = (perfil.get("tipo_moradia") or "").lower()
    tempo = int(perfil.get("tempo_disponivel_horas_semana") or 0)

    def _hard_ok(a):       
        especie = str(a.get("especie") or "").lower()
        porte = str(a.get("porte") or "").lower()

        if "aparta" in tm and tempo <= 6:
            if "gato" in especie:
                return True
            if "cachorro" in especie and porte in ("pequeno", "pequena", "mini"):
                return True
            return False
        if tempo <= 4 and "cachorro" in especie and porte in ("medio", "grande"):
            return False
        return True

    filtered = [a for a in animals if _hard_ok(a)]
    if not filtered:
        filtered = animals

    # vetores e ranking KNN Ponderado com Scikit-learn
    user_vec = _build_user_vector(perfil)
    
    user_vec_np = np.array([user_vec])
    animal_vectors = []
    animal_map = []
    
    for r in filtered:
        animal_vec = _build_animal_vector(r) 
        if len(animal_vec) == len(VEC_WEIGHTS):
            animal_vectors.append(animal_vec)
            animal_map.append(r)
        
    X_animals = np.array(animal_vectors)
    
    if X_animals.size == 0:
         return jsonify(_rows_to_payload([], []))

    distances = pairwise_distances(
        user_vec_np, 
        X_animals, 
        metric='minkowski',
        p=2, 
        w=VEC_WEIGHTS
    )[0] 

    scored: list[tuple[float, dict]] = []
    for dist, animal_data in zip(distances, animal_map):
        scored.append((float(dist), animal_data))

    scored.sort(key=lambda x: x[0])
    
    top = [a for _, a in scored[:n]]
    ids = [a["id"] for a in top]
    return jsonify(_rows_to_payload(top, ids))

# rotas adoções e metricas
@bp_api.patch("/animais/<int:aid>/adopt")
def adopt_animal(aid: int):
    """
    Marca (action=mark) ou desmarca (action=undo) o campo adotado_em do animal.
    Requer autenticação e que o usuário seja o dono (doador).
    """
    uid = _require_auth()
    if not uid:
        return _json_error("unauthenticated", 401)

    data = request.get_json(silent=True) or {}
    action = (data.get("action") or "mark").lower()
    if action not in ("mark", "undo"):
        return _json_error("invalid_action")

    with db() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT doador_id FROM animais WHERE id=%s", (aid,))
            owner = cur.fetchone()
            if not owner:
                return _json_error("not found", 404)
            if int(owner.get("doador_id") or 0) != int(uid):
                return _json_error("forbidden", 403)

            if action == "mark":
                # marca a data atual UTC
                cur.execute("UPDATE animais SET adotado_em = NOW() WHERE id=%s", (aid,))
            else:
                # desfaz o adotado
                cur.execute("UPDATE animais SET adotado_em = NULL WHERE id=%s", (aid,))

        # pega o registro atualizado para devolver
        with conn.cursor(dictionary=True) as cur2:
            cur2.execute(
                """
                SELECT id, nome, especie, raca, idade, porte, descricao,
                       cidade, photo_url, donor_name, donor_whatsapp,
                       doador_id, criado_em AS created_at, energia, bom_com_criancas,
                       adotado_em
                  FROM animais
                 WHERE id=%s
                """,
                (aid,),
            )
            row = cur2.fetchone()

    # Converte para o formato de frontend
    animal = _row_to_animal(row)
    # Garante serialização de data se necessário
    if row and row.get("adotado_em"):
        animal["adotado_em"] = row["adotado_em"].isoformat() if hasattr(row["adotado_em"], 'isoformat') else str(row["adotado_em"])
    
    return jsonify({"ok": True, "animal": animal})

@bp_api.get("/animais/metrics/adoptions")
def adoption_metrics():
    """
    Retorna métricas de adoção para o gráfico da Landing Page.
    """
    try:
        days = int(request.args.get("days") or 7)
    except ValueError:
        days = 7
    if days <= 0: days = 7
    days = min(days, 90)

    end = datetime.utcnow().date()
    start = end - timedelta(days=days - 1)

    sql = """
        SELECT DATE(adotado_em) AS day, COUNT(*) AS cnt
          FROM animais
         WHERE adotado_em IS NOT NULL
           AND DATE(adotado_em) BETWEEN %s AND %s
         GROUP BY DATE(adotado_em)
         ORDER BY DATE(adotado_em) ASC
    """
    with db() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute(sql, (start.isoformat(), end.isoformat()))
            rows = cur.fetchall() or []

    counts = { (r["day"].isoformat() if hasattr(r["day"], "isoformat") else str(r["day"])): int(r["cnt"] or 0) for r in rows }

    result = []
    for i in range(days):
        d = (start + timedelta(days=i))
        ds = d.isoformat()
        result.append({"day": ds, "count": counts.get(ds, 0)})

    return jsonify({"ok": True, "days": result})

# Registrar no app 
def register_blueprints(app):
    app.register_blueprint(bp_api)