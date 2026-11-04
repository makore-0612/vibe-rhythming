# Recomendación con motivo

Para ciertos productos, como la música, es importante decir **por qué** se recomienda algo. La razón es simple: solo viendo la portada de un disco no sabes si escucharlo. Necesitas saber el género, el artista, quizá la letra o los títulos de las canciones.

Esas explicaciones dependen del algoritmo:

- **Vecinos más cercanos:** "Se parece a *X*, que te gustó: comparten *amor* y *noche*; ambas son *pop*". Es el "te recomendamos esto porque viste…" de Netflix.
- **Naive Bayes:** qué características tienen mayor $P(x \mid \text{te gusta})$ frente a $P(x \mid \text{no te gusta})$ y cuánto empujan los log-momios.
- **Reglas:** la regla que se disparó, con su confianza y su soporte.
- **Regresión:** las características con mayor contribución $w_j \cdot x_j$.

Cada recomendación de esta app trae la explicación de su algoritmo. Compáralas: algunas son más convincentes que otras.
