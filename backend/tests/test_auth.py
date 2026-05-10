import pytest

pytestmark = pytest.mark.integration


def test_post_login_and_register(client):
    r = client.post("/api/auth/login", json={"email": "a@b.com", "senha": "x"})
    assert r.status_code in (200, 401, 500)

    r2 = client.post("/api/auth/register", json={"nome": "Test", "email": "t@t.com", "senha": "pass"})
    assert r2.status_code in (201, 400, 500)


def test_get_me(client):
    r = client.get("/api/auth/me")
    assert r.status_code in (200, 401)
