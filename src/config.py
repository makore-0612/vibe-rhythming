"""
Constantes, rutas y parámetros compartidos por el pipeline y la app.
"""

from pathlib import Path

APP_NAME = "Vibe Rhythming"
URL_APP = "https://rb.gy/rq925g"

RAIZ = Path(__file__).resolve().parent.parent
DIR_RAW = RAIZ / "data" / "raw"
DIR_INTERMEDIO = RAIZ / "data" / "intermedio"   # ignorado por git: aquí sí hay letras
DIR_PROCESADO = RAIZ / "data" / "processed"
RUTA_CSV = DIR_RAW / "spotify_dataset.csv"
RUTA_PALABRAS_OCULTAS = RAIZ / "data" / "palabras_ocultas.txt"

RUTA_CATALOGO = DIR_PROCESADO / "catalogo.parquet"
RUTA_CONTEOS = DIR_PROCESADO / "conteos.npz"
RUTA_ETIQUETAS = DIR_PROCESADO / "etiquetas.npz"
RUTA_USOS = DIR_PROCESADO / "usos.npz"
RUTA_VOCAB = DIR_PROCESADO / "vocab.json"
RUTA_SIMILARES = DIR_PROCESADO / "similares.parquet"
RUTA_EVAL_SIMILARES = DIR_PROCESADO / "eval_similares.json"
RUTA_LETRAS_INTERMEDIAS = DIR_INTERMEDIO / "letras.parquet"

SEMILLA = 42

# Catálogo
CATALOGO_N = 25_000
MIN_PALABRAS_LETRA = 50
TOPE_POR_ARTISTA_CATALOGO = 15
FRACCION_POPULARES = 0.8
EMOCIONES_VALIDAS = ["joy", "sadness", "anger", "fear", "love", "surprise"]
IDIOMAS_VALIDOS = ["en", "es"]

# Macrogéneros: primer valor de `Genre` → grupo para cuotas y chips.
MACROGENEROS = {
    "hip hop / rap": ["hip hop", "hip-hop", "rap", "trap", "grime", "emo rap", "cloud rap"],
    "rock": ["rock", "alternative rock", "indie rock", "hard rock", "progressive rock", "psychedelic rock",
             "classic rock", "garage rock", "indie", "alternative", "shoegaze", "grunge", "math rock",
             "britpop", "psychedelic", "new wave", "post-punk"],
    "punk / emo": ["punk", "punk rock", "pop punk", "emo", "post-hardcore", "hardcore", "screamo"],
    "metal": ["metal", "heavy metal", "metalcore", "progressive metal", "melodic death metal", "power metal",
              "deathcore", "nu metal", "thrash metal", "black metal", "death metal", "doom metal", "industrial"],
    "pop": ["pop", "pop rock", "indie pop", "synthpop", "electropop", "k-pop", "j-pop", "dream pop"],
    "electrónica": ["electronic", "drum and bass", "dance", "trance", "house", "techno", "electro", "dubstep",
                    "ambient", "chillwave", "chillout", "trip-hop", "lo-fi", "experimental"],
    "country / folk": ["country", "folk", "alt-country", "acoustic"],
    "r&b / soul / funk": ["soul", "funk", "rnb", "disco"],
    "jazz / blues": ["jazz", "blues", "swing"],
    "reggae / latina": ["reggae", "dancehall", "dub", "latin", "reggaeton"],
    "clásica / bandas sonoras": ["classical", "soundtrack"],
    "gospel / cristiana": ["gospel", "christian", "worship"],
}
MACROGENERO_OTRO = "otros"

# Columnas de audio en el CSV (0–100) → nombre en el catálogo (0–1).
COLS_AUDIO = {
    "Energy": "energia", "Danceability": "bailabilidad", "Positiveness": "positividad",
    "Speechiness": "habla", "Liveness": "en_vivo", "Acousticness": "acustica",
    "Instrumentalness": "instrumental",
}
COLS_USOS = {
    "Good for Party": "fiesta", "Good for Work/Study": "estudio",
    "Good for Relaxation/Meditation": "relajación", "Good for Exercise": "ejercicio",
    "Good for Running": "correr", "Good for Yoga/Stretching": "yoga",
    "Good for Driving": "manejar", "Good for Social Gatherings": "reuniones",
    "Good for Morning Routine": "mañana",
}

# Letras
VOCAB_MAX = 8_000
VOCAB_MAX_BIGRAMAS = 1_500
MIN_DF = 20
MAX_DF = 0.5
TERMINOS_POR_CANCION = 80
RELLENO = ["yeah", "oh", "la", "na", "uh", "ooh", "ah", "hey", "yo", "woah", "whoa", "mmm", "hmm", "ha",
           "huh", "uh-huh", "ay", "eh", "da", "doo", "ba", "nah", "ya", "gonna", "wanna", "gotta", "ain't",
           "im", "dont", "cant", "aint", "got", "get", "like", "just", "know", "oh-oh", "yeah-yeah", "hey-hey",
           "chorus", "verse", "x2", "x3", "repeat", "instrumental", "intro", "outro", "bridge", "hook"]

# Perfil demo "John": (artista, fragmento de título). Se resuelve contra el catálogo al cargarlo.
PERFIL_DEMO = {
    "me_gusta": [
        ("Coldplay", "Yellow"), ("Arctic Monkeys", "I Wanna Be Yours"), ("Linkin Park", "In The End"),
        ("The Neighbourhood", "Sweater Weather"), ("Hozier", "Take Me to Church"), ("Queen", "Don't Stop Me Now"),
        ("Red Hot Chili Peppers", "Can't Stop"), ("Nirvana", "Smells Like Teen Spirit"),
        ("Muse", "Supermassive Black Hole"), ("Foo Fighters", "Everlong"), ("Imagine Dragons", "Thunder"),
        ("Gorillaz", "Feel Good Inc."),
    ],
    "no_me_gusta": [
        ("Slayer", "Raining Blood"), ("Andrea Bocelli", "Con Te Partiro"), ("Morgan Wallen", "Thinkin Bout You"),
        ("Future", "Mask Off Remix"), ("21 Savage", "Ocean Drive"),
    ],
}

# Capítulo: secciones que aún son borrador (se quita la etiqueta sin tocar código).
SECCIONES_BORRADOR = {"05_seleccion.md", "06_vecinos.md", "08_regresion.md"}

# Presupuesto de artefactos (bytes)
PRESUPUESTO = {
    "catalogo.parquet": 10e6, "conteos.npz": 30e6, "etiquetas.npz": 5e6, "usos.npz": 5e6,
    "vocab.json": 1e6, "similares.parquet": 3e6, "eval_similares.json": 1e6,
}
PRESUPUESTO_TOTAL = 50e6
