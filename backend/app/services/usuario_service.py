# serviço mínimo para usuários — usa acesso SQL direto (compatível com seu api.py style)
import hashlib
from werkzeug.security import generate_password_hash
from ..extensions import db as db_ext

def _to_user_row(row):
    if not row:
        return None
    # normaliza nomes de colunas caso o banco retorne dicts
    return {
        "id": row.get("id") if isinstance(row, dict) else row[0],
        "nome": row.get("nome") if isinstance(row, dict) else row[1],
        "email": row.get("email") if isinstance(row, dict) else row[2],
        # senha salva como senha_hash
        "senha_hash": row.get("senha") if isinstance(row, dict) else row[3],
    }

def find_by_email(email: str):
    conn = db_ext.get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, nome, email, senha FROM usuarios WHERE email=%s LIMIT 1", (email,))
        row = cur.fetchone()
        return _to_user_row(row)
    finally:
        try:
            cur.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

def criar(data: dict):
    nome = data.get("nome")
    email = data.get("email")
    senha = data.get("senha", "senha-por-padrao")
    senha_hash = generate_password_hash(senha)

    conn = db_ext.get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO usuarios (nome, email, senha) VALUES (%s,%s,%s)",
            (nome, email, senha_hash),
        )
        try:
            conn.commit()
        except Exception:
            pass
        # tenta recuperar id (works with mysql)
        try:
            uid = cur.lastrowid
        except Exception:
            uid = None
        # busca e retorna o objeto
        if not uid:
            cur2 = conn.cursor(dictionary=True)
            cur2.execute("SELECT id, nome, email, senha FROM usuarios WHERE email=%s LIMIT 1", (email,))
            row = cur2.fetchone()
            try:
                cur2.close()
            except Exception:
                pass
            return _to_user_row(row)
        return {"id": uid, "nome": nome, "email": email, "senha_hash": senha_hash}
    finally:
        try:
            cur.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

def obter(uid: int):
    conn = db_ext.get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, nome, email, senha FROM usuarios WHERE id=%s LIMIT 1", (uid,))
        row = cur.fetchone()
        return _to_user_row(row)
    finally:
        try:
            cur.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

def listar():
    conn = db_ext.get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, nome, email, senha FROM usuarios ORDER BY id DESC LIMIT 200")
        rows = cur.fetchall() or []
        return [_to_user_row(r) for r in rows]
    finally:
        try:
            cur.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

def atualizar(uid: int, data: dict):
    fields = []
    params = []
    if "nome" in data:
        fields.append("nome=%s")
        params.append(data["nome"])
    if "email" in data:
        fields.append("email=%s")
        params.append(data["email"])
    if "senha" in data:
        from werkzeug.security import generate_password_hash
        fields.append("senha=%s")
        params.append(generate_password_hash(data["senha"]))
    if not fields:
        return False
    params.append(uid)
    conn = db_ext.get_conn()
    try:
        cur = conn.cursor()
        cur.execute(f"UPDATE usuarios SET {', '.join(fields)} WHERE id=%s", tuple(params))
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

def remover(uid: int):
    conn = db_ext.get_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM usuarios WHERE id=%s", (uid,))
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
