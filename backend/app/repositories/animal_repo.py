from ..extensions.db import get_conn

def list_all(limit=50):
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, nome, especie, idade FROM animais ORDER BY id DESC LIMIT %s", (limit,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def get_by_id(aid: int):
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, nome, especie, idade FROM animais WHERE id=%s", (aid,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row

def insert(data):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT INTO animais (nome, especie, idade) VALUES (%s,%s,%s)", (data["nome"], data["especie"], data["idade"]))
    conn.commit()
    new_id = cur.lastrowid
    cur.close(); conn.close()
    return new_id

def update(aid: int, data):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE animais SET nome=%s, especie=%s, idade=%s WHERE id=%s",
                (data["nome"], data["especie"], data["idade"], aid))
    conn.commit()
    affected = cur.rowcount
    cur.close(); conn.close()
    return affected

def delete(aid: int):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM animais WHERE id=%s", (aid,))
    conn.commit()
    affected = cur.rowcount
    cur.close(); conn.close()
    return affected
