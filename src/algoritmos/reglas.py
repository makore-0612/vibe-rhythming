"""
Reglas de asociación (sección 4.4.4): Apriori propio sobre las canciones calificadas del usuario.

Es la versión "un modelo por usuario". El consecuente es fijo: "like" o "no_like".
Una regla X → like tiene soporte = #canciones con X y me gusta, y
confianza = soporte / #canciones con X.
"""

from itertools import combinations

import numpy as np

TOP_LETRA = 100
MAX_CANDIDATOS = 200_000
MAX_REGLAS_POR_CLASE = 400


def a_bits(columna):
    """
    Convierte una columna booleana en un entero cuyos bits marcan las transacciones.

    inputs:
    -------
    columna (numpy.ndarray): bandera por transacción.

    outputs
    -------
    bits (int): entero con el bit i encendido si la transacción i contiene el token.
    """
    return int("".join("1" if v else "0" for v in columna[::-1]) or "0", 2)


def apriori(T, clase, min_soporte, min_confianza, max_long):
    """
    Encuentra reglas X → clase con Apriori sobre transacciones binarias.

    inputs:
    -------
    T (numpy.ndarray): matriz booleana (n_transacciones, n_tokens).
    clase (numpy.ndarray): 1 = me gusta, 0 = no me gusta, por transacción.
    min_soporte (int): canciones mínimas que cumplen X y la clase del consecuente.
    min_confianza (float): confianza mínima en [0, 1].
    max_long (int): tamaño máximo del antecedente.

    outputs
    -------
    reglas (list): dicts con "antecedente" (tupla de columnas), "consecuente" (1 o 0),
        "soporte" (int) y "confianza" (float).
    truncado (bool): True si se detuvo por exceso de candidatos.
    """
    bits_tok = [a_bits(T[:, j]) for j in range(T.shape[1])]
    bits_clase = {1: a_bits(clase == 1), 0: a_bits(clase == 0)}
    reglas, truncado = [], False

    def evaluar(items, bits):
        """
        Agrega las reglas que cumple un conjunto y dice si es frecuente para alguna clase.

        inputs:
        -------
        items (tuple): columnas del antecedente.
        bits (int): transacciones que contienen todos los items.

        outputs
        -------
        frecuente (bool): si el conjunto alcanza el soporte con alguna clase.
        """
        total = bits.bit_count()
        frecuente = False
        for c, bc in bits_clase.items():
            sop = (bits & bc).bit_count()
            if sop >= min_soporte:
                frecuente = True
                if sop / total >= min_confianza:
                    reglas.append({"antecedente": items, "consecuente": c, "soporte": sop, "confianza": sop / total})
        return frecuente

    nivel = {}
    for j, b in enumerate(bits_tok):
        if evaluar((j,), b):
            nivel[(j,)] = b
    for _ in range(2, max_long + 1):
        claves = sorted(nivel)
        siguiente = {}
        n_cand = 0
        for i, a in enumerate(claves):
            for b in claves[i + 1:]:
                if a[:-1] != b[:-1]:
                    break
                cand = a + (b[-1],)
                if any(sub not in nivel for sub in combinations(cand, len(cand) - 1)):
                    continue
                n_cand += 1
                if n_cand > MAX_CANDIDATOS:
                    truncado = True
                    break
                bits = nivel[a] & nivel[b]
                if evaluar(cand, bits):
                    siguiente[cand] = bits
            if truncado:
                break
        nivel = siguiente
        if not nivel or truncado:
            break
    return reglas, truncado


def puntuar(M, ent, params):
    """
    Minera reglas con las calificaciones del usuario y puntúa el catálogo.

    inputs:
    -------
    M (dict): modelo cargado.
    ent (dict): entrenamiento; los pseudo-negativos cuentan como "no me gusta".
    params (dict): "min_soporte" (int), "min_confianza" (float), "max_long" (int).

    outputs
    -------
    puntajes (numpy.ndarray): promedio de confianza de reglas like que dispara menos el de no_like,
        con desempates; NaN si no dispara ninguna regla.
    explicar (callable): ids → lista de explicaciones.
    diagnostico (dict): reglas, cobertura y avisos.
    """
    min_sop = int(params.get("min_soporte", 2))
    min_conf = float(params.get("min_confianza", 0.7))
    max_long = int(params.get("max_long", 3))
    ids, y = ent["ids"], ent["y"]

    # Transacciones: tokens sin bigramas, letra limitada a los 100 más frecuentes del perfil.
    Tp = M["B"][ids].toarray().astype(bool)
    es_letra = M["es_letra_tok"]
    frec = Tp.sum(0)
    letra_cols = np.flatnonzero(es_letra & (frec > 0) & M["visible_tok"])
    letra_top = letra_cols[np.argsort(-frec[letra_cols], kind="stable")][:TOP_LETRA]
    otras = np.flatnonzero(~es_letra & (frec > 0))
    cols = np.sort(np.concatenate([letra_top, otras]))
    reglas, truncado = apriori(Tp[:, cols], y, min_sop, min_conf, max_long)

    # Nos quedamos con las reglas más fuertes de cada clase para puntuar.
    reglas.sort(key=lambda r: (-r["confianza"], -r["soporte"], len(r["antecedente"])))
    por_clase = {1: [r for r in reglas if r["consecuente"] == 1][:MAX_REGLAS_POR_CLASE],
                 0: [r for r in reglas if r["consecuente"] == 0][:MAX_REGLAS_POR_CLASE]}
    usadas = sorted({cols[j] for c in por_clase.values() for r in c for j in r["antecedente"]})
    pos = {c: i for i, c in enumerate(usadas)}
    Bc = M["B_csc"][:, usadas].toarray().astype(bool) if usadas else np.zeros((M["n"], 0), bool)

    n = M["n"]
    suma, cuenta, disparos = {1: np.zeros(n), 0: np.zeros(n)}, {1: np.zeros(n), 0: np.zeros(n)}, {}
    for c, lista in por_clase.items():
        for k, r in enumerate(lista):
            dispara = np.all(Bc[:, [pos[cols[j]] for j in r["antecedente"]]], axis=1)
            suma[c][dispara] += r["confianza"]
            cuenta[c][dispara] += 1
            disparos[(c, k)] = dispara
    with np.errstate(invalid="ignore", divide="ignore"):
        prom = {c: np.where(cuenta[c] > 0, suma[c] / cuenta[c], 0.0) for c in (0, 1)}
    alguna = (cuenta[1] + cuenta[0]) > 0
    # Desempate: número de reglas like, luego similitud con el centroide de L (escala pequeña).
    L = ent["L"]
    centroide = np.asarray(M["bloques"]["letra"][L].mean(0)).ravel()
    sim_centroide = np.asarray(M["bloques"]["letra"] @ centroide).ravel()
    puntajes = prom[1] - prom[0] + 1e-3 * np.minimum(cuenta[1], 100) / 100 + 1e-5 * sim_centroide
    puntajes = np.where(alguna & (cuenta[1] > 0), puntajes, np.nan)

    nombres = M["nombres_tok"]

    def legible(r):
        """
        Traduce una regla a nombres de tokens.

        inputs:
        -------
        r (dict): regla con antecedente en columnas locales.

        outputs
        -------
        regla (dict): antecedente como lista de nombres, más consecuente, soporte y confianza.
        """
        return {"si": [nombres[cols[j]] for j in r["antecedente"]],
                "entonces": "te gusta" if r["consecuente"] == 1 else "no te gusta",
                "soporte": r["soporte"], "confianza": r["confianza"]}

    def explicar(lista):
        """
        Lista las reglas que dispara cada canción, primero las de "me gusta".

        inputs:
        -------
        lista (list): ids de canciones a explicar.

        outputs
        -------
        explicaciones (list): por canción, dict con reglas disparadas y conteos.
        """
        salida = []
        for c in lista:
            dispara_like = [legible(r) for k, r in enumerate(por_clase[1]) if disparos[(1, k)][c]]
            dispara_no = [legible(r) for k, r in enumerate(por_clase[0]) if disparos[(0, k)][c]]
            salida.append({"tipo": "reglas", "reglas_like": dispara_like[:3], "reglas_no_like": dispara_no[:2],
                           "n_like": len(dispara_like), "n_no_like": len(dispara_no)})
        return salida

    n_reales_d = len(ent["D"])
    avisos = []
    if ent["n_pseudo"] > 0 and n_reales_d < 5:
        avisos.append(f"Con {n_reales_d} 'no me gusta' reales, las reglas de 'no te gusta' salen sobre todo de "
                      f"{ent['n_pseudo']} pseudo-negativos al azar.")
    if truncado:
        avisos.append("Se detuvo la búsqueda por exceso de combinaciones; sube el soporte mínimo.")
    diagnostico = {
        "reglas": [legible(r) for r in por_clase[1][:50]] + [legible(r) for r in por_clase[0][:50]],
        "n_reglas_like": len([r for r in reglas if r["consecuente"] == 1]),
        "n_reglas_no_like": len([r for r in reglas if r["consecuente"] == 0]),
        "cobertura": float(np.mean(cuenta[1] > 0)), "cobertura_cualquiera": float(np.mean(alguna)),
        "transacciones": len(ids), "tokens": len(cols), "avisos": avisos, "truncado": truncado,
    }
    return puntajes, explicar, diagnostico
