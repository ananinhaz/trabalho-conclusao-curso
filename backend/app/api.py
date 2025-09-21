from .controllers.usuario_controller import bp as usuarios_bp
from .controllers.animal_controller import bp as animais_bp

def register_blueprints(app):
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(animais_bp)
