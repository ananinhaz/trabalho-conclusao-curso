import os
from unittest.mock import MagicMock, patch

from flask_jwt_extended import create_access_token

GET_USER_BY_ID_PATH = "app.controllers.auth_controller._get_user_by_id"
DB_CONTEXT_PATH = "app.controllers.auth_controller.db"
GENERATE_HASH_PATH = "app.controllers.auth_controller.generate_password_hash"
CHECK_HASH_PATH = "app.controllers.auth_controller.check_password_hash"
OAUTH_PATH = "app.controllers.auth_controller.oauth"


def setup_db_mock(mock_db, fetchone_result=None, lastrowid=1):
    mock_conn = MagicMock()
    mock_cur = MagicMock()

    if isinstance(fetchone_result, list):
        mock_cur.fetchone.side_effect = fetchone_result
    else:
        mock_cur.fetchone.side_effect = [fetchone_result]

    mock_cur.lastrowid = lastrowid
    mock_conn.cursor.return_value = mock_cur
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    mock_db.return_value = mock_conn
    mock_db.return_value.__enter__.return_value = mock_conn
    return mock_conn, mock_cur


@patch(GENERATE_HASH_PATH)
@patch(DB_CONTEXT_PATH)
@patch(GET_USER_BY_ID_PATH)
def test_register_success(mock_get_user_by_id, mock_db, mock_generate_hash, client):
    mock_generate_hash.return_value = "hashed_password"
    _, mock_cur = setup_db_mock(mock_db, fetchone_result=[None, None], lastrowid=99)
    mock_get_user_by_id.return_value = {"id": 99, "email": "new@user.com", "nome": "New User"}

    payload = {"nome": "New User", "email": "new@user.com", "senha": "password123"}
    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 201
    data = response.get_json()
    assert data["ok"] is True
    assert data["user"]["id"] == 99
    assert "access_token" in data
    assert mock_cur.execute.called


@patch(DB_CONTEXT_PATH)
def test_register_user_exists(mock_db, client):
    setup_db_mock(mock_db, fetchone_result={"id": 1})

    payload = {"nome": "Existing", "email": "test@mock.com", "senha": "123"}
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 400


@patch(CHECK_HASH_PATH)
@patch(DB_CONTEXT_PATH)
@patch(GET_USER_BY_ID_PATH)
def test_login_success(mock_get_user_by_id, mock_db, mock_check_hash, client):
    mock_check_hash.return_value = True
    setup_db_mock(mock_db, fetchone_result={"id": 1, "password_hash": "hashed_123"})
    mock_get_user_by_id.return_value = {"id": 1, "nome": "Mock User"}

    payload = {"email": "test@mock.com", "senha": "password123"}
    response = client.post("/api/auth/login", json=payload)

    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    assert data["user"]["id"] == 1


@patch(DB_CONTEXT_PATH)
def test_login_user_not_found(mock_db, client):
    setup_db_mock(mock_db, fetchone_result=None)
    payload = {"email": "not@found.com", "senha": "password123"}
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 401


@patch(CHECK_HASH_PATH)
@patch(DB_CONTEXT_PATH)
def test_login_incorrect_password(mock_db, mock_check_hash, client):
    mock_check_hash.return_value = False
    setup_db_mock(mock_db, fetchone_result={"id": 1, "password_hash": "hashed"})
    payload = {"email": "test@mock.com", "senha": "wrong"}
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 401


def test_login_missing_fields(client):
    response = client.post("/api/auth/login", json={"email": "missing@pass.com"})
    assert response.status_code == 401


@patch(GET_USER_BY_ID_PATH)
def test_me_authenticated(mock_get_user_by_id, client):
    mock_get_user_by_id.return_value = {"id": 1, "nome": "Logged User", "email": "log@user.com", "avatar_url": None}

    with client.application.app_context():
        token = create_access_token(identity="1")

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["authenticated"] is True
    assert data["user"]["id"] == 1


def test_me_unauthenticated(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


@patch(OAUTH_PATH)
def test_login_google_redirect(mock_oauth, client, monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
    mock_oauth.google.authorize_redirect.return_value = ("", 302, {"Location": "http://g.co/auth"})

    response = client.get("/api/auth/google?next=/dashboard")
    assert response.status_code == 302


@patch("app.controllers.auth_controller.requests.get")
@patch(DB_CONTEXT_PATH)
@patch(OAUTH_PATH)
def test_google_callback_new_user(mock_oauth, mock_db, mock_requests_get, client):
    mock_oauth.google.safe_authorize_access_token.return_value = {"access_token": "access_123"}

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "email": "new_google@user.com",
        "name": "New Google User",
        "picture": "http://avatar.com/new",
        "sub": "google_id_123",
    }
    mock_requests_get.return_value = mock_response

    _, mock_cur = setup_db_mock(mock_db, fetchone_result=[None, None], lastrowid=100)
    response = client.get("/api/auth/google/callback")

    assert response.status_code == 302
    assert "#token=" in response.headers["Location"]
    assert mock_cur.lastrowid == 100


@patch("app.controllers.auth_controller.requests.get")
@patch(DB_CONTEXT_PATH)
@patch(OAUTH_PATH)
def test_google_callback_existing_user(mock_oauth, mock_db, mock_requests_get, client):
    mock_oauth.google.safe_authorize_access_token.return_value = {"access_token": "access_123"}

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "email": "existing@user.com",
        "sub": "google_id_123",
        "picture": "http://avatar.com/existing",
    }
    mock_requests_get.return_value = mock_response

    setup_db_mock(mock_db, fetchone_result=[None, (1,)])

    response = client.get("/api/auth/google/callback")

    assert response.status_code == 302
    mock_cur = mock_db.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
    mock_cur.execute.assert_any_call(
        "UPDATE usuarios SET google_sub=%s, avatar_url=%s WHERE id=%s",
        ("google_id_123", "http://avatar.com/existing", 1),
    )


@patch("app.controllers.auth_controller.requests.get")
@patch(OAUTH_PATH)
def test_google_callback_token_fail(mock_oauth, mock_requests_get, client):
    mock_oauth.google.safe_authorize_access_token.return_value = {}
    response = client.get("/api/auth/google/callback")

    assert response.status_code == 400
    assert response.get_json().get("error") == "OAuth failure"
