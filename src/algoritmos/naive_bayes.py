"""
Naive Bayes (sección 4.4.3): método ansioso, implementado a mano en espacio logarítmico.

Con g_c(x) = log P(c) + log P(x | c):
    log P(x)        = logaddexp(g_like, g_nolike)
    log P(like | x) = g_like − log P(x)
    log-momios      = g_like − g_nolike
    puntaje_λ(x)    = log P(like | x) + λ · log P(x)
λ = 0 ordena por el posterior (lo que hace el libro: K normaliza para poder ordenar);
λ = 1 ordena por P(like, x), que favorece vectores comunes bajo el modelo.
"""

import numpy as np
import scipy.sparse as sp

from src import seleccion

M_TOKENS = 200


def entrenar_bernoulli(Xb, y, pesos, alpha):
    """
    Estima P(x_j = 1 | c) con suavizado de Laplace: (n_jc + α) / (n_c + 2α).

    inputs:
    -------
    Xb (numpy.ndarray): matriz binaria (n_canciones, n_tokens) del perfil.
    y (numpy.ndarray): 1 = me gusta, 0 = no me gusta.
    pesos (numpy.ndarray): peso de cada canción.
    alpha (float): parámetro de Laplace, mayor que 0.

    outputs
    -------
    modelo (dict): "p" (2, n_tokens) con fila 0 = no me gusta y fila 1 = me gusta,
        "log_prior" (2,), "n_c" (2,) y "n_jc" (2, n_tokens).
    """
    Xb = np.asarray(Xb, dtype=np.float64)
    pesos = np.asarray(pesos, dtype=np.float64)
    n_c = np.array([pesos[y == 0].sum(), pesos[y == 1].sum()])
    n_jc = np.vstack([pesos[y == 0] @ Xb[y == 0], pesos[y == 1] @ Xb[y == 1]])
    p = (n_jc + alpha) / (n_c[:, None] + 2 * alpha)
    return {"p": p, "log_prior": np.log(n_c / n_c.sum()), "n_c": n_c, "n_jc": n_jc}


def g_bernoulli(X, modelo):
    """
    Calcula g_c(x) = log P(c) + Σ_j log(1 − p_jc) + X @ (log p_jc − log(1 − p_jc)).

    inputs:
    -------
    X (scipy.sparse.csr_matrix | numpy.ndarray): tokens binarios de las canciones a puntuar.
    modelo (dict): salida de entrenar_bernoulli.

    outputs
    -------
    g (numpy.ndarray): matriz (n, 2) con g_nolike y g_like.
    """
    log_p, log_q = np.log(modelo["p"]), np.log1p(-modelo["p"])
    base = modelo["log_prior"] + log_q.sum(1)
    return np.asarray(X @ (log_p - log_q).T) + base


def entrenar_multinomial(Xc, y, pesos, alpha):
    """
    Estima θ_jc = (Σ conteos_jc + α) / (Σ_j Σ conteos_jc + α · m).

    inputs:
    -------
    Xc (numpy.ndarray): conteos (n_canciones, m) del perfil.
    y (numpy.ndarray): 1 = me gusta, 0 = no me gusta.
    pesos (numpy.ndarray): peso de cada canción.
    alpha (float): parámetro de Laplace.

    outputs
    -------
    modelo (dict): "theta" (2, m) y "log_prior" (2,).
    """
    Xc = np.asarray(Xc, dtype=np.float64)
    pesos = np.asarray(pesos, dtype=np.float64)
    n_c = np.array([pesos[y == 0].sum(), pesos[y == 1].sum()])
    f = np.vstack([pesos[y == 0] @ Xc[y == 0], pesos[y == 1] @ Xc[y == 1]])
    theta = (f + alpha) / (f.sum(1, keepdims=True) + alpha * Xc.shape[1])
    return {"theta": theta, "log_prior": np.log(n_c / n_c.sum())}


def g_multinomial(X, modelo):
    """
    Calcula g_c(x) = log P(c) + Σ_j x_j log θ_jc, sin el coeficiente multinomial.

    inputs:
    -------
    X (scipy.sparse.csr_matrix | numpy.ndarray): conteos de las canciones a puntuar.
    modelo (dict): salida de entrenar_multinomial.

    outputs
    -------
    g (numpy.ndarray): matriz (n, 2) con g_nolike y g_like.
    """
    return np.asarray(X @ np.log(modelo["theta"]).T) + modelo["log_prior"]


def posterior(g, lam=0.0):
    """
    Normaliza con la constante de proporcionalidad y calcula los puntajes.

    inputs:
    -------
    g (numpy.ndarray): matriz (n, 2) con g_nolike y g_like.
    lam (float): λ en [0, 1] del freno a lo poco común.

    outputs
    -------
    res (dict): "log_px", "log_post" (log P(like | x)), "post", "log_momios" y "puntaje_lambda".
    """
    log_px = np.logaddexp(g[:, 0], g[:, 1])
    log_post = g[:, 1] - log_px
    return {"log_px": log_px, "log_post": log_post, "post": np.exp(log_post),
            "log_momios": g[:, 1] - g[:, 0], "puntaje_lambda": log_post + lam * log_px}


def puntuar(M, ent, params):
    """
    Entrena Naive Bayes con las calificaciones del usuario y puntúa el catálogo.

    inputs:
    -------
    M (dict): modelo cargado.
    ent (dict): entrenamiento de src.perfil.armar_entrenamiento.
    params (dict): "variante" ("bernoulli" | "multinomial"), "alpha", "lambda", "criterio", "m".

    outputs
    -------
    puntajes (numpy.ndarray): log-momios (λ = 0) o puntaje_λ.
    explicar (callable): ids → lista de explicaciones.
    diagnostico (dict): tokens elegidos, probabilidades por clase y arreglos del posterior.
    """
    variante = params.get("variante", "bernoulli")
    alpha = float(params.get("alpha", 1.0))
    lam = float(params.get("lambda", 0.0)) if variante == "bernoulli" else 0.0
    criterio = params.get("criterio", "gini")
    m = int(params.get("m", M_TOKENS))
    ids, y, pesos = ent["ids"], ent["y"], ent["pesos"]

    if variante == "bernoulli":
        Xperfil = M["B"][ids].toarray()
        nombres = M["nombres_tok"]
        cols, _ = seleccion.seleccionar(Xperfil, y, nombres, criterio, m, pesos)
        modelo = entrenar_bernoulli(Xperfil[:, cols], y, pesos, alpha)
        Xcat = M["B_csc"][:, cols].tocsr().astype(np.float64)
        g = g_bernoulli(Xcat, modelo)
        visibles = M["visible_tok"][cols]
        p1, p0 = modelo["p"][1], modelo["p"][0]
        aporte_si, aporte_no = np.log(p1 / p0), np.log((1 - p1) / (1 - p0))
    else:
        Xperfil = M["conteos"][ids].toarray()
        presencia = (Xperfil > 0).astype(np.uint8)
        nombres = [f"letra:{t}" for t in M["vocab"]["legible"]]
        cols, _ = seleccion.seleccionar(presencia, y, nombres, criterio, m, pesos)
        modelo = entrenar_multinomial(Xperfil[:, cols], y, pesos, alpha)
        Xcat = M["conteos"][:, cols].astype(np.float64)
        g = g_multinomial(Xcat, modelo)
        visibles = M["visible_letra"][cols]
        aporte_si = np.log(modelo["theta"][1] / modelo["theta"][0])
        aporte_no = np.zeros_like(aporte_si)
    res = posterior(g, lam)
    puntajes = res["puntaje_lambda"] if lam > 0 else res["log_momios"]
    nombres_sel = [nombres[j] for j in cols]

    def explicar(lista):
        """
        Desglosa los log-momios de cada canción en el aporte de sus tokens.

        inputs:
        -------
        lista (list): ids de canciones a explicar.

        outputs
        -------
        explicaciones (list): por canción, dict con posterior, log-momios, log P(x) y los
            tokens presentes que más empujan hacia "me gusta" (solo visibles).
        """
        salida = []
        for c in lista:
            x = np.asarray(Xcat[c].toarray()).ravel() if sp.issparse(Xcat) else Xcat[c]
            presentes = np.flatnonzero(x > 0)
            aporte = aporte_si[presentes] * (x[presentes] if variante == "multinomial" else 1)
            orden = presentes[np.argsort(-aporte)]
            a_favor = [{"token": nombres_sel[j], "aporte": float(aporte_si[j] * (x[j] if variante == "multinomial" else 1))}
                       for j in orden if visibles[j] and aporte_si[j] > 0][:4]
            salida.append({"tipo": "naive_bayes", "variante": variante, "post": float(res["post"][c]),
                           "log_momios": float(res["log_momios"][c]), "log_px": float(res["log_px"][c]),
                           "a_favor": a_favor})
        return salida

    diagnostico = {
        "variante": variante, "alpha": alpha, "lambda": lam, "criterio": criterio,
        "tokens": nombres_sel, "visibles": visibles, "cols": cols,
        "p_like": modelo["p"][1] if variante == "bernoulli" else modelo["theta"][1],
        "p_nolike": modelo["p"][0] if variante == "bernoulli" else modelo["theta"][0],
        "aporte_presente": aporte_si, "aporte_ausente": aporte_no,
        "log_prior": modelo["log_prior"], "log_px": res["log_px"], "log_post": res["log_post"],
        "log_momios": res["log_momios"], "post": res["post"],
    }
    return puntajes, explicar, diagnostico
