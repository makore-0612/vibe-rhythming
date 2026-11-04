"""
Perfil del dataset crudo (fase 0).

Lee data/raw/spotify_dataset.csv de forma perezosa con polars y escribe
data/processed/perfil.md con filas, nulos, cardinalidades, duplicados,
distribuciones, idiomas y tamaño de letra.

Uso: python pipeline/perfil_dataset.py
"""

import re
import sys
import time
import unicodedata
from pathlib import Path

import polars as pl

RAIZ = Path(__file__).resolve().parent.parent
RUTA_CSV = RAIZ / "data" / "raw" / "spotify_dataset.csv"
RUTA_SALIDA = RAIZ / "data" / "processed" / "perfil.md"
SEMILLA = 42
N_MUESTRA_IDIOMA = 3000

COLS_AUDIO_0_100 = [
    "Energy", "Danceability", "Positiveness", "Speechiness",
    "Liveness", "Acousticness", "Instrumentalness",
]
COLS_USOS = [
    "Good for Party", "Good for Work/Study", "Good for Relaxation/Meditation",
    "Good for Exercise", "Good for Running", "Good for Yoga/Stretching",
    "Good for Driving", "Good for Social Gatherings", "Good for Morning Routine",
]


def normalizar_texto(s):
    """
    Pasa un texto a minúsculas, sin acentos y sin sufijos de versión.

    inputs:
    -------
    s (str): texto original (artista o título).

    outputs
    -------
    norm (str): texto normalizado para comparar duplicados.
    """
    if s is None:
        return ""
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[\(\[].*?(remaster|live|version|edit|mix|mono|stereo|demo).*?[\)\]]", "", s)
    s = re.sub(r"\s-\s.*(remaster|live|version|edit|mix|mono|stereo|demo).*$", "", s)
    s = re.sub(r"[^a-z0-9ñ ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def tabla_md(df):
    """
    Convierte un DataFrame pequeño de polars en tabla Markdown.

    inputs:
    -------
    df (polars.DataFrame): tabla a convertir.

    outputs
    -------
    md (str): tabla en formato Markdown.
    """
    cols = df.columns
    filas = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for fila in df.iter_rows():
        celdas = []
        for v in fila:
            if isinstance(v, float):
                celdas.append(f"{v:,.3f}")
            elif isinstance(v, int):
                celdas.append(f"{v:,}")
            else:
                celdas.append(str(v).replace("|", "\\|")[:60])
        filas.append("| " + " | ".join(celdas) + " |")
    return "\n".join(filas)


def describir_numerica(lf, col):
    """
    Calcula mínimo, cuantiles, máximo, media y nulos de una columna numérica.

    inputs:
    -------
    lf (polars.LazyFrame): datos con la columna ya convertida a número.
    col (str): nombre de la columna.

    outputs
    -------
    fila (dict): estadísticos de la columna.
    """
    c = pl.col(col)
    r = lf.select(
        c.min().alias("min"), c.quantile(0.05).alias("p05"), c.median().alias("mediana"),
        c.quantile(0.95).alias("p95"), c.max().alias("max"), c.mean().alias("media"),
        c.is_null().sum().alias("nulos"),
    ).collect().row(0, named=True)
    return {"columna": col, **{k: (float(v) if v is not None and k != "nulos" else v) for k, v in r.items()}}


def main():
    """
    Genera el reporte de perfil del dataset.

    inputs:
    -------
    (ninguno): lee la ruta fija RUTA_CSV.

    outputs
    -------
    (None): escribe RUTA_SALIDA e imprime el tiempo total.
    """
    t0 = time.time()
    if not RUTA_CSV.exists():
        sys.exit(f"Falta el dataset en {RUTA_CSV}")
    RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)

    crudo = pl.scan_csv(RUTA_CSV, infer_schema=False)
    columnas = crudo.collect_schema().names()
    secciones = [f"# Perfil del dataset\n\nArchivo: `data/raw/{RUTA_CSV.name}` "
                 f"({RUTA_CSV.stat().st_size / 1e9:.2f} GB)\n"]

    # Todo menos la letra cabe en memoria; de la letra solo guardamos longitudes.
    base = crudo.with_columns(
        pl.col("text").str.len_chars().alias("letra_chars"),
        pl.col("text").str.count_matches(r"\S+").alias("letra_palabras"),
    ).drop("text").collect()
    n = base.height
    secciones.append(f"## Tamaño\n\n- Filas: **{n:,}**\n- Columnas: **{len(columnas)}**\n"
                     f"- Columnas: {', '.join(f'`{c}`' for c in columnas)}\n")

    # Nulos y cardinalidades (cadena vacía cuenta como nulo).
    filas = []
    for c in columnas:
        if c == "text":
            vacios = crudo.select((pl.col("text").is_null() | (pl.col("text").str.strip_chars() == "")).sum()).collect().item()
            filas.append({"columna": c, "nulos": vacios, "pct_nulos": 100 * vacios / n, "distintos": -1, "ejemplo": "(letra)"})
            continue
        s = base[c]
        vacios = (s.is_null() | (s.str.strip_chars() == "")).sum()
        ejemplo = s.drop_nulls().head(1).to_list()
        filas.append({"columna": c, "nulos": int(vacios), "pct_nulos": 100 * vacios / n,
                      "distintos": s.n_unique(), "ejemplo": ejemplo[0] if ejemplo else ""})
    secciones.append("## Nulos y cardinalidad\n\n" + tabla_md(pl.DataFrame(filas)) + "\n")

    # Formatos de campos con texto estructurado.
    def patron(col):
        return (base.select(pl.col(col).str.replace_all(r"[A-Za-z]+", "A").str.replace_all(r"\d+", "9").alias("patron"))
                .group_by("patron").len().sort("len", descending=True).head(8))
    for col in ["Length", "Release Date", "Loudness (db)", "Tempo", "Popularity", "Time signature"]:
        secciones.append(f"## Formatos de `{col}`\n\n" + tabla_md(patron(col)) + "\n")

    # Conversión de tipos para distribuciones.
    num = base.lazy().with_columns(
        (pl.col("Length").str.split(":").list.get(0, null_on_oob=True).cast(pl.Int32, strict=False) * 60
         + pl.col("Length").str.split(":").list.get(1, null_on_oob=True).cast(pl.Int32, strict=False)).alias("duracion_s"),
        pl.col("Tempo").cast(pl.Float64, strict=False).alias("tempo"),
        pl.col("Loudness (db)").str.replace("db", "").cast(pl.Float64, strict=False).alias("volumen_db"),
        pl.col("Popularity").cast(pl.Float64, strict=False).alias("popularidad"),
        pl.col("Release Date").str.extract(r"(\d{4})").cast(pl.Int32, strict=False).alias("anio"),
        *[pl.col(c).cast(pl.Float64, strict=False) for c in COLS_AUDIO_0_100],
        *[pl.col(c).cast(pl.Float64, strict=False) for c in COLS_USOS],
        *[pl.col(f"Similarity Score {i}").cast(pl.Float64, strict=False) for i in (1, 2, 3)],
    )
    numericas = ["duracion_s", "tempo", "volumen_db", "popularidad", "anio", *COLS_AUDIO_0_100,
                 "Similarity Score 1", "Similarity Score 3", "letra_chars", "letra_palabras"]
    secciones.append("## Distribuciones numéricas\n\n`duracion_s`, `tempo`, `volumen_db`, `anio` y "
                     "`popularidad` son conversiones del texto original.\n\n"
                     + tabla_md(pl.DataFrame([describir_numerica(num, c) for c in numericas])) + "\n")

    usos = num.select([pl.col(c).mean().alias(c) for c in COLS_USOS]).collect().transpose(
        include_header=True, header_name="uso", column_names=["fraccion_1"])
    secciones.append("## Columnas `Good for ...` (fracción con 1)\n\n" + tabla_md(usos) + "\n")

    # Categóricas.
    for col in ["emotion", "Genre", "Key", "Time signature", "Explicit"]:
        vc = base.group_by(col).len().sort("len", descending=True)
        secciones.append(f"## `{col}` ({vc.height} valores)\n\n" + tabla_md(vc.head(25)) + "\n")
    multi = base.select(pl.col("Genre").str.contains(",").mean()).item()
    secciones.append(f"Fracción de registros con coma en `Genre` (varios géneros): **{multi:.1%}**\n")

    # Etiquetas ruidosas: emoción contra positividad.
    emo = (num.group_by("emotion").agg(pl.len().alias("n"), pl.col("Positiveness").mean().alias("positividad_media"),
                                       pl.col("Energy").mean().alias("energia_media"))
           .sort("n", descending=True).collect())
    secciones.append("## Relación `emotion` – `Positiveness`\n\nSi la etiqueta fuera fiel, `joy` tendría "
                     "positividad mucho mayor que `sadness`.\n\n" + tabla_md(emo.head(12)) + "\n")

    # Duplicados.
    norm = base.select(
        pl.col("Artist(s)").map_elements(normalizar_texto, return_dtype=pl.String).alias("a"),
        pl.col("song").map_elements(normalizar_texto, return_dtype=pl.String).alias("s"),
    )
    exactos = n - base.select(["Artist(s)", "song"]).unique().height
    normalizados = n - norm.unique().height
    filas_iguales = n - base.unique().height
    secciones.append(f"## Duplicados\n\n- Filas idénticas (sin contar letra): **{filas_iguales:,}**\n"
                     f"- Mismo artista y título exactos: **{exactos:,}**\n"
                     f"- Mismo artista y título normalizados: **{normalizados:,}**\n"
                     f"- Artistas distintos: **{base['Artist(s)'].n_unique():,}**\n")

    # Similar Songs: cuántos apuntan a canciones que existen en el dataset.
    claves = set(zip(norm["a"].to_list(), norm["s"].to_list()))
    muestra_sim = base.sample(n=min(20000, n), seed=SEMILLA)
    hits = total = 0
    for i in (1, 2, 3):
        for a, s in zip(muestra_sim[f"Similar Artist {i}"].to_list(), muestra_sim[f"Similar Song {i}"].to_list()):
            total += 1
            hits += (normalizar_texto(a), normalizar_texto(s)) in claves
    secciones.append(f"## `Similar Songs`\n\nVienen aplanadas en 9 columnas (artista, canción y puntaje × 3). "
                     f"En una muestra de 20,000 filas, **{hits / total:.1%}** de los similares existen en el "
                     f"dataset (artista y título normalizados).\n")

    # Idiomas en una muestra.
    from langdetect import DetectorFactory, detect
    DetectorFactory.seed = SEMILLA
    muestra = (crudo.select("text").with_row_index("i")
               .filter((pl.col("i").hash(SEMILLA) % max(1, n // N_MUESTRA_IDIOMA)) == 0)
               .head(N_MUESTRA_IDIOMA).collect()["text"].to_list())
    idiomas = {}
    for t in muestra:
        try:
            lang = detect((t or "")[:1000])
        except Exception:
            lang = "desconocido"
        idiomas[lang] = idiomas.get(lang, 0) + 1
    tab_id = pl.DataFrame({"idioma": list(idiomas), "n": list(idiomas.values())}).sort("n", descending=True)
    tab_id = tab_id.with_columns((100 * pl.col("n") / pl.col("n").sum()).alias("pct"))
    secciones.append(f"## Idiomas (muestra de {len(muestra):,} letras, `langdetect`)\n\n" + tabla_md(tab_id.head(15)) + "\n")

    # Saltos de línea dentro de la letra.
    con_salto = crudo.select(pl.col("text").str.contains("\n").mean()).collect().item()
    secciones.append(f"## Letras\n\nFracción con saltos de línea: **{con_salto:.1%}**. Letras con menos de "
                     f"50 palabras: **{(base['letra_palabras'] < 50).sum():,}**.\n")

    RUTA_SALIDA.write_text("\n".join(secciones), encoding="utf-8")
    print(f"Escrito {RUTA_SALIDA} en {time.time() - t0:.1f} s")


if __name__ == "__main__":
    main()
