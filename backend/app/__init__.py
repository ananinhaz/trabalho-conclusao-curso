# backend/app/__init__.py
import os
import urllib.parse
from flask import Flask, current_app
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

# keep your db/migrate vars if used elsewhere
db = SQLAlchemy()
migrate = Migrate()


def _normalize_database_url(url: str) -> str:
    if not url:
        return url
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    parsed = urllib.parse.urlsplit(url)
    qs = parsed.query
    if "sslmode=" not in qs:
        qs = (qs + "&sslmode=require") if qs else "sslmode=require"
        url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, qs, parsed.fragment))
    return url


def create_app():
    load_dotenv()
    app = Flask(__name__, instance_relative_config=False)

    #
    # IMPORTANT: set secret_key early so that `session` is available
    # (Authlib / Flask-OAuth requires session to store state).
    #
    # Provide FLASK_SECRET_KEY in Render (or SECRET_KEY). Fallback is a dev string.
    #
    app.secret_key = os.getenv("FLASK_SECRET_KEY") or os.getenv("SECRET_KEY") or "dev_secret_change_me"
    # Log presence only (do not log the secret value)
    app.logger.info("create_app: secret_key set? %s", bool(app.secret_key))

    # FRONT_HOME from env (used by oauth redirect construction and by CORS)
    FRONT_HOME = os.getenv("FRONT_HOME", "http://127.0.0.1:5173").rstrip("/")
    app.config["FRONT_HOME"] = FRONT_HOME

    # Database
    raw_db = os.getenv("DATABASE_URL")
    if raw_db:
        app.config['SQLALCHEMY_DATABASE_URI'] = _normalize_database_url(raw_db)
        app.logger.info("Using DATABASE_URL from env.")
    else:
        here = os.path.abspath(os.path.dirname(__file__))
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(here,'..','dev.db')}"
        app.logger.warning("No DATABASE_URL found — using sqlite fallback.")

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # JWT
    app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY", "DEV_JWT_SECRET_CHANGE_ME")
    jwt = JWTManager(app)

    # CORS: JWT flow DOES NOT require cookies -> disable credentials
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

    # preflight quick response
    from flask import request
    @app.before_request
    def _preflight():
        if request.method == "OPTIONS":
            return app.make_response(("", 200))

    # init oauth/db extensions if present (graceful)
    # NOTE: init_oauth must run after app.secret_key is set (so session works)
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

    # Register blueprints (import after app created to avoid cycles)
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

    # quick debug info in logs
    app.logger.info(
        "create_app: startup complete; FRONT_HOME=%s; GOOGLE_CLIENT_ID present=%s",
        FRONT_HOME,
        bool(os.getenv("GOOGLE_CLIENT_ID"))
    )

    return app


# expose for gunicorn
app = create_app()
