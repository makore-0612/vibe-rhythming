"""
Pruebas del motor con ejemplos calculados a mano (criterios de la fase 2).
"""

import sys
import time
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import config as C  # noqa: E402
from src import seleccion  # noqa: E402
from src.algoritmos import naive_bayes as nb  # noqa: E402
from src.algoritmos.reglas import apriori  # noqa: E402
from src.features import calcular_idf, es_visible  # noqa: E402

HAY_ARTEFACTOS = C.RUTA_CATALOGO.exists()


def test_idf_mini_catalogo_del_guion():
    """
    Cuatro películas: "ogro" aparece en una (idf = log 4 ≈ 1.39) y "aventura" en todas (idf = 0).

    inputs:
    -------
    (ninguno)

    outputs
    -------
    (None)
    """
    idf = calcular_idf([1, 4], 4)
    assert idf[0] == pytest.approx(1.386, abs=1e-3)
    assert idf[1] == pytest.approx(0.0, abs=1e-9)


# Mini ejemplo de Bernoulli: 2 tokens, 2 canciones por clase, α = 1.
#   p_like   = [(2+1)/(2+2), (1+1)/(2+2)] = [0.75, 0.50]
#   p_nolike = [(0+1)/(2+2), (1+1)/(2+2)] = [0.25, 0.50]
#   x = [1, 0]: P(x|like) = 0.75·0.5 = 0.375, P(x|nolike) = 0.25·0.5 = 0.125
#   P(like|x) = 0.375 / (0.375 + 0.125) = 0.75; log-momios = log 3
XB = np.array([[1, 0], [1, 1], [0, 1], [0, 0]])
YB = np.array([1, 1, 0, 0])


def test_bernoulli_a_mano():
    """
    Probabilidades, posterior y log-momios del mini ejemplo coinciden con el cálculo a mano.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    (None)
    """
    mod = nb.entrenar_bernoulli(XB, YB, np.ones(4), alpha=1.0)
    np.testing.assert_allclose(mod["p"][1], [0.75, 0.5])
    np.testing.assert_allclose(mod["p"][0], [0.25, 0.5])
    res = nb.posterior(nb.g_bernoulli(np.array([[1, 0]]), mod))
    assert res["post"][0] == pytest.approx(0.75)
    assert res["log_momios"][0] == pytest.approx(np.log(3))
    assert np.exp(res["log_px"][0]) == pytest.approx(0.5 * 0.375 + 0.5 * 0.125)


def test_posterior_suma_uno():
    """
    P(like|x) + P(no_like|x) = 1 para cualquier vector, también en Multinomial.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    (None)
    """
    rng = np.random.default_rng(0)
    X = rng.integers(0, 2, size=(50, 30))
    y = rng.integers(0, 2, size=50)
    mod = nb.entrenar_bernoulli(X, y, np.ones(50), 1.0)
    g = nb.g_bernoulli(X, mod)
    post_like = np.exp(g[:, 1] - np.logaddexp(g[:, 0], g[:, 1]))
    post_no = np.exp(g[:, 0] - np.logaddexp(g[:, 0], g[:, 1]))
    np.testing.assert_allclose(post_like + post_no, 1.0)
    modm = nb.entrenar_multinomial(X * 3, y, np.ones(50), 1.0)
    res = nb.posterior(nb.g_multinomial(X * 3, modm))
    np.testing.assert_allclose(res["post"] + np.exp(np.log1p(-res["post"])), 1.0)


def test_laplace_evita_ceros():
    """
    Sin suavizado hay probabilidades 0; con α > 0 todas quedan en (0, 1).

    inputs:
    -------
    (ninguno)

    outputs
    -------
    (None)
    """
    sin = (np.array([0, 2]) + 0) / (2 + 0)        # token 0 nunca aparece en "me gusta"
    assert (sin == 0).any()
    mod = nb.entrenar_bernoulli(XB, YB, np.ones(4), alpha=0.5)
    assert ((mod["p"] > 0) & (mod["p"] < 1)).all()
    modm = nb.entrenar_multinomial(XB, YB, np.ones(4), alpha=1.0)
    assert (modm["theta"] > 0).all()


def test_orden_posterior_igual_a_log_momios():
    """
    Ordenar por posterior y por log-momios da el mismo ranking (sin saturar, se compara en log).

    inputs:
    -------
    (ninguno)

    outputs
    -------
    (None)
    """
    rng = np.random.default_rng(1)
    X = rng.integers(0, 2, size=(200, 40))
    y = rng.integers(0, 2, size=200)
    mod = nb.entrenar_bernoulli(X[:60], y[:60], np.ones(60), 1.0)
    res = nb.posterior(nb.g_bernoulli(X, mod))
    np.testing.assert_array_equal(np.argsort(-res["log_post"], kind="stable"),
                                  np.argsort(-res["log_momios"], kind="stable"))


def test_apriori_mini_dataset():
    """
    Transacciones (a, b, c) con clase; soporte >= 2 y confianza >= 0.7.

    [a,b] like · [a,b] like · [a] no · [b,c] no · [a,b,c] like
    a → like: 3/4 = 0.75 · b → like: 3/4 = 0.75 · {a,b} → like: 3/3 = 1.0
    c no es frecuente (1 y 1), así que no hay reglas con c.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    (None)
    """
    T = np.array([[1, 1, 0], [1, 1, 0], [1, 0, 0], [0, 1, 1], [1, 1, 1]], dtype=bool)
    y = np.array([1, 1, 0, 0, 1])
    reglas, truncado = apriori(T, y, min_soporte=2, min_confianza=0.7, max_long=3)
    obtenidas = {(r["antecedente"], r["consecuente"]): (r["soporte"], round(r["confianza"], 4)) for r in reglas}
    assert obtenidas == {((0,), 1): (3, 0.75), ((1,), 1): (3, 0.75), ((0, 1), 1): (3, 1.0)}
    assert not truncado


def test_chi2_ejemplo_del_libro():
    """
    Tabla del libro (O = 60, 40, 140, 760) da χ² = 111.11.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    (None)
    """
    O = np.array([[60.0], [140.0], [40.0], [760.0]])   # orden: token&like, token&no, sin&like, sin&no
    assert seleccion.chi2(O)[0] == pytest.approx(111.11, abs=0.01)


def test_gini_entropia_desviacion():
    """
    Token perfecto: Gini 0, entropía 0, desviación máxima; token mezclado: Gini 0.5, entropía 1.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    (None)
    """
    X = np.array([[1, 1], [1, 0], [0, 1], [0, 0]])
    y = np.array([1, 1, 0, 0])
    O, soporte = seleccion.contingencia(X, y)
    np.testing.assert_allclose(seleccion.gini(O), [0.0, 0.5])
    np.testing.assert_allclose(seleccion.entropia(O), [0.0, 1.0])
    dev = seleccion.desviacion_normalizada(X, y)
    assert dev[0] == pytest.approx(2.0)   # μ+ = 1, μ− = −1, σ = 1
    assert dev[1] == pytest.approx(0.0)
    tabla = seleccion.tabla_criterios(X, y, ["a", "b"], min_soporte=2, a=1.5)
    assert list(seleccion.ordenar(tabla, "gini")["token"]) == ["a", "b"]
    assert tabla.set_index("token").loc["a", "peso_g"] == pytest.approx(1.5)


def test_palabras_ocultas():
    """
    Las palabras ocultas no se muestran, tampoco dentro de bigramas o con sufijos.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    (None)
    """
    ocultas = {"fuck", "ass", "puta"}
    assert not es_visible("letra:fucking", ocultas)
    assert not es_visible("give fuck", ocultas)
    assert es_visible("letra:assume", ocultas)
    assert es_visible("letra:love", ocultas)


@pytest.mark.skipif(not HAY_ARTEFACTOS, reason="faltan artefactos del pipeline")
def test_motor_completo_rapido_y_reproducible():
    """
    Los cuatro algoritmos devuelven 10 canciones no calificadas en menos de 500 ms,
    y los pseudo-negativos son reproducibles.

    inputs:
    -------
    (ninguno)

    outputs
    -------
    (None)
    """
    from src.datos import cargar_modelo
    from src.motor import ALGORITMOS, recomendar
    from src.perfil import pseudo_negativos
    M = cargar_modelo()
    rng = np.random.default_rng(3)
    L = rng.choice(M["n"], 10, replace=False).tolist()
    D = [i for i in rng.choice(M["n"], 8, replace=False).tolist() if i not in L][:3]
    assert pseudo_negativos(M, L, D) == pseudo_negativos(M, L, D)
    assert len(pseudo_negativos(M, L, D)) == 10 - len(D)
    for alg in ALGORITMOS:
        recomendar(M, alg, L, D)                     # calentamiento
        t = time.perf_counter()
        r = recomendar(M, alg, L, D)
        ms = (time.perf_counter() - t) * 1000
        assert ms < 500, f"{alg} tardó {ms:.0f} ms"
        assert 0 < len(r["ids"]) <= 10
        assert not set(r["ids"]) & set(L + D)
        assert len(r["explicaciones"]) == len(r["ids"])
        artistas = [M["artista_principal"][i] for i in r["ids"]]
        assert max(artistas.count(a) for a in artistas) <= 2
