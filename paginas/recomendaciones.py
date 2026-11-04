"""
Recomendaciones: selector de algoritmo, hiperparámetros, Top-10 explicado y diagnóstico.
"""

import html

import streamlit as st

from src.motor import ALGORITMOS
from src.perfil import MIN_LIKES, estado_requisitos
from src.seleccion import CRITERIOS
from src.ui import componentes as ui
from src.ui import estado, graficas
from src.ui.recursos import calcular, modelo


def hiperparametros(algoritmo, n_perfil):
    """
    Dibuja los controles del algoritmo elegido y devuelve sus valores.

    inputs:
    -------
    algoritmo (str): llave de ALGORITMOS.
    n_perfil (int): canciones calificadas reales.

    outputs
    -------
    params (dict): hiperparámetros.
    post (dict): opciones de post-procesamiento.
    """
    params = {"pesos": st.session_state.get("pesos_mezcladora")}
    with st.expander("Ajustes del algoritmo", icon=":material/tune:"):
        if algoritmo == "vecinos":
            params["k"] = st.slider("k (vecinos que votan)", 1, max(1, min(15, n_perfil)), min(3, n_perfil),
                                    help="Promedio de r · similitud entre los k más parecidos que calificaste.")
        elif algoritmo == "naive_bayes":
            params["variante"] = st.radio("Variante", ["bernoulli", "multinomial"], horizontal=True,
                                          format_func=str.capitalize)
            params["alpha"] = st.slider("α (suavizado de Laplace)", 0.1, 5.0, 1.0, 0.1)
            params["criterio"] = st.selectbox("Selección de características", list(CRITERIOS),
                                              format_func=lambda c: CRITERIOS[c]["nombre"])
            if params["variante"] == "bernoulli":
                params["lambda"] = st.slider("λ · freno a lo poco común", 0.0, 1.0, 0.0, 0.05,
                                             help="0 ordena por P(me gusta | x). 1 ordena por P(me gusta, x).")
            else:
                st.caption("Multinomial ignora el coeficiente multinomial, por eso λ solo existe en Bernoulli.")
        elif algoritmo == "reglas":
            params["min_soporte"] = st.slider("Soporte mínimo (canciones)", 2, 6, 2)
            params["min_confianza"] = st.slider("Confianza mínima", 0.5, 1.0, 0.7, 0.05)
            params["max_long"] = st.slider("Tamaño máximo del antecedente", 1, 3, 3)
        elif algoritmo == "regresion":
            params["variante"] = st.radio("Modelo", ["logistica", "svm"], horizontal=True,
                                          format_func=lambda v: "Regresión logística" if v == "logistica" else "SVM lineal (4.4.6)")
            params["C"] = st.select_slider("C (menos regularización →)", [0.01, 0.1, 0.3, 1.0, 3.0, 10.0, 100.0], 1.0)
        st.divider()
        post = {
            "diversidad": st.slider("Diversidad (MMR)", 0.0, 0.9, 0.0, 0.1,
                                    help="Penaliza canciones parecidas a las ya elegidas en la lista."),
            "novedad": st.slider("Novedad", 0.0, 1.0, 0.0, 0.1, help="Penaliza la popularidad."),
            "ocultar_explicitas": st.toggle("Ocultar contenido explícito", key="ocultar_explicitas"),
        }
    return params, post


def tarjeta_reco(M, rank, i, puntaje, expl, algoritmo):
    """
    Dibuja una recomendación con portada, explicación, enlace y botones de seguimiento.

    inputs:
    -------
    M (dict): modelo cargado.
    rank (int): posición en la lista.
    i (int): id de la canción.
    puntaje (float): puntaje del algoritmo.
    expl (dict): explicación estructurada.
    algoritmo (str): llave del algoritmo.

    outputs
    -------
    (None)
    """
    fila = M["cat"].iloc[i]
    etiqueta_puntaje = "log-momios" if algoritmo == "naive_bayes" else "puntaje"
    with st.container(key=f"reco_{i}"):
        st.html(
            f'<div style="display:flex;gap:12px;align-items:flex-start">'
            f'<div class="vr-rank" aria-label="Posición {rank}">{rank}</div>'
            f'<div class="vr-portada" style="width:72px;min-width:72px">{ui.portada(fila.artista, fila.titulo)}</div>'
            f'<div style="min-width:0;flex:1"><p class="vr-titulo" style="margin-top:0">{html.escape(fila.titulo)}</p>'
            f'<p class="vr-artista">{html.escape(fila.artista)}</p>'
            + ui.chips([fila.genero, fila.emocion, f"{etiqueta_puntaje} {puntaje:.2f}"])
            + f'</div></div><p class="vr-expl">{ui.texto_explicacion(M, expl)}</p>')
        a, b, c = st.columns(3, gap="small")
        a.link_button("Spotify", ui.url_spotify(fila.artista, fila.titulo), icon=":material/open_in_new:",
                      width="stretch")
        b.button("Sirvió", key=f"si_{i}", icon=":material/thumb_up:", width="stretch",
                 on_click=estado.calificar, args=(i, 1), help="La agrega a tus me gusta y recalcula")
        c.button("No", key=f"no_{i}", icon=":material/thumb_down:", width="stretch",
                 on_click=estado.calificar, args=(i, -1), help="La agrega a tus no me gusta y recalcula")


def diagnostico(M, algoritmo, res):
    """
    Muestra lo que hay detrás de cada algoritmo.

    inputs:
    -------
    M (dict): modelo cargado.
    algoritmo (str): llave del algoritmo.
    res (dict): resultado de calcular.

    outputs
    -------
    (None)
    """
    d = res["diagnostico"]
    if algoritmo == "vecinos":
        st.markdown(f"**Costo perezoso:** {d['comparaciones']:,} comparaciones "
                    f"({M['n']:,} candidatas × {d['perfil']} canciones calificadas), en {res['ms']:.0f} ms. "
                    "No hay entrenamiento: todo se calcula al momento de recomendar, y crece con el catálogo.")
    elif algoritmo == "naive_bayes":
        st.markdown(f"**Modelo:** {d['variante'].capitalize()} con α = {d['alpha']}, "
                    f"{len(d['tokens'])} características elegidas por {CRITERIOS[d['criterio']]['nombre']}. "
                    "El posterior se pega a 0 o 1 con muchas características; por eso se ordena con log-momios.")
        if d.get("tabla_tokens"):
            st.dataframe(
                [{"Característica": ui.token_legible(t), "P(x=1 | me gusta)": round(p1, 3),
                  "P(x=1 | no me gusta)": round(p0, 3)} for t, p1, p0 in d["tabla_tokens"]],
                hide_index=True, width="stretch")
        st.page_link("paginas/laboratorio.py", label="Ver la constante de Bayes en el Laboratorio",
                     icon=":material/science:")
    elif algoritmo == "reglas":
        st.markdown(f"**Cobertura:** {d['cobertura']:.1%} del catálogo dispara al menos una regla de «te gusta»; "
                    f"las canciones sin regla no se recomiendan. Reglas encontradas: "
                    f"{d['n_reglas_like']:,} de «te gusta» y {d['n_reglas_no_like']:,} de «no te gusta», "
                    f"sobre {d['transacciones']} canciones calificadas.")
        for r in d["reglas"][:8]:
            st.markdown(f"- Si {ui.lista_es(['*' + ui.token_legible(t) + '*' for t in r['si']])} → "
                        f"**{r['entonces']}** (confianza {r['confianza']:.2f}, soporte {r['soporte']})")
    elif algoritmo == "regresion":
        def nombre(n, w):
            if n.startswith("audio:"):
                return f"{n[6:]} {'alta' if w > 0 else 'baja'}"
            return ui.token_legible(n)
        filas = d["retrato_positivo"][:8] + d["retrato_negativo"][:8]
        if filas:
            fig = graficas.barras_divergentes([nombre(n, w) for n, w in filas], [w for _, w in filas],
                                              "Tu retrato sonoro: pesos del modelo", "te acerca", "te aleja")
            st.plotly_chart(fig, config={"displayModeBar": False})
        st.caption("Para el audio, un peso positivo significa que prefieres valores altos de esa característica.")


M = modelo()
L, D = list(st.session_state.L), list(st.session_state.D)
st.title("Tus recomendaciones")

if len(L) < MIN_LIKES:
    st.info(f"Necesitas al menos {MIN_LIKES} me gusta para ver recomendaciones; llevas {len(L)}.")
    a, b = st.columns(2)
    if a.button("Ir a la tienda", type="primary", icon=":material/storefront:", width="stretch"):
        st.switch_page("paginas/tienda.py")
    if b.button("Usar el perfil demo (John)", icon=":material/person:", width="stretch"):
        estado.cargar_demo(M)
        st.rerun()
    st.stop()

algoritmo = st.segmented_control(
    "Algoritmo", list(ALGORITMOS), default="vecinos", key="algoritmo",
    format_func=lambda a: ALGORITMOS[a]["nombre"], width="stretch") or "vecinos"
info = ALGORITMOS[algoritmo]
st.caption(f"Sección {info['seccion']} · {info['linea']}")

req = estado_requisitos(len(L), len(D))[algoritmo]
params, post = hiperparametros(algoritmo, len(L) + len(D))
res = calcular(algoritmo, tuple(L), tuple(D), params, post)
d = res["diagnostico"]

avisos = []
if d.get("n_pseudo"):
    avisos.append(f"Tienes {len(D)} «no me gusta»; completamos con {d['n_pseudo']} pseudo-negativos "
                  "(canciones al azar, estratificadas por género) para poder entrenar. Vecinos los ignora.")
if req["nivel"] == "mínimo":
    avisos.append(req["mensaje"])
avisos += d.get("avisos", [])
if st.session_state.get("pesos_mezcladora") and algoritmo in ("vecinos", "regresion"):
    w = st.session_state.pesos_mezcladora
    avisos.append("Usando los pesos de la Mezcladora: " + ", ".join(f"{b} {v:.2f}" for b, v in w.items()) + ".")
for a in avisos:
    st.caption(f":material/info: {a}")

st.markdown(f"<span class='vr-meta'>{len(L)} me gusta · {len(D)} no me gusta · calculado en {res['ms']:.0f} ms</span>",
            unsafe_allow_html=True)
if not res["ids"]:
    st.warning("Este algoritmo no encontró canciones que recomendar con tu selección y estos ajustes. "
               "Prueba bajar la confianza o el soporte, o califica más canciones.")
else:
    for k, (i, p, e) in enumerate(zip(res["ids"], res["puntajes"], res["explicaciones"])):
        tarjeta_reco(M, k + 1, i, p, e, algoritmo)

st.subheader("Detrás de la recomendación")
diagnostico(M, algoritmo, res)
