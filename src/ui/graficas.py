"""
Gráficas Plotly con fondo transparente, Montserrat y etiquetas directas.
"""

import plotly.graph_objects as go

from src.ui.tema import AZUL_100, AZUL_300, AZUL_500, AZUL_900, TINTA


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


def matriz_calor(etiquetas, valores, titulo):
    """
    Matriz cuadrada con anotaciones, en la escala de azules de la paleta.

    inputs:
    -------
    etiquetas (list): nombres de filas y columnas.
    valores (list): matriz (n, n) con valores en [0, 1].
    titulo (str): título de la figura.

    outputs
    -------
    fig (plotly.graph_objects.Figure): figura lista para st.plotly_chart.
    """
    fig = go.Figure(go.Heatmap(
        z=valores, x=etiquetas, y=etiquetas, zmin=0, zmax=1, showscale=False,
        colorscale=[[0, AZUL_900], [0.5, AZUL_500], [1, AZUL_100]],
        text=[[f"{v:.2f}" for v in fila] for fila in valores], texttemplate="%{text}",
        textfont=dict(size=15, color=TINTA), hovertemplate="%{y} · %{x}: %{z:.2f}<extra></extra>",
        xgap=3, ygap=3,
    ))
    fig.update_layout(title=titulo)
    fig.update_yaxes(autorange="reversed")
    return base(fig, 380)


def barras_votos(etiquetas, valores, titulo):
    """
    Barras horizontales de conteos con etiqueta directa, para proyectar.

    inputs:
    -------
    etiquetas (list): nombres de las opciones.
    valores (list): votos por opción.
    titulo (str): título de la figura.

    outputs
    -------
    fig (plotly.graph_objects.Figure): figura lista para st.plotly_chart.
    """
    total = sum(valores) or 1
    fig = go.Figure(go.Bar(
        x=valores, y=etiquetas, orientation="h", marker=dict(color=AZUL_100),
        text=[f"{v} · {v / total:.0%}" for v in valores], textposition="outside", cliponaxis=False,
        textfont=dict(color=TINTA, size=16), hovertemplate="%{y}: %{x}<extra></extra>",
    ))
    fig.update_xaxes(visible=False, range=[0, max(valores + [1]) * 1.3])
    fig.update_yaxes(autorange="reversed", tickfont=dict(size=15))
    fig.update_layout(title=titulo)
    return base(fig, 300)


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
