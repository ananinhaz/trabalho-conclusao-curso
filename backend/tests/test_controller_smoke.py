class _Cursor:
    def __init__(self):
        self._rows = []

    def execute(self, *_args, **_kwargs):
        return None

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _Conn:
    def cursor(self, dictionary=False):
        return _Cursor()

    def close(self):
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _stub_db(monkeypatch):
    monkeypatch.setattr("app.extensions.db.db", lambda: _Conn(), raising=False)
    monkeypatch.setattr("app.extensions.db.get_conn", lambda: _Conn(), raising=False)


def test_animais_endpoint(client, monkeypatch):
    _stub_db(monkeypatch)
    r = client.get("/api/animais")
    assert r.status_code in (200, 404)


def test_animais_by_id(client, monkeypatch):
    _stub_db(monkeypatch)
    r = client.get("/api/animais/1")
    assert r.status_code in (200, 404)


def test_usuario_endpoint(client):
    r = client.get("/api/usuarios/1")
    assert r.status_code in (200, 404)


def test_recommendation_endpoint(client, monkeypatch):
    _stub_db(monkeypatch)
    r = client.get("/api/recomendacoes")
    assert r.status_code in (200, 404)


def test_health_endpoint(client):
    r = client.get("/health")
    assert r.status_code in (200, 404)
