import pytest
from unittest.mock import patch, MagicMock

import backend.app.services.recommendation_service as rsvc

@pytest.fixture
def mock_get_conn():
    with patch("backend.app.services.recommendation_service.get_conn") as m:
        yield m

@pytest.fixture
def mock_knn_rank():
    with patch("backend.app.services.recommendation_service.knn_rank") as m:
        yield m

@pytest.mark.parametrize(
    "usuario_id,params,profile_result,params_override,expected",
    [
        # No usuario_id, no params: should default
        (
            None,
            {},
            None,
            {},
            {
                "tipo_moradia": "Apartamento",
                "tem_criancas": 0,
                "tempo_disponivel_horas_semana": 7,
                "estilo_vida": "Moderado",
                "especie_pref": None
            }
        ),
        # usuario_id, db returns row, nothing overridden
        (
            1,
            {},
            {
                "tipo_moradia": "Casa",
                "tem_criancas": 1,
                "tempo_disponivel_horas_semana": 15,
                "estilo_vida": "Ativo"
            },
            {},
            {
                "tipo_moradia": "Casa",
                "tem_criancas": 1,
                "tempo_disponivel_horas_semana": 15,
                "estilo_vida": "Ativo",
                "especie_pref": None
            }
        ),
        # usuario_id, db returns row, params overrides all
        (
            1,
            {
                "tipo_moradia": "Sitio",
                "tem_criancas": "0",
                "tempo_disponivel_horas_semana": "22",
                "estilo_vida": "Tranquilo",
                "especie_pref": "Cachorro"
            },
            {
                "tipo_moradia": "Casa",
                "tem_criancas": 1,
                "tempo_disponivel_horas_semana": 15,
                "estilo_vida": "Ativo"
            },
            {},
            {
                "tipo_moradia": "Sitio",
                "tem_criancas": 0,
                "tempo_disponivel_horas_semana": 22,
                "estilo_vida": "Tranquilo",
                "especie_pref": "Cachorro"
            }
        ),
        # usuario_id, db returns row with some nulls
        (
            2,
            {},
            {"tipo_moradia": None, "tem_criancas": None, "tempo_disponivel_horas_semana": None, "estilo_vida": None},
            {},
            {
                "tipo_moradia": "Apartamento",
                "tem_criancas": 0,
                "tempo_disponivel_horas_semana": 7,
                "estilo_vida": "Moderado",
                "especie_pref": None,
            }
        ),
        # usuario_id, exception in db fetch (should fallback, not raise)
        (
            3,
            {},
            Exception("fail"),
            {},
            {
                "tipo_moradia": "Apartamento",
                "tem_criancas": 0,
                "tempo_disponivel_horas_semana": 7,
                "estilo_vida": "Moderado",
                "especie_pref": None
            }
        ),
        # usuario_id is zero (should treat as no id)
        (
            0,
            {},
            None,
            {},
            {
                "tipo_moradia": "Apartamento",
                "tem_criancas": 0,
                "tempo_disponivel_horas_semana": 7,
                "estilo_vida": "Moderado",
                "especie_pref": None
            }
        ),
    ]
)
def test_carregar_prefs(usuario_id, params, profile_result, params_override, expected, mock_get_conn):
    if isinstance(profile_result, Exception):
        mock_get_conn.side_effect = profile_result
    elif profile_result is not None:
        # Patch db returning a profile_result dict
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = profile_result
        mock_cur.close.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_conn.close.return_value = None
        mock_get_conn.return_value = mock_conn
    else:
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = None
        mock_cur.close.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_conn.close.return_value = None
        mock_get_conn.return_value = mock_conn

    # Add additional keys to params if needed
    params.update(params_override)
    result = rsvc._carregar_prefs(usuario_id, params)
    assert result == expected

def test_carregar_prefs_params_cast(mock_get_conn):
    # Should cast string params to int
    params = {
        "tipo_moradia": "Apartamento",
        "tem_criancas": "1",
        "tempo_disponivel_horas_semana": "11",
        "estilo_vida": "Ativo",
        "especie_pref": "Cachorro"
    }
    mock_get_conn.return_value = MagicMock()  # shouldn't be called
    result = rsvc._carregar_prefs(None, dict(params))
    assert result == {
        "tipo_moradia": "Apartamento",
        "tem_criancas": 1,
        "tempo_disponivel_horas_semana": 11,
        "estilo_vida": "Ativo",
        "especie_pref": "Cachorro"
    }

def test_carregar_prefs_db_row_partially_overrides(mock_get_conn):
    # Params has value, db row (for some fields) has non-null, but not 'especie_pref'
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = {
        "tipo_moradia": "Casa",
        "tem_criancas": 0,
        "tempo_disponivel_horas_semana": None,
        "estilo_vida": "Ativo"
    }
    mock_cur.close.return_value = None
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_conn.close.return_value = None
    mock_get_conn.return_value = mock_conn

    params = {
        "tipo_moradia": None,
        "tem_criancas": "1",
        "tempo_disponivel_horas_semana": None,
        "estilo_vida": None,
        "especie_pref": "Gato"
    }
    # It combines: tipo_moradia from db, tem_criancas param cast, tempo_disponivel_horas_semana fallback, estilo_vida from db, especie_pref param
    result = rsvc._carregar_prefs(77, dict(params))
    assert result == {
        "tipo_moradia": "Casa",
        "tem_criancas": 0,
        "tempo_disponivel_horas_semana": 7,
        "estilo_vida": "Ativo",
        "especie_pref": "Gato"
    }

def test_carregar_animais_returns_rows(mock_get_conn):
    # Patches db to return two "animals"
    mock_cur = MagicMock()
    rows = [
        {"id": 1, "nome": "Rex", "especie": "Cachorro", "idade": 2, "porte": "M", "energia": "Alta", "bom_com_criancas": 1, "cidade": "SP", "disponivel": 1},
        {"id": 3, "nome": "Luna", "especie": "Gato", "idade": 3, "porte": "P", "energia": "Média", "bom_com_criancas": 0, "cidade": "RJ", "disponivel": 1},
    ]
    mock_cur.fetchall.return_value = rows
    mock_cur.close.return_value = None
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_conn.close.return_value = None
    mock_get_conn.return_value = mock_conn

    result = rsvc._carregar_animais()
    assert result == rows
    mock_cur.execute.assert_called_once()
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()

def test_carregar_animais_empty(mock_get_conn):
    # Returns empty list when no animals
    mock_cur = MagicMock()
    mock_cur.fetchall.return_value = []
    mock_cur.close.return_value = None
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_conn.close.return_value = None
    mock_get_conn.return_value = mock_conn
    result = rsvc._carregar_animais()
    assert result == []

def test_carregar_animais_db_exception(mock_get_conn):
    # Simulate db connection error
    mock_get_conn.side_effect = Exception("Database unavailable")
    with pytest.raises(Exception):
        rsvc._carregar_animais()

def test_recomendar_calls_internal_and_knn(mock_get_conn, mock_knn_rank):
    # Test normal operation
    mock_knn_rank.return_value = ["result"]
    # Patch _carregar_animais and _carregar_prefs to control returns
    with patch.object(rsvc, "_carregar_animais", return_value=[{"id": 1}]) as mock_animais, \
         patch.object(rsvc, "_carregar_prefs", return_value={"tipo_moradia": "Apartamento"}) as mock_prefs:
        res = rsvc.recomendar(5, {"param": "val"}, top_n=2)
        assert res == ["result"]
        mock_animais.assert_called_once()
        mock_prefs.assert_called_once_with(5, {"param": "val"})
        mock_knn_rank.assert_called_once_with([{"id": 1}], {"tipo_moradia": "Apartamento"}, top_n=2)

def test_recomendar_empty_animals(mock_get_conn, mock_knn_rank):
    mock_knn_rank.return_value = []
    with patch.object(rsvc, "_carregar_animais", return_value=[]), \
         patch.object(rsvc, "_carregar_prefs", return_value={}):
        res = rsvc.recomendar(None, {})
        assert res == []
        mock_knn_rank.assert_called_once()

def test_recomendar_knn_raises(mock_get_conn, mock_knn_rank):
    # Simulate knn_rank raising an error
    mock_knn_rank.side_effect = RuntimeError("fail")
    with patch.object(rsvc, "_carregar_animais", return_value=[{"id": 1}]), \
         patch.object(rsvc, "_carregar_prefs", return_value={"tipo_moradia": "Apartamento"}):
        with pytest.raises(RuntimeError):
            rsvc.recomendar(1, {}, top_n=5)