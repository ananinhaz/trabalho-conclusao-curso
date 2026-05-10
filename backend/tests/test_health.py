def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200


def test_db_health_endpoint(client):
    resp = client.get("/db-health")
    assert resp.status_code == 404


def test_tables_endpoint(client):
    resp = client.get("/tables")
    assert resp.status_code == 404
