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

    # FRONT_HOME from env (used by oauth redirect construction and by CORS)
    FRONT_HOME = os.getenv("FRONT_HOME", "http://127.0.0.1:5173").rstrip("/")

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
         resources={r"/*": {"origins": allowed_origins}},
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         expose_headers=["Content-Type", "Authorization"],
         )

    # preflight quick response
    from flask import request
    @app.before_request
    def _preflight():
        if request.method == "OPTIONS":
            return app.make_response(("", 200))

    # init oauth/db extensions if present (graceful)
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

    # health
    @app.get("/health")
    def health():
        return "ok", 200

    return app

# expose for gunicorn
app = create_app()
