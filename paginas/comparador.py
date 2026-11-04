"""
Comparador: listas de todos los algoritmos, métricas, Jaccard, evaluación offline y votación en vivo.
"""

import html
import json
import uuid
from collections import Counter

import pandas as pd
import streamlit as st

from src import config as C
from src import metricas, votos
from src.motor import ALGORITMOS
from src.perfil import MIN_LIKES
from src.ui import estado, graficas
from src.ui.recursos import calcular, modelo

NOMBRES = {a: info["nombre"] for a, info in ALGORITMOS.items()}


@st.cache_data(max_entries=30, show_spinner=False)
def relevancia(L, D, pesos):
    """
    Validación dejando uno fuera para cada algoritmo (costosa: entrena una vez por canción).

    inputs:
    -------
    L (tuple): ids de me gusta.
    D (tuple): ids de no me gusta.
    pesos (dict | None): pesos de la mezcladora.

    outputs
    -------
    res (dict): algoritmo → fracción de aciertos.
    """
    M = modelo()
    return {a: metricas.relevancia_loo(M, list(L), list(D), info["modulo"].puntuar, {"pesos": pesos})
            for a, info in ALGORITMOS.items()}


def listas(M, resultados):
    """
    Dibuja las listas lado a lado y resalta las canciones que aparecen en varias.

    inputs:
    -------
    M (dict): modelo cargado.
    resultados (dict): algoritmo → resultado de calcular.

    outputs
    -------
    (None)
    """
    veces = Counter(i for r in resultados.values() for i in r["ids"])
    cat = M["cat"]
    cols = st.columns(len(resultados), gap="small")
    for col, (alg, r) in zip(cols, resultados.items()):
        filas = []
        for k, i in enumerate(r["ids"]):
            marca = f'<span class="vr-chip">en {veces[i]}</span>' if veces[i] > 1 else ""
            peso = "700" if veces[i] > 1 else "500"
            filas.append(f'<li style="margin:0 0 6px 0;font-weight:{peso}">{html.escape(cat.titulo[i])} {marca}'
                         f'<br><span class="vr-meta">{html.escape(cat.artista[i])}</span></li>')
        with col:
            with st.container(key=f"reco_lista_{alg}"):
                st.html(f'<p class="vr-titulo" style="margin:0 0 6px 0">{NOMBRES[alg]}</p>'
                        f'<p class="vr-meta" style="margin:0 0 8px 0">{r["ms"]:.0f} ms</p>'
                        f'<ol style="padding-left:1.2rem;margin:0">{"".join(filas)}</ol>')


def votacion():
    """
    Votación en vivo con resultados que se actualizan solos cada pocos segundos.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    (None)
    """
    sesion = st.session_state.setdefault("id_sesion", uuid.uuid4().hex)
    st.subheader("¿Qué algoritmo te recomendó mejor?")
    actual = votos.voto_de(sesion)
    cols = st.columns(len(votos.OPCIONES), gap="small")
    for col, o in zip(cols, votos.OPCIONES):
        col.button(NOMBRES[o], key=f"voto_{o}", width="stretch", type="primary" if actual == o else "secondary",
                   icon=":material/how_to_vote:", on_click=votos.votar, args=(sesion, o))
    st.caption("Anónimo. Puedes cambiar tu voto. " + (f"Votaste por {NOMBRES[actual]}." if actual else ""))

    @st.fragment(run_every=3)
    def resultados_en_vivo():
        """
        Gráfica de votos que se refresca sola.

        inputs:
        -------
        (ninguno)

        outputs
        -------
        (None)
        """
        conteo = votos.resultados()
        total = sum(conteo.values())
        st.plotly_chart(graficas.barras_votos([NOMBRES[o] for o in votos.OPCIONES],
                                              [conteo[o] for o in votos.OPCIONES],
                                              f"Resultados en vivo · {total} voto{'s' if total != 1 else ''}"),
                        config={"displayModeBar": False, "staticPlot": True}, key="grafica_votos")

    resultados_en_vivo()
    with st.expander("Reiniciar votos (solo para quien expone)"):
        codigo = st.text_input("Código", type="password", key="codigo_votos")
        if st.button("Reiniciar", icon=":material/restart_alt:"):
            if votos.reiniciar(codigo):
                st.success("Votos reiniciados.")
            else:
                st.error("Código incorrecto o no configurado en los secretos de la app (codigo_votos).")


M = modelo()
L, D = list(st.session_state.L), list(st.session_state.D)
st.title("Comparador")

if len(L) < MIN_LIKES:
    st.info(f"Para comparar algoritmos necesitas al menos {MIN_LIKES} me gusta (llevas {len(L)}). "
            "Aun así puedes votar abajo.")
    if st.button("Usar el perfil demo (John)", type="primary", icon=":material/person:"):
        estado.cargar_demo(M)
        st.rerun()
else:
    pesos = st.session_state.get("pesos_mezcladora")
    post = {"diversidad": 0.0, "novedad": 0.0, "ocultar_explicitas": st.session_state.ocultar_explicitas}
    with st.spinner("Corriendo los cuatro algoritmos…"):
        resultados = {a: calcular(a, tuple(L), tuple(D), {"pesos": pesos}, post) for a in ALGORITMOS}
    st.caption("Todos con sus ajustes por defecto y los pesos actuales de la Mezcladora. "
               "Las canciones marcadas «en N» aparecen en varias listas.")
    listas(M, resultados)

    st.subheader("Métricas")
    filas = []
    for a, r in resultados.items():
        filas.append({
            "Algoritmo": NOMBRES[a],
            "Novedad": round(metricas.novedad(M, r["ids"]), 3),
            "Diversidad": round(metricas.diversidad(M, r["ids"], pesos), 3),
            "Serendipia (aprox.)": round(metricas.serendipia(M, r["ids"], L, pesos), 3),
            "Cobertura": f"{r['diagnostico']['cobertura_catalogo']:.0%}",
            "Latencia (ms)": round(r["ms"]),
        })
    tabla = pd.DataFrame(filas)
    loo = st.session_state.get("loo_resultado")
    if loo and loo["clave"] == (tuple(L), tuple(D)):
        tabla["Relevancia (dejar uno fuera)"] = [f"{loo['valores'][a]:.0%}" for a in ALGORITMOS]
    st.dataframe(tabla, hide_index=True, width="stretch")
    if st.button("Calcular relevancia dejando uno fuera", icon=":material/calculate:",
                 help="Reentrena cada algoritmo sin una de tus canciones y revisa si la coloca del lado correcto. "
                      "Puede tardar de 10 a 30 segundos."):
        with st.spinner("Reentrenando sin cada canción…"):
            st.session_state.loo_resultado = {"clave": (tuple(L), tuple(D)), "valores": relevancia(tuple(L), tuple(D), pesos)}
        st.rerun()
    st.caption("Novedad: promedio de 1 − popularidad/100. Diversidad: 1 − similitud promedio dentro de la lista. "
               "Serendipia: qué tan inesperadas son (poco parecidas a tu perfil frente al resto del catálogo) las de artista o género nuevo; es una aproximación. "
               "Cobertura: parte del catálogo a la que el algoritmo puede dar puntaje. "
               "La relevancia con pocas canciones es ruidosa.")

    a, b = st.columns([1, 1], gap="large")
    with a:
        algs = list(ALGORITMOS)
        jac = [[metricas.jaccard(resultados[x]["ids"], resultados[y]["ids"]) for y in algs] for x in algs]
        st.plotly_chart(graficas.matriz_calor([NOMBRES[x].split()[0] for x in algs], jac,
                                              "Solapamiento entre listas (Jaccard)"),
                        config={"displayModeBar": False})
    with b:
        ruta = C.RUTA_EVAL_SIMILARES
        if ruta.exists():
            ev = json.loads(ruta.read_text(encoding="utf-8"))
            st.markdown("**Evaluación offline con «Similar Songs»**")
            st.dataframe(pd.DataFrame([{"Similitud por": k, "Top-10": f"{v['aciertos@10']:.1%}",
                                        "Top-100": f"{v['aciertos@100']:.1%}"} for k, v in ev["resultados"].items()]),
                         hide_index=True, width="stretch")
            st.caption("Se desconoce cómo se generó esa columna del dataset; parece basada en el audio. "
                       "Es una referencia, no una verdad.")

st.divider()
votacion()
