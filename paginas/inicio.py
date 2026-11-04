"""
Inicio: propuesta, cifras del catálogo, QR y créditos.
"""

import io

import segno
import streamlit as st

from src import config as C
from src.ui import estado
from src.ui.componentes import svg_a_img
from src.ui.recursos import modelo
from src.ui.tema import AZUL_900, TINTA, ecualizador


@st.cache_data
def qr_svg(url):
    """
    Genera el QR de la app como SVG.

    inputs:
    -------
    url (str): dirección pública de la app.

    outputs
    -------
    svg (str): código SVG del QR, oscuro sobre claro para que cualquier cámara lo lea.
    """
    buf = io.BytesIO()
    segno.make(url, error="m").save(buf, kind="svg", scale=10, border=2, dark=AZUL_900, light=TINTA,
                                    xmldecl=False, svgns=True, nl=False)
    return buf.getvalue().decode()


def cargar_demo_e_ir():
    """
    Carga el perfil demo y marca la navegación pendiente a Recomendaciones.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    (None)
    """
    estado.cargar_demo(modelo())
    st.session_state["_ir_a_recos"] = True


M = modelo()
cat = M["cat"]
if st.session_state.pop("_ir_a_recos", False):
    st.switch_page("paginas/recomendaciones.py")

izq, der = st.columns([1.6, 1], gap="large", vertical_alignment="center")
with izq:
    st.html(f'<div class="vr-heroe"><p style="margin:0 0 6px 0">{ecualizador()}Sistemas de recomendación '
            f'basados en contenido</p><h1>{C.APP_NAME}</h1>'
            f'<p>Elige canciones como si llenaras un carrito y descubre por qué cada algoritmo '
            f'te recomienda lo que te recomienda.</p></div>')
    a, b = st.columns(2, gap="small")
    if a.button("Armar mi selección", type="primary", icon=":material/storefront:", width="stretch"):
        st.switch_page("paginas/tienda.py")
    b.button("Usar el perfil demo (John)", icon=":material/person:", on_click=cargar_demo_e_ir, width="stretch")
with der:
    st.html(f'<div style="background:{TINTA};border-radius:16px;padding:10px;max-width:340px;margin:auto">'
            f'{svg_a_img(qr_svg(C.URL_APP), "Código QR de la app")}</div>')
    st.caption(f"Escanea para abrirla en tu celular · {C.URL_APP.removeprefix('https://')}")

st.divider()
cifras = [
    (f"{len(cat):,}", "canciones en el catálogo"),
    (f"{cat['artista'].nunique():,}", "artistas"),
    (f"{len(M['vocab']['terminos']):,}", "términos de letra"),
    (f"{M['B'].shape[1]:,}", "características binarias"),
]
for col, (num, txt) in zip(st.columns(4), cifras):
    col.html(f'<div class="vr-cifra">{num}</div><div class="vr-cifra-txt">{txt}</div>')

st.divider()
c1, c2 = st.columns(2, gap="large")
with c1:
    st.markdown("#### Cómo funciona")
    st.markdown(
        "1. **Tienda:** marca *me gusta* y *no me gusta*. Con 6 me gusta se desbloquea el checkout.\n"
        "2. **Recomendaciones:** elige un algoritmo del capítulo y lee por qué te recomienda cada canción.\n"
        "3. **Laboratorio:** juega con la constante de Bayes y mira qué características te delatan.\n"
        "4. **El capítulo:** el resumen teórico, con enlaces para probar cada idea.")
    st.caption("Solo se usan metadatos, audio y letras vectorizadas; ninguna letra completa se publica. "
               "Sin audio: cada canción trae un enlace para buscarla en Spotify.")
with c2:
    st.markdown("#### Créditos")
    st.markdown(
        "**Castrillo Cruz Karen Arlet, Ramos González Nadia, Zamora Antiga Ángel Javier.** · Licenciatura en Ciencia de Datos, IIMAS, UNAM.\n\n"
        "Basado en el capítulo 4, *Content-Based Recommender Systems*, de "
        "Charu C. Aggarwal, *Recommender Systems: The Textbook*, Springer, 2016.\n\n"
        "Datos: *500K+ Spotify Songs with Lyrics, Emotions & More*, de DevDope "
        "([Kaggle](https://www.kaggle.com/datasets/devdope/900k-spotify/data)), bajo licencia "
        "[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). Uso académico, sin fines de lucro.")
