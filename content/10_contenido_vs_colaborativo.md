# Contenido contra colaborativo

## Ventajas y desventajas (sección 4.5)

**Ventajas de los sistemas basados en contenido:**

1. **Ítems nuevos.** Una canción recién agregada no tiene calificaciones, así que el filtrado colaborativo no la recomendaría. Un sistema basado en contenido sí, porque usa lo que el usuario ya calificó. El colaborativo sufre arranque en frío con usuarios e ítems nuevos; el basado en contenido, solo con usuarios nuevos.
2. **Explicaciones** en términos de las características de los ítems, algo que el colaborativo casi nunca puede dar.
3. **Facilidad**: se pueden usar clasificadores de texto existentes, y cada problema por usuario es pequeño.

**Desventajas:**

1. **Sobreespecialización.** Tienden a recomendar lo parecido a lo que ya viste, con poca novedad y serendipia. Si alguien nunca ha calificado música clásica, el sistema difícilmente se la recomendará, porque sus atributos son muy distintos; un sistema colaborativo podría descubrir que a quienes les gusta cierto pop también les gusta cierta música clásica.
2. **Usuarios nuevos.** No resuelven el arranque en frío para ellos; incluso puede ser peor, porque un clasificador necesita suficientes ejemplos para no sobreajustarse, y se desperdician los datos de los demás usuarios.

Por eso rara vez se usan solos: se combinan con otros en **sistemas híbridos**.

## Usar contenido para filtrado colaborativo (sección 4.6)

Un ítem se puede describir con las calificaciones que recibió en lugar de con sus atributos. Cada combinación de usuario y calificación se vuelve una palabra clave:

- *Terminator*: John#Like, Alice#Dislike, Tom#Like
- *Aliens*: John#Like, Peter#Dislike, Alice#Dislike, Sayani#Like

Sobre esta representación se puede aplicar cualquier clasificador de contenido, y cada uno corresponde aproximadamente a un método colaborativo: vecinos se parece al modelo de vecindario por ítems, la regresión a la regresión por usuario, y las reglas y Bayes a sus versiones por usuario. Así no se desperdician los datos de otros usuarios, y se pueden combinar palabras clave de calificaciones con palabras clave descriptivas en un solo modelo híbrido.
