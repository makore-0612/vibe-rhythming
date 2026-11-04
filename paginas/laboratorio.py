"""
Laboratorio: piezas interactivas del capítulo que usan la selección del usuario.
"""

import json

import numpy as np
import pandas as pd
import streamlit as st

from src import config as C
from src import seleccion
from src.algoritmos import PESOS_DEFECTO
from src.algoritmos import naive_bayes as nb
from src.perfil import MIN_LIKES, armar_entrenamiento
from src.ui import componentes as ui
from src.ui import estado, graficas
from src.ui.recursos import calcular, modelo

PESTANAS = ["La constante de Bayes", "Mezcladora", "¿Qué te delata?"]
BLOQUES_UI = {"letra": "Letra", "etiquetas": "Etiquetas", "audio": "Audio", "usos": "Usos"}
PRESETS = {
    "Por defecto": PESOS_DEFECTO,
    "Solo letra": {"letra": 1.0, "etiquetas": 0.0, "audio": 0.0, "usos": 0.0},
    "Solo etiquetas": {"letra": 0.0, "etiquetas": 1.0, "audio": 0.0, "usos": 0.0},
    "Solo audio": {"letra": 0.0, "etiquetas": 0.0, "audio": 1.0, "usos": 0.0},
}


@st.cache_data(max_entries=20, show_spinner=False)
def bayes(L, D, alpha, ocultar_explicitas):
    """
    Entrena Naive Bayes Bernoulli y devuelve los arreglos del posterior para todo el catálogo.

    inputs:
    -------
    L (tuple): ids de me gusta.
    D (tuple): ids de no me gusta.
    alpha (float): suavizado de Laplace.
    ocultar_explicitas (bool): si se excluyen canciones explícitas del ranking.

    outputs
    -------
    res (dict): log_post, log_px, log_momios, tokens elegidos, aportes y log-prior.
    """
    M = modelo()
    ent = armar_entrenamiento(M, list(L), list(D))
    _, _, d = nb.puntuar(M, ent, {"variante": "bernoulli", "alpha": alpha})
    excluir = np.zeros(M["n"], dtype=bool)
    excluir[list(L) + list(D)] = True
    if ocultar_explicitas:
        excluir |= M["explicita"]
    return {"log_post": d["log_post"], "log_px": d["log_px"], "log_momios": d["log_momios"],
            "cols": d["cols"], "tokens": d["tokens"], "visibles": d["visibles"],
            "aporte_si": d["aporte_presente"], "aporte_no": d["aporte_ausente"],
            "log_prior": d["log_prior"], "excluir": excluir, "n_pseudo": ent["n_pseudo"]}


def ranking(res, lam, n=10):
    """
    Ordena el catálogo con puntaje_λ = log P(me gusta | x) + λ · log P(x).

    inputs:
    -------
    res (dict): salida de bayes.
    lam (float): λ en [0, 1].
    n (int): tamaño de la lista.

    outputs
    -------
    ids (numpy.ndarray): los n primeros ids.
    posiciones (numpy.ndarray): posición (desde 1) de cada canción del catálogo con ese λ.
    """
    p = np.where(res["excluir"], -np.inf, res["log_post"] + lam * res["log_px"])
    orden = np.argsort(-p, kind="stable")
    posiciones = np.empty_like(orden)
    posiciones[orden] = np.arange(1, len(orden) + 1)
    return orden[:n], posiciones


def pestana_bayes(M, L, D):
    """
    Muestra la constante de proporcionalidad, el desglose de log-momios y el efecto de λ.

    inputs:
    -------
    M (dict): modelo cargado.
    L (list): ids de me gusta.
    D (list): ids de no me gusta.

    outputs
    -------
    (None)
    """
    st.markdown(
        "Para **decidir** si te gusta *una* canción basta comparar los numeradores "
        r"$P(c)\prod_j P(x_j\mid c)$. Para **ordenar** muchas, el libro normaliza con la constante "
        r"$K = 1/P(x)$ y ordena por $P(\text{gusta}\mid x)$. ¿Qué pasa si no normalizamos?")
    st.latex(r"\text{puntaje}_\lambda(x) = \log P(\text{gusta}\mid x) + \lambda\,\log P(x)")
    st.caption("λ = 0: posterior normalizado (lo que hace el libro). λ = 1: numerador sin normalizar, "
               "P(gusta, x), que favorece canciones con combinaciones de características comunes bajo tu modelo. "
               "Ojo: P(x) es la probabilidad bajo el modelo entrenado con tus canciones, no la popularidad del catálogo.")

    c1, c2 = st.columns(2)
    alpha = c1.slider("α (Laplace)", 0.1, 5.0, 1.0, 0.1, key="lab_alpha")
    lam = c2.slider("λ · freno a lo poco común", 0.0, 1.0, 1.0, 0.05, key="lab_lambda")
    res = bayes(tuple(L), tuple(D), alpha, st.session_state.ocultar_explicitas)
    if res["n_pseudo"]:
        st.caption(f":material/info: Se usaron {res['n_pseudo']} pseudo-negativos para completar los «no me gusta».")

    top0, pos0 = ranking(res, 0.0)
    topl, posl = ranking(res, lam)
    cat = M["cat"]
    filas = []
    for k, i in enumerate(topl):
        antes = int(pos0[i])
        cambio = "nueva" if antes > 10 else (f"↑{antes - (k + 1)}" if antes > k + 1 else
                                              (f"↓{(k + 1) - antes}" if antes < k + 1 else "="))
        filas.append({"#": k + 1, "Canción": cat.titulo[i], "Artista": cat.artista[i],
                      "Posición con λ = 0": antes, "Cambio": cambio,
                      "P(gusta | x)": f"{np.exp(res['log_post'][i]):.4f}",
                      "log P(x)": round(float(res["log_px"][i]), 1)})
    a, b = st.columns(2, gap="large")
    with a:
        st.markdown("**Ranking con λ = 0** (posterior)")
        st.dataframe(pd.DataFrame({"#": range(1, 11), "Canción": cat.titulo.to_numpy()[top0],
                                   "log P(x)": np.round(res["log_px"][top0], 1)}), hide_index=True, width="stretch")
    with b:
        st.markdown(f"**Ranking con λ = {lam:.2f}**")
        st.dataframe(pd.DataFrame(filas)[["#", "Canción", "Posición con λ = 0", "Cambio", "log P(x)"]],
                     hide_index=True, width="stretch")
    comunes = len(set(top0) & set(topl))
    st.caption(f"{comunes} de 10 canciones se repiten entre ambos rankings. Con λ alto suben las canciones con "
               "log P(x) mayor: las más «típicas» según el modelo.")

    st.markdown("#### Desglose de una canción")
    elegida = st.selectbox("Canción", topl, format_func=lambda i: f"{cat.titulo[i]} — {cat.artista[i]}",
                           key="lab_cancion")
    x = np.asarray(M["B_csc"][:, res["cols"]][elegida].toarray()).ravel() > 0
    aportes = np.where(x, res["aporte_si"], res["aporte_no"])
    prior = float(res["log_prior"][1] - res["log_prior"][0])
    presentes = np.flatnonzero(x & res["visibles"])
    top = presentes[np.argsort(-np.abs(aportes[presentes]))][:10]
    etiquetas = [ui.token_legible(res["tokens"][j]) for j in top]
    valores = [float(aportes[j]) for j in top]
    resto_pres = float(aportes[x].sum() - sum(valores))
    ausentes = float(aportes[~x].sum())
    etiquetas += ["Otras presentes", f"Ausentes ({int((~x).sum())})", "A priori"]
    valores += [resto_pres, ausentes, prior]
    st.plotly_chart(graficas.barras_divergentes(etiquetas, valores, "Aporte a los log-momios",
                                                "hacia «te gusta»", "hacia «no te gusta»"),
                    config={"displayModeBar": False})
    lm, lp, lx = res["log_momios"][elegida], res["log_post"][elegida], res["log_px"][elegida]
    st.markdown(f"Suma = **log-momios {lm:+.2f}** → P(gusta | x) = {np.exp(lp):.6f}. "
                f"log P(x) = {lx:.1f}. La suma de los aportes más el a priori da exactamente los log-momios.")


@st.cache_data
def evaluacion_offline():
    """
    Lee los resultados de la evaluación contra Similar Songs.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    res (dict | None): contenido de eval_similares.json o None si no existe.
    """
    if not C.RUTA_EVAL_SIMILARES.exists():
        return None
    return json.loads(C.RUTA_EVAL_SIMILARES.read_text(encoding="utf-8"))


def aplicar_preset(nombre):
    """
    Mueve todos los faders a un preajuste.

    inputs:
    -------
    nombre (str): llave de PRESETS.

    outputs
    -------
    (None)
    """
    st.session_state.pesos_mezcladora = dict(PRESETS[nombre])
    for b, v in PRESETS[nombre].items():
        st.session_state[f"mz_{b}"] = float(v)


def mover_fader(b):
    """
    Copia el valor de un fader a los pesos compartidos con Recomendaciones.

    inputs:
    -------
    b (str): bloque cuyo fader se movió.

    outputs
    -------
    (None)
    """
    st.session_state.pesos_mezcladora[b] = st.session_state[f"mz_{b}"]


def pestana_mezcladora(M, L, D):
    """
    Faders de peso por bloque con recomendaciones que cambian al instante.

    inputs:
    -------
    M (dict): modelo cargado.
    L (list): ids de me gusta.
    D (list): ids de no me gusta.

    outputs
    -------
    (None)
    """
    st.markdown("¿Qué pesa más en la sinopsis de *Shrek*: «pantano» o el actor? Aquí decides cuánto pesa "
                "cada bloque de características en la similitud. Es la **ponderación de características** "
                "(sección 4.3.4.5) hecha consola de sonido. Los pesos también se usan en Recomendaciones.")
    pesos = st.session_state.setdefault("pesos_mezcladora", dict(PESOS_DEFECTO))
    cols = st.columns(len(PRESETS))
    for col, nombre in zip(cols, PRESETS):
        col.button(nombre, on_click=aplicar_preset, args=(nombre,), width="stretch", key=f"preset_{nombre}")
    faders = st.columns(4, gap="medium")
    for col, (b, etiqueta) in zip(faders, BLOQUES_UI.items()):
        if f"mz_{b}" not in st.session_state:
            st.session_state[f"mz_{b}"] = float(pesos[b])
        col.slider(etiqueta, 0.0, 1.0, step=0.05, key=f"mz_{b}", on_change=mover_fader, args=(b,))
    total = sum(pesos.values()) or 1
    st.html('<div class="vr-medidor">' + "".join(
        f'<span>{BLOQUES_UI[b]} · <b>{pesos[b] / total:.0%}</b></span>'
        f'<div class="vr-barra"><span style="width:{100 * pesos[b] / total:.0f}%"></span></div>'
        for b in BLOQUES_UI) + "</div>")

    algoritmo = st.segmented_control("Algoritmo", ["vecinos", "regresion"], default="vecinos", key="mz_alg",
                                     format_func=lambda a: "Vecinos" if a == "vecinos" else "Regresión logística") or "vecinos"
    post = {"diversidad": 0.0, "novedad": 0.0, "ocultar_explicitas": st.session_state.ocultar_explicitas}
    res = calcular(algoritmo, tuple(L), tuple(D), {"pesos": dict(pesos)}, post)
    base = calcular(algoritmo, tuple(L), tuple(D), {"pesos": dict(PESOS_DEFECTO)}, post)
    pos_base = {i: k + 1 for k, i in enumerate(base["ids"])}
    cat = M["cat"]
    filas = []
    for k, i in enumerate(res["ids"]):
        antes = pos_base.get(i)
        cambio = "nueva" if antes is None else ("=" if antes == k + 1 else (f"↑{antes - k - 1}" if antes > k + 1 else f"↓{k + 1 - antes}"))
        filas.append({"#": k + 1, "Canción": cat.titulo[i], "Artista": cat.artista[i], "Género": cat.genero[i],
                      "Contra pesos por defecto": cambio})
    st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")
    nuevas = sum(1 for f in filas if f["Contra pesos por defecto"] == "nueva")
    st.caption(f"{nuevas} de {len(filas)} canciones no estaban en la lista con los pesos por defecto · {res['ms']:.0f} ms")

    ev = evaluacion_offline()
    if ev:
        with st.expander("¿Qué bloque se parece más a «Similar Songs» del dataset?"):
            r = ev["resultados"]
            st.markdown(
                "Para " + f"{ev['n_origenes']:,}" + " canciones, buscamos en qué lugar del catálogo queda la canción "
                "que el dataset marca como similar. Porcentaje que cae en el Top-10:")
            st.dataframe(pd.DataFrame([{"Bloque": k, "Aciertos en Top-10": f"{v['aciertos@10']:.1%}",
                                        "Rango mediano": v["rango_mediano"]} for k, v in r.items()]),
                         hide_index=True, width="stretch")
            st.caption("Solo con audio se recupera la mayoría: esa columna parece calculada con el audio. "
                       "Es una referencia, no una verdad.")


def pestana_delata(M, L, D):
    """
    Tabla de Gini, entropía, χ² y desviación normalizada calculada con la selección del usuario.

    inputs:
    -------
    M (dict): modelo cargado.
    L (list): ids de me gusta.
    D (list): ids de no me gusta.

    outputs
    -------
    (None)
    """
    st.markdown("¿Qué características separan lo que te gusta de lo que no? Se calculan con **tus** "
                "calificaciones (sección 4.3.4). Solo cuentan las que aparecen en al menos 2 canciones.")
    usar_pseudo = st.toggle("Completar con pseudo-negativos", value=len(D) < 5,
                            help="Sin suficientes «no me gusta», no hay contra qué comparar.")
    ent = armar_entrenamiento(M, L, D, usar_pseudo=usar_pseudo)
    if (ent["y"] == 0).sum() == 0:
        st.info("Necesitas al menos un «no me gusta» o activar los pseudo-negativos.")
        return
    Xp = M["B"][ent["ids"]].toarray()
    tabla = seleccion.tabla_criterios(Xp, ent["y"], M["nombres_tok"], ent["pesos"])
    tabla = tabla[M["visible_tok"][tabla["col"].to_numpy()]]
    criterio = st.segmented_control("Criterio", list(seleccion.CRITERIOS), default="gini",
                                    format_func=lambda c: seleccion.CRITERIOS[c]["nombre"], key="lab_criterio") or "gini"
    orden = seleccion.ordenar(tabla, criterio).head(25)
    mostrar = pd.DataFrame({
        "Característica": [ui.token_legible(t) for t in orden["token"]],
        "En me gusta": orden["en_me_gusta"].round(1), "En no me gusta": orden["en_no_me_gusta"].round(1),
        "Gini": orden["gini"].round(3), "Entropía": orden["entropia"].round(3),
        "χ²": orden["chi2"].round(2), "Desv. norm.": orden["desviacion"].round(2),
        "Peso g = 1.5 − Gini": orden["peso_g"].round(3),
    })
    st.dataframe(mostrar, hide_index=True, width="stretch")
    mejor = "menor" if not seleccion.CRITERIOS[criterio]["mayor_es_mejor"] else "mayor"
    st.caption(f"Ordenado por {seleccion.CRITERIOS[criterio]['nombre']}: {mejor} es más discriminativo. "
               "Los pseudo-negativos cuentan con peso 0.5. Las etiquetas del dataset pueden ser ruidosas.")


M = modelo()
L, D = list(st.session_state.L), list(st.session_state.D)
st.title("Laboratorio")
if len(L) < MIN_LIKES:
    st.info(f"El laboratorio usa tu selección: necesitas al menos {MIN_LIKES} me gusta (llevas {len(L)}).")
    if st.button("Usar el perfil demo (John)", type="primary", icon=":material/person:"):
        estado.cargar_demo(M)
        st.rerun()
    st.stop()

if st.session_state.get("lab_pestana") not in PESTANAS:
    st.session_state["lab_pestana"] = PESTANAS[0]
pestana = st.segmented_control("Pestaña", PESTANAS, key="lab_pestana", label_visibility="collapsed") or PESTANAS[0]
if pestana == "La constante de Bayes":
    pestana_bayes(M, L, D)
elif pestana == "Mezcladora":
    pestana_mezcladora(M, L, D)
else:
    pestana_delata(M, L, D)
