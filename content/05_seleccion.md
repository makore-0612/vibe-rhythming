# Recolección de gustos y selección de características

## Recolectar lo que le gusta al usuario (sección 4.3.3)

Además del contenido de los ítems, hace falta saber qué le gusta y qué no al **usuario activo**, aquel para quien se calcula la recomendación en ese momento. Según el libro, esos datos pueden llegar como:

1. **Calificaciones** binarias, por intervalos, ordinales o, rara vez, reales.
2. **Retroalimentación implícita**, como comprar o navegar; casi siempre solo captura preferencias positivas.
3. **Opiniones en texto**, de las que se extraen calificaciones con análisis de sentimiento.
4. **Casos**: ejemplos de ítems que le interesan, como la canción inicial de una estación de Pandora.

En todos los casos, al final se convierten en una calificación que funciona como **etiqueta de clase o variable dependiente** para aprender.

## Selección supervisada (sección 4.3.4)

No todas las palabras ayudan a predecir. Con las calificaciones del usuario podemos medir qué tan **discriminativa** es cada característica $w$. Sea $p_i(w)$ la fracción de los ítems que contienen $w$ y recibieron la calificación $i$, entre $t$ calificaciones posibles.

**Índice de Gini.** Menor es más discriminativo; vale 0 si todos los ítems con $w$ tienen la misma calificación.

$$\mathrm{Gini}(w) = 1 - \sum_{i=1}^{t} p_i(w)^2$$

**Entropía.** Misma idea con teoría de la información; menor es más discriminativo.

$$\mathrm{Entropía}(w) = -\sum_{i=1}^{t} p_i(w)\,\log p_i(w)$$

**Estadístico χ².** Compara la tabla de contingencia observada entre "contiene $w$" y "le gustó" contra la esperada si fueran independientes. Mayor indica más relación. Para una tabla de 2 × 2:

$$\chi^2 = \frac{(O_1+O_2+O_3+O_4)\,(O_1 O_4 - O_2 O_3)^2}{(O_1+O_2)(O_3+O_4)(O_1+O_3)(O_2+O_4)}$$

En el ejemplo del libro, con 1,000 ítems y la tabla 60, 40, 140, 760, el resultado es 111.11.

**Desviación normalizada.** Útil cuando las calificaciones tienen mucha granularidad. Con $\mu^+(w)$ la calificación promedio de los ítems que contienen $w$, $\mu^-(w)$ la de los que no, y $\sigma^2$ la varianza de todas:

$$\mathrm{Dev}(w) = \frac{|\mu^+(w) - \mu^-(w)|}{\sigma}$$

Mayor es más discriminativo.

## Ponderación (sección 4.3.4.5)

La ponderación es una versión suave de la selección: en vez de quitar características, cada una recibe un peso. El idf ya es una ponderación, pero no supervisada. Una supervisada sencilla, con $a > 1$:

$$g(w) = a - \mathrm{Gini}(w)$$

El peso queda en $(a-1,\, a)$, y valores pequeños de $a$ hacen la ponderación más sensible. Cada coordenada del vector se multiplica por $g(w)$.

*Cuidado práctico: una característica que aparece en una sola canción obtiene Gini 0 y parece perfecta sin serlo. Aquí exigimos que aparezca en al menos 2 canciones.*
