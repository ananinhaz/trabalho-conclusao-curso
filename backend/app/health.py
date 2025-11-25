from flask import Blueprint, jsonify
from .extensions.db import get_conn # <- ESTA IMPORTAÇÃO É CRÍTICA PARA O PATCH

health_bp = Blueprint("health", __name__)

@health_bp.get("/db-health")
def db_health():
    conn = None
    cur = None
    
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        
        return jsonify({"ok": True}), 200
        
    except Exception as e:
        # Garante o status 500
        return jsonify({"ok": False, "erro": str(e)}), 500
        
    finally:
        try:
            if cur:
                cur.close()
            if conn:
                conn.close()
        except Exception:
            pass

@health_bp.get("/tables")
def tables():
    conn = None
    cur = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SHOW TABLES")
        data = [r[0] for r in cur.fetchall()]
        return jsonify({"tabelas": data}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except Exception:
            pass