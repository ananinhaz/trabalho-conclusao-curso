import pytest
from app.extensions.db import db

def test_recommendation_flow(client):
    """
    Testa o fluxo de recomendação (IA) para garantir cobertura nas funções
    _build_user_vector, _build_animal_vector e na rota /recomendacoes.
    """
    #  Cria um usuário e perfil para ter base de comparação
    email = "ia_test_user@example.com"
    client.post("/auth/register", json={
        "nome": "IA User", "email": email, "senha": "123"
    })
    
    # Pega o ID
    uid = None
    with db() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT id FROM usuarios WHERE email=%s", (email,))
            uid = cur.fetchone()['id']
            
    # Cria Perfil do Adotante (Mora em Casa, Tem Crianças)
    with client.session_transaction() as sess:
        sess["user_id"] = uid
        
    client.post("/perfil_adotante", json={
        "tipo_moradia": "casa",
        "tem_criancas": 1,
        "tempo_disponivel_horas_semana": 20,
        "estilo_vida": "ativo"
    })

    # Cria alguns animais variados para a IA processar
    # Cachorro agitado (Match bom)
    client.post("/animais", json={
        "nome": "Rex", "especie": "cachorro", "idade": "adulto",
        "porte": "grande", "descricao": "Agitado", "cidade": "SP",
        "energia": "alta", "bom_com_criancas": 1
    })
    
    # Gato calmo (Match ruim para quem quer agito)
    client.post("/animais", json={
        "nome": "Miau", "especie": "gato", "idade": "idoso",
        "porte": "pequeno", "descricao": "Calmo", "cidade": "SP"
    })

    # Chama a rota de recomendação
    resp = client.get("/recomendacoes?n=5")
    assert resp.status_code == 200
    data = resp.get_json()
    
    # Garante que retornou uma lista e que tem itens
    assert "items" in data
    assert len(data["items"]) > 0
    
    top_animal = data["items"][0]
    assert "cachorro" in top_animal["especie"].lower()