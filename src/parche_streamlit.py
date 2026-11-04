"""
Parche para un bug del servidor Starlette de Streamlit 1.58 en Community Cloud.

Streamlit evita comprimir con gzip los archivos de su interfaz solo si la ruta empieza con "/static/".
En Community Cloud las rutas llevan el prefijo "/~/+/static/...", así que pasan por su middleware de
gzip, que a veces envía el cuerpo de la respuesta antes que la cabecera ("Expected ASGI message
'http.response.start', but got 'http.response.body'"). El navegador recibe entonces una descarga
fallida: "Failed to fetch dynamically imported module".

El parche hace que esas rutas también se salten la compresión. Si la estructura interna de Streamlit
cambia, no hace nada.
"""

try:
    from streamlit.web.server.starlette import starlette_gzip_middleware as _gzip
except ImportError:  # otra versión de Streamlit sin servidor Starlette
    _gzip = None


def evitar_gzip_en_estaticos(ruta):
    """
    Decide si una ruta HTTP se sirve sin compresión gzip.

    inputs:
    -------
    ruta (str): ruta de la petición, por ejemplo "/~/+/static/js/ButtonGroup.js".

    outputs
    -------
    evitar (bool): True para la raíz y para cualquier ruta con un segmento "/static/".
    """
    return not ruta or ruta == "/" or "/static/" in ruta


def aplicar():
    """
    Sustituye la función de Streamlit que decide qué rutas se saltan el gzip.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    aplicado (bool): True si el parche quedó activo.
    """
    if _gzip is None or not hasattr(_gzip, "_should_bypass_static_gzip"):
        return False
    _gzip._should_bypass_static_gzip = evitar_gzip_en_estaticos
    return True
