"""
Selección del usuario en session_state (solo listas de ids), sincronizada con la URL.
"""

import streamlit as st

from src import config as C


def _leer_ids(texto, n):
    """
    Convierte "1.2.3" en lista de ids válidos.

    inputs:
    -------
    texto (str): ids separados por punto.
    n (int): tamaño del catálogo.

    outputs
    -------
    ids (list): enteros únicos dentro de [0, n).
    """
    ids = []
    for t in (texto or "").split("."):
        if t.isdigit() and int(t) < n and int(t) not in ids:
            ids.append(int(t))
    return ids


def iniciar(n):
    """
    Inicializa la selección desde la URL la primera vez que corre la sesión.

    inputs:
    -------
    n (int): tamaño del catálogo.

    outputs
    -------
    (None)
    """
    if "L" not in st.session_state:
        st.session_state.L = _leer_ids(st.query_params.get("l"), n)
        st.session_state.D = [i for i in _leer_ids(st.query_params.get("d"), n) if i not in st.session_state.L]
    # Reasignar evita que Streamlit borre el valor cuando la página actual no dibuja el interruptor.
    st.session_state.ocultar_explicitas = st.session_state.get("ocultar_explicitas", True)


def sincronizar_url():
    """
    Escribe la selección actual en los parámetros de la URL.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    (None)
    """
    for clave, lista in (("l", st.session_state.L), ("d", st.session_state.D)):
        if lista:
            st.query_params[clave] = ".".join(str(i) for i in lista)
        elif clave in st.query_params:
            del st.query_params[clave]


def calificar(i, valor):
    """
    Marca una canción como me gusta (+1), no me gusta (−1) o la quita (0). Repetir la misma
    calificación la quita.

    inputs:
    -------
    i (int): id de la canción.
    valor (int): +1, −1 o 0.

    outputs
    -------
    (None)
    """
    i = int(i)
    L, D = st.session_state.L, st.session_state.D
    previo = 1 if i in L else (-1 if i in D else 0)
    if i in L:
        L.remove(i)
    if i in D:
        D.remove(i)
    if valor == 1 and previo != 1:
        L.append(i)
    elif valor == -1 and previo != -1:
        D.append(i)
    sincronizar_url()


def cargar_demo(M):
    """
    Reemplaza la selección por el perfil demo "John".

    inputs:
    -------
    M (dict): modelo cargado.

    outputs
    -------
    encontrados (int): canciones del perfil que sí existen en el catálogo.
    """
    cat = M["cat"]

    def buscar(artista, titulo):
        m = (cat["artista"].str.lower().str.contains(artista.lower(), regex=False)
             & cat["titulo"].str.lower().str.contains(titulo.lower(), regex=False))
        return int(cat.index[m][0]) if m.any() else None

    L = [x for x in (buscar(a, t) for a, t in C.PERFIL_DEMO["me_gusta"]) if x is not None]
    D = [x for x in (buscar(a, t) for a, t in C.PERFIL_DEMO["no_me_gusta"]) if x is not None and x not in L]
    st.session_state.L, st.session_state.D = L, D
    sincronizar_url()
    return len(L) + len(D)


def vaciar():
    """
    Borra la selección.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    (None)
    """
    st.session_state.L, st.session_state.D = [], []
    sincronizar_url()
