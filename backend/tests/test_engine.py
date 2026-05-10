import pandas as pd
from app.recommendation.engine import (
    _preferencias_porte,
    _energia_por_tempo_estilo,
    _split_columns,
    _build_feature_matrix,
    knn_rank,
)

def test_preferencias_porte_apartamento():
    prefs = _preferencias_porte("Apartamento")
    assert prefs["Pequeno"] == 1.0
    assert prefs["Grande"] == 0.0

def test_preferencias_porte_casa():
    prefs = _preferencias_porte("Casa")
    assert prefs["Grande"] == 1.0

def test_energia_por_tempo_tranquilo():
    result = _energia_por_tempo_estilo(5, "Tranquilo")
    assert result["Baixa"] == 1.0
    assert result["Alta"] == 0.0

def test_energia_por_tempo_ativo():
    result = _energia_por_tempo_estilo(20, "Ativo")
    assert result["Alta"] >= 1.0

def test_split_columns():
    df = pd.DataFrame(
        [{
            "id": 1,
            "nome": "Rex",
            "porte": "Medio",
            "energia": "Alta",
            "idade": 3,
            "bom_com_criancas": 1,
        }]
    )

    cat, num, passthrough = _split_columns(df)

    assert "porte" in cat
    assert "energia" in cat
    assert "idade" in num
    assert "id" in passthrough

def test_build_feature_matrix():
    df = pd.DataFrame(
        [
            {
                "id": 1,
                "nome": "Rex",
                "porte": "Medio",
                "energia": "Alta",
                "idade": 3,
                "bom_com_criancas": 1,
            }
        ]
    )

    X, meta, enc, scaler, cat_cols, num_cols = _build_feature_matrix(df)

    assert X.shape[0] == 1
    assert "id" in meta

def test_knn_rank_returns_results():
    animals = [
        {
            "id": 1,
            "nome": "Rex",
            "porte": "Medio",
            "energia": "Alta",
            "idade": 3,
            "bom_com_criancas": 1,
        },
        {
            "id": 2,
            "nome": "Luna",
            "porte": "Pequeno",
            "energia": "Baixa",
            "idade": 2,
            "bom_com_criancas": 1,
        },
    ]

    prefs = {
        "tipo_moradia": "Apartamento",
        "tempo_disponivel_horas_semana": 10,
        "estilo_vida": "Moderado",
        "tem_criancas": 1,
    }

    results = knn_rank(animals, prefs, top_n=2)

    assert len(results) == 2
    assert "_score" in results[0]
    assert "_rank" in results[0]

def test_knn_rank_empty():
    results = knn_rank([], {}, 5)
    assert results == []