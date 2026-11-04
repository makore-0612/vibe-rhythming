"""
Perfil del usuario: etiquetas, pseudo-negativos y requisitos por algoritmo (§5.1 y §5.5).
"""

import hashlib

import numpy as np

MIN_LIKES = 6
PESO_PSEUDO = 0.5

REQUISITOS = {
    "vecinos": {"min_l": 6, "rec_l": 10, "rec_d": 5},
    "naive_bayes": {"min_l": 6, "rec_l": 10, "rec_d": 5},
    "regresion": {"min_l": 6, "rec_l": 10, "rec_d": 5},
    "reglas": {"min_l": 6, "rec_total": 15, "rec_d": 5},
}


def semilla_de(ids):
    """
    Deriva una semilla reproducible a partir de una selección de canciones.

    inputs:
    -------
    ids (iterable): ids de canciones calificadas.

    outputs
    -------
    semilla (int): entero de 32 bits.
    """
    texto = ",".join(str(i) for i in sorted(int(x) for x in ids))
    return int(hashlib.md5(texto.encode()).hexdigest()[:8], 16)


def pseudo_negativos(M, L, D):
    """
    Muestrea pseudo-negativos estratificados por género hasta que |D| llegue a max(|L|, 10).

    inputs:
    -------
    M (dict): modelo cargado con src.datos.cargar_modelo.
    L (list): ids de canciones que le gustan al usuario.
    D (list): ids de canciones que no le gustan.

    outputs
    -------
    pseudo (list): ids de pseudo-negativos; vacío si no hacen falta.
    """
    faltan = max(len(L), 10) - len(D)
    if faltan <= 0:
        return []
    rng = np.random.default_rng(semilla_de(list(L) + [-1] + list(D)))
    excluir = np.zeros(M["n"], dtype=bool)
    excluir[list(L) + list(D)] = True
    generos, conteo = np.unique(M["genero"], return_counts=True)
    cuotas = np.floor(faltan * conteo / conteo.sum()).astype(int)
    # El resto se reparte entre los géneros más grandes.
    for j in np.argsort(-conteo)[: faltan - cuotas.sum()]:
        cuotas[j] += 1
    elegidos = []
    for g, q in zip(generos, cuotas):
        if q == 0:
            continue
        pool = np.flatnonzero((M["genero"] == g) & ~excluir)
        elegidos += rng.choice(pool, size=min(q, len(pool)), replace=False).tolist()
    return sorted(elegidos)


def armar_entrenamiento(M, L, D, usar_pseudo=True):
    """
    Junta las calificaciones del usuario en arreglos listos para entrenar.

    inputs:
    -------
    M (dict): modelo cargado.
    L (list): ids de me gusta.
    D (list): ids de no me gusta.
    usar_pseudo (bool): si se completan los negativos con pseudo-negativos.

    outputs
    -------
    ent (dict): ids (numpy.ndarray), y (1 = me gusta, 0 = no), pesos (1 o PESO_PSEUDO),
        es_pseudo (bandera), L, D, pseudo (listas) y n_pseudo (int).
    """
    L, D = [int(i) for i in L], [int(i) for i in D]
    pseudo = pseudo_negativos(M, L, D) if usar_pseudo else []
    ids = np.array(L + D + pseudo, dtype=np.int64)
    y = np.array([1] * len(L) + [0] * (len(D) + len(pseudo)), dtype=np.int8)
    es_pseudo = np.array([False] * (len(L) + len(D)) + [True] * len(pseudo))
    pesos = np.where(es_pseudo, PESO_PSEUDO, 1.0).astype(np.float64)
    return {"ids": ids, "y": y, "pesos": pesos, "es_pseudo": es_pseudo,
            "L": L, "D": D, "pseudo": pseudo, "n_pseudo": len(pseudo)}


def estado_requisitos(n_l, n_d):
    """
    Evalúa, para cada algoritmo, si la selección alcanza el mínimo o lo recomendado.

    inputs:
    -------
    n_l (int): número de me gusta.
    n_d (int): número de no me gusta reales.

    outputs
    -------
    estado (dict): algoritmo → {"nivel": "bloqueado" | "mínimo" | "recomendado",
        "progreso": float en [0, 1], "mensaje": str}.
    """
    estado = {}
    for alg, r in REQUISITOS.items():
        if n_l < r["min_l"]:
            nivel, msg = "bloqueado", f"Faltan {r['min_l'] - n_l} me gusta"
        elif alg == "reglas" and (n_l + n_d < r["rec_total"] or n_d < r["rec_d"]):
            faltan = []
            if n_l + n_d < r["rec_total"]:
                faltan.append(f"{r['rec_total'] - n_l - n_d} calificaciones más")
            if n_d < r["rec_d"]:
                faltan.append(f"{r['rec_d'] - n_d} no me gusta reales")
            nivel, msg = "mínimo", "Corre, pero aprende sobre todo de pseudo-negativos. Recomendado: " + " y ".join(faltan)
        elif alg != "reglas" and (n_l < r["rec_l"] or n_d < r["rec_d"]):
            faltan = []
            if n_l < r["rec_l"]:
                faltan.append(f"{r['rec_l'] - n_l} me gusta")
            if n_d < r["rec_d"]:
                faltan.append(f"{r['rec_d'] - n_d} no me gusta")
            nivel, msg = "mínimo", "Listo. Para mejorar: " + " y ".join(faltan)
        else:
            nivel, msg = "recomendado", "Listo"
        meta = r.get("rec_total", r.get("rec_l", 10) + r["rec_d"])
        estado[alg] = {"nivel": nivel, "progreso": min(1.0, (n_l + min(n_d, r["rec_d"])) / meta), "mensaje": msg}
    return estado
