"""
Pruebas del parche de gzip para rutas estáticas con prefijo de Community Cloud.
"""

import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import parche_streamlit  # noqa: E402

gz = pytest.importorskip("streamlit.web.server.starlette.starlette_gzip_middleware")


def pasa_directo(ruta):
    """
    Indica si el middleware de Streamlit entrega la petición sin envolver el `send` (sin gzip).

    inputs:
    -------
    ruta (str): ruta HTTP de la petición.

    outputs
    -------
    directo (bool): True si la app interna recibió el mismo `send` original.
    """
    recibido = {}

    async def app(scope, receive, send):
        recibido["send"] = send

    async def send(message):
        pass

    async def receive():
        return {"type": "http.request"}

    mw = gz.SelectiveGZipMiddleware(app, minimum_size=500)
    scope = {"type": "http", "path": ruta, "headers": [(b"accept-encoding", b"gzip")]}
    asyncio.run(mw(scope, receive, send))
    return recibido["send"] is send


def test_rutas_estaticas_sin_gzip():
    """
    Con el parche, los archivos de la interfaz con prefijo /~/+/ se saltan el gzip, y el resto no cambia.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    (None)
    """
    assert parche_streamlit.aplicar()
    assert pasa_directo("/static/js/ButtonGroup.js")
    assert pasa_directo("/~/+/static/js/ButtonGroup.js")
    assert pasa_directo("/~/+/app/static/Montserrat.ttf")
    assert not pasa_directo("/~/+/_stcore/health")
