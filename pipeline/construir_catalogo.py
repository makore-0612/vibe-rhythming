"""
Construye el catálogo reducido (§4.3 de CLAUDE.md).

Salidas:
- data/processed/catalogo.parquet: metadatos y audio, sin letras.
- data/processed/similares.parquet: pares de `Similar Songs` dentro del catálogo.
- data/processed/reporte_catalogo.md: distribuciones antes y después del muestreo.
- data/intermedio/letras.parquet: letras del catálogo (NO se publica).

Uso: python pipeline/construir_catalogo.py
"""

import math
import os
import sys
import time
import unicodedata
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import config as C  # noqa: E402

RE_TITULO_RUIDOSO = r"(?i)\b(track \d+|untitled|skit|interlude)\b|^(intro|outro)$"
RE_SUFIJO_VERSION = (r"(?i)\s*[\(\[\-]?\s*(\d{4}\s+)?(album version|original mix|remaster(ed)?(\s+\d{4})?(\s+version)?"
                     r"|live( version| at .*)?|radio edit|single version|mono|stereo|demo( version)?|acoustic version"
                     r"|bonus track|explicit|clean)\s*[\)\]]?\s*$")
RE_ESPANOL = r"\b(que|quiero|corazón|corazon|contigo|porque|pero|tú|mí|amor|vida|nada|nunca|siempre|eres|estoy)\b"


def sin_acentos(s):
    """
    Quita acentos y pasa a minúsculas.

    inputs:
    -------
    s (str): texto original.

    outputs
    -------
    limpio (str): texto en minúsculas sin marcas diacríticas.
    """
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def expr_normalizada(col):
    """
    Expresión de polars que normaliza artista o título para deduplicar y buscar.

    inputs:
    -------
    col (str): nombre de la columna de texto.

    outputs
    -------
    expr (polars.Expr): texto sin acentos, sin sufijos de versión y sin puntuación.
    """
    return (pl.col(col).str.replace(RE_SUFIJO_VERSION, "").str.replace(r"\s+-\s+.*$", "")
            .map_elements(sin_acentos, return_dtype=pl.String)
            .str.replace_all(r"['’`]", "").str.replace_all(r"[^a-z0-9ñ ]+", " ").str.replace_all(r"\s+", " ").str.strip_chars())


def macrogenero(genero_crudo):
    """
    Asigna el macrogénero a partir del primer valor de `Genre`.

    inputs:
    -------
    genero_crudo (str): valor original, posiblemente con varios géneros separados por coma.

    outputs
    -------
    macro (str): nombre del macrogénero o MACROGENERO_OTRO.
    """
    primero = (genero_crudo or "").split(",")[0].strip().lower()
    for macro, lista in C.MACROGENEROS.items():
        if primero in lista:
            return macro
    return C.MACROGENERO_OTRO


def detectar_idioma(texto):
    """
    Detecta el idioma de una letra con langdetect usando sus primeros 1,000 caracteres.

    inputs:
    -------
    texto (str): letra completa.

    outputs
    -------
    idioma (str): código ISO 639-1 o "??" si no se pudo detectar.
    """
    from langdetect import DetectorFactory, detect
    DetectorFactory.seed = C.SEMILLA
    try:
        return detect(texto[:1000])
    except Exception:
        return "??"


def cargar_y_limpiar():
    """
    Lee el CSV, convierte tipos, filtra registros inválidos y deduplica.

    inputs:
    -------
    (ninguno): lee C.RUTA_CSV.

    outputs
    -------
    df (polars.DataFrame): una fila por canción única, con letra y columnas tipadas.
    """
    lf = pl.scan_csv(C.RUTA_CSV, infer_schema=False)
    lf = lf.filter(
        pl.col("Artist(s)").str.strip_chars().str.len_chars() > 0,
        pl.col("song").str.strip_chars().str.len_chars() > 0,
        pl.col("text").str.count_matches(r"\S+") >= C.MIN_PALABRAS_LETRA,
        pl.col("emotion").is_in(C.EMOCIONES_VALIDAS),
        ~pl.col("song").str.contains(RE_TITULO_RUIDOSO),
        pl.col("song").str.contains(r"[A-Za-z0-9]"),
    )
    duracion = pl.col("Length").str.split(":")
    lf = lf.select(
        pl.col("Artist(s)").str.strip_chars().alias("artista"),
        pl.col("song").str.replace(RE_SUFIJO_VERSION, "").str.strip_chars().alias("titulo"),
        pl.col("Album").fill_null("").str.slice(0, 150).alias("album"),
        pl.col("text").alias("letra"),
        pl.col("Genre").str.slice(0, 150).alias("generos"),
        pl.col("emotion").alias("emocion"),
        pl.col("Release Date").str.extract(r"(\d{4})").cast(pl.Int16, strict=False).alias("anio"),
        pl.col("Key").str.split(" ").list.get(0).alias("tonica"),
        pl.when(pl.col("Key").str.ends_with("min")).then(pl.lit("menor")).otherwise(pl.lit("mayor")).alias("modo"),
        pl.col("Time signature").fill_null("4/4").alias("compas"),
        (pl.col("Explicit") == "Yes").alias("explicita"),
        pl.col("Popularity").cast(pl.Int16).alias("popularidad"),
        (duracion.list.get(0).cast(pl.Int32) * 60 + duracion.list.get(1).cast(pl.Int32)).cast(pl.Int16).alias("duracion_s"),
        pl.col("Tempo").cast(pl.Float32).alias("tempo"),
        pl.col("Loudness (db)").str.replace("db", "").cast(pl.Float32).alias("volumen_db"),
        *[(pl.col(o).cast(pl.Float32) / 100).alias(d) for o, d in C.COLS_AUDIO.items()],
        *[(pl.col(o) == "1").alias(f"uso_{d}") for o, d in C.COLS_USOS.items()],
        *[pl.col(f"Similar Artist {i}").alias(f"sim_artista_{i}") for i in (1, 2, 3)],
        *[pl.col(f"Similar Song {i}").alias(f"sim_titulo_{i}") for i in (1, 2, 3)],
        *[pl.col(f"Similarity Score {i}").cast(pl.Float32).alias(f"sim_puntaje_{i}") for i in (1, 2, 3)],
    )
    df = lf.collect()
    # Algunas colaboraciones listan decenas de artistas; para mostrar bastan los primeros.
    df = df.with_columns(
        pl.when(pl.col("artista").str.len_chars() > 120)
        .then(pl.col("artista").str.split(",").list.head(3).list.join(",") + pl.lit(" y otros"))
        .otherwise(pl.col("artista")).str.slice(0, 150).alias("artista"),
        pl.col("titulo").str.slice(0, 150),
    )
    df = df.with_columns(expr_normalizada("artista").alias("artista_norm"),
                         expr_normalizada("titulo").alias("titulo_norm"))
    df = (df.sort("popularidad", descending=True, maintain_order=True)
          .unique(["artista_norm", "titulo_norm"], keep="first", maintain_order=True))
    df = df.with_columns(
        pl.col("generos").map_elements(macrogenero, return_dtype=pl.String).alias("genero"),
        ((pl.col("anio") // 10) * 10).alias("decada"),
    )
    return df


def cuotas_por_genero(conteos, n_total):
    """
    Reparte n_total canciones entre géneros en proporción a la raíz de su tamaño.

    inputs:
    -------
    conteos (dict): género → número de canciones disponibles.
    n_total (int): tamaño objetivo del catálogo.

    outputs
    -------
    cuotas (dict): género → canciones asignadas, sin exceder lo disponible.
    """
    cuotas = {g: 0 for g in conteos}
    restante, activos = n_total, set(conteos)
    while restante > 0 and activos:
        raiz = {g: math.sqrt(conteos[g]) for g in activos}
        suma = sum(raiz.values())
        asignado = 0
        for g in list(activos):
            extra = min(conteos[g] - cuotas[g], int(round(restante * raiz[g] / suma)))
            cuotas[g] += extra
            asignado += extra
            if cuotas[g] >= conteos[g]:
                activos.discard(g)
        if asignado == 0:
            break
        restante -= asignado
    return cuotas


def distribucion_md(df, titulo):
    """
    Resume en Markdown las distribuciones principales de un DataFrame de canciones.

    inputs:
    -------
    df (polars.DataFrame): canciones con genero, emocion, decada y popularidad.
    titulo (str): encabezado de la sección.

    outputs
    -------
    md (str): sección en Markdown.
    """
    partes = [f"## {titulo}\n\nCanciones: **{df.height:,}** · artistas: **{df['artista'].n_unique():,}** · "
              f"popularidad media: **{df['popularidad'].mean():.1f}** · explícitas: **{df['explicita'].mean():.1%}**\n"]
    for col in ["genero", "emocion", "decada"] + (["idioma"] if "idioma" in df.columns else []):
        vc = df.group_by(col).len().sort("len", descending=True)
        partes.append(f"**{col}:** " + ", ".join(f"{v} {n / df.height:.1%}" for v, n in vc.iter_rows()) + "\n")
    return "\n".join(partes)


def main():
    """
    Ejecuta la construcción del catálogo y escribe los artefactos.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    (None): escribe archivos en data/processed y data/intermedio.
    """
    t0 = time.time()
    rng = np.random.default_rng(C.SEMILLA)
    C.DIR_PROCESADO.mkdir(parents=True, exist_ok=True)
    C.DIR_INTERMEDIO.mkdir(parents=True, exist_ok=True)

    df = cargar_y_limpiar()
    reporte = ["# Reporte del catálogo\n", distribucion_md(df, "Antes del muestreo (limpio y deduplicado)")]
    print(f"Limpio y deduplicado: {df.height:,} canciones ({time.time() - t0:.0f} s)")

    # Tope por artista: conserva sus canciones más populares.
    df = (df.with_columns(pl.col("popularidad").rank("ordinal", descending=True).over("artista").alias("_rank_art"))
          .filter(pl.col("_rank_art") <= C.TOPE_POR_ARTISTA_CATALOGO).drop("_rank_art"))
    df = df.with_row_index("_fila")

    conteos = dict(df.group_by("genero").len().iter_rows())
    cuotas = cuotas_por_genero(conteos, C.CATALOGO_N)

    # Candidatas por género: populares + azar, con holgura para lo que no sea inglés o español.
    holgura = 1.3
    candidatas = {}
    for g, q in cuotas.items():
        sub = df.filter(pl.col("genero") == g).sort("popularidad", descending=True)
        n_pop = int(round(q * C.FRACCION_POPULARES))
        top = sub.head(int(n_pop * holgura) + 5)["_fila"].to_list()
        resto = sub.slice(n_pop)["_fila"].to_numpy()
        azar = rng.choice(resto, size=min(len(resto), int((q - n_pop) * holgura) + 5), replace=False).tolist()
        candidatas[g] = (top, azar, n_pop, q - n_pop)

    # Todo lo que parezca español entra a detección, sin importar la cuota.
    posibles_es = (df.with_columns((pl.col("letra").str.to_lowercase().str.count_matches(RE_ESPANOL)
                                    / pl.col("letra").str.count_matches(r"\S+")).alias("_r"))
                   .filter(pl.col("_r") > 0.03)["_fila"].to_list())

    filas_a_detectar = sorted({f for t, a, _, _ in candidatas.values() for f in t + a} | set(posibles_es))
    letras = df["letra"]
    t1 = time.time()
    with Pool(max(1, min(12, (os.cpu_count() or 2) - 2))) as pool:
        idiomas = pool.map(detectar_idioma, [letras[i] for i in filas_a_detectar], chunksize=200)
    idioma_de = dict(zip(filas_a_detectar, idiomas))
    print(f"Idioma detectado en {len(filas_a_detectar):,} candidatas ({time.time() - t1:.0f} s)")

    elegidas = []
    for g, (top, azar, n_pop, n_azar) in candidatas.items():
        elegidas += [f for f in top if idioma_de[f] in C.IDIOMAS_VALIDOS][:n_pop]
        elegidas += [f for f in azar if idioma_de[f] in C.IDIOMAS_VALIDOS][:n_azar]
    elegidas = set(elegidas) | {f for f in posibles_es if idioma_de[f] == "es"}

    cat = (df.filter(pl.col("_fila").is_in(list(elegidas)))
           .with_columns(pl.col("_fila").replace_strict(idioma_de, return_dtype=pl.String).alias("idioma"))
           .sort(["popularidad", "artista", "titulo"], descending=[True, False, False])
           .with_row_index("id").with_columns(pl.col("id").cast(pl.Int32)))
    reporte.append(distribucion_md(cat, "Después del muestreo"))
    reporte.append("**Cuotas por macrogénero (raíz del tamaño):** "
                   + ", ".join(f"{g} {q:,}" for g, q in sorted(cuotas.items(), key=lambda x: -x[1])) + "\n")
    top_art = cat.head(40).select(pl.format("{} – {}", "artista", "titulo")).to_series().to_list()
    reporte.append("**Las 40 más populares del catálogo:** " + "; ".join(top_art) + "\n")

    # Pares de Similar Songs que caen dentro del catálogo.
    clave_a_id = {(a, t): i for i, a, t in cat.select("id", "artista_norm", "titulo_norm").iter_rows()}
    pares = []
    for i in (1, 2, 3):
        sim = cat.select("id", expr_normalizada(f"sim_artista_{i}").alias("a"),
                         expr_normalizada(f"sim_titulo_{i}").alias("t"), f"sim_puntaje_{i}")
        for origen, a, t, p in sim.iter_rows():
            destino = clave_a_id.get((a, t))
            if destino is not None and destino != origen:
                pares.append((origen, destino, i, p))
    similares = pl.DataFrame(pares, schema={"id_origen": pl.Int32, "id_similar": pl.Int32,
                                            "posicion": pl.Int8, "puntaje": pl.Float32}, orient="row")
    similares.write_parquet(C.RUTA_SIMILARES, compression="zstd")
    reporte.append(f"**Pares de `Similar Songs` dentro del catálogo:** {similares.height:,} "
                   f"({similares['id_origen'].n_unique():,} canciones de origen)\n")

    cat.select("id", "idioma", "letra").write_parquet(C.RUTA_LETRAS_INTERMEDIAS, compression="zstd")
    busqueda = pl.concat_str([pl.col("artista_norm"), pl.col("titulo_norm"),
                              pl.col("album").map_elements(sin_acentos, return_dtype=pl.String)], separator=" ")
    publico = cat.with_columns(busqueda.str.slice(0, 190).alias("busqueda"),
                               pl.col("titulo_norm").str.slice(0, 24).alias("titulo_base")).drop(
        ["letra", "_fila", "artista_norm", "titulo_norm"]
        + [c for c in cat.columns if c.startswith("sim_")])
    publico.write_parquet(C.RUTA_CATALOGO, compression="zstd")
    (C.DIR_PROCESADO / "reporte_catalogo.md").write_text("\n".join(reporte), encoding="utf-8")
    print(f"Catálogo: {publico.height:,} canciones, {similares.height:,} pares similares ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
