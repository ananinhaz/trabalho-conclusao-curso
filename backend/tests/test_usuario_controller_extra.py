def test_get_all_usuarios(client):
    rv = client.get("/api/usuarios")
    assert rv.status_code == 404


def test_get_usuario_by_id_not_found(client):
    rv = client.get("/api/usuarios/99999")
    assert rv.status_code == 404


def test_patch_usuario_not_found(client):
    rv = client.patch("/api/usuarios/99999", json={"nome": "Fake"})
    assert rv.status_code == 404
