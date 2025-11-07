# app/extensions/db.py
from __future__ import annotations
import os
from contextlib import contextmanager
from typing import Optional
from mysql.connector.pooling import MySQLConnectionPool
from mysql.connector import MySQLConnection, connect as mysql_connect

_pool: Optional[MySQLConnectionPool] = None

def init_db(app=None):
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = int(os.getenv("DB_PORT", "3306"))
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    database = os.getenv("DB_NAME", "adoptme")
    pool_name = os.getenv("DB_POOL_NAME", "adoptme_pool")
    pool_size = int(os.getenv("DB_POOL_SIZE", "12"))
    timeout = int(os.getenv("DB_TIMEOUT", "5"))

    common = dict(
        host=host, port=port, user=user, password=password, database=database,
        connection_timeout=timeout, use_pure=True, ssl_disabled=True,
    )

    # teste direto
    conn = mysql_connect(**common)
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
    finally:
        conn.close()

    global _pool
    _pool = MySQLConnectionPool(
        pool_name=pool_name,
        pool_size=pool_size,
        pool_reset_session=True,
        **common,
    )

def get_conn() -> MySQLConnection:
    global _pool
    if _pool is None:
        raise RuntimeError("DB pool não inicializado")

    conn = _pool.get_connection()
    try:
        if hasattr(conn, "is_connected") and not conn.is_connected():
            conn.reconnect(attempts=1, delay=0)
    except Exception:
        try:
            conn.reconnect(attempts=1, delay=0)
        except Exception:
            pass
    return conn

@contextmanager
def db():
    conn = get_conn()
    try:
        yield conn
        if getattr(conn, "in_transaction", False):
            conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass
