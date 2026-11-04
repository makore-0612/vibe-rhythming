"""
Tokens de color y CSS mínimo centralizado (§6 de CLAUDE.md).
"""

import streamlit as st

AZUL_100 = "#A4B7D7"
AZUL_300 = "#5C7AA3"
AZUL_500 = "#274472"
AZUL_700 = "#1B3454"
AZUL_900 = "#0E1A2B"
TINTA = "#F4F7FC"

CSS = f"""
<style>
:root {{
  --azul-100: {AZUL_100}; --azul-300: {AZUL_300}; --azul-500: {AZUL_500};
  --azul-700: {AZUL_700}; --azul-900: {AZUL_900}; --tinta: {TINTA};
}}
h1 {{ font-size: clamp(1.8rem, 5vw, 2.8rem) !important; font-weight: 800 !important; letter-spacing: -0.01em; }}
.block-container {{ padding-top: 4.2rem; padding-bottom: 4rem; max-width: 1280px; }}

/* Botón primario: texto oscuro sobre azul claro (contraste 8.6). */
button[data-testid="stBaseButton-primary"], a[data-testid="stBaseLinkButton-primary"] {{
  color: var(--azul-900) !important; font-weight: 700;
}}
button[data-testid="stBaseButton-primary"] p, a[data-testid="stBaseLinkButton-primary"] p {{ color: var(--azul-900) !important; }}
button[data-testid^="stBaseButton"], a[data-testid^="stBaseLinkButton"] {{ min-height: 44px; }}

/* Tarjetas de canción */
[class*="st-key-tarjeta_"] {{
  background: var(--azul-700); border: 1px solid var(--azul-500); border-radius: 16px;
  padding: 10px 10px 12px 10px; gap: 0.4rem;
}}
[class*="st-key-tarjeta_"]:hover {{ border-color: var(--azul-300); }}
.vr-portada svg {{ width: 100%; height: auto; display: block; border-radius: 10px; }}
.vr-titulo {{ font-weight: 700; font-size: 0.98rem; line-height: 1.25; margin: 6px 0 0 0;
  overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; color: var(--tinta); }}
.vr-artista {{ color: var(--azul-100); font-size: 0.86rem; margin: 0;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.vr-chips {{ display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; }}
.vr-chip {{ background: var(--azul-500); color: var(--tinta); border-radius: 999px; padding: 2px 9px;
  font-size: 0.74rem; font-weight: 500; white-space: nowrap; }}
.vr-estado {{ font-size: 0.78rem; font-weight: 700; color: var(--azul-100); letter-spacing: .02em; }}

/* Carrito */
.st-key-carrito {{
  background: var(--azul-700); border: 1px solid var(--azul-300); border-radius: 16px; padding: 14px 16px;
}}
.vr-medidor {{ display: grid; grid-template-columns: minmax(110px, auto) 1fr; gap: 4px 10px; align-items: center;
  font-size: 0.82rem; }}
.vr-barra {{ height: 8px; background: var(--azul-900); border-radius: 99px; overflow: hidden; border: 1px solid var(--azul-500); }}
.vr-barra > span {{ display: block; height: 100%; background: var(--azul-100); }}

/* Recomendaciones */
[class*="st-key-reco_"] {{
  background: var(--azul-700); border: 1px solid var(--azul-500); border-radius: 16px; padding: 12px 14px;
}}
.vr-rank {{ font-size: 1.6rem; font-weight: 800; color: var(--azul-100); line-height: 1; }}
.vr-expl {{ font-size: 0.9rem; color: var(--tinta); margin: 4px 0 0 0; }}
.vr-expl em {{ color: var(--azul-100); font-style: normal; font-weight: 600; }}
.vr-meta {{ font-size: 0.8rem; color: var(--azul-100); }}

/* Héroe */
.vr-heroe h1 {{ font-size: clamp(2rem, 6vw, 3.6rem); font-weight: 800; line-height: 1.05; margin: 0; letter-spacing: -0.02em; }}
.vr-heroe p {{ font-size: clamp(1rem, 2.4vw, 1.3rem); color: var(--azul-100); max-width: 46rem; }}
.vr-cifra {{ font-size: clamp(1.6rem, 4vw, 2.4rem); font-weight: 800; color: var(--tinta); line-height: 1.1; }}
.vr-cifra-txt {{ font-size: 0.85rem; color: var(--azul-100); }}
.vr-borrador {{ display: inline-block; border: 1px solid var(--azul-300); color: var(--azul-100); border-radius: 999px;
  padding: 1px 10px; font-size: 0.75rem; font-weight: 600; margin-bottom: 6px; }}
.vr-placeholder {{ border: 1px dashed var(--azul-300); color: var(--azul-100); border-radius: 10px; padding: 10px;
  font-size: 0.8rem; text-align: center; }}

/* Ecualizador discreto */
.vr-eq {{ display: inline-flex; gap: 3px; align-items: flex-end; height: 18px; margin-right: 8px; vertical-align: middle; }}
.vr-eq span {{ width: 4px; background: var(--azul-100); border-radius: 2px; animation: vr-eq 1.1s ease-in-out infinite; }}
.vr-eq span:nth-child(2) {{ animation-delay: .2s; }} .vr-eq span:nth-child(3) {{ animation-delay: .4s; }}
.vr-eq span:nth-child(4) {{ animation-delay: .6s; }}
@keyframes vr-eq {{ 0%, 100% {{ height: 30%; }} 50% {{ height: 100%; }} }}
@media (prefers-reduced-motion: reduce) {{
  .vr-eq span {{ animation: none; height: 60%; }}
  * {{ transition: none !important; scroll-behavior: auto !important; }}
}}

.katex-display {{ overflow-x: auto; overflow-y: hidden; max-width: 100%; }}
[class*="st-key-reco_"] [data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap !important; gap: 0.4rem; }}
[class*="st-key-reco_"] [data-testid="stColumn"] {{ min-width: 0 !important; flex: 1 1 0 !important; width: auto !important; }}

/* Celular */
@media (max-width: 640px) {{
  .block-container {{ padding-left: 0.8rem; padding-right: 0.8rem; padding-top: 3.6rem; }}
  .vr-titulo {{ font-size: 0.9rem; }}
  .st-key-rejilla [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; gap: 0.5rem; }}
  .st-key-rejilla [data-testid="stColumn"] {{ min-width: calc(50% - 0.25rem) !important;
    flex: 1 1 calc(50% - 0.25rem) !important; width: calc(50% - 0.25rem) !important; }}
}}
</style>
"""


def aplicar_tema():
    """
    Inyecta el CSS centralizado de la app.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    (None)
    """
    st.html(CSS)


def ecualizador():
    """
    HTML de la animación discreta de ecualizador.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    html (str): fragmento HTML.
    """
    return '<span class="vr-eq" aria-hidden="true"><span></span><span></span><span></span><span></span></span>'
