"""
Métricas de evaluación de listas (§5.8).
"""

import numpy as np

from src.algoritmos import normalizar_pesos, similitud_bloques


def novedad(M, ids):
    """
    Promedio de 1 − popularidad/100 en la lista.

    inputs:
    -------
    M (dict): modelo cargado.
    ids (list): canciones recomendadas.

    outputs
    -------
    valor (float): novedad en [0, 1]; NaN si la lista está vacía.
    """
    return float(np.mean(1 - M["popularidad"][ids] / 100)) if len(ids) else float("nan")


def diversidad(M, ids, pesos=None):
    """
    1 − similitud promedio entre pares de canciones de la lista.

    inputs:
    -------
    M (dict): modelo cargado.
    ids (list): canciones recomendadas.
    pesos (dict): pesos de bloques para la similitud.

    outputs
    -------
    valor (float): diversidad; NaN con menos de dos canciones.
    """
    if len(ids) < 2:
        return float("nan")
    S = similitud_bloques(M, np.array(ids), np.array(ids), normalizar_pesos(pesos))
    iu = np.triu_indices(len(ids), 1)
    return float(1 - S[iu].mean())


def serendipia(M, ids, L, pesos=None, umbral_sim=0.35):
    """
    Aproximación de serendipia: fracción de la lista con baja similitud al perfil y con
    artista o género que no aparecen entre los me gusta. Es una aproximación, no una medida exacta.

    inputs:
    -------
    M (dict): modelo cargado.
    ids (list): canciones recomendadas (ya con puntaje alto del modelo).
    L (list): ids de me gusta.
    pesos (dict): pesos de bloques.
    umbral_sim (float): similitud máxima con el perfil para considerarla sorpresa.

    outputs
    -------
    valor (float): fracción en [0, 1]; NaN si la lista está vacía.
    """
    if not len(ids) or not len(L):
        return float("nan")
    S = similitud_bloques(M, np.array(ids), np.array(L), normalizar_pesos(pesos)).max(1)
    artistas_l = {M["artista"][i] for i in L}
    generos_l = {M["genero"][i] for i in L}
    nuevo = np.array([(M["artista"][i] not in artistas_l) or (M["genero"][i] not in generos_l) for i in ids])
    return float(np.mean((S < umbral_sim) & nuevo))


def jaccard(a, b):
    """
    Índice de Jaccard entre dos listas.

    inputs:
    -------
    a (list): primera lista de ids.
    b (list): segunda lista de ids.

    outputs
    -------
    valor (float): |a ∩ b| / |a ∪ b|; 0 si ambas están vacías.
    """
    sa, sb = set(a), set(b)
    return len(sa & sb) / len(sa | sb) if sa | sb else 0.0


def cobertura(puntajes):
    """
    Fracción del catálogo a la que el algoritmo puede asignar un puntaje.

    inputs:
    -------
    puntajes (numpy.ndarray): puntaje por canción, NaN si no es recomendable.

    outputs
    -------
    valor (float): fracción en [0, 1].
    """
    return float(np.mean(~np.isnan(np.asarray(puntajes, dtype=np.float64))))


def relevancia_loo(M, L, D, puntuar, params):
    """
    Validación dejando uno fuera: entrena sin cada canción calificada y revisa si el
    algoritmo la coloca del lado correcto (por encima o por debajo de la mediana del catálogo).
    Con pocas canciones es ruidosa.

    inputs:
    -------
    M (dict): modelo cargado.
    L (list): ids de me gusta.
    D (list): ids de no me gusta reales.
    puntuar (callable): función puntuar del algoritmo.
    params (dict): parámetros del algoritmo.

    outputs
    -------
    valor (float): fracción de aciertos; NaN si no hay suficientes datos.
    """
    from src.perfil import armar_entrenamiento
    aciertos, total = 0, 0
    for fuera, es_like in [(i, True) for i in L] + [(i, False) for i in D]:
        L2 = [i for i in L if i != fuera]
        D2 = [i for i in D if i != fuera]
        if len(L2) < 2:
            continue
        p, _, _ = puntuar(M, armar_entrenamiento(M, L2, D2), params)
        p = np.asarray(p, dtype=np.float64)
        if np.isnan(p[fuera]):
            aciertos += 0 if es_like else 1
        else:
            arriba = p[fuera] > np.nanmedian(p)
            aciertos += int(arriba == es_like)
        total += 1
    return aciertos / total if total else float("nan")
