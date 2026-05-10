import base64
import json

from flask import Flask, session

import app.api as api_mod


def _jwt(payload: dict) -> str:
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return f"x.{body}.y"


def test_decode_jwt_payload_no_verify_valid_and_invalid():
    token = _jwt({"user_id": 7})
    assert api_mod._decode_jwt_payload_no_verify(token)["user_id"] == 7
    assert api_mod._decode_jwt_payload_no_verify("bad") == {}


def test_validate_and_get_payload_paths(monkeypatch):
    monkeypatch.setattr(api_mod, "JWT_SECRET", None)
    assert api_mod._validate_and_get_payload(_jwt({"id": 3}))["id"] == 3

    class FakeJwt:
        @staticmethod
        def decode(token, secret, algorithms=None):
            return {"sub": "9"}

    monkeypatch.setattr(api_mod, "JWT_SECRET", "secret")
    monkeypatch.setattr(api_mod, "pyjwt", FakeJwt)
    assert api_mod._validate_and_get_payload("any")["sub"] == "9"



def test_require_auth_sources(monkeypatch):
    app = Flask(__name__)
    app.secret_key = "x"

    with app.test_request_context("/"):
        session["user_id"] = "5"
        assert api_mod._require_auth() == 5

    with app.test_request_context("/", headers={"Authorization": "Bearer 12"}):
        assert api_mod._require_auth() == 12

    monkeypatch.setattr(api_mod, "_validate_and_get_payload", lambda _t: {"sub": "8"})
    with app.test_request_context("/", headers={"Authorization": "Bearer token"}):
        assert api_mod._require_auth() == 8

    with app.test_request_context("/", headers={"Authorization": "Basic x"}):
        assert api_mod._require_auth() is None



def test_normalizers_and_vectors():
    assert api_mod.to_bool_like(True) is True
    assert api_mod.to_bool_like("sim") is True
    assert api_mod.to_bool_like(None) is False

    assert api_mod._normalize_to_int_bool(True) == 1
    assert api_mod._normalize_to_int_bool("0") == 0
    assert api_mod._normalize_to_int_bool(None) is None

    uvec = api_mod._build_user_vector(
        {
            "tipo_moradia": "Apartamento",
            "tem_criancas": "1",
            "tempo_disponivel_horas_semana": "10",
            "estilo_vida": "moderado",
        }
    )
    assert len(uvec) == 4

    avec = api_mod._build_animal_vector(
        {
            "especie": "Cachorro",
            "porte": "medio",
            "idade": "2",
            "bom_com_criancas": 1,
        }
    )
    assert len(avec) == 4



def test_row_payload_helpers():
    row = {
        "id": 1,
        "nome": "A",
        "especie": "Gato",
        "raca": None,
        "idade": "1",
        "porte": "pequeno",
        "descricao": "d",
        "cidade": "c",
        "photo_url": None,
        "donor_name": "n",
        "donor_whatsapp": "w",
        "doador_id": 2,
        "created_at": None,
        "energia": "alta",
        "bom_com_criancas": "true",
        "adotado_em": None,
    }
    payload = api_mod._row_to_animal(row)
    assert payload["bom_com_criancas"] == 1

    rows_payload = api_mod._rows_to_payload([row], [1])
    assert rows_payload["ids"] == [1]
