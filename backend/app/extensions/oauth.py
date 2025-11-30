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
    # Preferir variáveis explícitas, se não houver, ficará None
    redirect_uri_env = (os.getenv("GOOGLE_REDIRECT_URI") or os.getenv("GOOGLE_CALLBACK") or "").strip() or None

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
        """
        Tenta o authorize_access_token padrão; se der MismatchingStateError,
        faz a troca manual POST ao endpoint de token do Google usando
        o redirect URI vindo da env (se disponível).
        """
        try:
            return oauth.google.authorize_access_token()
        except MismatchingStateError:
            current_app.logger.warning("safe_authorize_access_token: MismatchingStateError - tentando fallback manual.")
            code = request.args.get("code")
            if not code:
                current_app.logger.error("safe_authorize_access_token: code ausente nos args; abortando.")
                raise

            # **Importante**: forçar o uso do redirect_uri vindo da env para evitar invalid_grant
            if redirect_uri_env:
                redirect_uri = redirect_uri_env
            else:
                # Se não tiver env configurada, usar request.base_url como último recurso (pode causar invalid_grant)
                current_app.logger.warning(
                    "safe_authorize_access_token: GOOGLE_REDIRECT_URI/GOOGLE_CALLBACK não definido; usando request.base_url como fallback (pode falhar)."
                )
                redirect_uri = request.base_url

            token_endpoint = "https://oauth2.googleapis.com/token"
            data = {
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            }

            current_app.logger.info(
                "safe_authorize_access_token: POSTing to token endpoint; redirect_uri=%s", redirect_uri
            )

            try:
                resp = requests.post(token_endpoint, data=data, timeout=10)
            except Exception as e:
                current_app.logger.exception("safe_authorize_access_token: request to token endpoint failed: %s", e)
                raise

            # Log status e preview do corpo (não logar client_secret)
            body_preview = (resp.text[:500] + "...") if resp.text and len(resp.text) > 500 else (resp.text or "<empty>")
            current_app.logger.info(
                "safe_authorize_access_token: token endpoint returned status=%s body_preview=%s",
                resp.status_code, body_preview
            )

            if resp.status_code != 200:
                # registra o corpo completo em error (útil para debugging), depois raise
                current_app.logger.error("safe_authorize_access_token: fallback token endpoint returned %s: %s", resp.status_code, resp.text)
                resp.raise_for_status()

            try:
                token = resp.json()
            except ValueError:
                current_app.logger.error("safe_authorize_access_token: token endpoint returned non-json body: %s", resp.text)
                raise

            current_app.logger.debug("safe_authorize_access_token: token keys: %s", list(token.keys()))
            return token

    # Anexa o fallback ao provider (tenta em tempo de execução)
    try:
        oauth.google.safe_authorize_access_token = safe_authorize_access_token
    except Exception:
        app.logger.exception("init_oauth: não foi possível anexar safe_authorize_access_token ao provider google.")
