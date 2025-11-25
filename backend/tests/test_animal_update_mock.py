import pytest
import random
from unittest.mock import patch
from app.extensions.db import db
from datetime import datetime

AUTH_PATH = 'app.api._require_auth' 

@patch(AUTH_PATH)
def test_animal_crud_full_cycle_mocked(mock_require_auth, client):
    """
    Testa o ciclo completo: Criar -> Editar -> Deletar Animal,
    usando Mock para forçar a autenticação e contornar o 401.
    
    A correção para o erro 500 (IntegrityError: Column 'idade' cannot be null)
    foi incluir o campo 'idade' no payload de criação.
    """

    # Cria Usuário Novo e Limpo
    rand_int = random.randint(10000, 99999)
    email = f"crud_mock_{rand_int}@test.com"
    senha = "123"

    # Registrar
    reg = client.post("/auth/register", json={
        "nome": "Dono Mock", "email": email, "senha": senha
    })
    assert reg.status_code in (200, 201), "Erro no registro do usuário mock"

    # Pega o ID Real no Banco
    uid = None
    with db() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT id FROM usuarios WHERE email=%s", (email,))
            row = cur.fetchone()
            if row: uid = row['id']
    assert uid is not None, "Usuário registrado não encontrado no banco."

    mock_require_auth.return_value = uid

    payload_criacao = {
        "nome": "Toto Mockado", 
        "especie": "cachorro",
        "descricao": "Teste Crud Mockado", 
        "cidade": "Rio",
        "idade": 2 
    }
    resp = client.post("/animais", json=payload_criacao)

    assert resp.status_code == 200, f"Erro ao criar animal (mock): {resp.get_data(as_text=True)}"

    data = resp.get_json()
    assert "id" in data
    animal_id = data["id"]
    
    payload_edicao = {
        "nome": "Toto Editado Mock", 
        "especie": "gato", 
        "descricao": "Novo Desc Mock", 
        "cidade": "SP", 
        "photo_url": "http://foto.com/mock.jpg",
        "idade": 3, 
        "adotado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
    }
    resp_upd = client.put(f"/animais/{animal_id}", json=payload_edicao)
    assert resp_upd.status_code == 200, f"Erro ao editar animal: {resp_upd.get_data(as_text=True)}"

    # Verifica se salvou
    get_anim = client.get(f"/animais/{animal_id}")
    dados_novos = get_anim.get_json()
    assert dados_novos["nome"] == "Toto Editado Mock"
    
    # DELETE
    resp_del = client.delete(f"/animais/{animal_id}")
    assert resp_del.status_code == 200, f"Erro ao deletar animal: {resp_del.get_data(as_text=True)}"

    # Verifica se sumiu 
    get_anim_2 = client.get(f"/animais/{animal_id}")
    assert get_anim_2.status_code == 404

    # Limpa o mock
    mock_require_auth.return_value = None