# backend/app/services/animal_service.py
from typing import Any, Dict, List, Optional
from flask import session
from ..extensions.db import get_conn

# ---------- helpers ----------
def _first(data: Dict[str, Any], *keys, default=None):
    for k in keys:
        v = data.get(k, None)
        if v is not None and str(v).strip() != "":
            return v
    return default

def _get_user_id() -> Optional[int]:
    # ajuste aqui se você salva com outra chave na sessão
    return session.get("user_id") or session.get("uid")

# ---------- CRUD ----------
def criar(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aceita tanto nomes PT-BR quanto EN:
    - cidade|city
    - photo_url|url_foto|image_url
    - donor_name|nome_doador|doador_nome
    - donor_whatsapp|whatsapp_doador|doador_whatsapp
    """
    user_id = _get_user_id()

    nome           = _first(data, "nome", "name")
    especie        = _first(data, "especie", "species")
    idade          = _first(data, "idade", "age")
    raca           = _first(data, "raca", "breed")
    descricao      = _first(data, "descricao", "description")
    cidade         = _first(data, "cidade", "city")
    photo_url      = _first(data, "photo_url", "url_foto", "image_url")
    donor_name     = _first(data, "donor_name", "nome_doador", "doador_nome")
    donor_whatsapp = _first(data, "donor_whatsapp", "whatsapp_doador", "doador_whatsapp")

    porte          = _first(data, "porte", "size")
    energia        = _first(data, "energia", "energy")
    bom_kids       = _first(data, "bom_com_criancas", "good_with_kids")

    faltando = []
    if not nome:           faltando.append("nome")
    if not especie:        faltando.append("especie")
    if not cidade:         faltando.append("cidade/city")
    if not donor_name:     faltando.append("donor_name/nome_doador")
    if not donor_whatsapp: faltando.append("donor_whatsapp/whatsapp_doador")
    if faltando:
        raise ValueError(f"Dados obrigatórios ausentes: {', '.join(faltando)}")

    try:
        idade = int(idade) if (idade is not None and str(idade).strip() != "") else None
    except Exception:
        idade = None
    try:
        bom_kids = int(bom_kids) if bom_kids is not None else None
    except Exception:
        bom_kids = None

    sql = """
        INSERT INTO animais
            (usuario_id, nome, especie, raca, idade, porte, energia, bom_com_criancas,
             descricao, cidade, city, photo_url, donor_name, donor_whatsapp,
             disponivel, criado_em, created_at)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s,
             %s, %s, %s, %s, %s, %s,
             1, NOW(), NOW())
    """
    params = (
        user_id, nome, especie, raca, idade, porte, energia, bom_kids,
        descricao, cidade, cidade, photo_url, donor_name, donor_whatsapp
    )

    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(sql, params)
        conn.commit()
        return {"ok": True, "id": cur.lastrowid}
    except Exception as e:
        conn.rollback()
        # propaga como 400 lá no controller
        raise e
    finally:
        cur.close()

def listar(qs=None) -> List[Dict[str, Any]]:
    """
    Suporta filtros pela querystring (controller passa request.args):
      especie=..., porte=..., cidade=..., idade_min=..., idade_max=..., show=recommended
    Usa COALESCE(a.city, a.cidade) e COALESCE(a.created_at, a.criado_em) para compat.
    """
    qs = qs or {}
    especie    = qs.get("especie") or qs.get("species")
    porte      = qs.get("porte") or qs.get("size")
    cidade     = qs.get("cidade") or qs.get("city")
    idade_min  = qs.get("idade_min")
    idade_max  = qs.get("idade_max")
    show       = qs.get("show")  # "recommended" para habilitar ranking

    user_id = _get_user_id()

    base_sql = """
        SELECT
            a.id, a.nome, a.especie, a.raca, a.idade, a.porte,
            a.energia, a.bom_com_criancas,
            COALESCE(a.city, a.cidade)       AS city,
            COALESCE(a.created_at, a.criado_em) AS created_at,
            a.descricao, a.photo_url, a.donor_name, a.donor_whatsapp,
            a.disponivel
        FROM animais a
        WHERE a.disponivel = 1
    """
    where = []
    params = []

    if especie and especie.lower() != "todas":
        where.append("a.especie = %s")
        params.append(especie)

    if porte and porte.lower() != "qualquer":
        where.append("a.porte = %s")
        params.append(porte)

    if cidade:
        where.append("COALESCE(a.city, a.cidade) LIKE CONCAT('%', %s, '%')")
        params.append(cidade)

    # idades (opcionais)
    if idade_min:
        where.append("a.idade IS NOT NULL AND a.idade >= %s")
        params.append(int(idade_min))
    if idade_max:
        where.append("a.idade IS NOT NULL AND a.idade <= %s")
        params.append(int(idade_max))

    if where:
        base_sql += " AND " + " AND ".join(where)

    # Ordenação / recomendação
    order_sql = " ORDER BY COALESCE(a.created_at, a.criado_em) DESC"

    # Recomendação simples baseada no perfil do adotante
    if show == "recommended" and user_id:
        # boosts por match de porte, presença de crianças etc.
        rec_sql = f"""
            SELECT z.* FROM (
                {base_sql}
            ) z
            LEFT JOIN perfil_adotante p ON p.usuario_id = %s
        """
        params_rec = params + [user_id]
        # score:
        # +3 se p.tem_criancas=1 e animal é bom com crianças
        # +2 se porte casa com "Apartamento" (preferir pequeno/médio)
        score = """
            SELECT
              z.*,
              (
                (CASE WHEN p.tem_criancas = 1 AND z.bom_com_criancas = 1 THEN 3 ELSE 0 END) +
                (CASE
                    WHEN p.tipo_moradia = 'Apartamento' AND z.porte IN ('Pequeno','Médio') THEN 2
                    ELSE 0
                 END)
              ) AS rec_score
            FROM (""" + base_sql + """) z
            LEFT JOIN perfil_adotante p ON p.usuario_id = %s
            ORDER BY rec_score DESC, z.created_at DESC
        """
        conn = get_conn()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute(score, params + [user_id])
            rows = cur.fetchall()
            # front usa um check/selo — mandamos a flag
            for r in rows:
                r["recommended"] = True if r.get("rec_score", 0) > 0 else False
            return rows
        finally:
            cur.close()

    # Sem recomendação: lista normal
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(base_sql + order_sql, params)
        rows = cur.fetchall()
        for r in rows:
            r["recommended"] = False
        return rows
    finally:
        cur.close()

def obter(aid: int) -> Optional[Dict[str, Any]]:
    sql = """
        SELECT
            a.id, a.nome, a.especie, a.raca, a.idade, a.porte, a.energia, a.bom_com_criancas,
            COALESCE(a.city, a.cidade) AS city,
            COALESCE(a.created_at, a.criado_em) AS created_at,
            a.descricao, a.photo_url, a.donor_name, a.donor_whatsapp, a.disponivel
        FROM animais a
        WHERE a.id = %s
    """
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(sql, (aid,))
        return cur.fetchone()
    finally:
        cur.close()

def atualizar(aid: int, data: Dict[str, Any]) -> bool:
    # atualização simples (só alguns campos comuns)
    fields = []
    params = []

    for col, aliases in {
        "nome": ("nome","name"),
        "especie": ("especie","species"),
        "raca": ("raca","breed"),
        "idade": ("idade","age"),
        "porte": ("porte","size"),
        "descricao": ("descricao","description"),
        "photo_url": ("photo_url","url_foto","image_url"),
        "donor_name": ("donor_name","nome_doador","doador_nome"),
        "donor_whatsapp": ("donor_whatsapp","whatsapp_doador","doador_whatsapp"),
        "cidade": ("cidade","city"),
    }.items():
        v = _first(data, *aliases)
        if v is not None:
            if col == "cidade":
                fields.append("cidade = %s")
                params.append(v)
                fields.append("city = %s")
                params.append(v)
            else:
                fields.append(f"{col} = %s")
                params.append(v)

    if not fields:
        return False

    sql = "UPDATE animais SET " + ", ".join(fields) + " WHERE id = %s"
    params.append(aid)

    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(sql, tuple(params))
        conn.commit()
        return cur.rowcount > 0
    finally:
        cur.close()

def remover(aid: int) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM animais WHERE id = %s", (aid,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        cur.close()
