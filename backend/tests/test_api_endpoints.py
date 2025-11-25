import json
import types
import pytest
import importlib

# Helpers fakes para substituir a conexão / cursor do DB
class FakeCursor:
    def __init__(self, rows=None, one=None):
        # rows será retornado por fetchall; one por fetchone
        self._rows = rows or []
        self._one = one
        self.lastrowid = 42
        self._executed = []

    def execute(self, sql, params=None):
        self._executed.append((sql, params))

        return None

    def fetchall(self):
        return self._rows

    def fetchone(self):
        # se _one está definido, devolve; senão devolve primeira das rows
        if self._one is not None:
            return self._one
        return self._rows[0] if self._rows else None

    def close(self):
        # presente porque o código chama cur.close()
        return None

    # context manager support
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

class FakeConn:
    def __init__(self, rows=None, one=None):
        self._rows = rows or []
        self._one = one
        self._last_cursor = None

    def cursor(self, dictionary=False):
        self._last_cursor = FakeCursor(rows=self._rows, one=self._one)
        return self._last_cursor

    def close(self):
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

def fake_conn_factory(rows=None, one=None):
    def _factory():
        return FakeConn(rows=rows, one=one)
    return _factory

def test_get_animais_returns_list(client, monkeypatch):
    """GET /animais deve devolver a lista retornada pelo cursor."""
    fake_rows = [
        {"id": 1, "nome": "Alpha", "especie": "Cachorro", "idade": 3},
        {"id": 2, "nome": "Beta",  "especie": "Gato",      "idade": 2},
    ]
    # monkeypatch get_conn na extensão que o app usa
    monkeypatch.setattr("app.extensions.db.get_conn", fake_conn_factory(rows=fake_rows), raising=False)
    # Também patch no caminho alternativo (por segurança
    monkeypatch.setattr("app.extensions.db.db", fake_conn_factory(rows=fake_rows), raising=False)

    resp = client.get("/animais")
    assert resp.status_code == 200, f"GET /animais returned {resp.status_code} body={resp.get_data(as_text=True)}"

    data = resp.get_json()
    # API retorna lista 
    assert isinstance(data, list)
    names = [a.get("nome") for a in data]
    assert "Alpha" in names and "Beta" in names


def test_create_animal_requires_auth_and_creates(monkeypatch, client):
    """POST /animais com auth deve criar e retornar id."""
    # simula auth retornando user 3
    monkeypatch.setattr("app.api._require_auth", lambda: 3, raising=False)

    # prepara fake DB que aceita INSERT e fornece lastrowid
    fake_cursor = FakeCursor(rows=[])
    fake_conn = FakeConn(rows=[])
    # forçar lastrowid a algo conhecido
    fake_cursor.lastrowid = 123
    # montar um factory que devolve uma conn cujo cursor tem lastrowid
    def _get_conn():
        conn = FakeConn(rows=[])
        # ensure cursor() returns an object with lastrowid settable
        c = conn.cursor()
        c.lastrowid = 123
        return conn
    monkeypatch.setattr("app.extensions.db.get_conn", _get_conn, raising=False)

    novo = {
        "nome": "Bolt-TEST",
        "especie": "Cachorro",
        "idade": "2",
        "cidade": "Curitiba",
        "descricao": "bom",
    }

    r = client.post("/animais", json=novo)
    assert r.status_code in (200, 201), f"status {r.status_code} / body: {r.get_data(as_text=True)}"
    body = r.get_json()
    assert body.get("ok") is True
    assert "id" in body and isinstance(body["id"], int)


def test_create_animal_missing_required_fields_returns_400(client):
    """POST /animais sem os campos obrigatórios deve retornar 400."""

    import app.api as api_mod
    # safe patch
    api_mod._require_auth = lambda: 3

    novo = {
        "nome": "",  
        "especie": "Cachorro",
    }
    r = client.post("/animais", json=novo)
    assert r.status_code == 400
    j = r.get_json()
    assert j.get("error") is not None


def test_adopt_animal_mark_and_unmark(monkeypatch, client):
    """PATCH /animais/<id>/adopt deve marcar/desmarcar quando dono correto."""
    monkeypatch.setattr("app.api._require_auth", lambda: 3, raising=False)

    owner_row = {"doador_id": 3}
    updated_row = {
        "id": 99,
        "nome": "Zeta",
        "especie": "Cachorro",
        "raca": None,
        "idade": "2",
        "porte": "Medio",
        "descricao": "ok",
        "cidade": "Curitiba",
        "photo_url": None,
        "donor_name": "Ana",
        "donor_whatsapp": "000",
        "doador_id": 3,
        "created_at": None,
        "energia": None,
        "bom_com_criancas": 0,
        "adotado_em": "2025-11-20T00:00:00",
    }

    class MultiFakeConn(FakeConn):
        def __init__(self):
            super().__init__(rows=[], one=owner_row)
            self._after_update_one = updated_row

        def cursor(self, dictionary=False):
            cur = FakeCursor(rows=[], one=self._one)
            def _execute_and_watch(sql, params=None):
                cur._executed.append((sql, params))
                # detecta o UPDATE que muda adotado_em
                if "UPDATE animais SET adotado_em" in (sql or ""):
                    # atualiza o estado do connection: o próximo cursor() deve ver updated_row
                    self._one = self._after_update_one
            # substitui o método execute do cursor pela versão que observa o SQL
            cur.execute = _execute_and_watch
            return cur


    monkeypatch.setattr("app.extensions.db.get_conn", lambda: MultiFakeConn(), raising=False)

    # mark action
    r = client.patch("/animais/99/adopt", json={"action": "mark"})
    assert r.status_code == 200, f"mark returned {r.status_code} body={r.get_data(as_text=True)}"
    body = r.get_json()
    assert body.get("ok") is True
    assert "animal" in body and body["animal"].get("id") == 99

    # unmark action - reuse same conn behavior
    r2 = client.patch("/animais/99/adopt", json={"action": "undo"})
    assert r2.status_code == 200
    b2 = r2.get_json()
    assert b2.get("ok") is True

def test_recomendacoes_fallback_returns_recent(monkeypatch, client):
    """GET /recomendacoes sem user autenticado deve retornar fallback ordenado (LIMIT n)."""
    # prepara fake rows for fallback
    fake_rows = [
        {"id": 11, "nome": "A"},
        {"id": 12, "nome": "B"},
        {"id": 13, "nome": "C"},
    ]
    monkeypatch.setattr("app.extensions.db.get_conn", fake_conn_factory(rows=fake_rows), raising=False)

    resp = client.get("/recomendacoes?n=2")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, dict)
    assert "items" in data
    items = data["items"]
    assert isinstance(items, list)
    assert len(items) <= 2
    # garante que os nomes esperados estão presentes (A ou B etc)
    assert any(i.get("nome") in ("A", "B", "C") for i in items)
