# Modelos de regresión

## La idea (sección 4.4.5)

Los modelos de regresión sirven para calificaciones binarias, por intervalos o numéricas. El más simple es la **regresión lineal**: supone que la calificación es una función lineal de las frecuencias de las palabras.

Sea $D_L$ la matriz de $n \times d$ con los ítems que el usuario calificó (una columna por término) y $y$ el vector con sus calificaciones. Buscamos un vector de pesos $W$, uno por palabra, tal que

$$y \approx D_L W^T$$

Para evitar el sobreajuste se agrega una penalización $\lambda\lVert W\rVert^2$ (regularización de Tikhonov):

$$\min_W \; \lVert D_L W^T - y \rVert^2 + \lambda \lVert W \rVert^2$$

Esto tiene solución cerrada:

$$W^T = (D_L^T D_L + \lambda I)^{-1} D_L^T y$$

La calificación de un ítem nuevo $X$ es el producto punto entre $W$ y $X$. Con regularización $L_1$ (Lasso) no hay solución cerrada, pero muchos pesos quedan en cero: es una selección de características que se interpreta muy bien.

## Según el tipo de calificación

| Modelo | Calificación |
|---|---|
| Regresión lineal, polinomial o kernel | Real |
| Regresión logística binaria | Unaria, binaria |
| Logística multiclase | Categórica, ordinal |
| Probit | Unaria, binaria |
| Probit ordenado | Ordinal, por intervalos |

Las calificaciones unarias se suelen tratar como binarias, tomando los ítems sin etiqueta como negativos; existen modelos especializados para ese caso (positivo-no etiquetado). Cuando hay muchas características y pocos ejemplos, los modelos lineales suelen funcionar muy bien, incluso mejor que los no lineales, porque se sobreajustan menos.

## En esta app

Como tus calificaciones son binarias, usamos **regresión logística** con regularización $L_2$ (el control $C$ es el inverso de $\lambda$). Los pesos aprendidos forman **tu retrato sonoro**: qué características te acercan a una canción y cuáles te alejan. La variante **SVM lineal** (sección 4.4.6) es muy parecida; cambia la pérdida logística por la pérdida de bisagra (*hinge*).
