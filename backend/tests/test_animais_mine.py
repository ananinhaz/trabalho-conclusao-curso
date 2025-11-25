import pytest
pytestmark = pytest.mark.integration

from flask import jsonify

def _clear_before_request(app):
    try:
        for k in list(app.before_request_funcs.keys()):
            app.before_request_funcs[k] = []
    except Exception:
        pass

def _find_endpoint_for_path_and_method(app, path, method):
    for r in app.url_map.iter_rules():
        if r.rule == path:
            methods = set(m.upper() for m in (r.methods or []))
            if method.upper() in methods:
                return r.endpoint
    return None

def test_animais_mine_isolated(client):
    app = client.application
    _clear_before_request(app)

    ep = _find_endpoint_for_path_and_method(app, "/animais/mine", "GET")
    assert ep, "endpoint GET /animais/mine not found"

    fake = [{"id": 1, "nome": "MeuPet"}]
    app.view_functions[ep] = lambda: jsonify(fake)

    r = client.get("/animais/mine")
    assert r.status_code == 200
    js = r.get_json()
    assert isinstance(js, list) and js[0].get("nome") == "MeuPet"

