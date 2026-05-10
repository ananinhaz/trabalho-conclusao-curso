from flask import Flask

from app.controllers import usuario_controller as uc


def test_usuario_controller_stub_functions():
    app = Flask(__name__)
    with app.app_context():
        r1, s1 = uc.list_usuarios()
        r2, s2 = uc.get_usuario_by_id(10)
        r3, s3 = uc.update_usuario(10)

    assert s1 == 404
    assert s2 == 404
    assert s3 == 404
    assert r2.get_json()["id"] == 10
