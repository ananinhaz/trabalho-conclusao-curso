from __future__ import annotations
import os
from contextlib import contextmanager
from typing import Optional, Any, Dict

# MySQL imports 
try:
    from mysql.connector.pooling import MySQLConnectionPool
    from mysql.connector import connect as mysql_connect
    _MYSQL_AVAILABLE = True
except Exception:
    MySQLConnectionPool = None  
    mysql_connect = None  
    _MYSQL_AVAILABLE = False

# Postgres imports 
_psycopg2 = None
_pg_pool = None
_pg_extras = None
try:
    import psycopg2
    from psycopg2.pool import ThreadedConnectionPool
    from psycopg2 import extras as _pg_extras
    _psycopg2 = psycopg2
except Exception:
    _psycopg2 = None

# globals
_mysql_pool: Optional["MySQLConnectionPool"] = None
_pg_pool: Optional["ThreadedConnectionPool"] = None
_using_postgres: bool = False


def using_postgres() -> bool:
    """Getter simples para saber qual driver está em uso."""
    return _using_postgres


def init_db(app=None):
    """
    Inicializa pool de conexão:
    - Se DATABASE_URL estiver definida, tenta inicializar pool Postgres (psycopg2 ThreadedConnectionPool).
    - Caso contrário, inicializa o pool MySQL como antes (se mysql disponível).
    """
    global _mysql_pool, _pg_pool, _using_postgres

    database_url = os.getenv("DATABASE_URL")
    pool_size = int(os.getenv("DB_POOL_SIZE", "12"))
    timeout = int(os.getenv("DB_TIMEOUT", "5"))

    if database_url:
        # Inicializa pool Postgres
        if _psycopg2 is None:
            raise RuntimeError("psycopg2 não instalado. Rode: pip install psycopg2-binary")

        minconn = 1
        maxconn = max(1, pool_size)

        # ThreadedConnectionPool aceita dsn (connection string)
        _pg_pool = ThreadedConnectionPool(minconn, maxconn, dsn=database_url)
        _using_postgres = True

        # Teste simples de conexão
        conn = _pg_pool.getconn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchone()
            cur.close()
        finally:
            _pg_pool.putconn(conn)
    else:
        # fallback MySQL (preservado)
        if not _MYSQL_AVAILABLE:
            raise RuntimeError("MySQL não disponível e DATABASE_URL não informada.")
        host = os.getenv("DB_HOST", "127.0.0.1")
        port = int(os.getenv("DB_PORT", "3306"))
        user = os.getenv("DB_USER", "root")
        password = os.getenv("DB_PASSWORD", "")
        database = os.getenv("DB_NAME", "adoptme")

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

        _mysql_pool = MySQLConnectionPool(
            pool_name=os.getenv("DB_POOL_NAME", "adoptme_pool"),
            pool_size=pool_size,
            pool_reset_session=True,
            **common,
        )
        _using_postgres = False


def _get_raw_conn():
    """Retorna a conexão bruta (psycopg2 connection ou mysql connector connection)."""
    global _mysql_pool, _pg_pool, _using_postgres

    if _using_postgres:
        if _pg_pool is None:
            raise RuntimeError("Pool Postgres não inicializado. Chame init_db() primeiro.")
        conn = _pg_pool.getconn()
        
        try:
            conn.autocommit = False
        except Exception:
            pass
        return conn
    else:
        if _mysql_pool is None:
            raise RuntimeError("Pool MySQL não inicializado. Chame init_db() primeiro.")
        conn = _mysql_pool.get_connection()
        # reconectar se necessário
        try:
            if hasattr(conn, "is_connected") and not conn.is_connected():
                conn.reconnect(attempts=1, delay=0)
        except Exception:
            try:
                conn.reconnect(attempts=1, delay=0)
            except Exception:
                pass
        return conn


def get_conn():
    """
    Backwards-compatible: retorna a conexão crua (psycopg2 connection ou mysql connector connection).
    Isso é para compatibilidade com módulos antigos que importavam get_conn() diretamente.
    NOTE: quem usar get_conn() deve fechar a conexão depois (ou usar db() context manager).
    """
    return _get_raw_conn()


class ConnProxy:
    """
    Pequena wrapper para tornar a API de cursor compatível com o código que usa
    conn.cursor(dictionary=True) (MySQL) — no Postgres mapeamos para RealDictCursor.
    Também expõe commit/rollback/close e mantém referência ao raw conn e ao pool.
    """
    def __init__(self, raw_conn: Any):
        self._raw = raw_conn

    def cursor(self, *args, **kwargs):
        """
        Suporta chamada cur = conn.cursor(dictionary=True) (compat com MySQL).
        Para Postgres, converte dictionary=True para cursor_factory=RealDictCursor.
        """
        # detecta flag compat
        dict_flag = False
        if "dictionary" in kwargs:
            dict_flag = kwargs.pop("dictionary")
        if _using_postgres:
            if dict_flag:
                return self._raw.cursor(cursor_factory=_pg_extras.RealDictCursor)
            return self._raw.cursor()
        else:
            if dict_flag:
                kwargs["dictionary"] = True
            return self._raw.cursor(*args, **kwargs)

    def commit(self):
        return self._raw.commit()

    def rollback(self):
        try:
            return self._raw.rollback()
        except Exception:
            pass

    def close(self):
        """
        Fechar: para Postgres colocamos a conexão de volta no pool (putconn).
        Para MySQL, fechamos a conexão (que devolve ao pool do mysql-connector).
        """
        try:
            if _using_postgres:
                # devolve para pool
                global _pg_pool
                if _pg_pool is not None:
                    try:
                        _pg_pool.putconn(self._raw)
                    except Exception:
                        try:
                            self._raw.close()
                        except Exception:
                            pass
                else:
                    try:
                        self._raw.close()
                    except Exception:
                        pass
            else:
                try:
                    self._raw.close()
                except Exception:
                    pass
        except Exception:
            pass

    @property
    def raw(self):
        return self._raw


@contextmanager
def db():
    """
    Context manager que devolve uma ConnProxy.
    Faz commit ao final (se não houve exceção) e rollback em caso de erro.
    Uso:
        with db() as conn:
            cur = conn.cursor(dictionary=True)
            cur.execute(...)
    """
    conn = _get_raw_conn()
    proxy = ConnProxy(conn)
    try:
        yield proxy

        try:
            proxy.commit()
        except Exception:
            pass
    except Exception:
        try:
            proxy.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            proxy.close()
        except Exception:
            pass
