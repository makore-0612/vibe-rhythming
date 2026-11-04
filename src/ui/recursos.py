"""
Recursos compartidos entre sesiones (una copia por proceso).
"""

import numpy as np
import streamlit as st

from src.datos import cargar_modelo
from src.motor import recomendar


@st.cache_resource(show_spinner="Afinando el catálogo…")
def modelo():
    """
    Carga el modelo una sola vez por proceso, compartido entre sesiones.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    M (dict): modelo de src.datos.cargar_modelo.
    """
    return cargar_modelo()


@st.cache_data(max_entries=150, show_spinner=False)
def calcular(algoritmo, L, D, params, post):
    """
    Corre el motor y conserva solo lo que la interfaz necesita (sin arreglos del catálogo).

    inputs:
    -------
    algoritmo (str): llave de ALGORITMOS.
    L (tuple): ids de me gusta.
    D (tuple): ids de no me gusta.
    params (dict): hiperparámetros.
    post (dict): opciones de post-procesamiento.

    outputs
    -------
    res (dict): ids, puntajes, explicaciones, ms y diagnóstico ligero.
    """
    r = recomendar(modelo(), algoritmo, list(L), list(D), params, post)
    diag = {k: v for k, v in r["diagnostico"].items() if not isinstance(v, np.ndarray)}
    diag["cobertura_catalogo"] = float(np.mean(~np.isnan(np.asarray(r["puntajes_catalogo"], dtype=np.float64))))
    if algoritmo == "naive_bayes":
        d = r["diagnostico"]
        orden = np.argsort(-np.abs(np.log(d["p_like"] / d["p_nolike"])))
        diag["tabla_tokens"] = [(d["tokens"][j], float(d["p_like"][j]), float(d["p_nolike"][j]))
                                for j in orden if d["visibles"][j]][:12]
    return {"ids": r["ids"], "puntajes": r["puntajes"], "explicaciones": r["explicaciones"],
            "ms": r["ms"], "diagnostico": diag}
