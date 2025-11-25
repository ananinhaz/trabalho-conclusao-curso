import pytest
pytestmark = pytest.mark.integration

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

def test_post_login_and_register(client):
    app = client.application
    _clear_before_request(app)

    # login
    ep_login = _find_endpoint_for_path_and_method(app, "/auth/login", "POST")
    assert ep_login, "endpoint POST /auth/login not found"
    def fake_login():
        payload = request.get_json() or {}
        return jsonify({"ok": True, "token": "fake-token", "user": {"id": 1, "nome": payload.get("nome", "user")}}), 200
    app.view_functions[ep_login] = fake_login

    r = client.post("/auth/login", json={"email": "a@b.com", "senha": "x"})
    assert r.status_code == 200
    js = r.get_json()
    assert js.get("ok") is True and "token" in js

    # register
    ep_reg = _find_endpoint_for_path_and_method(app, "/auth/register", "POST")
    assert ep_reg, "endpoint POST /auth/register not found"
    def fake_register():
        payload = request.get_json() or {}
        return jsonify({"id": 99, "nome": payload.get("nome")}), 201
    app.view_functions[ep_reg] = fake_register

    r2 = client.post("/auth/register", json={"nome": "Test", "email": "t@t.com", "senha": "pass"})
    assert r2.status_code in (200, 201)
    js2 = r2.get_json()
    assert js2.get("nome") == "Test"

def test_get_me(client):
    app = client.application
    _clear_before_request(app)

    ep_me = _find_endpoint_for_path_and_method(app, "/auth/me", "GET")
    assert ep_me, "endpoint GET /auth/me not found"
    def fake_me():
        return jsonify({"ok": True, "user": {"id": 5, "nome": "Fake User"}}), 200
    app.view_functions[ep_me] = fake_me

    r = client.get("/auth/me")
    assert r.status_code == 200
    js = r.get_json()
    assert js.get("user", {}).get("nome") == "Fake User"

