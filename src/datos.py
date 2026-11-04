"""
Carga de artefactos con caché de proceso.

Sin dependencia de Streamlit: functools.lru_cache garantiza una sola copia por proceso,
y la app puede envolver cargar_modelo con st.cache_resource.
"""

import json
from functools import lru_cache

import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.preprocessing import normalize

from src import config as C
from src import features as F


@lru_cache(maxsize=1)
def cargar_modelo():
    """
    Carga el catálogo y construye todas las matrices que usan los algoritmos.

    inputs:
    -------
    (ninguno): lee los artefactos de data/processed/.

    outputs
    -------
    M (dict): catálogo, bloques normalizados, matrices para regresión, tokens binarios,
        nombres legibles de columnas y palabras ocultas. Ver las llaves al final de la función.
    """
    cat = pd.read_parquet(C.RUTA_CATALOGO)
    vocab = json.loads(C.RUTA_VOCAB.read_text(encoding="utf-8"))
    idf = np.array(vocab["idf"], dtype=np.float32)
    conteos = sp.load_npz(C.RUTA_CONTEOS).astype(np.float32).tocsr()
    etiquetas = sp.load_npz(C.RUTA_ETIQUETAS).astype(np.float32).tocsr()
    usos = sp.load_npz(C.RUTA_USOS).astype(np.float32).tocsr()
    audio_crudo = cat[F.COLS_AUDIO].to_numpy(dtype=np.float32)
    audio_z, audio_l2, _, _ = F.estandarizar_audio(audio_crudo)
    cortes = F.terciles(audio_crudo)

    letra = F.tfidf_amortiguado(conteos, idf)
    bloques = {
        "letra": letra,
        "etiquetas": normalize(etiquetas).astype(np.float32),
        "audio": audio_l2,
        "usos": normalize(usos).astype(np.float32),
    }
    # Para regresión: cada bloque escalado de modo que su norma típica sea 1.
    crudos = {
        "letra": letra,
        "etiquetas": bloques["etiquetas"],
        "audio": (audio_z / np.sqrt(audio_z.shape[1])).astype(np.float32),
        "usos": bloques["usos"],
    }
    nombres_col = {
        "letra": [f"letra:{t}" for t in vocab["legible"]],
        "etiquetas": vocab["etiquetas"],
        "audio": [f"audio:{F.NOMBRES_AUDIO[c]}" for c in F.COLS_AUDIO],
        "usos": [f"uso:{u}" for u in vocab["usos"]],
    }
    B, nombres_tok, es_letra = F.tokens_binarios(conteos, vocab["es_bigrama"], vocab["legible"], etiquetas,
                                                 vocab["etiquetas"], audio_crudo, cortes, usos, vocab["usos"])
    ocultas = F.cargar_ocultas(C.RUTA_PALABRAS_OCULTAS)
    generos, conteo_generos = np.unique(cat["genero"].to_numpy(), return_counts=True)
    return {
        "cat": cat,
        "n": len(cat),
        "conteos": conteos,
        "idf": idf,
        "vocab": vocab,
        "bloques": bloques,
        "crudos": crudos,
        "nombres_col": nombres_col,
        "B": B,
        "B_csc": B.tocsc(),
        "nombres_tok": nombres_tok,
        "es_letra_tok": es_letra,
        "visible_tok": np.array([F.es_visible(t, ocultas) for t in nombres_tok]),
        "visible_letra": np.array([F.es_visible(t, ocultas) for t in vocab["legible"]]),
        "ocultas": ocultas,
        "visible_col": {b: np.array([F.es_visible(n, ocultas) for n in nombres]) for b, nombres in nombres_col.items()},
        "generos_unicos": generos,
        "conteo_generos": conteo_generos,
        "cortes_audio": cortes,
        "explicita": cat["explicita"].to_numpy(dtype=bool),
        "popularidad": cat["popularidad"].to_numpy(dtype=np.float32),
        "genero": cat["genero"].to_numpy(),
        "artista": cat["artista"].to_numpy(),
        "titulo_base": cat["titulo_base"].to_numpy(),
        "artista_principal": cat["artista"].str.split(",").str[0].str.strip().str.lower().to_numpy(),
    }
