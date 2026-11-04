# Perfil del dataset

Archivo: `data/raw/spotify_dataset.csv` (1.15 GB)

## Tamaño

- Filas: **551,443**
- Columnas: **39**
- Columnas: `Artist(s)`, `song`, `text`, `Length`, `emotion`, `Genre`, `Album`, `Release Date`, `Key`, `Tempo`, `Loudness (db)`, `Time signature`, `Explicit`, `Popularity`, `Energy`, `Danceability`, `Positiveness`, `Speechiness`, `Liveness`, `Acousticness`, `Instrumentalness`, `Good for Party`, `Good for Work/Study`, `Good for Relaxation/Meditation`, `Good for Exercise`, `Good for Running`, `Good for Yoga/Stretching`, `Good for Driving`, `Good for Social Gatherings`, `Good for Morning Routine`, `Similar Artist 1`, `Similar Song 1`, `Similarity Score 1`, `Similar Artist 2`, `Similar Song 2`, `Similarity Score 2`, `Similar Artist 3`, `Similar Song 3`, `Similarity Score 3`

## Nulos y cardinalidad

| columna | nulos | pct_nulos | distintos | ejemplo |
|---|---|---|---|---|
| Artist(s) | 0 | 0.000 | 127,334 | !!! |
| song | 0 | 0.000 | 317,907 | Even When the Waters Cold |
| text | 0 | 0.000 | -1 | (letra) |
| Length | 0 | 0.000 | 1,243 | 03:47 |
| emotion | 0 | 0.000 | 13 | sadness |
| Genre | 0 | 0.000 | 3,097 | hip hop |
| Album | 26 | 0.005 | 154,684 | Thr!!!er |
| Release Date | 0 | 0.000 | 14,299 | 29th April 2013 |
| Key | 0 | 0.000 | 24 | D min |
| Tempo | 0 | 0.000 | 170 | 105 |
| Loudness (db) | 0 | 0.000 | 3,746 | -6.85db |
| Time signature | 8 | 0.001 | 5 | 4/4 |
| Explicit | 0 | 0.000 | 2 | No |
| Popularity | 0 | 0.000 | 100 | 40 |
| Energy | 0 | 0.000 | 101 | 83 |
| Danceability | 0 | 0.000 | 94 | 71 |
| Positiveness | 0 | 0.000 | 101 | 87 |
| Speechiness | 0 | 0.000 | 96 | 4 |
| Liveness | 0 | 0.000 | 100 | 16 |
| Acousticness | 0 | 0.000 | 101 | 11 |
| Instrumentalness | 0 | 0.000 | 101 | 0 |
| Good for Party | 0 | 0.000 | 2 | 0 |
| Good for Work/Study | 0 | 0.000 | 2 | 0 |
| Good for Relaxation/Meditation | 0 | 0.000 | 2 | 0 |
| Good for Exercise | 0 | 0.000 | 2 | 0 |
| Good for Running | 0 | 0.000 | 2 | 0 |
| Good for Yoga/Stretching | 0 | 0.000 | 2 | 0 |
| Good for Driving | 0 | 0.000 | 2 | 0 |
| Good for Social Gatherings | 0 | 0.000 | 2 | 0 |
| Good for Morning Routine | 0 | 0.000 | 2 | 0 |
| Similar Artist 1 | 0 | 0.000 | 90,280 | Corey Smith |
| Similar Song 1 | 0 | 0.000 | 218,727 | If I Could Do It Again |
| Similarity Score 1 | 0 | 0.000 | 361,212 | 0.9860607848219312 |
| Similar Artist 2 | 0 | 0.000 | 87,533 | Toby Keith |
| Similar Song 2 | 0 | 0.000 | 207,671 | Drinks After Work |
| Similarity Score 2 | 0 | 0.000 | 421,954 | 0.9837194773786985 |
| Similar Artist 3 | 0 | 0.000 | 86,963 | Space |
| Similar Song 3 | 0 | 0.000 | 206,001 | Neighbourhood |
| Similarity Score 3 | 0 | 0.000 | 439,500 | 0.9832363508466967 |

## Formatos de `Length`

| patron | len |
|---|---|
| 9:9 | 551,443 |

## Formatos de `Release Date`

| patron | len |
|---|---|
| 9A A 9 | 551,443 |

## Formatos de `Loudness (db)`

| patron | len |
|---|---|
| -9.9A | 482,767 |
| -9A | 68,292 |
| 9.9A | 361 |
| 9A | 23 |

## Formatos de `Tempo`

| patron | len |
|---|---|
| 9 | 551,443 |

## Formatos de `Popularity`

| patron | len |
|---|---|
| 9 | 551,443 |

## Formatos de `Time signature`

| patron | len |
|---|---|
| 9/9 | 551,435 |
| None | 8 |

## Distribuciones numéricas

`duracion_s`, `tempo`, `volumen_db`, `anio` y `popularidad` son conversiones del texto original.

| columna | min | p05 | mediana | p95 | max | media | nulos |
|---|---|---|---|---|---|---|---|
| duracion_s | 5.000 | 123.000 | 214.000 | 350.000 | 3,572.000 | 223.614 | 0 |
| tempo | 31.000 | 78.000 | 120.000 | 174.000 | 200.000 | 120.514 | 0 |
| volumen_db | -50.060 | -15.320 | -7.190 | -3.390 | 4.980 | -8.075 | 0 |
| popularidad | 0.000 | 5.000 | 30.000 | 67.000 | 100.000 | 32.258 | 0 |
| anio | 1,899.000 | 1,980.000 | 2,016.000 | 2,024.000 | 2,024.000 | 2,010.770 | 0 |
| Energy | 0.000 | 21.000 | 65.000 | 95.000 | 100.000 | 62.662 | 0 |
| Danceability | 6.000 | 28.000 | 60.000 | 87.000 | 99.000 | 59.195 | 0 |
| Positiveness | 0.000 | 10.000 | 47.000 | 89.000 | 100.000 | 47.738 | 0 |
| Speechiness | 2.000 | 3.000 | 6.000 | 38.000 | 97.000 | 11.664 | 0 |
| Liveness | 1.000 | 6.000 | 13.000 | 56.000 | 100.000 | 19.656 | 0 |
| Acousticness | 0.000 | 0.000 | 12.000 | 88.000 | 100.000 | 25.748 | 0 |
| Instrumentalness | 0.000 | 0.000 | 0.000 | 69.000 | 100.000 | 7.152 | 0 |
| Similarity Score 1 | 0.003 | 0.960 | 0.986 | 1.000 | 1.000 | 0.984 | 0 |
| Similarity Score 3 | 0.003 | 0.947 | 0.978 | 1.000 | 1.000 | 0.976 | 0 |
| letra_chars | 100.000 | 529.000 | 1,501.000 | 3,722.000 | 79,626.000 | 1,762.309 | 0 |
| letra_palabras | 11.000 | 102.000 | 294.000 | 729.000 | 15,841.000 | 345.073 | 0 |

## Columnas `Good for ...` (fracción con 1)

| uso | fraccion_1 |
|---|---|
| Good for Party | 0.062 |
| Good for Work/Study | 0.075 |
| Good for Relaxation/Meditation | 0.031 |
| Good for Exercise | 0.187 |
| Good for Running | 0.054 |
| Good for Yoga/Stretching | 0.021 |
| Good for Driving | 0.058 |
| Good for Social Gatherings | 0.012 |
| Good for Morning Routine | 0.066 |

## `emotion` (13 valores)

| emotion | len |
|---|---|
| joy | 209,009 |
| sadness | 171,078 |
| anger | 109,678 |
| fear | 28,097 |
| love | 27,963 |
| surprise | 5,592 |
| True | 17 |
| Love | 3 |
| pink | 2 |
| angry | 1 |
| thirst | 1 |
| confusion | 1 |
| interest | 1 |

## `Genre` (3097 valores)

| Genre | len |
|---|---|
| hip hop | 262,070 |
| pop | 11,451 |
| country | 7,392 |
| folk | 4,897 |
| jazz | 3,913 |
| soul | 3,689 |
| rock,pop,alternative rock | 3,527 |
| rock | 3,460 |
| rap,hip hop | 3,396 |
| hip hop,trap | 3,297 |
| rap,hip hop,trap | 3,018 |
| trap | 2,920 |
| rock,heavy metal,metal | 2,831 |
| rock,alternative rock,indie rock | 2,695 |
| reggae | 2,614 |
| indie rock | 2,394 |
| rock,alternative rock,punk | 2,388 |
| rap,hip-hop,hip hop | 2,158 |
| indie pop | 1,942 |
| punk | 1,755 |
| hip-hop,hip hop | 1,693 |
| classical | 1,618 |
| rock,electronic,synthpop | 1,616 |
| trap,hip hop | 1,592 |
| rock,trance,electronic | 1,533 |

## `Key` (24 valores)

| Key | len |
|---|---|
| C Maj | 47,745 |
| G Maj | 47,465 |
| D Maj | 44,568 |
| C# Maj | 44,409 |
| A Maj | 33,849 |
| G# Maj | 26,045 |
| B min | 25,772 |
| E min | 22,348 |
| F Maj | 22,298 |
| A min | 21,094 |
| A# min | 20,261 |
| B Maj | 19,764 |
| E Maj | 19,633 |
| F# min | 19,529 |
| F# Maj | 19,470 |
| F min | 19,073 |
| C# min | 18,583 |
| A# Maj | 16,250 |
| G min | 14,558 |
| C min | 12,224 |
| D min | 10,455 |
| G# min | 10,293 |
| D# Maj | 9,233 |
| D# min | 6,524 |

## `Time signature` (5 valores)

| Time signature | len |
|---|---|
| 4/4 | 501,051 |
| 3/4 | 36,934 |
| 5/4 | 9,468 |
| 1/4 | 3,982 |
| None | 8 |

## `Explicit` (2 valores)

| Explicit | len |
|---|---|
| No | 389,378 |
| Yes | 162,065 |

Fracción de registros con coma en `Genre` (varios géneros): **39.6%**

## Relación `emotion` – `Positiveness`

Si la etiqueta fuera fiel, `joy` tendría positividad mucho mayor que `sadness`.

| emotion | n | positividad_media | energia_media |
|---|---|---|---|
| joy | 209,009 | 49.614 | 62.056 |
| sadness | 171,078 | 44.524 | 62.317 |
| anger | 109,678 | 49.354 | 65.477 |
| fear | 28,097 | 45.516 | 63.194 |
| love | 27,963 | 49.131 | 58.103 |
| surprise | 5,592 | 48.503 | 60.755 |
| True | 17 | 38.824 | 61.765 |
| Love | 3 | 34.000 | 76.000 |
| pink | 2 | 24.000 | 75.500 |
| angry | 1 | 21.000 | 63.000 |
| thirst | 1 | 54.000 | 67.000 |
| confusion | 1 | 8.000 | 60.000 |

## Duplicados

- Filas idénticas (sin contar letra): **53,391**
- Mismo artista y título exactos: **53,391**
- Mismo artista y título normalizados: **58,641**
- Artistas distintos: **127,334**

## `Similar Songs`

Vienen aplanadas en 9 columnas (artista, canción y puntaje × 3). En una muestra de 20,000 filas, **88.8%** de los similares existen en el dataset (artista y título normalizados).

## Idiomas (muestra de 2,995 letras, `langdetect`)

| idioma | n | pct |
|---|---|---|
| en | 2,979 | 99.466 |
| id | 6 | 0.200 |
| tl | 2 | 0.067 |
| sw | 2 | 0.067 |
| it | 1 | 0.033 |
| fr | 1 | 0.033 |
| es | 1 | 0.033 |
| af | 1 | 0.033 |
| nl | 1 | 0.033 |
| pt | 1 | 0.033 |

## Letras

Fracción con saltos de línea: **0.0%**. Letras con menos de 50 palabras: **5,091**.
