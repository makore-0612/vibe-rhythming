# Introducción y terminología

Imagina la pantalla de inicio de tu cuenta de Netflix, los amigos que Facebook te sugiere agregar, los artículos que Amazon te propone comprar o las canciones que Spotify te recomienda. Si pudiéramos proyectar lo que cada persona ve, ninguna pantalla sería igual a otra. ¿Cómo logran estas empresas recomendaciones tan personalizadas, y para qué?

## Origen

Los sistemas de recomendación surgieron a principios de los años noventa, junto con el comercio electrónico. Al pasar de estantes físicos limitados a catálogos en línea apareció un problema masivo: la **sobrecarga de información**. Encontrar un producto, un artículo o una película relevante se volvió abrumador.

Las empresas vieron ahí una oportunidad. La Web facilitó obtener datos y que el usuario diera retroalimentación sobre lo que consumía, sin gran esfuerzo. Así empezaron a *datificar* nuestros gustos para personalizar lo que nos muestran. La idea básica: **usar todas las fuentes de datos disponibles para inferir los intereses de cada cliente**, apoyándose sobre todo en sus interacciones pasadas, porque lo que nos gustó antes suele ser el mejor indicador de lo que elegiremos después.

## Usuario, ítem y calificaciones

A la entidad que recibe la recomendación la llamamos **usuario**; al producto, película o canción que se recomienda, **ítem**.

Las calificaciones (*ratings*) pueden ser:

- **Continuas**, como una escala de −10 a 10.
- **Por intervalos**, como las estrellas del 1 al 5.
- **Ordinales**, como "malo", "regular", "bueno", "excelente".
- **Binarias**: me gusta o no me gusta. *Es lo que usa esta app.*
- **Unarias**: solo se registra la preferencia positiva, como un *like* o una compra.

Las unarias están ligadas a la **retroalimentación implícita**: comprar, reproducir o dar clic se interpreta como una señal de preferencia aunque nadie haya escrito una calificación.

## La matriz de calificaciones

Usuarios e ítems se relacionan con un modelo sencillo y poderoso: la **matriz de calificaciones** de tamaño $m \times n$, con $m$ usuarios en las filas y $n$ ítems en las columnas. La entrada $r_{ij}$ es la calificación del usuario $i$ al ítem $j$, y cuando la predice un algoritmo se escribe $\hat r_{ij}$.

El principio que sostiene a los algoritmos es que **existen dependencias significativas entre la actividad de los usuarios y la de los ítems**. Esas dependencias se aprenden de la matriz y sirven para predecir; entre más ítems haya calificado un usuario, más robustas serán las predicciones.

## Predecir es llenar huecos

La mayoría de las celdas de la matriz están vacías: nadie ha visto todo el catálogo de Netflix. Predecir significa estimar la calificación que un usuario le daría a lo que aún no ha visto, para decidir si vale la pena recomendárselo. En el fondo, es **imputar valores faltantes**.

El libro distingue tres familias de sistemas:

1. **Filtrado colaborativo:** usa las calificaciones de muchos usuarios de forma colectiva.
2. **Basados en conocimiento:** para ítems que se compran poco, como autos o casas; el usuario especifica requisitos que se combinan con conocimiento del dominio.
3. **Basados en contenido:** se apoyan en los atributos de los ítems. Son el tema de este capítulo.

## Predicción contra ranking

Hay dos formas de plantear el problema. En el **enfoque de predicción** el algoritmo intenta adivinar el valor exacto de la calificación. En el **enfoque de ranking (Top-k)**, que interesa más a las empresas, no importa si darías 4.8 o 4.9: basta con ordenar el catálogo de mayor a menor preferencia y mostrar los primeros 5 o 10. Esta app trabaja con ranking: cada algoritmo te entrega un Top-10.
