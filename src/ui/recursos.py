"""
Recursos compartidos entre sesiones (una copia por proceso).
"""

import numpy as np
import streamlit as st

from src import config as C
from src import datos
from src.motor import recomendar

# Si cambia cualquiera de estos archivos (por ejemplo, tras un push), el modelo se recarga.
ARCHIVOS_MODELO = [C.RAIZ / "src" / "datos.py", C.RAIZ / "src" / "features.py", C.RAIZ / "src" / "config.py",
                   C.RUTA_PALABRAS_OCULTAS, C.RUTA_CATALOGO, C.RUTA_CONTEOS, C.RUTA_ETIQUETAS, C.RUTA_USOS,
                   C.RUTA_VOCAB]


def firma_modelo():
    """
    Resume la versión del código y de los datos del modelo con sus fechas de modificación.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    firma (tuple): pares (archivo, fecha de modificación en ns); 0 si el archivo falta.
    """
    return tuple((p.name, p.stat().st_mtime_ns if p.exists() else 0) for p in ARCHIVOS_MODELO)


@st.cache_resource(show_spinner="Afinando el catálogo…", max_entries=1)
def _modelo_por_version(firma):
    """
    Carga el modelo para una versión dada; max_entries=1 libera la versión anterior.

    inputs:
    -------
    firma (tuple): salida de firma_modelo; solo sirve como llave del caché.

    outputs
    -------
    M (dict): modelo de src.datos.cargar_modelo.
    """
    datos.cargar_modelo.cache_clear()
    return datos.cargar_modelo()


def modelo():
    """
    Devuelve el modelo compartido entre sesiones, recargándolo si cambió el código o los datos.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    M (dict): modelo de src.datos.cargar_modelo.
    """
    return _modelo_por_version(firma_modelo())


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
