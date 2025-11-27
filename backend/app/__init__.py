import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

from .health import health_bp

def create_app():
    load_dotenv()

    app = Flask(__name__)

    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret"),
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=False,
        SESSION_PERMANENT=False,

        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={"connect_args": {"sslmode": "require"}, "pool_pre_ping": True}
    )

    CORS(
        app,
        supports_credentials=True,
        resources={r"/*": {"origins": [
            "http://127.0.0.1:8080",
            "http://localhost:8080",
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ]}},
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        expose_headers=["Content-Type"],
    )

    @app.before_request
    def _preflight():
        if request.method == "OPTIONS":
            return app.make_response(("", 200))

    # extensões
    from .extensions.oauth import init_oauth
    init_oauth(app)

    from .extensions.db import init_db
    init_db(app)

    # blueprints
    from .controllers.auth_controller import bp as auth_bp
    app.register_blueprint(auth_bp)

    from .api import register_blueprints
    register_blueprints(app)

    # Registro do Blueprint de saúde
    app.register_blueprint(health_bp)

    @app.get("/")
    def index():
        return "API AdoptMe OK"

    return app

app = create_app()
