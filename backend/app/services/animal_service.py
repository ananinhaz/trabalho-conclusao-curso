# shim mínimo para animal_service usado pelos controllers
from ..extensions import db as db_ext

def listar(limit=200):
    conn = db_ext.get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT id, nome, especie, raca, idade, porte, descricao, cidade,
                   photo_url, donor_name, donor_whatsapp, doador_id, criado_em as created_at,
                   energia, bom_com_criancas, adotado_em
            FROM animais
            ORDER BY criado_em DESC
            LIMIT %s
            """,
            (limit,),
        )
        rows = cur.fetchall() or []
        return rows
    finally:
        try:
            cur.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

def obter(aid):
    conn = db_ext.get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM animais WHERE id=%s LIMIT 1", (aid,))
        return cur.fetchone()
    finally:
        try:
            cur.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

# criar/atualizar/remover: deixo mínimos (ajusta conforme sua schema)
def criar(data, doador_id=None):
    conn = db_ext.get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO animais (doador_id, nome, especie, raca, idade, porte,
                                 descricao, cidade, photo_url, donor_name, donor_whatsapp,
                                 energia, bom_com_criancas)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                doador_id,
                data.get("nome"),
                data.get("especie"),
                data.get("raca"),
                data.get("idade"),
                data.get("porte"),
                data.get("descricao"),
                data.get("cidade"),
                data.get("photo_url"),
                data.get("donor_name"),
                data.get("donor_whatsapp"),
                data.get("energia"),
                data.get("bom_com_criancas"),
            ),
        )
        try:
            conn.commit()
        except Exception:
            pass
        try:
            return {"id": cur.lastrowid}
        except Exception:
            return {"ok": True}
    finally:
        try:
            cur.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

def atualizar(aid, data):
    # implemente conforme necessidade; para evitar erros de import, deixamos stub
    return True

def remover(aid):
    conn = db_ext.get_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM animais WHERE id=%s", (aid,))
        try:
            conn.commit()
        except Exception:
            pass
        return True
    finally:
        try:
            cur.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
