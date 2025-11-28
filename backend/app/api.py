from __future__ import annotations
from flask import Blueprint, request, jsonify, session
import numpy as np
from sklearn.metrics.pairwise import pairwise_distances
from datetime import datetime, timedelta

from .extensions import db as db_ext

bp_api = Blueprint("api", __name__)

# IA — PESOS
VEC_WEIGHTS = np.array([
    1.0,
    1.0,
    5.0,
    1.0
])

def is_postgres() -> bool:
    """Detecta se o backend está usando Postgres (compatível com os testes)."""
    try:
        fn = getattr(db_ext, "using_postgres", None)
        if callable(fn):
            return bool(fn())
    except Exception:
        pass
    try:
        return bool(getattr(db_ext, "_using_postgres", False))
    except Exception:
        return False


def _require_auth() -> int | None:
    uid = session.get("user_id")
    return int(uid) if uid else None


def to_bool_like(v):
    """Normaliza valores vindos do front/testes para boolean."""
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    s = str(v).strip().lower()
    if s in ("1", "true", "t", "yes", "y"):
        return True
    return False


def _normalize_to_int_bool(v):
    """Converte valores booleanos/t/f/1/0 para 1/0 ou None se v is None."""
    if v is None:
        return None
    try:
        # Se já é bool
        if isinstance(v, bool):
            return 1 if v else 0
        # números
        if isinstance(v, (int, float)):
            return 1 if int(v) != 0 else 0
        s = str(v).strip().lower()
        if s in ("1", "true", "t", "yes", "y"):
            return 1
        return 0
    except Exception:
        return None


def _row_to_animal(row: dict) -> dict:
    """Normaliza saída de animal para o front."""
    bom = row.get("bom_com_criancas")
    bom_val = _normalize_to_int_bool(bom)

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
        "bom_com_criancas": bom_val,
        "adotado_em": row.get("adotado_em"),
    }


def _json_error(msg: str, code: int = 400):
    return jsonify({"ok": False, "error": msg}), code


def _rows_to_payload(rows, ids):
    return {"items": [_row_to_animal(r) for r in rows], "ids": ids or []}


# IA — VETORES

def _build_user_vector(perfil: dict) -> list[float]:
    tm = (perfil.get("tipo_moradia") or "").lower()
    tem_criancas = to_bool_like(perfil.get("tem_criancas"))
    tempo = int(perfil.get("tempo_disponivel_horas_semana") or 0)
    estilo = (perfil.get("estilo_vida") or "").lower()

    tm_vec = 0.5
    if "aparta" in tm:
        tm_vec = 0.0
    elif "casa" in tm or "quintal" in tm:
        tm_vec = 1.0

    tempo_norm = min(tempo, 20) / 20.0

    if "ativo" in estilo or "esport" in estilo:
        estilo_vec = 1.0
    elif "tranq" in estilo or "calmo" in estilo:
        estilo_vec = 0.0
    else:
        estilo_vec = 0.5

    return [tm_vec, float(tem_criancas), tempo_norm, estilo_vec]


def _build_animal_vector(a: dict) -> list[float]:
    especie = str(a.get("especie") or "").lower()
    porte = str(a.get("porte") or "").lower()
    
    idade_raw = str(a.get("idade") or "0")
    try:
        n = float(idade_raw.split()[0].replace(",", "."))
        if n <= 1:
            idade = "filhote"
        elif n <= 7:
            idade = "adulto"
        else:
            idade = "idoso"
    except Exception:
        idade = idade_raw.lower()

    #  TIPO DE MORADIA
    # Se usuário mora em ap (0.0), prefere Gato ou Pequeno (0.0)
    # Se usuário mora em Casa (1.0), prefere Médio/Grande (0.5 a 1.0)
    if especie == "gato" or porte == "pequeno":
        v0 = 0.0
    elif porte == "medio" or "médio" in porte:
        v0 = 0.5
    else:
        v0 = 1.0

    # CRIANÇAS 
    # Se o animal é bom com crianças -> 1.0
    # Se não é (ou não sabemos) -> 0.0
    bom_com_criancas = to_bool_like(a.get("bom_com_criancas"))
    v1 = 1.0 if bom_com_criancas else 0.0

    # TEMPO DISPONÍVEL 
    # usuario com pouco tempo (0.0) -> Gato (0.0)
    # usuario com muito tempo (1.0) -> Filhote ou Cachorro (1.0)
    if especie == "gato":
        v2 = 0.0
    elif idade == "filhote" or especie == "cachorro":
        v2 = 1.0
    else:
        v2 = 0.5

    #  ESTILO DE VIDA 
    # usuario calmo (0.0) -> evita agitação
    # usuario ativo (1.0) -> quer cachorro ou filhote (1.0)
    if especie == "cachorro" or idade == "filhote":
        v3 = 1.0
    else:
        v3 = 0.0

    return [v0, v1, v2, v3]

# PERFIL DO ADOTANTE

@bp_api.get("/perfil_adotante")
def get_perfil_adotante():
    uid = _require_auth()
    if not uid:
        return _json_error("unauthenticated", 401)

    with db_ext.db() as conn:
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

    # Normaliza tem_criancas para 0/1/null
    if row and "tem_criancas" in row:
        row["tem_criancas"] = _normalize_to_int_bool(row.get("tem_criancas"))

    return jsonify({"ok": True, "perfil": row})


@bp_api.post("/perfil_adotante")
def upsert_perfil_adotante():
    uid = _require_auth()
    if not uid:
        return _json_error("unauthenticated", 401)

    data = request.get_json(silent=True) or {}
    tipo_moradia = (data.get("tipo_moradia") or "").strip()
    tem_criancas = to_bool_like(data.get("tem_criancas"))
    tempo = int(data.get("tempo_disponivel_horas_semana") or 0)
    estilo_vida = (data.get("estilo_vida") or "").strip()

    if not tipo_moradia or not estilo_vida:
        return _json_error("Dados obrigatórios ausentes")

    with db_ext.db() as conn:
        with conn.cursor() as cur:
            if is_postgres():
                cur.execute(
                    """
                    INSERT INTO perfil_adotante
                        (usuario_id, tipo_moradia, tem_criancas,
                         tempo_disponivel_horas_semana, estilo_vida)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (usuario_id) DO UPDATE
                      SET tipo_moradia = EXCLUDED.tipo_moradia,
                          tem_criancas = EXCLUDED.tem_criancas,
                          tempo_disponivel_horas_semana = EXCLUDED.tempo_disponivel_horas_semana,
                          estilo_vida = EXCLUDED.estilo_vida
                    """,
                    (uid, tipo_moradia, tem_criancas, tempo, estilo_vida),
                )
            else:
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


# LISTAGEM DE ANIMAIS

@bp_api.get("/animais")
def list_animais():
    especie = request.args.get("especie") or ""
    idade = (request.args.get("idade") or "").lower()
    porte = (request.args.get("porte") or "").lower()
    cidade_qs = (request.args.get("cidade") or "").strip().lower()

    where = []
    params = []

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

    with db_ext.db() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall() or []

    return jsonify([_row_to_animal(r) for r in rows])

# CRIAÇÃO DE ANIMAL

@bp_api.post("/animais")
def create_animal():
    uid = _require_auth()
    if not uid:
        return _json_error("unauthenticated", 401)

    data = request.get_json(silent=True) or {}

    def _safe_strip(v):
        if v is None:
            return None
        if isinstance(v, str):
            return v.strip()
        return str(v).strip()

    nome = _safe_strip(data.get("nome"))
    especie = _safe_strip(data.get("especie"))
    raca = _safe_strip(data.get("raca"))
    idade_raw = data.get("idade")
    idade = _safe_strip(idade_raw) if idade_raw not in (None, "") else None
    porte = _safe_strip(data.get("porte"))
    descricao = _safe_strip(data.get("descricao"))
    cidade = _safe_strip(data.get("cidade"))
    photo_url = _safe_strip(data.get("photo_url"))
    donor_name = _safe_strip(data.get("donor_name"))
    donor_whatsapp = _safe_strip(data.get("donor_whatsapp"))
    energia = _safe_strip(data.get("energia"))

    bom_com_criancas = to_bool_like(data.get("bom_com_criancas"))

    if not (nome and especie and descricao and cidade):
        return _json_error("Dados obrigatórios ausentes")

    with db_ext.db() as conn:
        with conn.cursor() as cur:
            if is_postgres():
                cur.execute(
                    """
                    INSERT INTO animais
                        (doador_id, nome, especie, raca, idade, porte,
                         descricao, cidade, photo_url, donor_name, donor_whatsapp,
                         energia, bom_com_criancas)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING id
                    """,
                    (
                        uid, nome, especie, raca, idade, porte,
                        descricao, cidade, photo_url, donor_name, donor_whatsapp,
                        energia, bom_com_criancas
                    ),
                )
                row = cur.fetchone()
                animal_id = row[0] if row else None
            else:
                cur.execute(
                    """
                    INSERT INTO animais
                        (doador_id, nome, especie, raca, idade, porte,
                         descricao, cidade, photo_url, donor_name, donor_whatsapp,
                         energia, bom_com_criancas)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        uid, nome, especie, raca, idade, porte,
                        descricao, cidade, photo_url, donor_name, donor_whatsapp,
                        energia, bom_com_criancas
                    ),
                )
                try:
                    animal_id = cur.lastrowid
                except Exception:
                    animal_id = None

    return jsonify({"ok": True, "id": animal_id})


# GET /animais/<id>

@bp_api.get("/animais/<int:aid>")
def get_animal(aid: int):
    with db_ext.db() as conn:
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
    if "bom_com_criancas" in row:
        row["bom_com_criancas"] = _normalize_to_int_bool(row.get("bom_com_criancas"))
    if row and row.get("adotado_em") is not None:
        try:
            row["adotado_em"] = row["adotado_em"].isoformat()
        except Exception:
            row["adotado_em"] = str(row["adotado_em"])
    return jsonify(_row_to_animal(row))


# UPDATE ANIMAL

@bp_api.put("/animais/<int:aid>")
def update_animal(aid: int):
    uid = _require_auth()
    if not uid:
        return _json_error("unauthenticated", 401)

    data = request.get_json(silent=True) or {}
    adotado_em = data.get("adotado_em")

    def _safe_strip_val(v):
        if v is None:
            return None
        if isinstance(v, str):
            return v.strip()
        return str(v).strip()

    nome = _safe_strip_val(data.get("nome"))
    especie = _safe_strip_val(data.get("especie"))
    raca = data.get("raca")
    idade = data.get("idade")
    porte = data.get("porte")
    descricao = _safe_strip_val(data.get("descricao"))
    cidade = _safe_strip_val(data.get("cidade"))
    photo_url = _safe_strip_val(data.get("photo_url"))
    energia = data.get("energia")
    bom_com_criancas = to_bool_like(data.get("bom_com_criancas"))

    with db_ext.db() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT * FROM animais WHERE id=%s", (aid,))
            owner = cur.fetchone()
            if not owner:
                return _json_error("not found", 404)
            if int(owner.get("doador_id") or 0) != int(uid):
                return _json_error("forbidden", 403)

            if not nome: nome = owner.get('nome')
            if not especie: especie = owner.get('especie')
            if not descricao: descricao = owner.get('descricao')
            if not cidade: cidade = owner.get('cidade')
            if not photo_url: photo_url = owner.get('photo_url')
            if 'adotado_em' not in data:
                adotado_em = owner.get('adotado_em')

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


# DELETE ANIMAL
@bp_api.delete("/animais/<int:aid>")
def delete_animal(aid: int):
    uid = _require_auth()
    if not uid:
        return _json_error("unauthenticated", 401)
    with db_ext.db() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT doador_id FROM animais WHERE id=%s", (aid,))
            owner = cur.fetchone()
            if not owner:
                return _json_error("not found", 404)
            if int(owner.get("doador_id") or 0) != int(uid):
                return _json_error("forbidden", 403)
            cur.execute("DELETE FROM animais WHERE id=%s", (aid,))
    return jsonify({"ok": True})

# ANIMAIS MINE

@bp_api.get("/animais/mine")
def animais_mine():
    uid = _require_auth()
    if not uid:
        return _json_error("unauthenticated", 401)

    with db_ext.db() as conn:
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

# RECOMENDAÇÕES (IA) - FALLBACK + PERFIL + KNN

@bp_api.get("/recomendacoes")
def recomendacoes():
    n = int(request.args.get("n") or 6)
    uid = _require_auth()

    # fallback quando não autenticado
    if not uid:
        conn = db_ext.get_conn()
        try:
            cur = conn.cursor()
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

            # normaliza/limit em função do tipo de cursor
            if rows and isinstance(rows[0], dict):
                limited = rows[:n]
            else:
                cols = None
                try:
                    desc = getattr(cur, "description", None)
                    if desc:
                        cols = [d[0] for d in desc]
                except Exception:
                    cols = None
                normalized = []
                for r in rows:
                    if isinstance(r, dict):
                        normalized.append(r)
                    elif cols and len(cols) == len(r):
                        normalized.append({k: v for k, v in zip(cols, r)})
                    else:
                        d = {}
                        d["id"] = r[0] if len(r) > 0 else None
                        d["nome"] = r[1] if len(r) > 1 else None
                        normalized.append(d)
                limited = normalized[:n]

            try:
                cur.close()
            except Exception:
                pass
        finally:
            try:
                conn.close()
            except Exception:
                pass

        return jsonify(_rows_to_payload(limited[:n], []))

    # se autenticado, busca perfil 
    with db_ext.db() as conn:
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

    if perfil and "tem_criancas" in perfil:
        perfil["tem_criancas"] = _normalize_to_int_bool(perfil.get("tem_criancas"))

    if not perfil:
        # sem perfil -> fallback simples
        with db_ext.db() as conn:
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
        return jsonify(_rows_to_payload(rows[:n], []))

    # se tem perfil -> pega todos os animais e processa IA
    with db_ext.db() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                """
                SELECT id, nome, especie, raca, idade, porte, descricao,
                       cidade, photo_url, donor_name, donor_whatsapp, doador_id,
                       criado_em AS created_at,
                       energia, bom_com_criancas, adotado_em
                  FROM animais
                """
            )
            animals = cur.fetchall() or []

    # filtros 
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

    # vetores e ranking
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

    scored = [(float(dist), animal_data) for dist, animal_data in zip(distances, animal_map)]
    scored.sort(key=lambda x: x[0])

    top = [a for _, a in scored[:n]]
    ids = [a["id"] for a in top]
    return jsonify(_rows_to_payload(top, ids))

# marcar/desmarcar adotado_em

@bp_api.patch("/animais/<int:aid>/adopt")
def adopt_animal(aid: int):
    uid = _require_auth()
    if not uid:
        return _json_error("unauthenticated", 401)

    data = request.get_json(silent=True) or {}
    action = (data.get("action") or "mark").lower()
    if action not in ("mark", "undo"):
        return _json_error("invalid_action")

    conn = None
    cur = None
    cur2 = None
    try:
        conn = db_ext.get_conn()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT doador_id FROM animais WHERE id=%s", (aid,))
        owner = cur.fetchone()

        if not owner:
            return _json_error("not found", 404)

        if int(owner.get("doador_id") or 0) != int(uid):
            return _json_error("forbidden", 403)

        if action == "mark":
            cur.execute("UPDATE animais SET adotado_em = NOW() WHERE id=%s", (aid,))
        else:
            cur.execute("UPDATE animais SET adotado_em = NULL WHERE id=%s", (aid,))

        try:
            conn.commit()
        except Exception:
            pass

        cur2 = conn.cursor(dictionary=True)
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

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print("ERROR adopt_animal:", str(e))
        print(tb)
        return jsonify({"ok": False, "error": "internal", "message": str(e), "trace": tb}), 500

    finally:
        try:
            if cur:
                cur.close()
        except Exception:
            pass
        try:
            if cur2:
                cur2.close()
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass

    if not row:
        return _json_error("not found", 404)

    if row.get("adotado_em") is not None:
        try:
            row["adotado_em"] = row["adotado_em"].isoformat()
        except Exception:
            row["adotado_em"] = str(row["adotado_em"])

    if "bom_com_criancas" in row:
        row["bom_com_criancas"] = _normalize_to_int_bool(row.get("bom_com_criancas"))

    return jsonify({"ok": True, "animal": _row_to_animal(row)})


# MÉTRICAS DE ADOÇÃO

@bp_api.get("/animais/metrics/adoptions")
def adoption_metrics():
    try:
        days = int(request.args.get("days") or 7)
    except Exception:
        days = 7
    if days <= 0:
        days = 7
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
    with db_ext.db() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute(sql, (start.isoformat(), end.isoformat()))
            rows = cur.fetchall() or []

    counts = {
        (r["day"].isoformat() if hasattr(r["day"], "isoformat") else str(r["day"])): int(r["cnt"] or 0)
        for r in rows
    }

    result = []
    for i in range(days):
        d = start + timedelta(days=i)
        ds = d.isoformat()
        result.append({"day": ds, "count": counts.get(ds, 0)})

    return jsonify({"ok": True, "days": result})

# REGISTRO DE BLUEPRINTS
def register_blueprints(app):
    app.register_blueprint(bp_api)
