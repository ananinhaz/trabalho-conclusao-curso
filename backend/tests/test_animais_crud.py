import pytest
pytestmark = pytest.mark.integration


def test_criar_e_listar_animal(client, monkeypatch):
    novo = {
    "nome": "Bolt",
    "especie": "Cachorro",
    "idade": 2,
    "cidade": "Curitiba",
    "descricao": "Cachorro bem educado, test"
}

    # Patch rápido da função _require_auth usada pela app (retorna user id "3")
    #    -> assim a app pensa que já tem um usuário autenticado
    try:
        monkeypatch.setattr("app.api._require_auth", lambda: 3, raising=False)
    except Exception:
        # fallback: importa e monkeypatcha diretamente
        import app.api as api_mod
        monkeypatch.setattr(api_mod, "_require_auth", lambda: 3, raising=False)

    #  por segurança, coloca session["user_id"]
    with client.session_transaction() as sess:
        sess["user_id"] = 3

    # POST para criar
    r = client.post("/animais", json=novo)
    assert r.status_code in (200, 201), f"status {r.status_code} / body: {r.get_data(as_text=True)}"

    # GET para listar e verificar que o item criado (ou pelo menos o nome) aparece
    lista = client.get("/animais").get_json()
    items = lista["items"] if isinstance(lista, dict) and "items" in lista else lista
    assert any(a.get("nome") == "Bolt" for a in items), f"esperava 'Bolt' em items, body={lista}"

