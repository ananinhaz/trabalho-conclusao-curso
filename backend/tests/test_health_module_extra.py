from flask import Flask

import app.health as health_mod


class OkCursor:
    def execute(self, *_args, **_kwargs):
        return None

    def fetchone(self):
        return (1,)

    def fetchall(self):
        return [("animais",), ("usuarios",)]

    def close(self):
        return None


class OkConn:
    def __init__(self, module_name="sqlite3"):
        self.__class__.__module__ = module_name

    def cursor(self):
        return OkCursor()

    def close(self):
        return None


class BoomConn:
    def cursor(self):
        raise RuntimeError("db error")

    def close(self):
        return None


def _client():
    app = Flask(__name__)
    app.register_blueprint(health_mod.health_bp)
    return app.test_client()


def test_db_health_ok(monkeypatch):
    monkeypatch.setattr(health_mod, "get_conn", lambda: OkConn())
    client = _client()
    rv = client.get("/db-health")
    assert rv.status_code == 200


def test_db_health_error(monkeypatch):
    monkeypatch.setattr(health_mod, "get_conn", lambda: BoomConn())
    client = _client()
    rv = client.get("/db-health")
    assert rv.status_code == 500


def test_tables_postgres(monkeypatch):
    monkeypatch.setattr(health_mod, "get_conn", lambda: OkConn(module_name="psycopg2.extensions"))
    client = _client()
    rv = client.get("/tables")
    assert rv.status_code == 200
    assert "tabelas" in rv.get_json()


def test_tables_mysql(monkeypatch):
    monkeypatch.setattr(health_mod, "get_conn", lambda: OkConn(module_name="mysql.connector.connection"))
    client = _client()
    rv = client.get("/tables")
    assert rv.status_code == 200


def test_tables_error(monkeypatch):
    monkeypatch.setattr(health_mod, "get_conn", lambda: BoomConn())
    client = _client()
    rv = client.get("/tables")
    assert rv.status_code == 500
