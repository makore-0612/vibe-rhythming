"""
Punto de entrada único del motor: elige algoritmo, entrena, post-procesa y explica.
"""

import time

from src import perfil, reranking
from src.algoritmos import naive_bayes, reglas, regresion, vecinos

ALGORITMOS = {
    "vecinos": {"nombre": "Vecinos más cercanos", "modulo": vecinos, "seccion": "4.4.1",
                "linea": "Busca las canciones que calificaste más parecidas a cada candidata."},
    "naive_bayes": {"nombre": "Naive Bayes", "modulo": naive_bayes, "seccion": "4.4.3",
                    "linea": "Calcula la probabilidad de que te guste según las características que comparte con tus gustos."},
    "reglas": {"nombre": "Reglas de asociación", "modulo": reglas, "seccion": "4.4.4",
               "linea": "Encuentra combinaciones de características que aparecen en lo que te gusta."},
    "regresion": {"nombre": "Regresión logística", "modulo": regresion, "seccion": "4.4.5",
                  "linea": "Aprende un peso por característica: tu retrato sonoro."},
}


def recomendar(M, algoritmo, L, D, params=None, post=None):
    """
    Corre un algoritmo completo para una selección de usuario.

    inputs:
    -------
    M (dict): modelo cargado con src.datos.cargar_modelo.
    algoritmo (str): llave de ALGORITMOS.
    L (list): ids de me gusta.
    D (list): ids de no me gusta.
    params (dict): hiperparámetros del algoritmo (incluye "pesos" de la mezcladora).
    post (dict): opciones de reranking.postprocesar (n, max_por_artista, diversidad, novedad,
        ocultar_explicitas).

    outputs
    -------
    resultado (dict): "ids", "puntajes", "explicaciones", "diagnostico", "ms" y, de apoyo,
        "puntajes_catalogo" y "entrenamiento".
    """
    params = dict(params or {})
    post = dict(post or {})
    t0 = time.perf_counter()
    ent = perfil.armar_entrenamiento(M, L, D)
    puntajes, explicar, diag = ALGORITMOS[algoritmo]["modulo"].puntuar(M, ent, params)
    ids, finales = reranking.postprocesar(M, puntajes, list(L) + list(D), pesos=params.get("pesos"), **post)
    explicaciones = explicar(ids)
    diag["n_pseudo"] = ent["n_pseudo"]
    return {"ids": ids, "puntajes": finales, "explicaciones": explicaciones, "diagnostico": diag,
            "ms": (time.perf_counter() - t0) * 1000, "puntajes_catalogo": puntajes, "entrenamiento": ent}
