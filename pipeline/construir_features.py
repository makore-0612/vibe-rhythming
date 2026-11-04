"""
Construye las características del catálogo (§4.4 de CLAUDE.md).

Salidas en data/processed/:
- conteos.npz: conteos de letra (CSR, uint16), solo los términos con mayor TF-IDF por canción.
- etiquetas.npz: one-hot de género, subgénero, emoción, década, tónica, modo, compás y explícita.
- usos.npz: columnas `Good for ...` que sí varían.
- vocab.json: términos, idf, forma legible, tipo de término y nombres de columnas de cada bloque.

Uso: python pipeline/construir_features.py
"""

import json
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import polars as pl
import scipy.sparse as sp
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import config as C  # noqa: E402
from src.features import calcular_idf  # noqa: E402

RE_PALABRA = re.compile(r"[a-záéíóúñü]+(?:'[a-z]+)?")
MIN_CANCIONES_SUBGENERO = 20
MIN_FRACCION_USO = 0.01


def palabras_vacias():
    """
    Junta las stop words de inglés y español con el relleno típico de canciones.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    vacias (set): palabras a descartar, también en su versión sin apóstrofo.
    """
    base = set(stopwords.words("english")) | set(stopwords.words("spanish")) | set(C.RELLENO)
    return base | {p.replace("'", "") for p in base}


def tokenizar(letra, idioma, vacias, stemmers, cache, formas):
    """
    Convierte una letra en la lista de raíces sin stop words.

    inputs:
    -------
    letra (str): letra completa.
    idioma (str): "en" o "es"; decide el stemmer.
    vacias (set): palabras a descartar.
    stemmers (dict): idioma → SnowballStemmer.
    cache (dict): (idioma, palabra) → raíz, para no repetir el stemming.
    formas (collections.defaultdict): raíz → Counter de formas originales; se actualiza aquí.

    outputs
    -------
    raices (list): raíces en el orden en que aparecen.
    """
    raices = []
    stem = stemmers["es" if idioma == "es" else "en"]
    for m in RE_PALABRA.finditer(letra.lower()):
        palabra = m.group().replace("'", "")
        if len(palabra) < 3 or palabra in vacias:
            continue
        clave = (idioma, palabra)
        raiz = cache.get(clave)
        if raiz is None:
            raiz = cache[clave] = stem.stem(palabra)
        formas[raiz][palabra] += 1
        raices.append(raiz)
    return raices


def construir_vocabulario(docs, n_docs):
    """
    Elige unigramas y bigramas por frecuencia de documento con filtros min_df y max_df.

    inputs:
    -------
    docs (list): lista de listas de raíces por canción.
    n_docs (int): número de canciones.

    outputs
    -------
    terminos (list): términos del vocabulario; los bigramas usan "raíz1 raíz2".
    df (numpy.ndarray): frecuencia de documento de cada término.
    """
    df_uni, df_bi = Counter(), Counter()
    for raices in docs:
        df_uni.update(set(raices))
        df_bi.update({f"{a} {b}" for a, b in zip(raices, raices[1:]) if a != b})
    max_df = C.MAX_DF * n_docs
    bi = [t for t, n in df_bi.most_common() if C.MIN_DF <= n <= max_df][:C.VOCAB_MAX_BIGRAMAS]
    uni = [t for t, n in df_uni.most_common() if C.MIN_DF <= n <= max_df][:C.VOCAB_MAX - len(bi)]
    terminos = uni + bi
    df = np.array([df_uni[t] if " " not in t else df_bi[t] for t in terminos], dtype=np.int32)
    return terminos, df


def matriz_conteos(docs, indice):
    """
    Cuenta términos del vocabulario por canción.

    inputs:
    -------
    docs (list): lista de listas de raíces por canción.
    indice (dict): término → columna.

    outputs
    -------
    X (scipy.sparse.csr_matrix): conteos de forma (n_docs, n_terminos), en float32.
    """
    filas, cols, vals = [], [], []
    for i, raices in enumerate(docs):
        c = Counter(t for t in raices if t in indice)
        c.update(b for b in (f"{a} {b}" for a, b in zip(raices, raices[1:])) if b in indice)
        filas += [i] * len(c)
        cols += [indice[t] for t in c]
        vals += list(c.values())
    return sp.csr_matrix((np.array(vals, dtype=np.float32), (filas, cols)), shape=(len(docs), len(indice)))


def podar_por_tfidf(X, idf, k):
    """
    Conserva en cada fila solo los k términos con mayor TF-IDF amortiguado.

    inputs:
    -------
    X (scipy.sparse.csr_matrix): conteos.
    idf (numpy.ndarray): idf de cada término.
    k (int): términos a conservar por canción.

    outputs
    -------
    X_podada (scipy.sparse.csr_matrix): conteos con a lo más k entradas por fila.
    """
    X = X.tocsr()
    datos = np.zeros_like(X.data)
    for i in range(X.shape[0]):
        ini, fin = X.indptr[i], X.indptr[i + 1]
        if fin - ini <= k:
            datos[ini:fin] = X.data[ini:fin]
            continue
        puntaje = np.log1p(X.data[ini:fin]) * idf[X.indices[ini:fin]]
        mejores = np.argpartition(-puntaje, k)[:k]
        datos[ini + mejores] = X.data[ini + mejores]
    X_podada = sp.csr_matrix((datos, X.indices.copy(), X.indptr.copy()), shape=X.shape)
    X_podada.eliminate_zeros()
    return X_podada


def bloque_one_hot(valores_por_cancion, prefijo):
    """
    Construye un bloque binario a partir de listas de valores por canción.

    inputs:
    -------
    valores_por_cancion (list): una lista de valores (str) por canción.
    prefijo (str): prefijo legible de las columnas, por ejemplo "género".

    outputs
    -------
    X (scipy.sparse.csr_matrix): matriz binaria (n_canciones, n_valores).
    nombres (list): nombres de columna con forma "prefijo:valor".
    """
    valores = sorted({v for vs in valores_por_cancion for v in vs})
    indice = {v: j for j, v in enumerate(valores)}
    filas = [i for i, vs in enumerate(valores_por_cancion) for _ in vs]
    cols = [indice[v] for vs in valores_por_cancion for v in vs]
    X = sp.csr_matrix((np.ones(len(cols), dtype=np.float32), (filas, cols)),
                      shape=(len(valores_por_cancion), len(valores)))
    return X, [f"{prefijo}:{v}" for v in valores]


def main():
    """
    Ejecuta la construcción de características y escribe los artefactos.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    (None): escribe conteos.npz, etiquetas.npz, usos.npz y vocab.json.
    """
    t0 = time.time()
    cat = pl.read_parquet(C.RUTA_CATALOGO)
    letras = pl.read_parquet(C.RUTA_LETRAS_INTERMEDIAS)
    assert (cat["id"] == letras["id"]).all(), "catálogo y letras desalineados"

    vacias = palabras_vacias()
    stemmers = {"en": SnowballStemmer("english"), "es": SnowballStemmer("spanish")}
    cache, formas = {}, defaultdict(Counter)
    docs = [tokenizar(t, idi, vacias, stemmers, cache, formas)
            for t, idi in zip(letras["letra"].to_list(), letras["idioma"].to_list())]
    print(f"Tokenizado ({time.time() - t0:.0f} s)")

    n = len(docs)
    terminos, df = construir_vocabulario(docs, n)
    idf = calcular_idf(df, n)
    X = matriz_conteos(docs, {t: j for j, t in enumerate(terminos)})
    X = podar_por_tfidf(X, idf, C.TERMINOS_POR_CANCION)
    X.data = np.minimum(X.data, np.iinfo(np.uint16).max).astype(np.uint16)
    sp.save_npz(C.RUTA_CONTEOS, X.astype(np.uint16), compressed=True)

    def legible(t):
        return " ".join(formas[r].most_common(1)[0][0] for r in t.split(" "))

    # Etiquetas.
    generos_crudos = [[g.strip().lower() for g in (s or "").split(",") if g.strip()] for s in cat["generos"].to_list()]
    frec_sub = Counter(g for gs in generos_crudos for g in set(gs))
    bloques, nombres = [], []
    for valores, prefijo in [
        ([[g] for g in cat["genero"].to_list()], "género"),
        ([[g for g in set(gs) if frec_sub[g] >= MIN_CANCIONES_SUBGENERO] for gs in generos_crudos], "subgénero"),
        ([[e] for e in cat["emocion"].to_list()], "emoción"),
        ([[f"{d}s"] for d in cat["decada"].to_list()], "década"),
        ([[t] for t in cat["tonica"].to_list()], "tónica"),
        ([[m] for m in cat["modo"].to_list()], "modo"),
        ([[c] for c in cat["compas"].to_list()], "compás"),
        ([["sí"] if e else [] for e in cat["explicita"].to_list()], "explícita"),
    ]:
        Xb, nb = bloque_one_hot(valores, prefijo)
        bloques.append(Xb)
        nombres += nb
    sp.save_npz(C.RUTA_ETIQUETAS, sp.hstack(bloques, format="csr").astype(np.uint8), compressed=True)

    # Usos: se descartan los que casi no varían.
    cols_uso = [f"uso_{d}" for d in C.COLS_USOS.values()]
    fracciones = {c: float(cat[c].mean()) for c in cols_uso}
    usos_ok = [c for c in cols_uso if MIN_FRACCION_USO <= fracciones[c] <= 1 - MIN_FRACCION_USO]
    U = sp.csr_matrix(cat.select(usos_ok).to_numpy().astype(np.uint8))
    sp.save_npz(C.RUTA_USOS, U, compressed=True)

    vocab = {
        "terminos": terminos,
        "idf": [round(float(v), 4) for v in idf],
        "legible": [legible(t) for t in terminos],
        "es_bigrama": [" " in t for t in terminos],
        "etiquetas": nombres,
        "usos": [c.removeprefix("uso_") for c in usos_ok],
        "fraccion_usos": {c.removeprefix("uso_"): round(f, 4) for c, f in fracciones.items()},
        "n_canciones": n,
    }
    C.RUTA_VOCAB.write_text(json.dumps(vocab, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    nnz_fila = np.diff(X.indptr)
    print(f"Vocabulario: {len(terminos):,} términos ({sum(vocab['es_bigrama']):,} bigramas); "
          f"términos por canción: mediana {np.median(nnz_fila):.0f}, mín {nnz_fila.min()}; "
          f"etiquetas: {len(nombres)}; usos: {len(usos_ok)} de {len(cols_uso)} ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
