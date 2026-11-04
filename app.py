"""
Punto de entrada de la app: tema, carga de datos y navegación.

Uso: streamlit run app.py
"""

import streamlit as st

from src import config as C
from src import parche_streamlit
from src.ui import estado
from src.ui.recursos import modelo
from src.ui.tema import aplicar_tema

parche_streamlit.aplicar()  # bug de gzip de Streamlit 1.58 en Community Cloud; ver el módulo

st.set_page_config(page_title=C.APP_NAME, page_icon=":material/album:", layout="wide",
                   initial_sidebar_state="collapsed")


aplicar_tema()
estado.iniciar(modelo()["n"])
estado.sincronizar_url()  # st.switch_page borra los parámetros; se reescriben en cada ejecución

paginas = [
    st.Page("paginas/inicio.py", title="Inicio", icon=":material/home:", default=True),
    st.Page("paginas/tienda.py", title="Tienda", icon=":material/storefront:"),
    st.Page("paginas/recomendaciones.py", title="Recomendaciones", icon=":material/auto_awesome:"),
    st.Page("paginas/laboratorio.py", title="Laboratorio", icon=":material/science:"),
    st.Page("paginas/comparador.py", title="Comparador", icon=":material/compare_arrows:"),
    st.Page("paginas/capitulo.py", title="El capítulo", icon=":material/menu_book:"),
]
st.navigation(paginas, position="top").run()
