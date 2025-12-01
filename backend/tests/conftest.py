# tests/conftest.py
import os
import sys
import tempfile
import sqlite3
import importlib
import logging
from contextlib import contextmanager
import pathlib
import pytest

# --- Ensure project root is on sys.path so `import app` works during pytest collection --- #
project_root = pathlib.Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# --- Configurações gerais para evitar que a app tente usar Neon/Postgres --- #
os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret")

# --- Cria arquivo sqlite temporário (persistente durante a sessão de testes) --- #
_tmp_dir = tempfile.TemporaryDirectory(prefix="adoptme_test_")
_tmp_db_path = os.path.join(_tmp_dir.name, "test_db.sqlite")


# --- Wrapper para cursor/connection que aproxima comportamento do MySQLCursor usado nos tests --- #
class SQLiteCursorWrapper:
    def __init__(self, cur, dict_mode=False):
        self._cur = cur
        self._dict = dict_mode

    def execute(self, sql, params=None):
        if params is None:
            params = ()
        # converte placeholder %s -> ? para sqlite
        sql_converted = sql.replace("%s", "?")
        return self._cur.execute(sql_converted, params)

    def executemany(self, sql, seq_of_params):
        sql_converted = sql.replace("%s", "?")
        return self._cur.executemany(sql_converted, seq_of_params)

    def fetchone(self):
        row = self._cur.fetchone()
        if row is None:
            return None
        if self._dict:
            return dict(row)
        return row

    def fetchall(self):
        rows = self._cur.fetchall()
        if self._dict:
            return [dict(r) for r in rows]
        return rows

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


class SQLiteConnectionWrapper:
    def __init__(self, path):
        self._path = path
        # check_same_thread=False permite acesso em threads diferentes durante os testes
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

    def cursor(self, dictionary=False):
        cur = self._conn.cursor()
        return SQLiteCursorWrapper(cur, dict_mode=bool(dictionary))

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


def _ensure_schema(path):
    """Garante as tabelas mínimas necessárias para os testes."""
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            email TEXT UNIQUE,
            password_hash TEXT,
            google_sub TEXT,
            avatar_url TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS animais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            especie TEXT,
            raca TEXT,
            idade TEXT,
            porte TEXT,
            descricao TEXT,
            cidade TEXT,
            photo_url TEXT,
            doador_id INTEGER,
            adotado_em TEXT,
            energia TEXT,
            bom_com_criancas INTEGER
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS perfil_adotante (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            tipo_moradia TEXT,
            tem_criancas INTEGER,
            tempo_disponivel_horas_semana INTEGER,
            estilo_vida TEXT
        )
        """
    )
    con.commit()
    con.close()


@pytest.fixture(scope="session")
def tmp_db_path():
    _ensure_schema(_tmp_db_path)
    return _tmp_db_path


@pytest.fixture(scope="session")
def app(tmp_db_path):
    """
    Fixture app modificada para garantir que DATABASE_URL aponte para o sqlite
    temporário ANTES de importar/instanciar a aplicação.
    """

    # --- SETA DATABASE_URL ANTES de importar create_app para evitar abrir pool no Postgres/Neon ---
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_db_path}"
    os.environ["FLASK_ENV"] = "testing"
    os.environ["SECRET_KEY"] = "test-secret"

    # Agora importamos a app (create_app irá ler DATABASE_URL já apontando para sqlite)
    from app import create_app
    import app.extensions.db as extdb

    app = create_app()
    app.config["TESTING"] = True

    ctx = app.app_context()
    ctx.push()

    # Força import dos módulos que registram rotas (adapte nomes se necessário)
    controllers_to_try = (
        "app.api",
        "app.health",
        "app.controllers.auth_controller",
        "app.controllers.recomendation_controller",
        "app.controllers.perfil_adotante_controller",
        "app.controllers.adopter_controller",
        "app.controllers.animal_controller",
        "app.controllers.usuario_controller",
    )
    for mod in controllers_to_try:
        try:
            importlib.import_module(mod)
        except Exception:
            app.logger.debug(f"could not import {mod} during test setup", exc_info=True)

    # conexão local sqlite compatível com a API usada nos controllers (db() / get_conn)
    def _get_conn():
        return SQLiteConnectionWrapper(tmp_db_path)

    @contextmanager
    def _db_ctx():
        conn = _get_conn()
        try:
            yield conn
            try:
                conn.commit()
            except Exception:
                pass
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

    # sobrescreve funções/objetos do módulo de extensão de DB para garantir isolamento
    try:
        extdb.get_conn = _get_conn
    except Exception:
        app.logger.debug("could not set extdb.get_conn", exc_info=True)

    try:
        extdb.db = _db_ctx
    except Exception:
        app.logger.debug("could not set extdb.db", exc_info=True)

    # Log das rotas registradas (útil para debugging dos testes que procuram endpoints)
    try:
        rules = sorted(str(r) for r in app.url_map.iter_rules())
        app.logger.debug("Registered routes (url_map):\n" + "\n".join(rules))
    except Exception:
        app.logger.debug("could not list url_map", exc_info=True)

    yield app

    try:
        ctx.pop()
    except Exception:
        pass


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def isolate_fs_and_env(monkeypatch, tmp_db_path):
    """
    Mantém garantia adicional por teste — garante FLASK_ENV/SECRET_KEY/DATABASE_URL
    mesmo se algum teste alterar variáveis.
    """
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_db_path}")
    monkeypatch.setenv("FLASK_ENV", "testing")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    yield