# La idea de los sistemas basados en contenido

A John le encantó *Terminator*. ¿De verdad hace falta preguntarle a miles de usuarios para adivinar que probablemente también le guste *Aliens*? No: basta con saber que ambas son de ciencia ficción, futuristas y con acción.

Esa es la idea: en lugar de mirar a otros usuarios, **miramos dentro de los ítems, a sus atributos**, y recomendamos cosas parecidas a las que ya le gustaron. "Parecidas" significa que comparten características, no que les gustaron a las mismas personas.

Y hay una ventaja enorme: si mañana sale una película que nadie ha calificado, el filtrado colaborativo no tiene con qué trabajar porque su columna en la matriz está vacía. Un sistema basado en contenido sí puede recomendarla, porque ya sabe de qué trata.

## Dos fuentes de datos

1. **La descripción de los ítems:** atributos como la sinopsis, el género o la descripción del fabricante. *Aquí: la letra, el género, la emoción, la década y las características de audio de cada canción.*
2. **El perfil del usuario:** se construye con su retroalimentación, explícita (estrellas, me gusta) o implícita (lo que compra, escucha o en lo que da clic).

En su versión más sencilla, el perfil es una tabla: cada fila es un ítem que John ya calificó, las columnas son sus características y la etiqueta es la calificación de John. Es exactamente un problema de **clasificación o regresión**, con las características como $X$ y las calificaciones como $y$.

Detalle importante: solo se usan las calificaciones de John. **Cada usuario tiene su propio modelo.** Incluso el usuario podría escribir las palabras clave que le interesan, algo cercano a los sistemas basados en conocimiento.

## ¿Cuándo conviene usarlos?

Cuando hay mucha información sobre los ítems, casi siempre en forma de texto: descripciones de productos, noticias, páginas web. Por eso brillan en dominios ricos en texto no estructurado; un ejemplo clásico es recomendar páginas web a partir de lo que has navegado. También se usan en comercio electrónico, combinando palabras clave con atributos como el fabricante, el género o el precio.

## Los tres componentes

1. **Preprocesamiento y extracción de características** (fuera de línea).
2. **Aprendizaje del perfil del usuario** (fuera de línea).
3. **Filtrado y recomendación** (en línea, en tiempo real, así que debe ser rapidísimo).

En esta app, el paso 1 se corrió una sola vez sobre el dataset; los pasos 2 y 3 ocurren cada vez que pides recomendaciones, en milisegundos.
