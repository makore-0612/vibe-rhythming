"""
Punto de entrada del servidor.

`streamlit run app.py` detecta el st.App de abajo e importa este archivo al arrancar el servidor.
Así el parche de gzip (bug de Streamlit 1.58 en Community Cloud, ver src/parche_streamlit.py) queda
activo antes de servir el primer archivo de la interfaz. La app en sí vive en principal.py.

Uso: streamlit run app.py
"""

from src import parche_streamlit

parche_streamlit.aplicar()

from streamlit.web.server.starlette import App  # noqa: E402

app = App("principal.py")
