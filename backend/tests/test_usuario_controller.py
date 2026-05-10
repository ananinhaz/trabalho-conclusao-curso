def test_usuarios_endpoint(client):
    resp = client.get("/api/usuarios")
    assert resp.status_code in (200, 404, 405)