"""
Tienda: búsqueda, filtros, cuadrícula paginada y carrito.
"""

import unicodedata

import numpy as np
import streamlit as st

from src.ui import componentes as ui
from src.ui import estado
from src.ui.recursos import modelo

POR_PAGINA = 12
MODOS = ["Lo más popular", "Sorpréndeme", "Califica rápido"]


@st.cache_resource
def orden_popular():
    """
    Orden "lo más popular" con variedad: primero la mejor canción de cada artista, luego la segunda…

    inputs:
    -------
    (ninguno)

    outputs
    -------
    ids (numpy.ndarray): ids del catálogo en orden de exhibición.
    """
    cat = modelo()["cat"]
    rango = cat.groupby("artista")["popularidad"].rank(method="first", ascending=False)
    return cat.assign(_r=rango).sort_values(["_r", "popularidad"], ascending=[True, False]).index.to_numpy()


@st.cache_resource
def orden_rapido():
    """
    Orden para "Califica rápido": intercala géneros sobre el orden popular para variar.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    ids (numpy.ndarray): ids alternando géneros.
    """
    M = modelo()
    por_genero = {}
    for i in orden_popular():
        por_genero.setdefault(M["genero"][i], []).append(i)
    colas = list(por_genero.values())
    salida = []
    for k in range(max(len(c) for c in colas)):
        salida += [c[k] for c in colas if k < len(c)]
        if len(salida) > 3000:
            break
    return np.array(salida)


def normalizar(texto):
    """
    Minúsculas y sin acentos, para comparar con la columna de búsqueda.

    inputs:
    -------
    texto (str): consulta del usuario.

    outputs
    -------
    norm (str): texto normalizado.
    """
    s = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in s if not unicodedata.combining(c)).strip()


@st.cache_data(max_entries=200)
def buscar(consulta):
    """
    Busca canciones cuyo texto de búsqueda contenga todas las palabras de la consulta.

    inputs:
    -------
    consulta (str): texto normalizado.

    outputs
    -------
    ids (numpy.ndarray): coincidencias ordenadas por popularidad.
    """
    cat = modelo()["cat"]
    mascara = np.ones(len(cat), dtype=bool)
    for palabra in consulta.split():
        mascara &= cat["busqueda"].str.contains(palabra, regex=False).to_numpy()
    sub = cat[mascara]
    return sub.sort_values("popularidad", ascending=False).index.to_numpy()


def filtrar(M, ids, f):
    """
    Aplica los filtros de la tienda a una lista de ids conservando el orden.

    inputs:
    -------
    M (dict): modelo cargado.
    ids (numpy.ndarray): ids candidatos.
    f (dict): filtros elegidos.

    outputs
    -------
    ids_filtrados (numpy.ndarray): ids que pasan los filtros.
    """
    cat = M["cat"]
    ok = np.ones(len(ids), dtype=bool)
    if st.session_state.ocultar_explicitas:
        ok &= ~M["explicita"][ids]
    if f["generos"]:
        ok &= np.isin(M["genero"][ids], f["generos"])
    if f["emociones"]:
        ok &= np.isin(cat["emocion"].to_numpy()[ids], f["emociones"])
    if f["decadas"]:
        ok &= np.isin(cat["decada"].to_numpy()[ids], f["decadas"])
    energia = cat["energia"].to_numpy()[ids]
    ok &= (energia >= f["energia"][0]) & (energia <= f["energia"][1])
    pop = M["popularidad"][ids]
    ok &= (pop >= f["popularidad"][0]) & (pop <= f["popularidad"][1])
    return ids[ok]


def controles_filtros(M):
    """
    Dibuja los filtros en un panel desplegable y devuelve lo elegido.

    inputs:
    -------
    M (dict): modelo cargado.

    outputs
    -------
    f (dict): géneros, emociones, décadas y rangos de energía y popularidad.
    """
    cat = M["cat"]
    with st.popover("Filtros", icon=":material/tune:", width="stretch"):
        f = {
            "generos": st.multiselect("Género", sorted(cat["genero"].unique()), key="f_gen"),
            "emociones": st.multiselect("Emoción (etiqueta del dataset, puede ser ruidosa)",
                                        sorted(cat["emocion"].unique()), key="f_emo"),
            "decadas": st.multiselect("Década", sorted(int(d) for d in cat["decada"].dropna().unique()),
                                      format_func=lambda d: f"{d}s", key="f_dec"),
            "energia": st.slider("Energía", 0.0, 1.0, (0.0, 1.0), 0.05, key="f_ene"),
            "popularidad": st.slider("Popularidad", 0, 100, (0, 100), 5, key="f_pop"),
        }
        st.toggle("Ocultar contenido explícito", key="ocultar_explicitas")
    return f


def cuadricula(M, ids, clave):
    """
    Dibuja una página de tarjetas en rejilla responsiva.

    inputs:
    -------
    M (dict): modelo cargado.
    ids (numpy.ndarray): ids de la página.
    clave (str): prefijo de llaves.

    outputs
    -------
    (None)
    """
    with st.container(key="rejilla"):
        for inicio in range(0, len(ids), 4):
            cols = st.columns(4, gap="small")
            for col, i in zip(cols, ids[inicio:inicio + 4]):
                with col:
                    ui.tarjeta(M, int(i), clave)


def reiniciar_pagina():
    """
    Vuelve a la primera página de resultados.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    (None)
    """
    st.session_state.pagina = 0


@st.fragment
def tienda():
    """
    Contenido interactivo de la tienda; se redibuja solo, sin recargar la página completa.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    (None)
    """
    M = modelo()
    ui.carrito(M)
    st.write("")
    c1, c2 = st.columns([3, 1], gap="small", vertical_alignment="bottom")
    consulta = c1.text_input("Buscar por canción, artista o álbum", key="consulta",
                             placeholder="Ej. coldplay, sweater weather, queen…", on_change=reiniciar_pagina)
    with c2:
        f = controles_filtros(M)

    consulta_n = normalizar(consulta or "")
    if consulta_n:
        modo = None
        ids = buscar(consulta_n)
        st.caption(f"{len(ids):,} resultados para «{consulta}»")
    else:
        modo = st.segmented_control("Explorar", MODOS, default=MODOS[0], key="modo", label_visibility="collapsed",
                                     on_change=reiniciar_pagina)
        modo = modo or MODOS[0]
        if modo == "Sorpréndeme":
            semilla = st.session_state.setdefault("semilla_sorpresa", 7)
            ids = np.random.default_rng(semilla).permutation(M["n"])
            if st.button("Otra tanda", icon=":material/shuffle:"):
                st.session_state.semilla_sorpresa += 1
                st.session_state.pagina = 0
                st.rerun(scope="fragment")
        elif modo == "Califica rápido":
            ids = orden_rapido()
        else:
            ids = orden_popular()
    ids = filtrar(M, ids, f)

    if modo == "Califica rápido":
        calificadas = set(st.session_state.L) | set(st.session_state.D)
        pendientes = [i for i in ids if i not in calificadas]
        saltadas = st.session_state.setdefault("saltadas", [])
        pendientes = [i for i in pendientes if i not in saltadas] or pendientes
        if not pendientes:
            st.info("No quedan canciones con estos filtros.")
            return
        i = int(pendientes[0])
        st.caption("Una por una, de géneros variados. Califica o salta.")
        _, centro, _ = st.columns([1, 1.4, 1])
        with centro:
            ui.tarjeta(M, i, "rapido")
            if st.button("Saltar", icon=":material/skip_next:", width="stretch"):
                saltadas.append(i)
                st.rerun(scope="fragment")
        return

    total_paginas = max(1, int(np.ceil(len(ids) / POR_PAGINA)))
    pagina = min(st.session_state.get("pagina", 0), total_paginas - 1)
    if len(ids) == 0:
        st.info("Ninguna canción coincide. Prueba con otra búsqueda o quita filtros.")
        return
    cuadricula(M, ids[pagina * POR_PAGINA:(pagina + 1) * POR_PAGINA], "t")

    a, b, c = st.columns([1, 2, 1], vertical_alignment="center")
    if a.button("Anterior", icon=":material/chevron_left:", disabled=pagina == 0, width="stretch"):
        st.session_state.pagina = pagina - 1
        st.rerun(scope="fragment")
    b.html(f'<p style="text-align:center;margin:0" class="vr-meta">Página {pagina + 1} de {total_paginas:,}</p>')
    if c.button("Siguiente", icon=":material/chevron_right:", disabled=pagina >= total_paginas - 1, width="stretch"):
        st.session_state.pagina = pagina + 1
        st.rerun(scope="fragment")


st.title("Tienda")
a, b = st.columns([3, 1], vertical_alignment="center")
a.caption("Marca lo que te gusta y lo que no. Tu selección vive en la URL: puedes recargar o compartirla.")
if b.button("Cargar perfil demo (John)", icon=":material/person:", width="stretch"):
    estado.cargar_demo(modelo())
    st.rerun()
tienda()
