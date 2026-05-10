import pytest
import requests
from unittest.mock import patch, MagicMock
from flask import Flask
from authlib.integrations.base_client.errors import MismatchingStateError
from app.extensions.oauth import init_oauth, oauth


@pytest.fixture
def app_oauth():
    app = Flask(__name__)
    app.config["GOOGLE_CLIENT_ID"] = "fake-id"
    app.config["GOOGLE_CLIENT_SECRET"] = "fake-secret"
    app.config["GOOGLE_REDIRECT_URI"] = "http://localhost/callback"
    init_oauth(app)
    return app


def test_init_oauth_registers_google(app_oauth):
    assert "google" in oauth._registry


def test_safe_token_standard_flow(app_oauth):
    with patch.object(oauth.google, "authorize_access_token") as mock_auth:
        expected_token = {"access_token": "valid_token"}
        mock_auth.return_value = expected_token

        token = oauth.google.safe_authorize_access_token()

        assert token == expected_token
        mock_auth.assert_called_once()


def test_safe_token_fallback_success(app_oauth):
    with patch.object(oauth.google, "authorize_access_token") as mock_auth:
        mock_auth.side_effect = MismatchingStateError()

        with app_oauth.test_request_context("/callback?code=my_auth_code"):
            with patch.object(
                oauth.google,
                "load_server_metadata",
                return_value={
                    "token_endpoint": "https://oauth.test/token",
                    "userinfo_endpoint": "https://oauth.test/userinfo",
                },
            ):
                with patch("app.extensions.oauth.requests.post") as mock_post:
                    mock_resp = MagicMock()
                    mock_resp.status_code = 200
                    mock_resp.json.return_value = {"access_token": "manual_fallback_token"}
                    mock_post.return_value = mock_resp

                    token = oauth.google.safe_authorize_access_token()

                    assert token["access_token"] == "manual_fallback_token"
                    _, kwargs = mock_post.call_args
                    assert kwargs["data"]["code"] == "my_auth_code"
                    assert kwargs["data"]["grant_type"] == "authorization_code"


def test_safe_token_fallback_no_code(app_oauth):
    with patch.object(oauth.google, "authorize_access_token") as mock_auth:
        mock_auth.side_effect = MismatchingStateError()

        with app_oauth.test_request_context("/callback"):
            with pytest.raises(MismatchingStateError):
                oauth.google.safe_authorize_access_token()


def test_safe_token_fallback_request_fail(app_oauth):
    with patch.object(oauth.google, "authorize_access_token") as mock_auth:
        mock_auth.side_effect = MismatchingStateError()

        with app_oauth.test_request_context("/callback?code=bad_code"):
            with patch.object(
                oauth.google,
                "load_server_metadata",
                return_value={
                    "token_endpoint": "https://oauth.test/token",
                    "userinfo_endpoint": "https://oauth.test/userinfo",
                },
            ):
                with patch("app.extensions.oauth.requests.post") as mock_post:
                    mock_resp = MagicMock()
                    mock_resp.status_code = 400
                    mock_resp.text = "Bad Request"
                    mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError("Boom")
                    mock_post.return_value = mock_resp

                    with pytest.raises(requests.exceptions.HTTPError):
                        oauth.google.safe_authorize_access_token()
