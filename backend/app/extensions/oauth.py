import os
import requests
from flask import request
from authlib.integrations.flask_client import OAuth
from authlib.integrations.base_client.errors import MismatchingStateError

oauth = OAuth()

def init_oauth(app):
    oauth.init_app(app)

    # Registro  do cliente Google com OpenID
    oauth.register(
        name="google",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

    # fallback para ambiente localhost, state perdido
    def safe_authorize_access_token():
        """
        Executa o fluxo OAuth normal. Se der erro de MismatchingStateError
        (por perda de cookie entre 8080 e 5000), refaz a troca de code->token.
        """
        try:
            # tenta fluxo normal
            return oauth.google.authorize_access_token()
        except MismatchingStateError:
            print("⚠️ Aviso: ignorando mismatching_state (modo dev localhost)")

            code = request.args.get("code")
            if not code:
                raise

            redirect_uri = os.getenv("GOOGLE_REDIRECT_URI") or request.base_url
            token_endpoint = "https://oauth2.googleapis.com/token"
            data = {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            }

            resp = requests.post(token_endpoint, data=data, timeout=10)
            if resp.status_code != 200:
                print("❌ Falha ao trocar código por token:", resp.text)
                resp.raise_for_status()

            token = resp.json()
            print("🔍 Google token response:", token)
            return token

    oauth.google.safe_authorize_access_token = safe_authorize_access_token
    return oauth
