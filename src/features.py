"""
Matrices por bloque y tokens binarios a partir de los artefactos del pipeline.

Sin dependencia de Streamlit: src/datos.py se encarga del caché.
"""

import re

import numpy as np
import scipy.sparse as sp
from sklearn.preprocessing import normalize

BLOQUES = ["letra", "etiquetas", "audio", "usos"]

COLS_AUDIO = ["tempo", "volumen_db", "duracion_s", "energia", "bailabilidad", "positividad",
              "habla", "en_vivo", "acustica", "instrumental"]
NOMBRES_AUDIO = {"tempo": "tempo", "volumen_db": "volumen", "duracion_s": "duración", "energia": "energía",
                 "bailabilidad": "bailabilidad", "positividad": "positividad", "habla": "habla",
                 "en_vivo": "en vivo", "acustica": "acústica", "instrumental": "instrumental"}
NIVELES = ["baja", "media", "alta"]


def calcular_idf(df, n):
    """
    Frecuencia inversa de documento: idf = log(n / df), con logaritmo natural.

    inputs:
    -------
    df (numpy.ndarray): número de canciones que contienen cada término.
    n (int): número total de canciones.

    outputs
    -------
    idf (numpy.ndarray): idf por término en float32.
    """
    return np.log(n / np.asarray(df, dtype=np.float64)).astype(np.float32)


def tfidf_amortiguado(conteos, idf):
    """
    Calcula TF-IDF amortiguado log(1 + f) · idf y normaliza cada fila con L2.

    inputs:
    -------
    conteos (scipy.sparse.csr_matrix): conteos de términos por canción.
    idf (numpy.ndarray): idf de cada término.

    outputs
    -------
    X (scipy.sparse.csr_matrix): TF-IDF con filas de norma 1, en float32.
    """
    X = conteos.astype(np.float32).tocsr(copy=True)
    X.data = np.log1p(X.data)
    X = X @ sp.diags(idf.astype(np.float32))
    return normalize(X.tocsr()).astype(np.float32)


def estandarizar_audio(audio):
    """
    Estandariza las columnas de audio con media 0 y desviación 1, y normaliza filas con L2.

    inputs:
    -------
    audio (numpy.ndarray): matriz (n, n_audio) con valores crudos.

    outputs
    -------
    Z (numpy.ndarray): valores estandarizados (para regresión).
    Z_l2 (numpy.ndarray): valores estandarizados con filas de norma 1 (para coseno).
    media (numpy.ndarray): media por columna.
    desv (numpy.ndarray): desviación por columna.
    """
    media, desv = audio.mean(0), audio.std(0) + 1e-6
    Z = ((audio - media) / desv).astype(np.float32)
    return Z, normalize(Z).astype(np.float32), media, desv


def terciles(audio):
    """
    Calcula los cortes de terciles de cada columna de audio.

    inputs:
    -------
    audio (numpy.ndarray): matriz (n, n_audio) con valores crudos.

    outputs
    -------
    cortes (numpy.ndarray): matriz (2, n_audio) con los percentiles 33.3 y 66.7.
    """
    return np.quantile(audio, [1 / 3, 2 / 3], axis=0)


def nivel_tercil(valores, cortes_col):
    """
    Asigna "baja", "media" o "alta" según los terciles de una columna.

    inputs:
    -------
    valores (numpy.ndarray): valores crudos de una columna.
    cortes_col (numpy.ndarray): dos cortes de terciles.

    outputs
    -------
    niveles (numpy.ndarray): índice 0, 1 o 2 por valor.
    """
    return np.digitize(valores, cortes_col, right=True)


def tokens_binarios(conteos, es_bigrama, legibles, etiquetas, nombres_etiquetas, audio, cortes, usos, nombres_usos):
    """
    Construye la matriz binaria de tokens legibles para Bernoulli, reglas y selección.

    inputs:
    -------
    conteos (scipy.sparse.csr_matrix): conteos de letra.
    es_bigrama (list): bandera por término de letra.
    legibles (list): forma legible por término.
    etiquetas (scipy.sparse.csr_matrix): bloque one-hot de etiquetas.
    nombres_etiquetas (list): nombres "prefijo:valor" de las etiquetas.
    audio (numpy.ndarray): audio crudo (n, n_audio) en el orden de COLS_AUDIO.
    cortes (numpy.ndarray): cortes de terciles (2, n_audio).
    usos (scipy.sparse.csr_matrix): bloque binario de usos.
    nombres_usos (list): nombres de los usos.

    outputs
    -------
    B (scipy.sparse.csr_matrix): matriz binaria (n, n_tokens) en uint8.
    nombres (list): nombre legible de cada token, por ejemplo "letra:love" o "energía:alta".
    es_letra (numpy.ndarray): bandera booleana de tokens de letra.
    """
    n = conteos.shape[0]
    cols_uni = np.flatnonzero(~np.asarray(es_bigrama))
    L = (conteos[:, cols_uni] > 0).astype(np.uint8)
    vistos, nombres_letra = {}, []
    for j in cols_uni:
        nombre = f"letra:{legibles[j]}"
        vistos[nombre] = vistos.get(nombre, 0) + 1
        nombres_letra.append(nombre if vistos[nombre] == 1 else f"{nombre}·{vistos[nombre]}")

    filas, cols, nombres_audio = [], [], []
    for k, col in enumerate(COLS_AUDIO):
        niv = nivel_tercil(audio[:, k], cortes[:, k])
        for v in range(3):
            idx = np.flatnonzero(niv == v)
            filas.append(idx)
            cols.append(np.full(len(idx), len(nombres_audio)))
            nombres_audio.append(f"{NOMBRES_AUDIO[col]}:{NIVELES[v]}")
    A = sp.csr_matrix((np.ones(sum(len(f) for f in filas), dtype=np.uint8),
                       (np.concatenate(filas), np.concatenate(cols))), shape=(n, len(nombres_audio)))
    B = sp.hstack([L, (etiquetas > 0).astype(np.uint8), A, (usos > 0).astype(np.uint8)], format="csr")
    nombres = nombres_letra + list(nombres_etiquetas) + nombres_audio + [f"uso:{u}" for u in nombres_usos]
    es_letra = np.zeros(len(nombres), dtype=bool)
    es_letra[:len(nombres_letra)] = True
    return B, nombres, es_letra


def cargar_ocultas(ruta):
    """
    Lee la lista de palabras que no se muestran en pantalla.

    inputs:
    -------
    ruta (pathlib.Path): archivo de texto, una palabra por línea; '#' inicia comentario.

    outputs
    -------
    ocultas (set): palabras en minúsculas.
    """
    if not ruta.exists():
        return set()
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    return {l.strip().lower() for l in lineas if l.strip() and not l.startswith("#")}


def es_visible(nombre, ocultas):
    """
    Indica si un término o token puede mostrarse frente al grupo.

    inputs:
    -------
    nombre (str): término legible, con o sin prefijo ("letra:love", "fall love").
    ocultas (set): palabras ocultas.

    outputs
    -------
    visible (bool): False si alguna palabra del término está en la lista o la contiene como raíz.
    """
    texto = nombre.split(":", 1)[-1].split("·")[0].lower()
    for palabra in re.findall(r"[a-záéíóúñü']+", texto):
        p = palabra.replace("'", "")
        if p in ocultas or any(p.startswith(o) and len(o) >= 4 for o in ocultas):
            return False
    return True
