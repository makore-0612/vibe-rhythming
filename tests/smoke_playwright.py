"""
Smoke test visual: recorre el flujo y toma capturas a 390 px y 1920 px.

Requiere la app corriendo: streamlit run app.py
Uso: python tests/smoke_playwright.py [url]
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
DIR = Path(__file__).resolve().parent / "capturas"
TAMANOS = {"movil": (390, 844), "proyector": (1920, 1080)}


def esperar(pagina, ms=1500):
    """
    Espera a que Streamlit termine de correr el script.

    inputs:
    -------
    pagina (playwright.sync_api.Page): pestaña del navegador.
    ms (int): pausa extra en milisegundos.

    outputs
    -------
    (None)
    """
    pagina.wait_for_timeout(400)
    pagina.wait_for_selector('[data-testid="stStatusWidget"]', state="detached", timeout=30000)
    pagina.wait_for_timeout(ms)


def errores(pagina):
    """
    Busca excepciones de Streamlit dibujadas en la página.

    inputs:
    -------
    pagina (playwright.sync_api.Page): pestaña del navegador.

    outputs
    -------
    textos (list): textos de las excepciones encontradas.
    """
    return [e.inner_text()[:300] for e in pagina.query_selector_all('[data-testid="stException"]')]


def recorrer(navegador, nombre, ancho, alto):
    """
    Recorre las páginas principales y guarda capturas.

    inputs:
    -------
    navegador (playwright.sync_api.Browser): navegador abierto.
    nombre (str): prefijo de las capturas.
    ancho (int): ancho de la ventana.
    alto (int): alto de la ventana.

    outputs
    -------
    fallas (list): errores encontrados.
    """
    pagina = navegador.new_page(viewport={"width": ancho, "height": alto})
    fallas = []

    def captura(etiqueta, completa=False):
        esperar(pagina)
        fallas.extend(f"{nombre}/{etiqueta}: {e}" for e in errores(pagina))
        # Streamlit hace scroll en stMain: si su ancho de scroll supera el visible, hay scroll horizontal.
        desborde = pagina.evaluate(
            "(() => { const m = document.querySelector('[data-testid=stMain]');"
            " return m.scrollWidth > m.clientWidth + 1 || document.documentElement.scrollWidth > innerWidth + 1; })()")
        if desborde:
            fallas.append(f"{nombre}/{etiqueta}: scroll horizontal")
        if completa:  # Streamlit hace scroll dentro de un contenedor: se agranda la ventana.
            pagina.set_viewport_size({"width": ancho, "height": 4200})
            esperar(pagina, 800)
        pagina.screenshot(path=str(DIR / f"{nombre}_{etiqueta}.png"))
        if completa:
            pagina.set_viewport_size({"width": ancho, "height": alto})

    pagina.goto(URL)
    pagina.wait_for_selector("text=Armar mi selección", timeout=60000)
    esperar(pagina, 1500)
    captura("1_inicio")
    pagina.get_by_role("button", name="Usar el perfil demo (John)").click()
    esperar(pagina, 2500)
    captura("2_recomendaciones")
    captura("2b_recomendaciones_completa", completa=True)
    for alg in ["Naive Bayes", "Reglas de asociación", "Regresión logística"]:
        pagina.get_by_role("button", name=alg).first.click()
        esperar(pagina, 2000)
        captura(f"3_{alg.split()[0].lower()}", completa=alg.startswith("Regresión"))
    pagina.goto(URL + "/tienda" + pagina.url[pagina.url.find("?"):] if "?" in pagina.url else URL + "/tienda")
    esperar(pagina, 2500)
    captura("4_tienda")
    captura("4b_tienda_completa", completa=True)
    pagina.goto(URL + "/laboratorio" + (pagina.url[pagina.url.find("?"):] if "?" in pagina.url else ""))
    esperar(pagina, 2500)
    captura("5_laboratorio", completa=True)
    pagina.get_by_text("¿Qué te delata?").first.click()
    captura("5b_delata", completa=True)
    pagina.goto(URL + "/capitulo")
    captura("6_capitulo", completa=True)
    pagina.close()
    return fallas


def main():
    """
    Ejecuta el recorrido en ambos tamaños e informa errores.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    (None): sale con código 1 si hubo errores.
    """
    DIR.mkdir(exist_ok=True)
    with sync_playwright() as p:
        navegador = p.chromium.launch()
        fallas = []
        for nombre, (w, h) in TAMANOS.items():
            fallas += recorrer(navegador, nombre, w, h)
        navegador.close()
    for f in fallas:
        print("FALLA", f)
    print(f"Capturas en {DIR}")
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
