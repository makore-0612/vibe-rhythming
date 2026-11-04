"""
Vecinos más cercanos (sección 4.4.1): método perezoso.

Puntaje de un candidato c: promedio de r_i · s(c, i) entre sus k vecinos calificados más similares,
con r = +1 (me gusta) o −1 (no me gusta). Los pseudo-negativos se ignoran.
"""

import numpy as np

from src.algoritmos import etiquetas_compartidas, normalizar_pesos, palabras_compartidas, similitud_bloques


def puntuar(M, ent, params):
    """
    Calcula el puntaje de vecinos para todo el catálogo.

    inputs:
    -------
    M (dict): modelo cargado.
    ent (dict): entrenamiento de src.perfil.armar_entrenamiento.
    params (dict): "k" (int, opcional) y "pesos" (dict de la mezcladora).

    outputs
    -------
    puntajes (numpy.ndarray): puntaje por canción.
    explicar (callable): ids → lista de explicaciones.
    diagnostico (dict): k usado, comparaciones realizadas y tamaño del perfil.
    """
    real = ~ent["es_pseudo"]
    ids = ent["ids"][real]
    r = np.where(ent["y"][real] == 1, 1.0, -1.0).astype(np.float32)
    k = int(params.get("k") or min(3, len(ids)))
    k = max(1, min(k, len(ids)))
    pesos = normalizar_pesos(params.get("pesos"))

    S = similitud_bloques(M, slice(None), ids, pesos)          # (n, |perfil|)
    vecinos = np.argpartition(-S, k - 1, axis=1)[:, :k]          # índices dentro del perfil
    s_k = np.take_along_axis(S, vecinos, axis=1)
    contrib = s_k * r[vecinos]
    puntajes = contrib.mean(1)

    def explicar(lista):
        """
        Explica cada canción con el vecino calificado que más aporta.

        inputs:
        -------
        lista (list): ids de canciones a explicar.

        outputs
        -------
        explicaciones (list): por canción, dict con tipo, vecinos (id, similitud, r) y
            palabras y etiquetas compartidas con el vecino principal.
        """
        salida = []
        for c in lista:
            orden = np.argsort(-contrib[c])
            vec = [{"id": int(ids[vecinos[c, j]]), "sim": float(s_k[c, j]), "r": int(r[vecinos[c, j]])}
                   for j in orden]
            principal = vec[0]["id"]
            salida.append({"tipo": "vecinos", "vecinos": vec,
                           "palabras": palabras_compartidas(M, c, principal),
                           "etiquetas": etiquetas_compartidas(M, c, principal)})
        return salida

    diagnostico = {"k": k, "perfil": len(ids), "comparaciones": int(S.size), "pesos": pesos,
                   "nota": "Perezoso: no entrena; compara cada candidata con cada canción calificada."}
    return puntajes, explicar, diagnostico
