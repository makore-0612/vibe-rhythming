"""
Pruebas sobre los artefactos publicables de data/processed/.
"""

import json
import sys
from pathlib import Path

import numpy as np
import polars as pl
import pytest
import scipy.sparse as sp

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import config as C  # noqa: E402

MAX_CHARS = 200


def cadenas_json(obj):
    """
    Recorre un objeto JSON y devuelve todas sus cadenas, incluidas las llaves.

    inputs:
    -------
    obj (object): objeto cargado con json.

    outputs
    -------
    cadenas (list): todas las cadenas encontradas.
    """
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        return [s for k, v in obj.items() for s in [k, *cadenas_json(v)]]
    if isinstance(obj, list):
        return [s for v in obj for s in cadenas_json(v)]
    return []


@pytest.mark.parametrize("ruta", sorted(C.DIR_PROCESADO.glob("*.parquet")), ids=lambda p: p.name)
def test_parquet_sin_letras(ruta):
    """
    Falla si alguna columna de texto de un parquet publicado tiene cadenas de más de 200 caracteres.

    inputs:
    -------
    ruta (pathlib.Path): archivo parquet a revisar.

    outputs
    -------
    (None)
    """
    df = pl.read_parquet(ruta)
    assert "letra" not in df.columns and "text" not in df.columns
    for col in df.columns:
        if df[col].dtype == pl.String:
            largo = df[col].str.len_chars().max() or 0
            assert largo <= MAX_CHARS, f"{ruta.name}:{col} tiene cadenas de {largo} caracteres"


@pytest.mark.parametrize("ruta", sorted(C.DIR_PROCESADO.glob("*.json")), ids=lambda p: p.name)
def test_json_sin_letras(ruta):
    """
    Falla si un JSON publicado contiene cadenas de más de 200 caracteres.

    inputs:
    -------
    ruta (pathlib.Path): archivo JSON a revisar.

    outputs
    -------
    (None)
    """
    largos = [len(s) for s in cadenas_json(json.loads(ruta.read_text(encoding="utf-8")))]
    assert max(largos, default=0) <= MAX_CHARS


def test_npz_solo_numeros():
    """
    Los NPZ publicados solo pueden contener arreglos numéricos.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    (None)
    """
    for ruta in C.DIR_PROCESADO.glob("*.npz"):
        with np.load(ruta, allow_pickle=False) as z:
            for k in z.files:
                if k == "format":  # metadato de scipy: b"csr"
                    assert z[k].nbytes <= 8
                    continue
                assert z[k].dtype.kind in "biuf", f"{ruta.name}:{k} no es numérico"


def test_formas_alineadas():
    """
    Todas las matrices tienen una fila por canción y columnas acordes al vocabulario.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    (None)
    """
    n = pl.read_parquet(C.RUTA_CATALOGO).height
    vocab = json.loads(C.RUTA_VOCAB.read_text(encoding="utf-8"))
    assert sp.load_npz(C.RUTA_CONTEOS).shape == (n, len(vocab["terminos"]))
    assert sp.load_npz(C.RUTA_ETIQUETAS).shape == (n, len(vocab["etiquetas"]))
    assert sp.load_npz(C.RUTA_USOS).shape == (n, len(vocab["usos"]))
    assert len(vocab["idf"]) == len(vocab["terminos"]) == len(vocab["legible"])


def test_presupuesto():
    """
    Ningún artefacto excede su límite y el total queda bajo 50 MB.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    (None)
    """
    total = 0
    for nombre, limite in C.PRESUPUESTO.items():
        tam = (C.DIR_PROCESADO / nombre).stat().st_size
        assert tam <= limite, nombre
        total += tam
    assert total <= C.PRESUPUESTO_TOTAL
