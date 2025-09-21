from flask import Blueprint, jsonify
from .extensions.db import get_conn

health_bp = Blueprint("health", __name__)

@health_bp.get("/db-health")
def db_health():
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        return jsonify({"ok": True}), 200
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500
    finally:
        try:
            cur.close(); conn.close()
        except Exception:
            pass

@health_bp.get("/tables")
def tables():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SHOW TABLES")
    data = [r[0] for r in cur.fetchall()]
    cur.close(); conn.close()
    return jsonify({"tabelas": data})
