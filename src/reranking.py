"""
Post-procesamiento común (§5.7): exclusiones, tope por artista, diversidad (MMR) y novedad.
"""

import numpy as np

from src.algoritmos import normalizar_pesos, similitud_bloques

TAM_POOL = 200


def artista_principal(artista):
    """
    Devuelve el primer artista de una colaboración.

    inputs:
    -------
    artista (str): campo de artista, posiblemente con varios separados por coma.

    outputs
    -------
    principal (str): primer artista, en minúsculas.
    """
    return artista.split(",")[0].strip().lower()


def postprocesar(M, puntajes, excluir, n=10, max_por_artista=2, diversidad=0.0, novedad=0.0,
                 ocultar_explicitas=True, pesos=None):
    """
    Convierte puntajes del catálogo en una lista final de recomendaciones.

    inputs:
    -------
    M (dict): modelo cargado.
    puntajes (numpy.ndarray): puntaje por canción; NaN = no recomendable.
    excluir (list): ids ya calificados.
    n (int): tamaño de la lista.
    max_por_artista (int): tope de canciones por artista principal.
    diversidad (float): λ de MMR en [0, 1]; 0 = solo relevancia.
    novedad (float): penalización por popularidad en [0, 1].
    ocultar_explicitas (bool): si se descartan canciones explícitas.
    pesos (dict): pesos de bloques para la similitud de MMR.

    outputs
    -------
    ids (list): canciones elegidas en orden.
    puntajes_finales (list): puntaje original de cada una.
    """
    p = np.array(puntajes, dtype=np.float64)
    excluir = list(excluir)
    p[excluir] = np.nan
    # Otras versiones de lo ya calificado (mismo artista y mismo inicio de título).
    for e in excluir:
        base = M["titulo_base"][e]
        for i in np.flatnonzero(M["artista_principal"] == M["artista_principal"][e]):
            if M["titulo_base"][i].startswith(base) or base.startswith(M["titulo_base"][i]):
                p[i] = np.nan
    if ocultar_explicitas:
        p[M["explicita"]] = np.nan
    validos = np.flatnonzero(~np.isnan(p))
    if len(validos) == 0:
        return [], []
    pool = validos[np.argsort(-p[validos], kind="stable")[:TAM_POOL]]

    # Relevancia escalada a [0, 1] dentro del pool para combinar con novedad y diversidad.
    rel = p[pool]
    rango = rel.max() - rel.min()
    rel = (rel - rel.min()) / rango if rango > 0 else np.ones_like(rel)
    rel = rel - novedad * M["popularidad"][pool] / 100.0

    S = similitud_bloques(M, pool, pool, normalizar_pesos(pesos)) if diversidad > 0 else None
    elegidos, por_artista = [], {}
    disponibles = np.ones(len(pool), dtype=bool)
    while len(elegidos) < n and disponibles.any():
        valor = (1 - diversidad) * rel
        if S is not None and elegidos:
            valor = valor - diversidad * S[:, elegidos].max(1)
        valor = np.where(disponibles, valor, -np.inf)
        k = int(np.argmax(valor))
        disponibles[k] = False
        art = M["artista_principal"][pool[k]]
        if por_artista.get(art, 0) >= max_por_artista:
            continue
        por_artista[art] = por_artista.get(art, 0) + 1
        elegidos.append(k)
    ids = [int(pool[k]) for k in elegidos]
    return ids, [float(p[i]) for i in ids]
