"""
Prueba de carga: N sesiones simultáneas con perfiles distintos, midiendo tiempos y RAM del servidor.

Requiere la app corriendo en local: streamlit run app.py
Uso: python tests/carga_playwright.py [n_sesiones] [url]
"""

import asyncio
import random
import statistics
import sys
import time

import psutil
from playwright.async_api import async_playwright

N = int(sys.argv[1]) if len(sys.argv) > 1 else 30
URL = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8501"
N_CATALOGO = 25_000
ALGORITMOS = ["Naive Bayes", "Reglas de asociación", "Regresión logística"]


def proceso_servidor(puerto=8501):
    """
    Encuentra el proceso de Streamlit que escucha en el puerto.

    inputs:
    -------
    puerto (int): puerto del servidor.

    outputs
    -------
    proceso (psutil.Process | None): proceso del servidor.
    """
    for c in psutil.net_connections(kind="tcp"):
        if c.laddr and c.laddr.port == puerto and c.status == psutil.CONN_LISTEN:
            return psutil.Process(c.pid)
    return None


async def vigilar_ram(proceso, pico, alto):
    """
    Registra la RAM máxima del servidor (incluye procesos hijos) hasta que se active `alto`.

    inputs:
    -------
    proceso (psutil.Process): servidor.
    pico (list): lista de un elemento donde se guarda el máximo en bytes.
    alto (asyncio.Event): señal para terminar.

    outputs
    -------
    (None)
    """
    while not alto.is_set():
        try:
            ram = proceso.memory_info().rss + sum(h.memory_info().rss for h in proceso.children(recursive=True))
            pico[0] = max(pico[0], ram)
        except psutil.Error:
            pass
        await asyncio.sleep(0.25)


async def esperar(pagina):
    """
    Espera a que Streamlit termine de ejecutar el script.

    inputs:
    -------
    pagina (playwright.async_api.Page): pestaña.

    outputs
    -------
    (None)
    """
    await pagina.wait_for_timeout(300)
    await pagina.wait_for_selector('[data-testid="stStatusWidget"]', state="detached", timeout=120000)


async def sesion(navegador, k, tiempos, fallas):
    """
    Simula a un compañero: abre sus recomendaciones, cambia de algoritmo y abre el comparador.

    inputs:
    -------
    navegador (playwright.async_api.Browser): navegador compartido.
    k (int): número de sesión (semilla del perfil).
    tiempos (dict): paso → lista de segundos; se llena aquí.
    fallas (list): errores; se llena aquí.

    outputs
    -------
    (None)
    """
    rng = random.Random(k)
    ids = rng.sample(range(N_CATALOGO), 16)
    L, D = ids[:11], ids[11:]
    q = f"?l={'.'.join(map(str, L))}&d={'.'.join(map(str, D))}"
    contexto = await navegador.new_context(viewport={"width": 390, "height": 844})
    pagina = await contexto.new_page()
    try:
        await asyncio.sleep(rng.random() * 3)  # llegadas escalonadas, como en clase
        t = time.perf_counter()
        await pagina.goto(URL + "/recomendaciones" + q, timeout=120000)
        await pagina.wait_for_selector("text=calculado en", timeout=120000)
        tiempos["recomendaciones"].append(time.perf_counter() - t)
        for alg in ALGORITMOS:
            t = time.perf_counter()
            await pagina.get_by_role("button", name=alg).first.click()
            await esperar(pagina)
            tiempos[alg].append(time.perf_counter() - t)
        t = time.perf_counter()
        await pagina.goto(URL + "/comparador" + q, timeout=120000)
        await pagina.wait_for_selector("text=Métricas", timeout=120000)
        await esperar(pagina)
        tiempos["comparador"].append(time.perf_counter() - t)
        errores = await pagina.query_selector_all('[data-testid="stException"]')
        if errores:
            fallas.append(f"sesión {k}: {(await errores[0].inner_text())[:150]}")
    except Exception as e:
        fallas.append(f"sesión {k}: {type(e).__name__}: {str(e)[:150]}")
    finally:
        await contexto.close()


async def main():
    """
    Lanza N sesiones simultáneas e imprime percentiles de tiempo y RAM pico.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    (None)
    """
    proceso = proceso_servidor()
    ram_inicial = proceso.memory_info().rss if proceso else 0
    pico, alto = [ram_inicial], asyncio.Event()
    tiempos = {p: [] for p in ["recomendaciones", *ALGORITMOS, "comparador"]}
    fallas = []
    async with async_playwright() as p:
        navegador = await p.chromium.launch()
        vigia = asyncio.create_task(vigilar_ram(proceso, pico, alto)) if proceso else None
        t0 = time.perf_counter()
        await asyncio.gather(*(sesion(navegador, k, tiempos, fallas) for k in range(N)))
        total = time.perf_counter() - t0
        alto.set()
        if vigia:
            await vigia
        await navegador.close()
    print(f"{N} sesiones en {total:.0f} s · fallas: {len(fallas)}")
    for paso, ts in tiempos.items():
        if ts:
            ts = sorted(ts)
            print(f"  {paso:22s} n={len(ts):2d}  mediana {statistics.median(ts):5.1f} s  "
                  f"p90 {ts[int(0.9 * (len(ts) - 1))]:5.1f} s  máx {ts[-1]:5.1f} s")
    if proceso:
        print(f"RAM servidor: inicial {ram_inicial / 1e6:.0f} MB · pico {pico[0] / 1e6:.0f} MB · "
              f"final {proceso.memory_info().rss / 1e6:.0f} MB")
    for f in fallas[:10]:
        print("FALLA", f)
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    asyncio.run(main())
