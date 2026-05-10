import pytest


class FakeCursor:
    def __init__(self, rows=None):
        self._rows = rows or []

    def execute(self, _sql, _params=None):
        return None

    def fetchall(self):
        return self._rows

    def close(self):
        return None


class FakeConn:
    def __init__(self, rows=None):
        self._rows = rows or []

    def cursor(self, dictionary=False):
        return FakeCursor(rows=self._rows)

    def close(self):
        return None


def test_get_recommendations_for_user(client, monkeypatch):
    monkeypatch.setattr("app.api._require_auth", lambda: None, raising=False)
    monkeypatch.setattr(
        "app.extensions.db.get_conn",
        lambda: FakeConn(rows=[{"id": 1, "nome": "Bolt", "bom_com_criancas": 1}]),
        raising=False,
    )

    rv = client.get("/api/recomendacoes?n=1")
    assert rv.status_code == 200
    data = rv.get_json()
    assert isinstance(data, dict)
    assert data["items"][0]["id"] == 1


def test_get_recommendations_for_user_empty(client, monkeypatch):
    monkeypatch.setattr("app.api._require_auth", lambda: None, raising=False)
    monkeypatch.setattr("app.extensions.db.get_conn", lambda: FakeConn(rows=[]), raising=False)

    rv = client.get("/api/recomendacoes")
    assert rv.status_code == 200
    data = rv.get_json()
    assert isinstance(data.get("items"), list)


def test_get_recommendations_for_user_unauthenticated(client, monkeypatch):
    monkeypatch.setattr("app.api._require_auth", lambda: None, raising=False)
    monkeypatch.setattr("app.extensions.db.get_conn", lambda: FakeConn(rows=[]), raising=False)

    rv = client.get("/api/recomendacoes")
    assert rv.status_code == 200

