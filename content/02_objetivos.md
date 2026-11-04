# Objetivos de los sistemas de recomendación

¿Por qué nos recomiendan lo que nos recomiendan? Globalmente, el objetivo es uno: **aumentar las ventas y las ganancias**. Para lograrlo hay que ofrecer ítems que nos resulten afines. Por siglos nos hemos preguntado por qué nos gusta lo que nos gusta; hoy los anunciantes buscan la fórmula para que un artículo le guste a cada consumidor. Esa fórmula combina cuatro objetivos locales:

1. **Relevancia.** Sugerir ítems afines a los intereses históricos del usuario. Optimizar solo para la relevancia es peligroso: produce listas predecibles y monótonas, con demasiada familiaridad y cero sorpresa.
2. **Novedad.** La palabra más común en los anuncios no es "compra" ni "ahora": es "nuevo". Un buen sistema expone ítems de la **cola larga**, productos menos populares que el usuario no habría encontrado por sí mismo.
3. **Serendipia.** Un descubrimiento afortunado e inesperado: el algoritmo muestra algo que nunca habríamos buscado y que, sorpresivamente, nos encanta.
4. **Diversidad.** Que el Top-k sea heterogéneo, para que el usuario tenga alternativas distintas entre las cuales elegir.

*En Recomendaciones, los ajustes de "Diversidad" y "Novedad" reordenan tu lista para perseguir estos objetivos.*

## El espectro de aplicaciones

Un ítem puede ser un producto, una canción, una noticia o incluso una persona. Tres casos lo ilustran:

- **Amazon** entendió que no bastaba la retroalimentación explícita e integró la implícita: navegación, clics e historial de compras. Lo que haces en silencio dice más de ti que lo que calificas en voz alta.
- **Netflix** impulsó a la academia con el *Netflix Prize* y, de cara al usuario, apostó por la **explicación**: "Te recomendamos esto porque viste…". Justificar la recomendación genera confianza y lealtad.
- **Google News** trabaja con calificaciones unarias: un clic revela afinidad, pero la ausencia de clic no distingue entre "odié el titular" y "no estaba viendo la pantalla". Aprender solo de interacciones positivas es difícil. *En esta app, cuando no marcas suficientes "no me gusta", completamos con pseudo-negativos al azar: es exactamente ese problema.*

La formulación cambia de un caso a otro, pero el principio es el mismo: aprender de los datos.
