"""
El capítulo: resumen en Markdown desde content/, con enlaces para probar cada idea.
"""

import streamlit as st

from src import config as C

SECCIONES = {
    "01_introduccion.md": "Introducción",
    "02_objetivos.md": "Objetivos",
    "03_idea_contenido.md": "La idea",
    "04_extraccion.md": "Extracción de características",
    "05_seleccion.md": "Selección de características",
    "06_vecinos.md": "Vecinos más cercanos",
    "07_clasificadores.md": "Naive Bayes y reglas",
    "08_regresion.md": "Regresión",
    "09_explicaciones.md": "Explicaciones",
    "10_contenido_vs_colaborativo.md": "Contenido contra colaborativo",
}
# Sección → (texto del botón, página, pestaña del laboratorio o None).
PROBAR = {
    "02_objetivos.md": ("Probar diversidad y novedad", "paginas/recomendaciones.py", None),
    "04_extraccion.md": ("Ver qué características pesan", "paginas/laboratorio.py", "¿Qué te delata?"),
    "05_seleccion.md": ("Calcular Gini, entropía y χ² con tus canciones", "paginas/laboratorio.py", "¿Qué te delata?"),
    "06_vecinos.md": ("Probar vecinos más cercanos", "paginas/recomendaciones.py", None),
    "07_clasificadores.md": ("Probar la constante de Bayes", "paginas/laboratorio.py", "La constante de Bayes"),
    "08_regresion.md": ("Ver tu retrato sonoro", "paginas/recomendaciones.py", None),
    "09_explicaciones.md": ("Ver recomendaciones explicadas", "paginas/recomendaciones.py", None),
}
ALGORITMO_DE = {"06_vecinos.md": "vecinos", "08_regresion.md": "regresion", "07_clasificadores.md": "naive_bayes"}


@st.cache_data
def leer(nombre):
    """
    Lee una sección del capítulo.

    inputs:
    -------
    nombre (str): archivo dentro de content/.

    outputs
    -------
    texto (str): Markdown de la sección, o aviso si falta.
    """
    ruta = C.RAIZ / "content" / nombre
    return ruta.read_text(encoding="utf-8") if ruta.exists() else f"*Falta `{nombre}`.*"


def ir(pagina, pestana, algoritmo):
    """
    Prepara la navegación hacia una página y, si aplica, una pestaña o algoritmo.

    inputs:
    -------
    pagina (str): ruta de la página.
    pestana (str | None): pestaña del laboratorio.
    algoritmo (str | None): algoritmo a preseleccionar en Recomendaciones.

    outputs
    -------
    (None)
    """
    if pestana:
        st.session_state["lab_pestana"] = pestana
    if algoritmo:
        st.session_state["algoritmo"] = algoritmo
    st.session_state["_ir_a"] = pagina


if "_ir_a" in st.session_state:
    st.switch_page(st.session_state.pop("_ir_a"))

st.title("El capítulo")
st.caption("Resumen del capítulo 4 de *Recommender Systems: The Textbook* (Aggarwal, 2016), "
           "parafraseado a partir del guion del equipo.")

seccion = st.selectbox("Sección", list(SECCIONES), format_func=lambda s: f"{s[:2]} · {SECCIONES[s]}",
                       key="seccion_capitulo")
if seccion in C.SECCIONES_BORRADOR:
    st.html('<span class="vr-borrador">Borrador</span>')
st.markdown(leer(seccion))

if seccion in PROBAR:
    texto, pagina, pestana = PROBAR[seccion]
    st.button(texto, type="primary", icon=":material/play_arrow:", on_click=ir,
              args=(pagina, pestana, ALGORITMO_DE.get(seccion)))

orden = list(SECCIONES)
k = orden.index(seccion)
a, _, b = st.columns([1, 2, 1])
if k > 0:
    a.button(f"← {SECCIONES[orden[k - 1]]}", on_click=lambda: st.session_state.update(seccion_capitulo=orden[k - 1]),
             width="stretch")
if k < len(orden) - 1:
    b.button(f"{SECCIONES[orden[k + 1]]} →", on_click=lambda: st.session_state.update(seccion_capitulo=orden[k + 1]),
             width="stretch")
