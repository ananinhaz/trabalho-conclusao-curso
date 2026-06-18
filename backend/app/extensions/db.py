from __future__ import annotations
import os
import sqlite3
import urllib.parse
from contextlib import contextmanager
from typing import Optional, Any, Dict

from ..constants import (
    POSTGRESQL_PSYCOPG2_SCHEME,
    POSTGRESQL_URL_SCHEME,
    POSTGRES_URL_SCHEME,
)

_LOCAL_DB_HOSTS = frozenset({"localhost", "127.0.0.1", "db", "postgres", "::1"})


def normalize_database_url(url: str, *, for_sqlalchemy: bool = False) -> str:
    """Normaliza DSN Postgres: driver e sslmode (disable local, require remoto)."""
    if not url or url.lower().startswith("sqlite:"):
        return url
    if url.startswith(POSTGRES_URL_SCHEME):
        repl = POSTGRESQL_PSYCOPG2_SCHEME if for_sqlalchemy else POSTGRESQL_URL_SCHEME
        url = url.replace(POSTGRES_URL_SCHEME, repl, 1)
    elif for_sqlalchemy and url.startswith(POSTGRESQL_URL_SCHEME):
        scheme = url.split(":", 1)[0]
        if "+psycopg2" not in scheme:
            url = url.replace(POSTGRESQL_URL_SCHEME, POSTGRESQL_PSYCOPG2_SCHEME, 1)

    parsed = urllib.parse.urlsplit(url)
    host = (parsed.hostname or "").lower()
    qs = parsed.query
    if "sslmode=" not in qs:
        sslmode = "disable" if host in _LOCAL_DB_HOSTS else "require"
        qs = (qs + f"&sslmode={sslmode}") if qs else f"sslmode={sslmode}"
        url = urllib.parse.urlunsplit(
            (parsed.scheme, parsed.netloc, parsed.path, qs, parsed.fragment)
        )
    return url

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
_using_sqlite: bool = False
_sqlite_path: Optional[str] = None


def using_postgres() -> bool:
    """Getter simples para saber qual driver estÃ¡ em uso."""
    return _using_postgres


def using_sqlite() -> bool:
    """True quando DATABASE_URL aponta para SQLite (testes e dev local)."""
    return _using_sqlite


class _SQLiteCursorWrapper:
    """Wrapper para cursor SQLite: converte %s -> ? e suporta dictionary=True."""

    def __init__(self, cur, dict_mode=False):
        self._cur = cur
        self._dict = dict_mode

    def execute(self, sql, params=None):
        if params is None:
            params = ()
        sql_converted = sql.replace("%s", "?")
        return self._cur.execute(sql_converted, params)

    def executemany(self, sql, seq_of_params):
        sql_converted = sql.replace("%s", "?")
        return self._cur.executemany(sql_converted, seq_of_params)

    def fetchone(self):
        row = self._cur.fetchone()
        if row is None:
            return None
        return dict(row) if self._dict else row

    def fetchall(self):
        rows = self._cur.fetchall()
        return [dict(r) for r in rows] if self._dict else rows

    def close(self):
        try:
            self._cur.close()
        except Exception:
            pass

    @property
    def lastrowid(self):
        return self._cur.lastrowid

    @property
    def rowcount(self):
        try:
            return self._cur.rowcount
        except Exception:
            return -1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


class _SQLiteConnectionWrapper:
    """Wrapper para conexÃ£o SQLite compatÃ­vel com MySQL cursor(dictionary=True)."""

    def __init__(self, path):
        self._path = path
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

    def cursor(self, dictionary=False):
        cur = self._conn.cursor()
        return _SQLiteCursorWrapper(cur, dict_mode=bool(dictionary))

    def commit(self):
        try:
            self._conn.commit()
        except Exception:
            pass

    def rollback(self):
        try:
            self._conn.rollback()
        except Exception:
            pass

    def close(self):
        try:
            self._conn.close()
        except Exception:
            pass

    def __getattr__(self, item):
        return getattr(self._conn, item)


def init_db(app=None):
    """
    Inicializa pool de conexão:
    - Se DATABASE_URL começar com sqlite:, usa SQLite (testes e dev local).
    - Se DATABASE_URL for postgres://, usa pool Postgres (psycopg2).
    - Caso contrário, usa pool MySQL (DB_HOST, DB_PORT, etc.).
    """
    global _mysql_pool, _pg_pool, _using_postgres, _using_sqlite, _sqlite_path

    database_url = normalize_database_url((os.getenv("DATABASE_URL") or "").strip())
    if os.getenv("PYTEST_CURRENT_TEST") and "postgres" in database_url:
        raise RuntimeError("Tests cannot use the production database")

    if database_url and database_url.lower().split(":", 1)[0] == "sqlite":
        _using_sqlite = True
        _using_postgres = False
        path = database_url.replace("sqlite:///", "").split("?")[0]
        _sqlite_path = path
        return

    pool_size = int(os.getenv("DB_POOL_SIZE", "12"))
    timeout = int(os.getenv("DB_TIMEOUT", "5"))

    if database_url:
        # Inicializa pool Postgres
        if _psycopg2 is None:
            raise RuntimeError("psycopg2 não instalado. Rode: pip install psycopg2-binary")

        minconn = 1
        maxconn = max(1, pool_size)

        # ThreadedConnectionPool aceita dsn (connection string)
        global _pg_pool
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

        global _mysql_pool
        _mysql_pool = MySQLConnectionPool(
            pool_name=os.getenv("DB_POOL_NAME", "adoptme_pool"),
            pool_size=pool_size,
            pool_reset_session=True,
            **common,
        )
        _using_postgres = False


def _get_raw_conn():
    """Retorna a conexÃ£o bruta (psycopg2, mysql connector ou SQLite wrapper)."""
    global _mysql_pool, _pg_pool, _using_postgres, _using_sqlite, _sqlite_path

    if _using_sqlite and _sqlite_path:
        return _SQLiteConnectionWrapper(_sqlite_path)

    if _using_postgres:
        if _pg_pool is None:
            raise RuntimeError("Pool Postgres nÃ£o inicializado. Chame init_db() primeiro.")
        conn = _pg_pool.getconn()
        
        try:
            conn.autocommit = False
        except Exception:
            pass
        return conn
    else:
        if _mysql_pool is None:
            raise RuntimeError("Pool MySQL nÃ£o inicializado. Chame init_db() primeiro.")
        conn = _mysql_pool.get_connection()
        # reconectar se necessÃ¡rio
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
    Backwards-compatible: retorna a conexÃ£o crua (psycopg2 connection ou mysql connector connection).
    Isso Ã© para compatibilidade com mÃ³dulos antigos que importavam get_conn() diretamente.
    NOTE: quem usar get_conn() deve fechar a conexÃ£o depois (ou usar db() context manager).
    """
    return _get_raw_conn()


class ConnProxy:
    """
    Pequena wrapper para tornar a API de cursor compatÃ­vel com o cÃ³digo que usa
    conn.cursor(dictionary=True) (MySQL) â€” no Postgres mapeamos para RealDictCursor.
    TambÃ©m expÃµe commit/rollback/close e mantÃ©m referÃªncia ao raw conn e ao pool.
    """
    def __init__(self, raw_conn: Any):
        self._raw = raw_conn

    def cursor(self, *args, **kwargs):
        """
        Suporta chamada cur = conn.cursor(dictionary=True) (compat com MySQL).
        Para Postgres, converte dictionary=True para cursor_factory=RealDictCursor.
        """
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
        Fechar: para Postgres colocamos a conexÃ£o de volta no pool (putconn).
        Para MySQL, fechamos a conexÃ£o (que devolve ao pool do mysql-connector).
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
def _db_context_manager():
    """
    Context manager que devolve uma ConnProxy.
    Faz commit ao final (se nÃ£o houve exceÃ§Ã£o) e rollback em caso de erro.
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

# Export the db context manager for import by other modules.
# Usage: from app.extensions.db import db
db = _db_context_manager

