import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # --------------------------
    # CONFIGURAÇÕES DO SERVIDOR
    # --------------------------
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # JWT
    app.config['JWT_SECRET_KEY'] = os.environ.get("JWT_SECRET_KEY", "DEV_KEY_CHANGE_IN_PROD")
    app.config['JWT_TOKEN_LOCATION'] = ["headers"]
    app.config['JWT_HEADER_NAME'] = "Authorization"
    app.config['JWT_HEADER_TYPE'] = "Bearer"

    # FRONTEND EM PRODUÇÃO
    FRONT_HOME = os.environ.get(
        "FRONT_HOME",
        "https://trabalho-conclusao-curso-adoptme.vercel.app"
    )
    app.config["FRONT_HOME"] = FRONT_HOME

    # -------------------------
    # CORS (ESSENCIAL PARA JWT)
    # -------------------------
    CORS(app,
         resources={r"/api/*": {
             "origins": [FRONT_HOME],
         }},
         supports_credentials=False,
         expose_headers=["Authorization"]
    )

    # Inicializações
    db.init_app(app)
    migrate.init_app(app, db)
    JWTManager(app)

    # -------------------------
    # BLUEPRINTS
    # -------------------------
    from .auth_controller import auth_bp
    from .animais_controller import animais_bp
    from .perfil_controller import perfil_bp

    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(animais_bp, url_prefix="/api")
    app.register_blueprint(perfil_bp, url_prefix="/api")

    return app
