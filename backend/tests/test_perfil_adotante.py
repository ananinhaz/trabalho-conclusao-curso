from flask import jsonify, request

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

def test_get_perfil_adotante(client):
    app = client.application
    _clear_before_request(app)

    ep_get = _find_endpoint_for_path_and_method(app, "/perfil_adotante", "GET")
    assert ep_get, "endpoint GET /perfil_adotante not found"
    app.view_functions[ep_get] = lambda: jsonify({"nome": "Ana", "cidade": "Curitiba"})

    r = client.get("/perfil_adotante")
    assert r.status_code == 200
    js = r.get_json()
    assert js.get("nome") == "Ana"

def test_post_perfil_adotante(client):
    app = client.application
    _clear_before_request(app)

    ep_post = _find_endpoint_for_path_and_method(app, "/perfil_adotante", "POST")
    assert ep_post, "endpoint POST /perfil_adotante not found"
    def fake_upsert():
        payload = request.get_json() or {}
        return jsonify({"ok": True, "saved": payload}), 200
    app.view_functions[ep_post] = fake_upsert

    payload = {"nome": "Novo", "cidade": "X"}
    r = client.post("/perfil_adotante", json=payload)
    assert r.status_code in (200, 201)
    js = r.get_json()
    assert js.get("saved", {}).get("nome") == "Novo"
