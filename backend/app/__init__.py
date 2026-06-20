import os
from flask import Flask, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv


def create_app():
    load_dotenv()
    app = Flask(__name__, instance_relative_config=False)

    app.secret_key = os.getenv("FLASK_SECRET_KEY") or os.getenv("SECRET_KEY") or "dev_secret_change_me"
    # Log presence only (do not log the secret value)
    app.logger.info("create_app: secret_key set? %s", bool(app.secret_key))

    # FRONT_HOME from env (used by oauth redirect construction and by CORS)
    FRONT_HOME = os.getenv("FRONT_HOME", "http://127.0.0.1:5173").rstrip("/")
    app.config["FRONT_HOME"] = FRONT_HOME

    # JWT
    app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY", "DEV_JWT_SECRET_CHANGE_ME")
    jwt = JWTManager(app)

    allowed_origins = [
        "http://127.0.0.1:8080",
        "http://localhost:8080",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        FRONT_HOME,
    ]
    CORS(app,
     supports_credentials=False,
     resources={r"/api/*": {"origins": allowed_origins}},   # limitar ao /api
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
     expose_headers=["Content-Type", "Authorization"],
)

    @app.before_request
    def _preflight():
        if request.method == "OPTIONS":
            return app.make_response(("", 200))

    try:
        from .extensions.oauth import init_oauth
        init_oauth(app)
        app.logger.info("OAuth extension initialized.")
    except Exception as e:
        app.logger.info("No oauth extension initialized or failed: %s", str(e))

    try:
        from .extensions.db import init_db
        init_db(app)
        app.logger.info("DB extension initialized.")
    except Exception as e:
        app.logger.exception("DB init failed (will still start): %s", e)

    # Registra blueprints 
    try:
        from .controllers.auth_controller import bp as auth_bp
        app.register_blueprint(auth_bp, url_prefix="/api/auth")
    except Exception as e:
        app.logger.exception("Failed to register auth_controller: %s", e)
        raise

    try:
        from .api import register_blueprints
        register_blueprints(app)
    except Exception:
        app.logger.info("No api.register_blueprints available; skipping.")

    # root status (responde na raiz para indicar que o backend está OK)
    @app.route("/", methods=["GET"])
    def root_status():
        return "AdoptMe OK", 200

    # health
    @app.get("/health")
    def health():
        return "ok", 200

    app.logger.info(
        "create_app: startup complete; FRONT_HOME=%s; GOOGLE_CLIENT_ID present=%s",
        FRONT_HOME,
        bool(os.getenv("GOOGLE_CLIENT_ID"))
    )

    return app

