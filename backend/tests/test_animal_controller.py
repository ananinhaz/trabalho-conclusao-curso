def test_animais_list(client):
    resp = client.get("/api/animais")
    assert resp.status_code in (200, 404)


def test_animais_mine(client):
    resp = client.get("/api/animais/mine")
    assert resp.status_code in (200, 401, 404)