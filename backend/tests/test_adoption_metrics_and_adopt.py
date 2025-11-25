import pytest
pytestmark = pytest.mark.integration

def test_adoption_metrics(client):
    r = client.get("/animais/metrics/adoptions?days=7")
    assert r.status_code == 200
    j = r.get_json()
    assert "days" in j and isinstance(j["days"], list)

def test_adopt_mark_unmark_requires_auth(client):
    r = client.patch("/animais/1/adopt", json={"action":"mark"})
    assert r.status_code in (401,404)

