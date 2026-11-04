"""
Gráficas Plotly con fondo transparente, Montserrat y etiquetas directas.
"""

import plotly.graph_objects as go

from src.ui.tema import AZUL_100, AZUL_300, AZUL_500, TINTA


def base(fig, alto):
    """
    Aplica el estilo común a una figura.

    inputs:
    -------
    fig (plotly.graph_objects.Figure): figura a estilizar.
    alto (int): alto en píxeles.

    outputs
    -------
    fig (plotly.graph_objects.Figure): la misma figura con estilo.
    """
    fig.update_layout(
        height=alto, margin=dict(l=8, r=48, t=36, b=8), paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Montserrat", color=TINTA, size=13),
        showlegend=False, title_font=dict(size=15),
    )
    fig.update_xaxes(gridcolor=AZUL_500, zerolinecolor=AZUL_300, color=AZUL_100)
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)", color=TINTA, automargin=True)
    return fig


def barras_divergentes(etiquetas, valores, titulo, texto_pos="a favor", texto_neg="en contra"):
    """
    Barras horizontales con valores positivos y negativos, etiquetadas directamente.

    inputs:
    -------
    etiquetas (list): nombres legibles de cada barra.
    valores (list): valores con signo.
    titulo (str): título de la figura.
    texto_pos (str): leyenda corta para los positivos (se muestra en el título del eje).
    texto_neg (str): leyenda corta para los negativos.

    outputs
    -------
    fig (plotly.graph_objects.Figure): figura lista para st.plotly_chart.
    """
    pares = sorted(zip(valores, etiquetas))
    valores = [v for v, _ in pares]
    etiquetas = [e for _, e in pares]
    colores = [AZUL_100 if v > 0 else AZUL_300 for v in valores]
    fig = go.Figure(go.Bar(
        x=valores, y=etiquetas, orientation="h", marker=dict(color=colores, line=dict(width=0)),
        text=[f"{v:+.2f}" for v in valores], textposition="outside", cliponaxis=False,
        textfont=dict(color=TINTA, size=12), hovertemplate="%{y}: %{x:+.3f}<extra></extra>",
    ))
    fig.update_xaxes(title_text=f"← {texto_neg}   ·   {texto_pos} →", title_font=dict(size=12, color=AZUL_100))
    fig.update_layout(title=titulo)
    return base(fig, max(260, 28 * len(valores) + 90))
