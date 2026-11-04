# Vecinos más cercanos

## El clasificador (sección 4.4.1)

Es una de las técnicas más simples. Primero se define una función de similitud; la más usada en texto es el **coseno**, porque se ajusta a documentos de distinta longitud:

$$\mathrm{Coseno}(X, Y) = \frac{\sum_{i} x_i y_i}{\sqrt{\sum_i x_i^2}\,\sqrt{\sum_i y_i^2}}$$

donde $x_i$ y $y_i$ son las frecuencias ya ponderadas (por ejemplo, con TF-IDF). Para datos estructurados se usan otras medidas, como la distancia euclidiana.

Para cada ítem sin calificar se buscan sus $k$ vecinos más cercanos entre los que el usuario ya calificó, y se promedian sus calificaciones; ese promedio es la predicción. Una mejora es ponderar cada calificación por su similitud. Luego se ordenan los ítems por la predicción y se recomiendan los primeros.

*En esta app: el puntaje de una canción es el promedio de $r_i \cdot s(c, i)$ entre sus $k$ vecinos, con $r = +1$ si te gustó y $-1$ si no.*

## Su costo

El reto principal es computacional: hay que comparar cada ítem sin calificar con cada ítem calificado, así que el costo es $|D_L| \times |D_U|$. Es un método **perezoso**: no entrena nada y hace todo el trabajo al momento de recomendar.

El libro propone agrupar: dividir los ítems calificados de cada calificación en $p$ grupos con *k-means*, unir cada grupo en un documento más grande y buscar los vecinos entre esos pocos documentos. Si cada calificación forma un solo grupo, el vector resultante es un **prototipo**, idea muy cercana al clasificador de Rocchio.

## Relación con los sistemas basados en casos (sección 4.4.2)

Los vecinos más cercanos se conectan con los sistemas basados en conocimiento, en particular con los **basados en casos**. La diferencia: ahí el usuario da de forma interactiva un solo ejemplo, y como solo hay uno, la función de similitud se diseña con mucho conocimiento del dominio. Ese ejemplo funciona más como un requisito que como una calificación histórica.
