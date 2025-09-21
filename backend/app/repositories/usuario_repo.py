from ..extensions.db import get_conn

def list_all(limit=50):
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, nome, email FROM usuarios ORDER BY id DESC LIMIT %s", (limit,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def get_by_id(uid: int):
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, nome, email FROM usuarios WHERE id=%s", (uid,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row

def insert(data):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT INTO usuarios (nome, email) VALUES (%s,%s)", (data["nome"], data["email"]))
    conn.commit()
    new_id = cur.lastrowid
    cur.close(); conn.close()
    return new_id

def update(uid: int, data):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE usuarios SET nome=%s, email=%s WHERE id=%s", (data["nome"], data["email"], uid))
    conn.commit()
    affected = cur.rowcount
    cur.close(); conn.close()
    return affected

def delete(uid: int):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM usuarios WHERE id=%s", (uid,))
    conn.commit()
    affected = cur.rowcount
    cur.close(); conn.close()
    return affected
    