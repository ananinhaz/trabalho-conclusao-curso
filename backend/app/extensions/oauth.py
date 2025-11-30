# backend/app/extensions/oauth.py
import os
import requests
from flask import request, current_app
from authlib.integrations.flask_client import OAuth
from authlib.integrations.base_client.errors import MismatchingStateError

oauth = OAuth()

def init_oauth(app):
    """
    Inicializa o OAuth e registra o provider 'google' apenas se as envs necessárias existirem.
    Anexa um fallback safe_authorize_access_token para lidar com MismatchingStateError em alguns setups.
    """
    oauth.init_app(app)

    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri_env = os.getenv("GOOGLE_REDIRECT_URI") or os.getenv("GOOGLE_CALLBACK")

    if not client_id or not client_secret:
        app.logger.warning("init_oauth: GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET ausentes — provider google NÃO será registrado.")
        return

    try:
        oauth.register(
            name="google",
            client_id=client_id,
            client_secret=client_secret,
            # Using OpenID Connect discovery for endpoints
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
        app.logger.info("init_oauth: provider 'google' registrado.")
    except Exception as exc:
        app.logger.exception("init_oauth: falha ao registrar provider google: %s", exc)
        return

    # Fallback para troca code -> token caso haja MismatchingStateError (cookies/session perdidos)
    def safe_authorize_access_token():
        try:
            return oauth.google.authorize_access_token()
        except MismatchingStateError:
            current_app.logger.warning("safe_authorize_access_token: MismatchingStateError - tentando fallback manual.")
            code = request.args.get("code")
            if not code:
                raise

            # Prioriza redirect uri definido em env; caso contrário usa request.base_url (callback)
            redirect_uri = redirect_uri_env or request.base_url
            token_endpoint = "https://oauth2.googleapis.com/token"
            data = {
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            }

            resp = requests.post(token_endpoint, data=data, timeout=10)
            if resp.status_code != 200:
                current_app.logger.error(
                    "safe_authorize_access_token: fallback token endpoint returned %s: %s",
                    resp.status_code, resp.text
                )
                resp.raise_for_status()

            token = resp.json()
            current_app.logger.debug("safe_authorize_access_token: token keys: %s", list(token.keys()))
            return token

    # Anexa o fallback ao provider
    try:
        oauth.google.safe_authorize_access_token = safe_authorize_access_token
    except Exception:
        app.logger.exception("init_oauth: não foi possível anexar safe_authorize_access_token ao provider google.")
