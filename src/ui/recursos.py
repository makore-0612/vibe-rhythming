"""
Recursos compartidos entre sesiones (una copia por proceso).
"""

import streamlit as st

from src.datos import cargar_modelo


@st.cache_resource(show_spinner="Afinando el catálogo…")
def modelo():
    """
    Carga el modelo una sola vez por proceso, compartido entre sesiones.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    M (dict): modelo de src.datos.cargar_modelo.
    """
    return cargar_modelo()
