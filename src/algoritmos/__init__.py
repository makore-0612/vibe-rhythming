"""
Utilidades comunes de los algoritmos.

Cada algoritmo expone `puntuar(M, ent, params)`, que devuelve:
- puntajes (numpy.ndarray): un valor por canción del catálogo; NaN = no recomendable.
- explicar (callable): recibe una lista de ids y devuelve una explicación estructurada por id.
- diagnostico (dict): datos propios del algoritmo para la interfaz.
"""

import numpy as np
import scipy.sparse as sp

PESOS_DEFECTO = {"letra": 1.0, "etiquetas": 1.0, "audio": 1.0, "usos": 0.5}
PREFIJOS_ETIQUETA_VISIBLES = ("género:", "subgénero:", "emoción:", "década:")


def normalizar_pesos(pesos):
    """
    Completa los pesos de la mezcladora y los escala para que sumen 1.

    inputs:
    -------
    pesos (dict): bloque → peso no negativo; puede omitir bloques.

    outputs
    -------
    w (dict): bloque → peso en [0, 1] con suma 1 (o pesos por defecto si todos son cero).
    """
    w = {b: max(0.0, float((pesos or {}).get(b, PESOS_DEFECTO[b]))) for b in PESOS_DEFECTO}
    total = sum(w.values())
    if total == 0:
        return normalizar_pesos(PESOS_DEFECTO)
    return {b: v / total for b, v in w.items()}


def similitud_bloques(M, filas, columnas, pesos):
    """
    Similitud coseno ponderada por bloque: s = Σ w_b · s_b.

    inputs:
    -------
    M (dict): modelo cargado.
    filas (numpy.ndarray | slice): ids de las canciones de las filas (por ejemplo, todo el catálogo).
    columnas (numpy.ndarray): ids de las canciones de las columnas (por ejemplo, el perfil).
    pesos (dict): pesos normalizados de los bloques.

    outputs
    -------
    S (numpy.ndarray): matriz densa (len(filas), len(columnas)).
    """
    S = None
    for b, w in pesos.items():
        if w == 0:
            continue
        X = M["bloques"][b]
        prod = X[filas] @ X[columnas].T
        prod = prod.toarray() if sp.issparse(prod) else np.asarray(prod)
        S = w * prod if S is None else S + w * prod
    return S.astype(np.float32)


def palabras_compartidas(M, a, b, k=3):
    """
    Términos de letra que más aportan a la similitud entre dos canciones, solo visibles.

    inputs:
    -------
    M (dict): modelo cargado.
    a (int): id de una canción.
    b (int): id de otra canción.
    k (int): número máximo de términos.

    outputs
    -------
    palabras (list): formas legibles ordenadas por aporte.
    """
    X = M["bloques"]["letra"]
    prod = X[a].multiply(X[b]).tocoo()
    orden = np.argsort(-prod.data)
    legibles = M["vocab"]["legible"]
    return [legibles[prod.col[i]] for i in orden if M["visible_letra"][prod.col[i]]][:k]


def etiquetas_compartidas(M, a, b, k=3):
    """
    Etiquetas legibles (género, subgénero, emoción, década) que comparten dos canciones.

    inputs:
    -------
    M (dict): modelo cargado.
    a (int): id de una canción.
    b (int): id de otra canción.
    k (int): número máximo de etiquetas.

    outputs
    -------
    etiquetas (list): nombres "prefijo:valor".
    """
    E = M["bloques"]["etiquetas"]
    comunes = np.intersect1d(E[a].indices, E[b].indices)
    nombres = [M["vocab"]["etiquetas"][j] for j in comunes]
    return [n for n in nombres if n.startswith(PREFIJOS_ETIQUETA_VISIBLES)][:k]
