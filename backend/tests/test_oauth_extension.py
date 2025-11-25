import pytest
import requests
from unittest.mock import patch, MagicMock
from flask import Flask
from authlib.integrations.base_client.errors import MismatchingStateError
from app.extensions.oauth import init_oauth, oauth

@pytest.fixture
def app_oauth():
    """Cria uma app Flask básica e inicializa o OAuth."""
    app = Flask(__name__)
    app.config['GOOGLE_CLIENT_ID'] = 'fake-id'
    app.config['GOOGLE_CLIENT_SECRET'] = 'fake-secret'
    app.config['GOOGLE_REDIRECT_URI'] = 'http://localhost/callback'
    
    init_oauth(app)
    return app

def test_init_oauth_registers_google(app_oauth):
    """Testa se o cliente google foi registrado."""
    assert "google" in oauth._registry

def test_safe_token_standard_flow(app_oauth):
    """
    Cenário 1: O authorize_access_token funciona normalmente.
    Não deve entrar no bloco except MismatchingStateError.
    """
    # Mocka a função original do authlib
    with patch.object(oauth.google, 'authorize_access_token') as mock_auth:
        expected_token = {'access_token': 'valid_token'}
        mock_auth.return_value = expected_token
        
        token = oauth.google.safe_authorize_access_token()
        
        assert token == expected_token
        mock_auth.assert_called_once()

def test_safe_token_fallback_success(app_oauth):
    """
    Cenário 2: Ocorre MismatchingStateError, temos o 'code' na URL,
    e a requisição manual POST retorna 200 OK.
    """
    with patch.object(oauth.google, 'authorize_access_token') as mock_auth:
        # Força o erro inicial
        mock_auth.side_effect = MismatchingStateError()
        
        # Simula o contexto de requisição com o parâmetro 'code'
        with app_oauth.test_request_context('/callback?code=my_auth_code'):
            
            # Mocka o requests.post para simular a resposta do Google
            with patch('app.extensions.oauth.requests.post') as mock_post:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = {'access_token': 'manual_fallback_token'}
                mock_post.return_value = mock_resp
                
                # Executa a função
                token = oauth.google.safe_authorize_access_token()
                
                assert token['access_token'] == 'manual_fallback_token'
                
                # Verifica se montou o payload corretamente
                args, kwargs = mock_post.call_args
                assert kwargs['data']['code'] == 'my_auth_code'
                assert kwargs['data']['grant_type'] == 'authorization_code'

def test_safe_token_fallback_no_code(app_oauth):
    """
    Cenário 3: Ocorre MismatchingStateError, mas NÃO temos 'code' na URL.
    Deve relançar a exceção original.
    """
    with patch.object(oauth.google, 'authorize_access_token') as mock_auth:
        mock_auth.side_effect = MismatchingStateError()
        
        with app_oauth.test_request_context('/callback'):
            with pytest.raises(MismatchingStateError):
                oauth.google.safe_authorize_access_token()

def test_safe_token_fallback_request_fail(app_oauth):
    """
    Cenário 4: Ocorre MismatchingStateError, temos 'code',
    mas o POST manual retorna erro (ex: 400).
    """
    with patch.object(oauth.google, 'authorize_access_token') as mock_auth:
        mock_auth.side_effect = MismatchingStateError()
        
        with app_oauth.test_request_context('/callback?code=bad_code'):
            with patch('app.extensions.oauth.requests.post') as mock_post:
                mock_resp = MagicMock()
                mock_resp.status_code = 400
                mock_resp.text = "Bad Request"
                mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError("Boom")
                mock_post.return_value = mock_resp
                
                with pytest.raises(requests.exceptions.HTTPError):
                    oauth.google.safe_authorize_access_token()