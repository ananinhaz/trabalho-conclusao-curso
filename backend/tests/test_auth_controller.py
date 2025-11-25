import pytest
from unittest.mock import patch, MagicMock
from werkzeug.wrappers import Response # Para inspecionar o retorno de _commit_and_redirect

GET_USER_BY_ID_PATH = 'app.controllers.auth_controller._get_user_by_id'
DB_CONTEXT_PATH = 'app.controllers.auth_controller.db'
GENERATE_HASH_PATH = 'app.controllers.auth_controller.generate_password_hash'
CHECK_HASH_PATH = 'app.controllers.auth_controller.check_password_hash'
OAUTH_PATH = 'app.controllers.auth_controller.oauth'


def setup_db_mock(mock_db, fetchone_result=None, lastrowid=1):
    """Configuração robusta para o mock de banco de dados."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    
    if isinstance(fetchone_result, list):
         mock_cur.fetchone.side_effect = fetchone_result
    else:
         mock_cur.fetchone.side_effect = [fetchone_result]
    
    mock_cur.fetchall.return_value = []
    mock_cur.lastrowid = lastrowid
    
    # cursor usado como context manager
    mock_conn.cursor.return_value = mock_cur
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    
    mock_db.return_value = mock_conn
    mock_db.return_value.__enter__.return_value = mock_conn
    
    return mock_conn, mock_cur


#  Testes de Registro e Login 

@patch(GENERATE_HASH_PATH)
@patch(DB_CONTEXT_PATH)
@patch(GET_USER_BY_ID_PATH)
def test_register_success(mock_get_user_by_id, mock_db, mock_generate_hash, client):
    """Testa o registro de um novo usuário."""
    mock_generate_hash.return_value = "hashed_password"
    mock_conn, mock_cur = setup_db_mock(mock_db)

    # Check email: None (Usuário não existe)
    mock_cur.fetchone.side_effect = [None, None]
    mock_cur.lastrowid = 99
    
    mock_get_user_by_id.return_value = {"id": 99, "email": "new@user.com", "nome": "New User"}

    payload = {"nome": "New User", "email": "new@user.com", "senha": "password123"}
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 200
    data = response.get_json()
    assert data.get('ok') is True

    # Verifica que o retorno contém o usuário criado 
    assert data.get("user") and data["user"]["id"] == 99


@patch(DB_CONTEXT_PATH)
def test_register_user_exists(mock_db, client):
    """Testa o registro quando o email já existe."""
    setup_db_mock(mock_db, fetchone_result={"id": 1})
    
    payload = {"nome": "Existing", "email": "test@mock.com", "senha": "123"}
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 400
    assert "Email já cadastrado" in response.get_json().get('error')


@patch(CHECK_HASH_PATH)
@patch(DB_CONTEXT_PATH)
@patch(GET_USER_BY_ID_PATH)
def test_login_success(mock_get_user_by_id, mock_db, mock_check_hash, client):
    """Testa o login com credenciais corretas."""
    mock_check_hash.return_value = True
    setup_db_mock(mock_db, fetchone_result={"id": 1, "password_hash": "hashed_123"}) 
    mock_get_user_by_id.return_value = {"id": 1, "nome": "Mock User"}

    payload = {"email": "test@mock.com", "senha": "password123"}
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 200
    assert response.get_json().get('ok') is True

    # Verifica que o JSON devolve o usuário correto
    assert response.get_json().get("user") and response.get_json()["user"]["id"] == 1


@patch(DB_CONTEXT_PATH)
def test_login_user_not_found(mock_db, client):
    """Testa o login quando o usuário não é encontrado no DB."""
    setup_db_mock(mock_db, fetchone_result=None)
    payload = {"email": "not@found.com", "senha": "password123"}
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 401


@patch(CHECK_HASH_PATH)
@patch(DB_CONTEXT_PATH)
def test_login_incorrect_password(mock_db, mock_check_hash, client):
    """Testa o login com senha incorreta."""
    mock_check_hash.return_value = False
    setup_db_mock(mock_db, fetchone_result={"id": 1, "password_hash": "hashed"})
    payload = {"email": "test@mock.com", "senha": "wrong"}
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 401


def test_login_missing_fields(client):
    """Testa o login sem o campo de senha."""
    payload = {"email": "missing@pass.com"}
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 401


@patch(DB_CONTEXT_PATH)
def test_me_authenticated(mock_db, client):
    """Testa a rota /me quando há um usuário logado."""
    mock_user_data = {"id": 1, "nome": "Logged User", "email": "log@user.com", "avatar_url": None}
    setup_db_mock(mock_db, fetchone_result=mock_user_data)
    
    # Injeta a sessão manualmente
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        
    response = client.get("/auth/me")
    
    assert response.status_code == 200
    data = response.get_json()
    assert data.get('authenticated') is True
    assert data.get('user')['id'] == 1


@patch(DB_CONTEXT_PATH)
def test_me_unauthenticated(mock_db, client):
    """Testa a rota /me quando nenhum usuário está logado."""
    setup_db_mock(mock_db, fetchone_result=None)
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_logout_success(client):
    """Testa o logout e a limpeza da sessão."""
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        
    response = client.post("/auth/logout")
    assert response.status_code == 200
    
    with client.session_transaction() as sess:
        assert 'user_id' not in sess


# Testes de Funções Auxiliares 

@patch(DB_CONTEXT_PATH)
def test_get_user_by_id(mock_db, client):
    """Testa a função interna _get_user_by_id."""
    from app.controllers.auth_controller import _get_user_by_id
    
    real_dict = {"id": 1, "nome": "Test", "email": "a@a.com", "avatar_url": None}
    setup_db_mock(mock_db, fetchone_result=real_dict)
    
    result = _get_user_by_id(1)
    assert result == real_dict


@patch(DB_CONTEXT_PATH)
def test_get_user_by_id_not_found(mock_db, client):
    """Testa _get_user_by_id quando o usuário não existe."""
    from app.controllers.auth_controller import _get_user_by_id
    setup_db_mock(mock_db, fetchone_result=None)
    result = _get_user_by_id(999)
    assert result is None


@patch(DB_CONTEXT_PATH)
def test_commit_and_redirect(mock_db, client):
    """
    Testa a função auxiliar de redirecionamento. 
    CORRIGIDO: Agora espera status 200 e a estrutura de tupla (body, status, headers)
    """
    from app.controllers.auth_controller import _commit_and_redirect

    mock_conn, _ = setup_db_mock(mock_db)
    
    response_result = _commit_and_redirect("/perfil")
    
    assert isinstance(response_result, tuple)
    assert response_result[1] == 200 
    
    assert response_result[2].get('Content-Type') == "text/html; charset=utf-8"
    
    expected_url_part = "http://127.0.0.1:5173/perfil"
    assert expected_url_part in response_result[0]


#  Testes Google OAuth 

@patch(OAUTH_PATH)
def test_login_google_redirect(mock_oauth, client):
    """Testa o redirecionamento inicial para o Google."""
    mock_oauth.google.authorize_redirect.return_value = (
        "", 302, {"Location": "http://g.co/auth"}
    )
    response = client.get("/auth/login/google?next=/dashboard")
    assert response.status_code == 302
    assert response.headers['Location'] == "http://g.co/auth"


@patch(DB_CONTEXT_PATH)
@patch('app.controllers.auth_controller.requests.get') # Mock para a requisição de userinfo
@patch(OAUTH_PATH)
def test_google_callback_new_user(mock_oauth, mock_requests_get, mock_db, client):
    """
    Testa o callback do Google para um novo usuário.
    Rota: /auth/google/callback
    """
    
    # Mock do token (safe_authorize_access_token)
    mock_oauth.google.safe_authorize_access_token.return_value = {
        'access_token': 'access_123',
    }
    
    # Mock da requisição requests.get (userinfo)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'email': 'new_google@user.com',
        'name': 'New Google User',
        'picture': 'http://avatar.com/new',
        'sub': 'google_id_123'
    }
    mock_requests_get.return_value = mock_response
    
    setup_db_mock(mock_db, fetchone_result=[None, None], lastrowid=100)
    
    response = client.get("/auth/google/callback") 
    
    assert response.status_code == 200
    assert 'Autenticado com sucesso. Redirecionando' in response.data.decode('utf-8')
    
    mock_cur = mock_db.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
    assert mock_cur.lastrowid == 100


@patch(DB_CONTEXT_PATH)
@patch('app.controllers.auth_controller.requests.get') 
@patch(OAUTH_PATH)
def test_google_callback_existing_user(mock_oauth, mock_requests_get, mock_db, client):
    """Testa o callback do Google para um usuário já existente (busca por email)."""
    
    mock_oauth.google.safe_authorize_access_token.return_value = {'access_token': 'access_123'}
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'email': 'existing@user.com',
        'sub': 'google_id_123',
        'picture': 'http://avatar.com/existing',
    }
    mock_requests_get.return_value = mock_response
    
    existing_user_id = {"id": 1}

    setup_db_mock(mock_db, fetchone_result=[None, existing_user_id])
    
    response = client.get("/auth/google/callback")
    
    assert response.status_code == 200
    mock_cur = mock_db.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
    mock_cur.execute.assert_any_call(
        "UPDATE usuarios SET google_sub=%s, avatar_url=%s WHERE id=%s",
        ('google_id_123', 'http://avatar.com/existing', 1),
    )


@patch(DB_CONTEXT_PATH)
@patch('app.controllers.auth_controller.requests.get')
@patch(OAUTH_PATH)
def test_google_callback_token_fail(mock_oauth, mock_requests_get, mock_db, client):
    """Testa falha na obtenção do token Google (simula token sem access_token)."""
    mock_oauth.google.safe_authorize_access_token.return_value = {}
    response = client.get("/auth/google/callback")
    
    assert response.status_code == 400
    assert "Google não retornou access_token" in response.get_json().get('error')
