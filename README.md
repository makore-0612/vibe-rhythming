[![Plataforma en vivo](assets/readmeport.png)](https://vibe-rhythming.streamlit.app/)

# Vibe Rhythming

* Castrillo Cruz Karen Arlet
* Ramos González Nadia
* Zamora Antiga Ángel Javier

---

Aplicación que contiene sistemas de recomendación basados en contenido que procesan recomendaciones para el usuario en tiempo real a través de cuatro clasificadores distintos: Vecinos más cercanos, Naive Bayes, Reglas de Asociación y Regresión Logística. Dentro de la interfaz podrás seleccionar los parámetros de cada modelo, mejorar las recomendaciones acorde a tus preferencias y darle peso a cada componente a considerar en las sugerencias.

Dentro de la página y en el HTML presente en el repositorio podrás conocer más acerca del tema a partir del capítulo 4 del libro de Charu C. Aggarwal. 

# Estructura

```
.
├── app.py                      # Punto de entrada: aplica el parche y lanza la app (st.App)
├── principal.py                # Script de Streamlit: tema, carga de datos y navegación
├── requirements.txt            # Dependencias de la app
├── requirements-pipeline.txt   # Dependencias del procesamiento de datos
├── .streamlit/
│   └── config.toml             # Tema (paleta y tipografía) y servidor
├── assets/                     # Imágenes del README y logos
├── static/                     # Tipografía Montserrat autoalojada y su licencia
├── content/                    # Resumen del capítulo 4 en Markdown (10 secciones)
├── data/
│   ├── palabras_ocultas.txt    # Términos que no se muestran en pantalla
│   └── processed/              # Artefactos que usa la app (≈ 5.5 MB, sin letras)
│       ├── catalogo.parquet    # 25,006 canciones: metadatos y audio
│       ├── conteos.npz         # Conteos de términos de las letras
│       ├── etiquetas.npz       # Género, emoción, década, tonalidad…
│       ├── usos.npz            # Columnas «Good for …»
│       ├── vocab.json          # Vocabulario, idf y formas legibles
│       ├── similares.parquet   # Pares de «Similar Songs» dentro del catálogo
│       ├── eval_similares.json # Evaluación offline
│       ├── perfil.md           # Perfil del dataset original
│       └── reporte_catalogo.md # Distribuciones antes y después del muestreo
├── pipeline/                   # Procesamiento fuera de línea (se corre una vez)
│   ├── perfil_dataset.py       # Perfil del CSV original
│   ├── construir_catalogo.py   # Limpieza, deduplicación y muestreo
│   ├── construir_features.py   # Letras → TF-IDF; etiquetas, audio y usos
│   ├── evaluar_similares.py    # Evaluación contra «Similar Songs»
│   └── run_all.py              # Corre todo y verifica el tamaño de los artefactos
├── src/                        # Motor de recomendación
│   ├── config.py               # Constantes y rutas
│   ├── datos.py                # Carga de artefactos y matrices
│   ├── features.py             # TF-IDF, bloques y tokens binarios
│   ├── perfil.py               # Me gusta, no me gusta y pseudo-negativos
│   ├── seleccion.py            # Gini, entropía, χ² y desviación normalizada
│   ├── algoritmos/
│   │   ├── vecinos.py          # Vecinos más cercanos (4.4.1)
│   │   ├── naive_bayes.py      # Bernoulli y multinomial (4.4.3)
│   │   ├── reglas.py           # Apriori por usuario (4.4.4)
│   │   └── regresion.py        # Regresión logística y SVM lineal (4.4.5–4.4.6)
│   ├── motor.py                # Entrena, ordena y explica en una sola llamada
│   ├── reranking.py            # Exclusiones, tope por artista, diversidad y novedad
│   ├── metricas.py             # Novedad, diversidad, serendipia, Jaccard…
│   ├── votos.py                # Votación en vivo compartida entre sesiones
│   ├── parche_streamlit.py     # Corrección de un bug de Streamlit 1.58 en la nube
│   └── ui/                     # Tema, componentes, gráficas y estado de la sesión
├── paginas/                    # Páginas de la app
│   ├── inicio.py
│   ├── tienda.py
│   ├── recomendaciones.py
│   ├── laboratorio.py
│   ├── comparador.py
│   └── capitulo.py
└── tests/                      # Pruebas con pytest y recorridos con Playwright
```

No se incluyen en el repositorio, por derechos de autor o tamaño: `data/raw/` (el CSV original de 1.1 GB, que se descarga de Kaggle), `data/intermedio/` (letras temporales del procesamiento) y `docs/`. Para regenerar los artefactos:

```bash
pip install -r requirements-pipeline.txt
python -c "import nltk; nltk.download('stopwords')"
python pipeline/run_all.py
```

Para correr la app:

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

## Datos y licencias

- **Dataset:** *500K+ Spotify Songs with Lyrics, Emotions & More*, de DevDope, en [Kaggle](https://www.kaggle.com/datasets/devdope/900k-spotify/data) (551,443 filas en el CSV usado). Licencia [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/): uso no comercial y con atribución. Este proyecto es académico y sin fines de lucro. Solo se publican metadatos, características numéricas y conteos de términos derivados, nunca las letras.
- **Montserrat:** SIL Open Font License 1.1 (`static/OFL.txt`).
- **Portadas:** generadas con SVG a partir de un hash de artista y título; no son portadas reales.
- **Capítulo:** Basado en el capítulo 4, Content-Based Recommender Systems, de Charu C. Aggarwal, Recommender Systems: The Textbook, Springer, 2016.

> Instituto de Investigaciones en Matemáticas Aplicadas y en Sistemas, Universidad Nacional Autónoma de México. 
---
<img src="https://mmss.iimas.unam.mx/dmmss/wp-content/uploads/2026/02/cropped-LogoUNAM_IIMAS_Negro50-scaled-2.png" width="100"/>
