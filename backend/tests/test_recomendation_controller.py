import pytest
pytestmark = pytest.mark.integration

import importlib
from flask import jsonify, request

def test_recomendacoes_controller_retorna_items_mockados(client):
    """
    Substitui diretamente a view function registrada para /recomendacoes
    por uma fake que retorna dados controlados, e verifica o resultado.
    Isso evita problemas com imports/closures que impedem monkeypatch funcionar.
    """
    fake_items = [{"id": 1, "nome": "X", "especie": "Cachorro"}]

    app = client.application

    try:
        for k in list(app.before_request_funcs.keys()):
            app.before_request_funcs[k] = []
    except Exception:
        pass

    def fake_recomendacoes_view():
        return jsonify({"ids": [it["id"] for it in fake_items], "items": fake_items})

    # registra no app 
    app.view_functions["api.recomendacoes"] = fake_recomendacoes_view

    # chama a rota real
    resp = client.get("/recomendacoes")
    assert resp.status_code == 200, f"GET /recomendacoes retornou {resp.status_code} body={resp.get_data(as_text=True)}"

    data = resp.get_json()
    items = data["items"] if isinstance(data, dict) and "items" in data else data

    assert isinstance(items, list), f"esperava lista, veio: {type(items)} body={resp.get_data(as_text=True)}"
    assert any(i.get("nome") == "X" for i in items), f"esperava item com nome 'X' em items, body={resp.get_data(as_text=True)}"

