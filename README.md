# Vibe Rhythming

Tienda de música con recomendación basada en contenido, para acompañar la exposición del capítulo 4 de *Recommender Systems: The Textbook* (Charu C. Aggarwal, Springer, 2016).

Equipo: Nadia, Ángel y Karen · Licenciatura en Ciencia de Datos, IIMAS, UNAM.

## Correr la app

```bash
pip install -r requirements.txt
streamlit run app.py
```

La app solo usa los archivos de `data/processed/` (unos 5.5 MB). No necesita internet, bases de datos ni APIs.

## Reprocesar los datos

Coloca el CSV original en `data/raw/spotify_dataset.csv` (esa carpeta nunca se sube al repositorio) y corre:

```bash
pip install -r requirements-pipeline.txt
python -c "import nltk; nltk.download('stopwords')"
python pipeline/run_all.py        # unos 70 s; imprime tamaños y falla si se excede el presupuesto
python -m pytest tests            # incluye el test de que no se publiquen letras
```

Pasos del pipeline:

1. `perfil_dataset.py`: genera el reporte del dataset crudo (`data/processed/perfil.md`).
2. `construir_catalogo.py`: limpia, deduplica, agrupa en macrogéneros y muestrea unas 25,000 canciones (`reporte_catalogo.md` muestra las distribuciones antes y después).
3. `construir_features.py`: construye conteos de letra, idf, etiquetas y usos. **Las letras se vectorizan y se descartan**: en `data/processed/` no queda texto de letras.
4. `evaluar_similares.py`: hace la evaluación offline contra la columna `Similar Songs`.

## Desplegar en Streamlit Community Cloud

1. Confirma que `data/raw/`, `data/intermedio/` y `docs/capitulo4.pdf` estén ignorados (`git status` no debe mostrarlos).
2. Sube el repositorio a GitHub.
3. En [share.streamlit.io](https://share.streamlit.io) crea una app nueva con archivo principal `app.py`. En *Advanced settings* elige Python 3.12 o 3.13.
4. En *Secrets* agrega `codigo_votos = "..."`, que se usa para reiniciar la votación en vivo.
5. Copia la URL pública en `URL_APP` (`src/config.py`); el QR de Inicio se regenera solo.

## Datos y licencias

- **Dataset:** *500K+ Spotify Songs with Lyrics, Emotions & More*, de DevDope, en [Kaggle](https://www.kaggle.com/datasets/devdope/900k-spotify/data) (551,443 filas en el CSV usado). Licencia [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/): uso no comercial y con atribución. Este proyecto es académico y sin fines de lucro. Solo se publican metadatos, características numéricas y conteos de términos derivados, nunca las letras.
- **Montserrat:** SIL Open Font License 1.1 (`static/OFL.txt`).
- **Portadas:** generadas con SVG a partir de un hash de artista y título; no son portadas reales.
- **Capítulo:** el resumen está parafraseado. El PDF del libro no se incluye.
