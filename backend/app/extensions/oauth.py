# backend/app/extensions/oauth.py
from __future__ import annotations
import os
import logging
from typing import Optional, Dict, Any

from authlib.integrations.flask_client import OAuth
from authlib.integrations.base_client.errors import MismatchingStateError
import requests
from flask import current_app, request

oauth = OAuth()
logger = logging.getLogger("app.oauth")

def init_oauth(app):
    """
    Inicializa oauth e registra provider 'google' usando discovery (OIDC).
    Deixa disponível `oauth.google.safe_authorize_access_token()` (implementado aqui).
    """
    oauth.init_app(app)

    # configurações principais (pegar de env)
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    # optional redirect env (used by controller to build redirect statically)
    redirect_uri_env = os.getenv("GOOGLE_REDIRECT_URI") or os.getenv("GOOGLE_CALLBACK")

    # Register google using OpenID Connect discovery metadata (recommended)
    # If discovery fails for any reason, register minimal endpoints later.
    try:
        oauth.register(
            name="google",
            client_id=client_id,
            client_secret=client_secret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
        logger.info("oauth: registered google provider using OIDC discovery.")
    except Exception as e:
        # fallback: try basic registration if discovery fails (still works if you supply endpoints)
        logger.exception("oauth: discovery registration failed: %s", e)
        # you can set explicit endpoints if needed via envs
        token_endpoint = os.getenv("GOOGLE_TOKEN_ENDPOINT", "https://oauth2.googleapis.com/token")
        userinfo_endpoint = os.getenv("GOOGLE_USERINFO_ENDPOINT", "https://openidconnect.googleapis.com/v1/userinfo")
        authorize_endpoint = os.getenv("GOOGLE_AUTH_ENDPOINT", "https://accounts.google.com/o/oauth2/v2/auth")

        oauth.register(
            name="google",
            client_id=client_id,
            client_secret=client_secret,
            access_token_url=token_endpoint,
            authorize_url=authorize_endpoint,
            client_kwargs={"scope": "openid email profile"},
            userinfo_endpoint=userinfo_endpoint,
        )
        logger.info("oauth: registered google provider with manual endpoints.")

    # enhance google client with safe_authorize_access_token fallback
    _patch_safe_authorize(oauth.google)


def _patch_safe_authorize(google_client):
    """
    Add safe_authorize_access_token() method to the client instance.
    It will attempt authlib's authorize_access_token() first and if a
    MismatchingStateError occurs it will perform a manual token exchange
    (POST to token endpoint) using the 'code' query param.
    The returned value is a dict similar to authlib token dict.
    """
    def safe_authorize_access_token():
        # try normal flow first
        try:
            return google_client.authorize_access_token()
        except MismatchingStateError as mse:
            current_app.logger.warning("oauth: safe_authorize_access_token: MismatchingStateError - attempting manual token exchange: %s", mse)
            # fallback manual token exchange
            code = request.args.get("code")
            if not code:
                raise

            # determine token endpoint
            token_endpoint = None
            userinfo_endpoint = None
            try:
                md = google_client.load_server_metadata()
                token_endpoint = md.get("token_endpoint")
                userinfo_endpoint = md.get("userinfo_endpoint") or md.get("userinfo_endpoint")  # try both
            except Exception:
                token_endpoint = getattr(google_client, "access_token_url", None) or os.getenv("GOOGLE_TOKEN_ENDPOINT")
                userinfo_endpoint = os.getenv("GOOGLE_USERINFO_ENDPOINT", "https://openidconnect.googleapis.com/v1/userinfo")

            if not token_endpoint:
                raise RuntimeError("No token endpoint available for manual exchange")

            data = {
                "code": code,
                "client_id": google_client.client_id,
                "client_secret": google_client.client_secret,
                "redirect_uri": (os.getenv("GOOGLE_REDIRECT_URI") or request.base_url),
                "grant_type": "authorization_code",
            }
            headers = {"Accept": "application/json"}
            resp = requests.post(token_endpoint, data=data, headers=headers, timeout=10)
            # if non-200 raise HTTPError so controller logs properly
            resp.raise_for_status()
            token_json = resp.json()
            # augment token_json with token_type if missing
            if "token_type" not in token_json:
                token_json["token_type"] = "Bearer"
            # Attach userinfo endpoint for later use if available
            token_json["_userinfo_endpoint"] = userinfo_endpoint
            return token_json

    # attach to client
    setattr(google_client, "safe_authorize_access_token", safe_authorize_access_token)
