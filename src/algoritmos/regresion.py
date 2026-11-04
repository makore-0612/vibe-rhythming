"""
Regresión logística (sección 4.4.5) con variante SVM lineal (sección 4.4.6).

Ambas aprenden un peso por característica sobre la matriz por bloques ponderada con la mezcladora.
La explicación de una canción es la contribución w_j · x_j de cada característica.
"""

import warnings

import numpy as np
import scipy.sparse as sp
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC

from src.algoritmos import normalizar_pesos
from src.features import es_visible


def matriz_ponderada(M, pesos):
    """
    Une los bloques escalados por su peso de mezcladora en una sola matriz dispersa.

    inputs:
    -------
    M (dict): modelo cargado.
    pesos (dict): pesos normalizados de los bloques.

    outputs
    -------
    X (scipy.sparse.csr_matrix): matriz (n, n_caracteristicas).
    nombres (list): nombre legible de cada columna.
    """
    partes, nombres = [], []
    for b, w in pesos.items():
        X = M["crudos"][b]
        X = sp.csr_matrix(X) if not sp.issparse(X) else X
        partes.append(X * np.float32(np.sqrt(w)))
        nombres += M["nombres_col"][b]
    return sp.hstack(partes, format="csr"), nombres


def puntuar(M, ent, params):
    """
    Entrena el modelo lineal con las calificaciones del usuario y puntúa el catálogo.

    inputs:
    -------
    M (dict): modelo cargado.
    ent (dict): entrenamiento; pseudo-negativos con peso 0.5.
    params (dict): "variante" ("logistica" | "svm"), "C" (float) y "pesos" (dict).

    outputs
    -------
    puntajes (numpy.ndarray): valor de la función de decisión (log-momios en la logística).
    explicar (callable): ids → lista de explicaciones.
    diagnostico (dict): retrato sonoro (pesos más grandes) y parámetros.
    """
    variante = params.get("variante", "logistica")
    C = float(params.get("C", 1.0))
    pesos = normalizar_pesos(params.get("pesos"))
    X, nombres = matriz_ponderada(M, pesos)
    ids, y, w = ent["ids"], ent["y"], ent["pesos"]

    if variante == "svm":
        modelo = LinearSVC(C=C, class_weight="balanced", max_iter=5000)
    else:
        modelo = LogisticRegression(C=C, class_weight="balanced", max_iter=2000)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        modelo.fit(X[ids], y, sample_weight=w)
    coef = modelo.coef_.ravel()
    puntajes = np.asarray(X @ coef).ravel() + modelo.intercept_[0]
    visibles = np.array([es_visible(n, M["ocultas"]) for n in nombres])

    def explicar(lista):
        """
        Lista las características que más empujan hacia "me gusta" en cada canción.

        inputs:
        -------
        lista (list): ids de canciones a explicar.

        outputs
        -------
        explicaciones (list): por canción, dict con puntaje y contribuciones w_j · x_j.
        """
        salida = []
        for c in lista:
            fila = X[c].tocoo()
            contrib = fila.data * coef[fila.col]
            orden = np.argsort(-contrib)
            a_favor = [{"caracteristica": nombres[fila.col[i]], "valor": float(fila.data[i]),
                        "contribucion": float(contrib[i])}
                       for i in orden if contrib[i] > 0 and visibles[fila.col[i]]][:4]
            en_contra = [{"caracteristica": nombres[fila.col[i]], "valor": float(fila.data[i]),
                          "contribucion": float(contrib[i])}
                         for i in orden[::-1] if contrib[i] < -0.005 and visibles[fila.col[i]]][:2]
            salida.append({"tipo": "regresion", "variante": variante, "puntaje": float(puntajes[c]),
                           "a_favor": a_favor, "en_contra": en_contra})
        return salida

    orden = np.argsort(-coef)
    pos = [(nombres[j], float(coef[j])) for j in orden if coef[j] > 0 and visibles[j]][:12]
    neg = [(nombres[j], float(coef[j])) for j in orden[::-1] if coef[j] < 0 and visibles[j]][:12]
    diagnostico = {"variante": variante, "C": C, "pesos": pesos, "retrato_positivo": pos,
                   "retrato_negativo": neg, "intercepto": float(modelo.intercept_[0]),
                   "n_caracteristicas": X.shape[1]}
    return puntajes, explicar, diagnostico
