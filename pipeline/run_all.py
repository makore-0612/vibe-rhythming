"""
Corre el pipeline completo y verifica el presupuesto de artefactos (§4.5 de CLAUDE.md).

Uso: python pipeline/run_all.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from src import config as C  # noqa: E402

import construir_catalogo  # noqa: E402
import construir_features  # noqa: E402
import evaluar_similares  # noqa: E402


def revisar_presupuesto():
    """
    Imprime el tamaño de cada artefacto y falla si se excede el presupuesto.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    total (int): bytes totales de los artefactos publicables.
    """
    total, errores = 0, []
    for nombre, limite in C.PRESUPUESTO.items():
        ruta = C.DIR_PROCESADO / nombre
        if not ruta.exists():
            errores.append(f"falta {nombre}")
            continue
        tam = ruta.stat().st_size
        total += tam
        estado = "ok" if tam <= limite else "EXCEDIDO"
        print(f"  {nombre:22s} {tam / 1e6:7.2f} MB  (límite {limite / 1e6:.0f} MB)  {estado}")
        if tam > limite:
            errores.append(f"{nombre} excede su límite")
    print(f"  {'TOTAL':22s} {total / 1e6:7.2f} MB  (límite {C.PRESUPUESTO_TOTAL / 1e6:.0f} MB)")
    if total > C.PRESUPUESTO_TOTAL:
        errores.append("el total excede el presupuesto")
    if errores:
        sys.exit("Presupuesto no cumplido: " + "; ".join(errores))
    return total


def main():
    """
    Ejecuta los pasos del pipeline en orden y revisa el presupuesto.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    (None)
    """
    t0 = time.time()
    for paso in (construir_catalogo, construir_features, evaluar_similares):
        print(f"== {paso.__name__}")
        paso.main()
    print(f"== Artefactos")
    revisar_presupuesto()
    print(f"Pipeline completo en {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
