import pytest

pytestmark = pytest.mark.integration


class FakeCursor:
    def __init__(self, rows=None, one=None):
        self._rows = rows or []
        self._one = one
        self.lastrowid = 101

    def execute(self, _sql, _params=None):
        return None

    def fetchall(self):
        return self._rows

    def fetchone(self):
        if self._one is not None:
            return self._one
        return self._rows[0] if self._rows else None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConn:
    def __init__(self, rows=None, one=None):
        self._rows = rows or []
        self._one = one

    def cursor(self, dictionary=False):
        return FakeCursor(rows=self._rows, one=self._one)

    def commit(self):
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_get_animais(client, monkeypatch):
    rows = [{"id": 42, "nome": "Toto", "especie": "Cachorro", "bom_com_criancas": 1}]
    monkeypatch.setattr("app.extensions.db.db", lambda: FakeConn(rows=rows), raising=False)

    rv = client.get("/api/animais")
    assert rv.status_code == 200
    data = rv.get_json()
    assert isinstance(data, list)
    assert data and data[0]["id"] == 42


def test_get_animal_by_id_found(client, monkeypatch):
    row = {
        "id": 42,
        "nome": "Toto",
        "especie": "Cachorro",
        "raca": None,
        "idade": "2",
        "porte": "medio",
        "descricao": "ok",
        "cidade": "SP",
        "photo_url": None,
        "donor_name": "Ana",
        "donor_whatsapp": "123",
        "doador_id": 3,
        "created_at": None,
        "energia": None,
        "bom_com_criancas": 1,
        "adotado_em": None,
    }
    monkeypatch.setattr("app.extensions.db.db", lambda: FakeConn(one=row), raising=False)

    rv = client.get("/api/animais/42")
    assert rv.status_code == 200
    assert rv.get_json()["id"] == 42


def test_get_animal_by_id_not_found(client, monkeypatch):
    monkeypatch.setattr("app.extensions.db.db", lambda: FakeConn(one=None), raising=False)

    rv = client.get("/api/animais/99999")
    assert rv.status_code == 404


def test_post_animais(client, monkeypatch):
    monkeypatch.setattr("app.api._require_auth", lambda: 3, raising=False)
    monkeypatch.setattr("app.extensions.db.db", lambda: FakeConn(), raising=False)

    new_animal = {
        "nome": "Luna",
        "especie": "Gato",
        "idade": 2,
        "cidade": "SP",
        "descricao": "Gato fofo",
    }

    rv = client.post("/api/animais", json=new_animal)
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["ok"] is True
    assert data["id"] == 101
