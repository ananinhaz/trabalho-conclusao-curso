from __future__ import annotations

from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, MinMaxScaler
from sklearn.neighbors import NearestNeighbors

# =========================
# Pesos por atributo
# =========================
WEIGHTS: Dict[str, float] = {
    "porte":   1.0,   # moradia -> porte (reduzido para dar destaque à energia)
    "energia": 6.0,   # muito forte
    "criancas": 3.5,  # forte
    "especie": 0.0,   # neutro (por ora)
    "idade":   0.0,   # neutro (não influencia)
}

# -------------------------
# Mapeamentos do PERFIL
# -------------------------
def _preferencias_porte(tipo_moradia: str | None) -> Dict[str, float]:
    """
    Preferência de porte baseada em moradia.
    Banco usa ENUM sem acento: Pequeno, Medio, Grande.
    """
    t = (tipo_moradia or "").strip().capitalize()
    if t == "Apartamento":
        return {"Pequeno": 1.0, "Medio": 0.5, "Grande": 0.0}
    # Casa (default)
    return {"Pequeno": 0.4, "Medio": 0.8, "Grande": 1.0}


def _energia_por_tempo_estilo(horas_semana: int | None, estilo_vida: str | None) -> Dict[str, float]:
    """
    Preferência de energia do animal considerando tempo disponível e estilo de vida.
    Banco usa ENUM sem acento: Baixa, Media, Alta.
    """
    if horas_semana is None:
        horas_semana = 7

    # base por tempo disponível
    if horas_semana <= 6:
        base = {"Baixa": 1.0, "Media": 0.0, "Alta": 0.0}
    elif horas_semana <= 14:
        base = {"Baixa": 0.4, "Media": 1.0, "Alta": 0.5}
    else:
        base = {"Baixa": 0.0, "Media": 0.6, "Alta": 1.0}

    # ajuste por estilo
    est = (estilo_vida or "").strip().capitalize()
    if est == "Tranquilo":
        base["Baixa"] = max(base["Baixa"], 1.0)
        base["Media"] = 0.0
        base["Alta"]  = 0.0
    elif est == "Ativo":
        base["Alta"]  = max(base["Alta"], 1.0)
        base["Media"] *= 0.8
        base["Baixa"] *= 0.3
    # Moderado mantém

    return base


# -------------------------
# Seleção de colunas
# -------------------------
def _split_columns(df: pd.DataFrame) -> Tuple[List[str], List[str], List[str]]:
    cat_cols: List[str] = []
    num_cols: List[str] = []
    passthrough_cols: List[str] = []

    # Categóricas principais
    if "porte" in df.columns:
        cat_cols.append("porte")
    if "energia" in df.columns:
        cat_cols.append("energia")
    # Opcional (neutro no score no momento)
    if "especie" in df.columns:
        cat_cols.append("especie")

    # Numéricas
    if "bom_com_criancas" in df.columns:
        num_cols.append("bom_com_criancas")  # 0/1
    if "idade" in df.columns:
        num_cols.append("idade")

    for c in ("id", "nome"):
        if c in df.columns:
            passthrough_cols.append(c)

    return cat_cols, num_cols, passthrough_cols


# -------------------------
# Construção da matriz dos ANIMAIS (fit)
# -------------------------
def _build_feature_matrix(df_anim: pd.DataFrame):
    cat_cols, num_cols, _ = _split_columns(df_anim)

    enc = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    X_cat = enc.fit_transform(df_anim[cat_cols]) if cat_cols else np.zeros((len(df_anim), 0))

    scaler = MinMaxScaler()
    X_num = scaler.fit_transform(df_anim[num_cols]) if num_cols else np.zeros((len(df_anim), 0))

    # Aplica pesos por atributo
    blocks: List[np.ndarray] = []
    if X_cat.shape[1] > 0:
        cat_names = enc.get_feature_names_out(cat_cols)
        Xc = X_cat.copy()
        for j, name in enumerate(cat_names):
            if name.startswith("porte_"):
                Xc[:, j] *= WEIGHTS["porte"]
            elif name.startswith("energia_"):
                Xc[:, j] *= WEIGHTS["energia"]
            elif name.startswith("especie_"):
                Xc[:, j] *= WEIGHTS["especie"]
        blocks.append(Xc)

    if X_num.shape[1] > 0:
        Xn = X_num.copy()
        for k, col in enumerate(num_cols):
            if col == "bom_com_criancas":
                Xn[:, k] *= WEIGHTS["criancas"]
            elif col == "idade":
                Xn[:, k] *= WEIGHTS["idade"]
        blocks.append(Xn)

    X_anim = np.concatenate(blocks, axis=1) if blocks else np.zeros((len(df_anim), 0))

    meta = {
        "id": df_anim["id"].to_numpy() if "id" in df_anim else np.arange(len(df_anim)),
        "nome": df_anim["nome"].to_numpy() if "nome" in df_anim else np.array([""] * len(df_anim)),
    }
    return X_anim, meta, enc, scaler, cat_cols, num_cols


# -------------------------
# Vetor do USUÁRIO (mesmo espaço das features dos animais)
# -------------------------
def _build_user_vector(
    prefs: Dict[str, Any],
    enc: OneHotEncoder,
    scaler: MinMaxScaler,
    cat_cols: List[str],
    num_cols: List[str],
) -> np.ndarray:
    # Preferências distribuídas (categorias)
    pref_porte = _preferencias_porte(prefs.get("tipo_moradia")) if "porte" in cat_cols else {}
    pref_energia = _energia_por_tempo_estilo(
        prefs.get("tempo_disponivel_horas_semana"),
        prefs.get("estilo_vida"),
    ) if "energia" in cat_cols else {}
    especie_pref = prefs.get("especie_pref") if "especie" in cat_cols else None

    # Linha nominal para o encoder
    row_cat: Dict[str, Any] = {}
    if "porte" in cat_cols:
        row_cat["porte"] = next(iter(pref_porte)) if pref_porte else None
    if "energia" in cat_cols:
        row_cat["energia"] = next(iter(pref_energia)) if pref_energia else None
    if "especie" in cat_cols:
        row_cat["especie"] = especie_pref

    # Numéricas
    row_num: Dict[str, Any] = {}
    if "bom_com_criancas" in num_cols:
        # Se tem crianças, preferência forte por 1.0. Sem crianças: 0.5 (neutro).
        row_num["bom_com_criancas"] = 1.0 if int(prefs.get("tem_criancas", 0)) == 1 else 0.5
    if "idade" in num_cols:
        # neutro ~ meio da escala (sem efeito no score por WEIGHTS)
        row_num["idade"] = 5

    df_u_cat = pd.DataFrame([row_cat]) if row_cat else pd.DataFrame([{}])
    df_u_num = pd.DataFrame([row_num]) if row_num else pd.DataFrame([{}])

    # Transformações
    if cat_cols:
        for c in cat_cols:
            if c not in df_u_cat.columns:
                df_u_cat[c] = None
        X_cat_u = enc.transform(df_u_cat[cat_cols])
        cat_names = enc.get_feature_names_out(cat_cols)

        # Zera todas as categorias de energia/porte/especie antes de setar (segurança)
        for j, name in enumerate(cat_names):
            if name.startswith("porte_") or name.startswith("energia_") or name.startswith("especie_"):
                X_cat_u[0, j] = 0.0

        # Injetar distribuição de preferências diretamente nos one-hot (com pesos)
        for j, name in enumerate(cat_names):
            if name.startswith("porte_"):
                k = name.split("porte_")[1]
                X_cat_u[0, j] = pref_porte.get(k, 0.0) * WEIGHTS["porte"]
            elif name.startswith("energia_"):
                k = name.split("energia_")[1]
                X_cat_u[0, j] = pref_energia.get(k, 0.0) * WEIGHTS["energia"]
            elif name.startswith("especie_"):
                k = name.split("especie_")[1]
                X_cat_u[0, j] = (1.0 * WEIGHTS["especie"]) if (especie_pref and k == especie_pref) else 0.0
    else:
        X_cat_u = np.zeros((1, 0))

    if num_cols:
        for c in num_cols:
            if c not in df_u_num.columns:
                df_u_num[c] = 0
        X_num_u = scaler.transform(df_u_num[num_cols])
        for k, col in enumerate(num_cols):
            if col == "bom_com_criancas":
                X_num_u[:, k] *= WEIGHTS["criancas"]
            elif col == "idade":
                X_num_u[:, k] *= WEIGHTS["idade"]
    else:
        X_num_u = np.zeros((1, 0))

    return np.concatenate([X_cat_u, X_num_u], axis=1)


# -------------------------
# KNN principal (métrica EUCLIDEANA)
# -------------------------
def knn_rank(animals: List[Dict[str, Any]], prefs: Dict[str, Any], top_n: int = 10) -> List[Dict[str, Any]]:
    """
    Recebe lista de animais (dicts do DB) e preferências do adotante.
    Usa kNN com distância Euclidiana sobre features ponderadas.
    Converte para score de similaridade: score = 1 / (1 + distância).
    """
    if not animals:
        return []

    df_anim = pd.DataFrame(animals).copy()

    X_anim, meta, enc, scaler, cat_cols, num_cols = _build_feature_matrix(df_anim)
    x_user = _build_user_vector(prefs, enc, scaler, cat_cols, num_cols)

    # Euclidiana penaliza descasamentos (ex.: energia Media quando o usuário quer Baixa)
    nbrs = NearestNeighbors(metric="euclidean", algorithm="brute")
    nbrs.fit(X_anim)

    k = min(top_n, len(df_anim))
    distances, indices = nbrs.kneighbors(x_user, n_neighbors=k)
    idx = indices[0]
    dists = distances[0]

    # Converte distância -> similaridade [0, 1]
    sims = 1.0 / (1.0 + dists)

    results: List[Dict[str, Any]] = []
    for rank, (i, sim) in enumerate(zip(idx, sims), start=1):
        item = df_anim.iloc[i].to_dict()
        item["_rank"] = rank
        item["_score"] = round(float(sim), 4)
        results.append(item)
    return results
