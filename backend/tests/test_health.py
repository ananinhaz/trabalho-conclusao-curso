import pytest
from unittest.mock import patch, MagicMock

DB_PATH = 'app.health.get_conn' 

HEALTH_ROUTE = "/db-health" 

def test_health_check_success(client):
    """
    Testa o endpoint de saúde em caso de sucesso (BD online).
    """
    resp = client.get(HEALTH_ROUTE)
    
    assert resp.status_code == 200
    
    data = resp.get_json()
    
    assert data is not None
    assert data.get('ok') is True

@patch(DB_PATH)
def test_health_check_db_failure(mock_get_conn, client):
    """
    Testa o endpoint de saúde quando há uma FALHA na conexão inicial do DB (get_conn falha).
    Isso deve retornar 500.
    """
    # Força o get_conn() a levantar uma exceção
    mock_get_conn.side_effect = Exception("Falha simulada na conexão com o DB")
    
    resp = client.get(HEALTH_ROUTE)
    
    # Espera 500
    assert resp.status_code == 500 
    
    data = resp.get_json()
    assert data.get('ok') is False
    assert 'Falha simulada' in data.get('erro', '')
    
@patch(DB_PATH)
def test_health_check_cursor_error(mock_get_conn, client):
    """
    Testa o endpoint de saúde quando a CONEXÃO é estabelecida, mas a QUERY SQL falha.
    """
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    # Simula o erro na execução da query SQL
    mock_cursor.execute.side_effect = Exception("Erro simulado na query SQL")

    # Garante que get_conn retorna uma conexão que, por sua vez, retorna um cursor que falha
    mock_conn.cursor.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    resp = client.get(HEALTH_ROUTE)

    # Deve retornar erro 500
    assert resp.status_code == 500 
    
    data = resp.get_json()
    assert data.get('ok') is False
    assert 'Erro simulado na query SQL' in data.get('erro', '')
    
def test_tables_endpoint_success(client):
    """
    Testa a rota secundária /tables.
    """
    resp = client.get("/tables")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "tabelas" in data
    assert isinstance(data["tabelas"], list)