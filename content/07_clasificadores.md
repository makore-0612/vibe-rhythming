# Cómo clasificar: Naive Bayes y reglas

Ya sabemos identificar qué información ayuda a deducir qué contenido será relevante para cada usuario, y vimos un primer algoritmo para recomendar: el vecino más cercano. Pese a ser explicable, ese cálculo suele ser costoso. Entonces conviene un enfoque **ansioso** (*eager*), que entrena un modelo antes de recomendar; por ejemplo, un clasificador Naive Bayes.

## Naive Bayes (sección 4.4.3)

En estos sistemas se usan dos variantes:

- **Bernoulli:** modela si una palabra aparece o no en el vector.
- **Multinomial:** modela cuántas veces aparece cada palabra.

La variable objetivo es "le gusta" o "no le gusta": queremos saber si a un usuario le gusta un ítem dado que tiene ciertas características. La hipótesis que da nombre al método es que la aparición de cada palabra es **independiente** de las demás, dada la clase:

$$P(\text{le gusta} \mid x_1, \dots, x_d) \;\propto\; P(\text{le gusta}) \prod_{i=1}^{d} P(x_i \mid \text{le gusta})$$

## La constante de proporcionalidad

El denominador $P(x_1, \dots, x_d)$ no depende de la clase, así que para decidir si a un usuario le gusta **un** ítem basta comparar los numeradores. Pero para **ordenar muchos ítems** hace falta la probabilidad real, y entonces la constante importa. El libro la obtiene de que las probabilidades de ambas clases suman 1:

$$K = \frac{1}{P(\text{gusta})\prod_i P(x_i \mid \text{gusta}) + P(\text{no gusta})\prod_i P(x_i \mid \text{no gusta})}$$

Con $K$ se calcula la probabilidad de que al usuario le guste cada ítem, y los ítems se ordenan según esa probabilidad: un **ranking de afinidad**.

En la práctica, con muchas características esa probabilidad se pega a 0 o a 1, y se ordena por log-momios, que dan el mismo orden sin problemas numéricos. En el Laboratorio puedes ver qué pasa si, en vez de normalizar, se ordena por el numerador $P(\text{gusta}, x)$, que favorece las canciones con combinaciones de características comunes.

## Suavizado de Laplace

Si una palabra nunca apareció en las canciones que te gustan, su probabilidad estimada es 0 y anula todo el producto. Para evitar ese sobreajuste se usa el **suavizado de Laplace**:

$$P(x_i = 1 \mid c) = \frac{n_{ic} + \alpha}{n_c + 2\alpha}$$

## Reglas de asociación (sección 4.4.4)

Una alternativa que facilita entender cómo funciona el sistema son las reglas de asociación: "si es ciencia ficción y del director Nolan, entonces muy probablemente le guste al usuario". Se pueden combinar con SON (para minar todo el catálogo o usuarios en un clúster) o con Toivonen (cuando hay muchos registros), pero como este enfoque construye un modelo especializado por usuario, basta con Apriori.

## ¿Tengo alternativa? (sección 4.4.6)

Las opciones anteriores son las más usadas en la literatura, pero no las únicas: también hay árboles de decisión y máquinas de soporte vectorial. Los árboles no son adecuados para alta dimensionalidad y rinden peor que otros métodos. Las máquinas de soporte vectorial rinden bien en alta dimensión y resisten el sobreajuste, pero son menos explicables, tardan más en entrenarse y requieren más datos.
