"""
Componentes visuales: portada SVG, tarjeta de canción, carrito y explicaciones.
"""

import base64
import hashlib
import html
import urllib.parse

import streamlit as st

from src.perfil import MIN_LIKES, estado_requisitos
from src.ui import estado
from src.ui.tema import AZUL_100, AZUL_300, AZUL_500, AZUL_700, AZUL_900, TINTA

NOMBRES_ALG = {"vecinos": "Vecinos", "naive_bayes": "Naive Bayes", "reglas": "Reglas", "regresion": "Regresión / SVM"}


def svg_a_img(svg, alt):
    """
    Envuelve un SVG en una etiqueta <img> con data-URI; st.html elimina los <svg> en línea.

    inputs:
    -------
    svg (str): código SVG.
    alt (str): texto alternativo.

    outputs
    -------
    img (str): etiqueta <img> lista para insertar en HTML.
    """
    datos = base64.b64encode(svg.encode("utf-8")).decode()
    return f'<img src="data:image/svg+xml;base64,{datos}" alt="{html.escape(alt)}" style="width:100%;height:auto;display:block;border-radius:10px">'


def portada(artista, titulo):
    """
    Portada lista para HTML.

    inputs:
    -------
    artista (str): artista de la canción.
    titulo (str): título de la canción.

    outputs
    -------
    img (str): etiqueta <img> con la portada generada.
    """
    return svg_a_img(portada_svg(artista, titulo), f"Portada generada para {titulo}")


def portada_svg(artista, titulo):
    """
    Genera una portada abstracta determinista a partir del hash de artista y título.

    inputs:
    -------
    artista (str): artista de la canción.
    titulo (str): título de la canción.

    outputs
    -------
    svg (str): SVG cuadrado con degradado de la paleta y forma de vinilo u ondas.
    """
    h = hashlib.sha1(f"{artista}|{titulo}".encode()).digest()
    paleta = [AZUL_900, AZUL_700, AZUL_500, AZUL_300]
    c1, c2 = paleta[h[0] % 2], paleta[2 + h[1] % 2]
    ang = h[2] % 360
    uid = h.hex()[:10]
    estilo = h[3] % 3
    formas = []
    if estilo == 0:  # vinilo
        cx, cy = 60 + h[4] % 80, 60 + h[5] % 80
        for k, r in enumerate((70, 55, 42, 30)):
            formas.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{AZUL_100}" '
                          f'stroke-opacity="{0.15 + 0.1 * k:.2f}" stroke-width="{1 + h[6 + k] % 3}"/>')
        formas.append(f'<circle cx="{cx}" cy="{cy}" r="12" fill="{AZUL_100}" fill-opacity=".85"/>')
        formas.append(f'<circle cx="{cx}" cy="{cy}" r="3" fill="{AZUL_900}"/>')
    elif estilo == 1:  # ondas
        for k in range(5):
            y0 = 40 + k * 30 + h[4 + k] % 12
            amp = 8 + h[9 + k] % 22
            formas.append(f'<path d="M0 {y0} Q 50 {y0 - amp} 100 {y0} T 200 {y0}" fill="none" stroke="{AZUL_100}" '
                          f'stroke-opacity="{0.2 + 0.13 * k:.2f}" stroke-width="{2 + k % 3}"/>')
    else:  # barras de ecualizador
        for k in range(10):
            alto = 20 + h[4 + k] % 120
            formas.append(f'<rect x="{12 + k * 18}" y="{180 - alto}" width="11" height="{alto}" rx="4" '
                          f'fill="{AZUL_100}" fill-opacity="{0.25 + (h[14 + k % 4] % 60) / 100:.2f}"/>')
    inicial = html.escape((titulo.strip()[:1] or "♪").upper())
    return (f'<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" role="img" '
            f'aria-label="Portada generada para {html.escape(titulo)}">'
            f'<defs><linearGradient id="g{uid}" gradientTransform="rotate({ang} .5 .5)">'
            f'<stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs>'
            f'<rect width="200" height="200" fill="url(#g{uid})"/>{"".join(formas)}'
            f'<text x="14" y="188" font-family="Montserrat, Arial, Helvetica, sans-serif" font-weight="800" font-size="30" fill="{TINTA}" '
            f'fill-opacity=".9">{inicial}</text></svg>')


def chips(etiquetas):
    """
    Renderiza chips de texto.

    inputs:
    -------
    etiquetas (list): textos cortos.

    outputs
    -------
    html (str): fragmento HTML.
    """
    return '<div class="vr-chips">' + "".join(f'<span class="vr-chip">{html.escape(str(e))}</span>'
                                              for e in etiquetas if e) + "</div>"


def url_spotify(artista, titulo):
    """
    Construye el enlace de búsqueda en Spotify.

    inputs:
    -------
    artista (str): artista.
    titulo (str): título.

    outputs
    -------
    url (str): https://open.spotify.com/search/<artista canción>.
    """
    consulta = f"{artista.split(',')[0]} {titulo}"
    return "https://open.spotify.com/search/" + urllib.parse.quote(consulta)


def tarjeta(M, i, clave):
    """
    Dibuja la tarjeta de una canción con botones de me gusta y no me gusta.

    inputs:
    -------
    M (dict): modelo cargado.
    i (int): id de la canción.
    clave (str): prefijo único para las llaves de los widgets.

    outputs
    -------
    (None)
    """
    fila = M["cat"].iloc[i]
    en_l, en_d = i in st.session_state.L, i in st.session_state.D
    with st.container(key=f"tarjeta_{clave}_{i}"):
        marca = "♥ TE GUSTA" if en_l else ("✕ NO TE GUSTA" if en_d else "&nbsp;")
        st.html(
            f'<div class="vr-portada">{portada(fila.artista, fila.titulo)}</div>'
            f'<p class="vr-titulo">{html.escape(fila.titulo)}</p>'
            f'<p class="vr-artista">{html.escape(fila.artista)}</p>'
            + chips([fila.genero, fila.emocion, f"{int(fila.decada)}s" if fila.decada == fila.decada else None])
            + f'<div class="vr-estado">{marca}</div>')
        c1, c2 = st.columns(2, gap="small")
        c1.button("Sí", key=f"l_{clave}_{i}", icon=":material/thumb_up:", width="stretch",
                  type="primary" if en_l else "secondary", on_click=estado.calificar, args=(i, 1),
                  help="Quitar de me gusta" if en_l else "Me gusta")
        c2.button("No", key=f"d_{clave}_{i}", icon=":material/thumb_down:", width="stretch",
                  type="primary" if en_d else "secondary", on_click=estado.calificar, args=(i, -1),
                  help="Quitar de no me gusta" if en_d else "No me gusta")


def medidor_html(n_l, n_d):
    """
    Medidor de requisitos por algoritmo.

    inputs:
    -------
    n_l (int): me gusta.
    n_d (int): no me gusta reales.

    outputs
    -------
    html (str): rejilla con barra y estado por algoritmo.
    """
    filas = []
    for alg, e in estado_requisitos(n_l, n_d).items():
        etiqueta = {"bloqueado": "falta", "mínimo": "listo", "recomendado": "ideal"}[e["nivel"]]
        filas.append(f'<span title="{html.escape(e["mensaje"])}">{NOMBRES_ALG[alg]} · <b>{etiqueta}</b></span>'
                     f'<div class="vr-barra" role="progressbar" aria-valuenow="{int(e["progreso"] * 100)}" '
                     f'aria-valuemin="0" aria-valuemax="100"><span style="width:{e["progreso"] * 100:.0f}%"></span></div>')
    return f'<div class="vr-medidor">{"".join(filas)}</div>'


def carrito(M, mostrar_cta=True):
    """
    Carrito con conteos, medidor por algoritmo y botón de checkout.

    inputs:
    -------
    M (dict): modelo cargado.
    mostrar_cta (bool): si se muestra el botón "Ver mis recomendaciones".

    outputs
    -------
    (None)
    """
    L, D = st.session_state.L, st.session_state.D
    with st.container(key="carrito"):
        c1, c2 = st.columns([1, 1.3], gap="medium", vertical_alignment="center")
        with c1:
            st.markdown(f"**Tu selección** · {len(L)} me gusta · {len(D)} no me gusta")
            faltan = max(0, MIN_LIKES - len(L))
            if faltan:
                st.caption(f"Marca {faltan} me gusta más para desbloquear tus recomendaciones. "
                           "Lo ideal: 10 me gusta y 5 no me gusta.")
            elif len(D) < 5:
                st.caption("Listo. Agregar algunos «no me gusta» mejora Naive Bayes, reglas y regresión.")
            else:
                st.caption("Selección completa para todos los algoritmos.")
            if mostrar_cta:
                if st.button("Ver mis recomendaciones", type="primary", icon=":material/shopping_cart_checkout:",
                             disabled=len(L) < MIN_LIKES, width="stretch", key="cta_carrito"):
                    st.switch_page("paginas/recomendaciones.py")
        with c2:
            st.html(medidor_html(len(L), len(D)))
        if L or D:
            with st.expander("Ver canciones seleccionadas"):
                cat = M["cat"]
                for titulo, ids, valor in (("Me gusta", L, 1), ("No me gusta", D, -1)):
                    if not ids:
                        continue
                    st.markdown(f"**{titulo}**")
                    for i in ids:
                        a, b = st.columns([5, 1], vertical_alignment="center")
                        a.markdown(f"{cat.titulo[i]} — <span class='vr-meta'>{html.escape(cat.artista[i])}</span>",
                                   unsafe_allow_html=True)
                        b.button("Quitar", key=f"q_{valor}_{i}", icon=":material/close:", on_click=estado.calificar,
                                 args=(i, 0), width="stretch")
                st.button("Vaciar selección", on_click=estado.vaciar, icon=":material/delete:", key="vaciar")


def logo_o_placeholder(ruta, ancho=None):
    """
    Muestra un logo o, si falta, un recuadro neutro con el nombre del archivo.

    inputs:
    -------
    ruta (pathlib.Path): ruta del archivo de imagen.
    ancho (int): ancho en píxeles; None usa el ancho del contenedor.

    outputs
    -------
    (None)
    """
    if ruta.exists():
        st.image(str(ruta), width=ancho or "stretch")
    else:
        st.html(f'<div class="vr-placeholder">{html.escape(ruta.name)}</div>')


# ---------------------------------------------------------------- explicaciones

def token_legible(nombre):
    """
    Convierte un nombre de token o característica en texto para mostrar.

    inputs:
    -------
    nombre (str): por ejemplo "letra:love", "género:rock", "energía:alta" o "audio:energía".

    outputs
    -------
    texto (str): por ejemplo "«love»", "género rock", "energía alta", "energía".
    """
    prefijo, _, valor = nombre.partition(":")
    valor = valor.split("·")[0]
    if prefijo == "letra":
        return f"«{valor}»"
    if prefijo == "audio":
        return valor
    if prefijo == "explícita":
        return "letra explícita"
    if prefijo == "uso":
        return f"buena para {valor}"
    return f"{prefijo} {valor}"


def lista_es(items):
    """
    Une elementos en español: "a, b y c".

    inputs:
    -------
    items (list): textos.

    outputs
    -------
    texto (str): elementos unidos.
    """
    items = [i for i in items if i]
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " y " + items[-1]


def texto_explicacion(M, e):
    """
    Redacta la explicación de una recomendación según su algoritmo.

    inputs:
    -------
    M (dict): modelo cargado.
    e (dict): explicación estructurada devuelta por el algoritmo.

    outputs
    -------
    texto (str): HTML corto con énfasis en los motivos.
    """
    cat = M["cat"]
    esc = html.escape
    if e["tipo"] == "vecinos":
        v = e["vecinos"][0]
        accion = "que te gustó" if v["r"] > 0 else "que no te gustó"
        txt = f'Se parece a <em>{esc(cat.titulo[v["id"]])}</em> de {esc(cat.artista[v["id"]])} ({v["sim"]:.2f}), {accion}'
        detalles = []
        if e["palabras"]:
            detalles.append("comparten " + lista_es([f"<em>{esc(p)}</em>" for p in e["palabras"]]))
        if e["etiquetas"]:
            detalles.append("ambas son " + lista_es([f"<em>{esc(t.split(':', 1)[1])}</em>" for t in e["etiquetas"][:2]]))
        return txt + (": " + "; ".join(detalles) if detalles else "") + "."
    if e["tipo"] == "naive_bayes":
        prob = e["post"]
        prob_txt = ">99.9 %" if prob > 0.999 else f"{prob:.1%}"
        txt = f'Probabilidad de que te guste: <em>{prob_txt}</em> (log-momios {e["log_momios"]:+.1f})'
        if e["a_favor"]:
            txt += ". A favor: " + lista_es([f'<em>{esc(token_legible(t["token"]))}</em> ({t["aporte"]:+.1f})'
                                              for t in e["a_favor"][:3]])
        return txt + "."
    if e["tipo"] == "reglas":
        if not e["reglas_like"]:
            return "No dispara reglas de «te gusta»."
        r = e["reglas_like"][0]
        txt = (f'Regla: si {lista_es([f"<em>{esc(token_legible(t))}</em>" for t in r["si"]])} → te gusta '
               f'(confianza {r["confianza"]:.2f}, soporte {r["soporte"]})')
        extra = e["n_like"] - 1
        if extra > 0:
            txt += f". Dispara {extra} regla{'s' if extra > 1 else ''} más de «te gusta»"
        if e["n_no_like"]:
            txt += f" y {e['n_no_like']} de «no te gusta»"
        return txt + "."
    if e["tipo"] == "regresion":
        def describir(c):
            nombre = c["caracteristica"]
            if nombre.startswith("audio:"):
                return f'{nombre[6:]} {"alta" if c["valor"] > 0 else "baja"}'
            return token_legible(nombre)
        txt = "Lo que más pesó: " + lista_es([f'<em>{esc(describir(c))}</em> ({c["contribucion"]:+.2f})'
                                              for c in e["a_favor"][:3]])
        if e["en_contra"]:
            txt += f'. En contra: <em>{esc(describir(e["en_contra"][0]))}</em> ({e["en_contra"][0]["contribucion"]:+.2f})'
        return txt + "."
    return ""
