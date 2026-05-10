# tests/conftest.py
import os
import sys
import tempfile
import sqlite3
import importlib
import pathlib
import pytest

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
import os

os.environ["DATABASE_URL"] = "sqlite:///test.db"

# Ensure project root on sys.path for `import app`
project_root = pathlib.Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configurações para testes (SQLite)
os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret")

_tmp_dir = tempfile.TemporaryDirectory(prefix="adoptme_test_")
_tmp_db_path = os.path.join(_tmp_dir.name, "test_db.sqlite")


def _ensure_schema(path):
    """Garante as tabelas necessárias para os testes (compatível com api.py e SQLite)."""
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
            donor_name TEXT,
            donor_whatsapp TEXT,
            doador_id INTEGER,
            criado_em TEXT,
            adotado_em TEXT,
            energia TEXT,
            bom_com_criancas INTEGER
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS perfil_adotante (
            usuario_id INTEGER PRIMARY KEY,
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

    # Importa a app (create_app usa DATABASE_URL=sqlite e init_db em extensions/db usa SQLite)
    from app import create_app

    app = create_app()
    app.config["TESTING"] = True

    ctx = app.app_context()
    ctx.push()

    # Força import dos módulos que registram rotas
    controllers_to_try = (
        "app.api",
        "app.health",
        "app.controllers.auth_controller",
        "app.controllers.recommendation_controller",
        "app.controllers.adopter_controller",
        "app.controllers.animal_controller",
        "app.controllers.usuario_controller",
    )
    for mod in controllers_to_try:
        try:
            importlib.import_module(mod)
        except Exception:
            app.logger.debug(f"could not import {mod} during test setup", exc_info=True)

    # Log das rotas registradas (útil para debugging)
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