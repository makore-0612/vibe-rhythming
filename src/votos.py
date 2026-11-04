"""
Votación en vivo compartida entre sesiones: un diccionario protegido con un Lock dentro de
st.cache_resource. Es anónima y se borra si la app se reinicia.
"""

import threading

import streamlit as st

OPCIONES = ["vecinos", "naive_bayes", "reglas", "regresion"]


@st.cache_resource
def urna():
    """
    Crea la urna compartida una sola vez por proceso.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    urna (dict): "conteos" (opción → votos), "por_sesion" (sesión → opción) y "lock".
    """
    return {"conteos": {o: 0 for o in OPCIONES}, "por_sesion": {}, "lock": threading.Lock()}


def votar(sesion, opcion):
    """
    Registra o cambia el voto de una sesión.

    inputs:
    -------
    sesion (str): identificador anónimo de la sesión.
    opcion (str): una de OPCIONES.

    outputs
    -------
    (None)
    """
    u = urna()
    with u["lock"]:
        previo = u["por_sesion"].get(sesion)
        if previo == opcion:
            return
        if previo is not None:
            u["conteos"][previo] -= 1
        u["conteos"][opcion] += 1
        u["por_sesion"][sesion] = opcion


def resultados():
    """
    Copia los conteos actuales.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    conteos (dict): opción → votos.
    """
    u = urna()
    with u["lock"]:
        return dict(u["conteos"])


def voto_de(sesion):
    """
    Devuelve la opción votada por una sesión.

    inputs:
    -------
    sesion (str): identificador anónimo de la sesión.

    outputs
    -------
    opcion (str | None): opción votada o None.
    """
    return urna()["por_sesion"].get(sesion)


def reiniciar(codigo):
    """
    Borra todos los votos si el código coincide con st.secrets["codigo_votos"].

    inputs:
    -------
    codigo (str): código escrito por quien expone.

    outputs
    -------
    ok (bool): True si se reinició.
    """
    try:
        esperado = st.secrets.get("codigo_votos")
    except Exception:
        esperado = None
    if not esperado or codigo != esperado:
        return False
    u = urna()
    with u["lock"]:
        u["conteos"] = {o: 0 for o in OPCIONES}
        u["por_sesion"] = {}
    return True
