"""
Punto de entrada de la app: tema, carga de datos, encabezado y navegación.

Uso: streamlit run app.py
"""

import streamlit as st
from PIL import Image

from src import config as C
from src.ui import estado
from src.ui.recursos import modelo
from src.ui.tema import aplicar_tema

st.set_page_config(page_title=C.APP_NAME, page_icon=":material/album:", layout="wide",
                   initial_sidebar_state="collapsed")


@st.cache_resource
def logo_combinado():
    """
    Une los dos logos en una sola imagen para el encabezado; si falta alguno, se omite.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    imagen (PIL.Image.Image | None): logos lado a lado a 160 px de alto, o None si no hay ninguno.
    """
    alto, sep = 160, 40
    piezas = []
    for nombre in ("logoinst.png", "logolic.png"):
        ruta = C.RAIZ / "assets" / nombre
        if ruta.exists():
            im = Image.open(ruta).convert("RGBA")
            piezas.append(im.resize((int(im.width * alto / im.height), alto)))
    if not piezas:
        return None
    lienzo = Image.new("RGBA", (sum(p.width for p in piezas) + sep * (len(piezas) - 1), alto), (0, 0, 0, 0))
    x = 0
    for p in piezas:
        lienzo.paste(p, (x, 0), p)
        x += p.width + sep
    return lienzo


aplicar_tema()
estado.iniciar(modelo()["n"])
estado.sincronizar_url()  # st.switch_page borra los parámetros; se reescriben en cada ejecución
#logo = logo_combinado()
#if logo is not None:
st.logo("assets/logoinst.png", size="large")

paginas = [
    st.Page("paginas/inicio.py", title="Inicio", icon=":material/home:", default=True),
    st.Page("paginas/tienda.py", title="Tienda", icon=":material/storefront:"),
    st.Page("paginas/recomendaciones.py", title="Recomendaciones", icon=":material/auto_awesome:"),
    st.Page("paginas/laboratorio.py", title="Laboratorio", icon=":material/science:"),
    st.Page("paginas/comparador.py", title="Comparador", icon=":material/compare_arrows:"),
    st.Page("paginas/capitulo.py", title="El capítulo", icon=":material/menu_book:"),
]
st.navigation(paginas, position="top").run()
