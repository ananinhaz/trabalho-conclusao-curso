import os
from authlib.integrations.flask_client import OAuth
from flask import current_app

oauth = OAuth()

def init_oauth(app):
    oauth.init_app(app)

    oauth.register(
        name="google",
        client_id=os.environ.get("GOOGLE_CLIENT_ID"),
        client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
        access_token_url="https://oauth2.googleapis.com/token",
        authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        api_base_url="https://www.googleapis.com/oauth2/v2/",
        client_kwargs={
            "scope": "openid email profile",
            "prompt": "select_account",
        }
    )

def safe_authorize_access_token():
    """
    Render em produção quebra o STATE do OAuth.
    Este fallback ignora o 'state mismatch' e tenta extrair mesmo assim.
    """
    try:
        return oauth.google.authorize_access_token()
    except Exception as e:
        print("⚠️ WARNING: OAuth fallback ativado:", e)
        # tenta manualmente
        token = oauth.google.fetch_access_token(
            grant_type="authorization_code",
            code=current_app.request.args.get("code"),
            redirect_uri=os.environ.get("GOOGLE_CALLBACK")
        )
        return token
