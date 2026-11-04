"""
Selección y ponderación supervisada de características (sección 4.3.4 del libro).

Fórmulas contrastadas con docs/capitulo4.pdf:
- Gini(w)    = 1 − Σ_i p_i(w)²                          (4.3), menor = más discriminativo
- Entropía(w)= −Σ_i p_i(w) log p_i(w)                   (4.4), menor = más discriminativo
- χ²(w)      = n (O1·O4 − O2·O3)² / [(O1+O2)(O3+O4)(O1+O3)(O2+O4)]   (4.6), mayor = más relacionado
- Dev(w)     = |μ+(w) − μ−(w)| / σ                      (4.7), mayor = más discriminativo
- g(w)       = a − Gini(w), a > 1                       (4.8), peso de cada característica
"""

import numpy as np
import pandas as pd

CRITERIOS = {
    "gini": {"nombre": "Índice de Gini", "mayor_es_mejor": False},
    "entropia": {"nombre": "Entropía", "mayor_es_mejor": False},
    "chi2": {"nombre": "χ² (chi cuadrada)", "mayor_es_mejor": True},
    "desviacion": {"nombre": "Desviación normalizada", "mayor_es_mejor": True},
}
MIN_SOPORTE = 2


def contingencia(Xb, y, pesos=None):
    """
    Cuenta, para cada token, la tabla 2×2 de presencia contra clase.

    inputs:
    -------
    Xb (numpy.ndarray): matriz binaria densa (n_canciones, n_tokens).
    y (numpy.ndarray): 1 = me gusta, 0 = no me gusta.
    pesos (numpy.ndarray): peso de cada canción; None equivale a 1.

    outputs
    -------
    O (numpy.ndarray): matriz (4, n_tokens) con O1 = token y me gusta, O2 = token y no me gusta,
        O3 = sin token y me gusta, O4 = sin token y no me gusta.
    soporte (numpy.ndarray): número de canciones (sin pesos) que contienen cada token.
    """
    Xb = np.asarray(Xb, dtype=np.float64)
    w = np.ones(len(y)) if pesos is None else np.asarray(pesos, dtype=np.float64)
    like = (np.asarray(y) == 1).astype(np.float64) * w
    nolike = (np.asarray(y) == 0).astype(np.float64) * w
    O1, O2 = like @ Xb, nolike @ Xb
    O3, O4 = like.sum() - O1, nolike.sum() - O2
    return np.vstack([O1, O2, O3, O4]), (Xb > 0).sum(0)


def gini(O):
    """
    Índice de Gini de cada token entre las canciones que lo contienen (ecuación 4.3).

    inputs:
    -------
    O (numpy.ndarray): tabla de contingencia (4, n_tokens).

    outputs
    -------
    g (numpy.ndarray): Gini por token, en [0, 0.5] con dos clases.
    """
    n = O[0] + O[1]
    with np.errstate(invalid="ignore", divide="ignore"):
        p1, p2 = O[0] / n, O[1] / n
    return np.where(n > 0, 1 - p1 ** 2 - p2 ** 2, np.nan)


def entropia(O):
    """
    Entropía en base 2 de cada token entre las canciones que lo contienen (ecuación 4.4).

    inputs:
    -------
    O (numpy.ndarray): tabla de contingencia (4, n_tokens).

    outputs
    -------
    h (numpy.ndarray): entropía por token, en [0, 1] con dos clases.
    """
    n = O[0] + O[1]
    with np.errstate(invalid="ignore", divide="ignore"):
        p = np.vstack([O[0] / n, O[1] / n])
        terminos = np.where(p > 0, -p * np.log2(np.where(p > 0, p, 1)), 0.0)
    return np.where(n > 0, terminos.sum(0), np.nan)


def chi2(O):
    """
    Estadístico χ² de la tabla 2×2 con la fórmula cerrada del libro (ecuación 4.6).

    inputs:
    -------
    O (numpy.ndarray): tabla de contingencia (4, n_tokens).

    outputs
    -------
    x2 (numpy.ndarray): χ² por token; 0 si algún margen es cero.
    """
    O1, O2, O3, O4 = O
    den = (O1 + O2) * (O3 + O4) * (O1 + O3) * (O2 + O4)
    with np.errstate(invalid="ignore", divide="ignore"):
        x2 = (O1 + O2 + O3 + O4) * (O1 * O4 - O2 * O3) ** 2 / den
    return np.where(den > 0, x2, 0.0)


def desviacion_normalizada(Xb, y, pesos=None):
    """
    Desviación normalizada de cada token con calificaciones +1 / −1 (ecuación 4.7).

    inputs:
    -------
    Xb (numpy.ndarray): matriz binaria densa (n_canciones, n_tokens).
    y (numpy.ndarray): 1 = me gusta, 0 = no me gusta.
    pesos (numpy.ndarray): peso de cada canción; None equivale a 1.

    outputs
    -------
    dev (numpy.ndarray): |μ+(w) − μ−(w)| / σ por token.
    """
    Xb = np.asarray(Xb, dtype=np.float64)
    w = np.ones(len(y)) if pesos is None else np.asarray(pesos, dtype=np.float64)
    r = np.where(np.asarray(y) == 1, 1.0, -1.0)
    media = (w * r).sum() / w.sum()
    sigma = np.sqrt((w * (r - media) ** 2).sum() / w.sum())
    con = w @ Xb
    sin = w.sum() - con
    with np.errstate(invalid="ignore", divide="ignore"):
        mu_mas = ((w * r) @ Xb) / con
        mu_menos = ((w * r).sum() - (w * r) @ Xb) / sin
        dev = np.abs(mu_mas - mu_menos) / sigma
    return np.where((con > 0) & (sin > 0) & (sigma > 0), dev, 0.0)


def tabla_criterios(Xb, y, nombres, pesos=None, a=1.5, min_soporte=MIN_SOPORTE):
    """
    Calcula todos los criterios para cada token con soporte suficiente.

    inputs:
    -------
    Xb (numpy.ndarray): matriz binaria densa (n_canciones, n_tokens).
    y (numpy.ndarray): 1 = me gusta, 0 = no me gusta.
    nombres (list): nombre legible de cada token.
    pesos (numpy.ndarray): peso de cada canción.
    a (float): parámetro de la ponderación g(w) = a − Gini(w); debe ser mayor que 1.
    min_soporte (int): canciones mínimas que deben contener el token.

    outputs
    -------
    tabla (pandas.DataFrame): columnas token, col, soporte, en_me_gusta, en_no_me_gusta,
        gini, entropia, chi2, desviacion, peso_g; solo tokens con soporte >= min_soporte.
    """
    O, soporte = contingencia(Xb, y, pesos)
    ok = soporte >= min_soporte
    tabla = pd.DataFrame({
        "token": np.asarray(nombres, dtype=object)[ok],
        "col": np.flatnonzero(ok),
        "soporte": soporte[ok],
        "en_me_gusta": O[0][ok],
        "en_no_me_gusta": O[1][ok],
        "gini": gini(O)[ok],
        "entropia": entropia(O)[ok],
        "chi2": chi2(O)[ok],
        "desviacion": desviacion_normalizada(Xb, y, pesos)[ok],
    })
    tabla["peso_g"] = a - tabla["gini"]
    return tabla


def ordenar(tabla, criterio):
    """
    Ordena la tabla de criterios del token más al menos discriminativo.

    inputs:
    -------
    tabla (pandas.DataFrame): salida de tabla_criterios.
    criterio (str): una llave de CRITERIOS.

    outputs
    -------
    ordenada (pandas.DataFrame): tabla ordenada; desempata por soporte.
    """
    asc = not CRITERIOS[criterio]["mayor_es_mejor"]
    return tabla.sort_values([criterio, "soporte"], ascending=[asc, False], kind="stable")


def seleccionar(Xb, y, nombres, criterio="gini", m=200, pesos=None):
    """
    Elige los m tokens más discriminativos según el criterio.

    inputs:
    -------
    Xb (numpy.ndarray): matriz binaria densa (n_canciones, n_tokens).
    y (numpy.ndarray): 1 = me gusta, 0 = no me gusta.
    nombres (list): nombre legible de cada token.
    criterio (str): una llave de CRITERIOS.
    m (int): número de tokens a conservar.
    pesos (numpy.ndarray): peso de cada canción.

    outputs
    -------
    cols (numpy.ndarray): índices de columna de los tokens elegidos.
    tabla (pandas.DataFrame): tabla de criterios ordenada.
    """
    tabla = ordenar(tabla_criterios(Xb, y, nombres, pesos), criterio)
    return tabla["col"].to_numpy()[:m], tabla
