# Extracción de características

El objetivo de esta etapa es extraer **características discriminativas**: las que mejor predicen lo que le gusta al usuario. Lo más común son las palabras clave, porque las descripciones en texto están en todos lados. A veces todo se vuelve una *bolsa de palabras*; otras conviene una representación estructurada, por ejemplo con números como el precio o con pocas opciones posibles como el color.

## Un ejemplo musical (sección 4.3.1.3)

El libro describe Pandora, una radio por internet que asocia cada canción con características del *Music Genome Project*, como "raíces trance", "riffs de sintetizador" o "batería recta". El usuario da una canción de ejemplo para crear una "estación", recibe canciones parecidas y las califica; con esas calificaciones el modelo se refina. Aunque esas características son muy distintas de las palabras de un texto, se pueden tratar como palabras clave: el "documento" de una canción es su bolsa de características. El primer paso, dar una canción de ejemplo, se parece más a un sistema basado en casos (de conocimiento); el refinamiento con calificaciones ya es basado en contenido. Pandora, además, explica sus recomendaciones con los atributos de las canciones.

*Esta app hace algo parecido con cuatro bloques de características por canción: letra (TF-IDF), etiquetas (género, emoción, década, tonalidad), audio (energía, bailabilidad, tempo…) y usos ("buena para fiesta", "para correr"…).*

## No todas las palabras valen lo mismo

La sinopsis de *Shrek* en IMDb dice: "Después de que su **pantano** se llena de criaturas mágicas, un ogro acepta rescatar a una princesa…". En una bolsa de palabras, "pantano" pesaría lo mismo que el nombre del actor principal, y seguramente a John le importa más quién actúa. Hay dos soluciones:

1. **Conocimiento del dominio:** dar más peso a mano al título o al actor, casi siempre por prueba y error.
2. **Aprender los pesos:** la **ponderación de características**, una versión suave de la selección. En lugar de decidir si una variable entra o no, se le asigna un peso.

## Limpieza del texto

1. **Quitar *stop words*:** artículos, preposiciones y palabras como "el", "un", "de". Están en todos lados y no dicen nada del ítem. *Aquí también quitamos relleno de canciones: "yeah", "oh", "la", "na".*
2. ***Stemming*:** junta variaciones de una palabra; "rescatar", "rescató" y "rescatando" se vuelven una raíz. A veces se equivoca y junta palabras sin relación.
3. **Extracción de frases:** detecta palabras que suelen ir juntas (colocaciones) y relaciones semánticas. *Aquí añadimos los bigramas más frecuentes, como "fall love" o "every night".*

## TF-IDF

Con el texto limpio, cada ítem es un vector con la frecuencia de cada **término**. Pero las palabras que aparecen en casi todos los documentos no ayudan a distinguir: si todas las películas dicen "aventura", esa palabra no aporta. La solución es la **frecuencia inversa de documento**:

$$\mathrm{idf}_i = \log\left(\frac{n}{n_i}\right)$$

donde $n$ es el total de documentos y $n_i$ es en cuántos aparece el término $i$. Con 4 películas, "ogro" aparece en 1: $\log(4/1) \approx 1.39$. "Aventura" aparece en las 4: $\log(4/4) = 0$. Es como quitar *stop words*, pero suave: en vez de borrar la palabra, le bajamos el volumen.

Para que una palabra repetida muchísimas veces no domine, la frecuencia se puede **amortiguar** con una raíz o un logaritmo. Juntando todo:

$$h(x_i) = f(x_i) \cdot \mathrm{idf}_i$$

*En esta app usamos $\log(1 + f) \cdot \mathrm{idf}$ y normalizamos cada vector a longitud 1.*
