"""
Configuración centralizada de Analista Pro.
Un único lugar para cambiar temporadas, ligas y parámetros globales.
"""

# ── Temporada actual ──────────────────────────────────────────────────────────
CURRENT_SEASON_CODE = "2526"
CURRENT_SEASON_START = "2025-08-01"   # Cambiar cada año en pretemporada
CURRENT_SEASON_LABEL = "2025/26"

# ── Ligas cubiertas ───────────────────────────────────────────────────────────
LEAGUES = {
    "SP1": "La Liga",
    "SP2": "Segunda División",
}

# ── Parámetros de análisis ────────────────────────────────────────────────────
ROLLING_WINDOW_DEFAULT = 5       # Últimos N partidos para forma reciente
ROLLING_WINDOW_OPTIONS = [3, 5, 10]
MIN_MATCHES_FOR_STATS = 3        # Mínimo de partidos para mostrar métricas

# ── Value Detection ───────────────────────────────────────────────────────────
MIN_SAMPLE_VALUE = 30            # Partidos mínimos para considerar un patrón de valor
MIN_ACCURACY_VALUE = 0.60        # Acierto mínimo (60%) para mostrar como value
VALUE_EDGE_THRESHOLD = 0.03      # Diferencia mínima (3%) para marcar como verde

# ── Descarga de datos ─────────────────────────────────────────────────────────
FOOTBALL_DATA_BASE_URL = "https://www.football-data.co.uk/mmz4281"
DATA_DIR = "datos"               # lowercase, consistente en todos los módulos
SEASONS_RANGE = range(4, 27)     # 04/05 → 26/27

# ── Normalización de nombres de equipos ──────────────────────────────────────
# Mapea cualquier variación al nombre canónico usado en los CSVs de football-data
TEAM_ALIASES: dict[str, str] = {
    # La Liga
    "atletico madrid": "Ath Madrid",
    "atletico de madrid": "Ath Madrid",
    "atlético madrid": "Ath Madrid",
    "atletico": "Ath Madrid",
    "ath madrid": "Ath Madrid",
    "athletic bilbao": "Athletic Club",
    "ath bilbao": "Athletic Club",
    "athletic": "Athletic Club",
    "athletic club": "Athletic Club",
    "real betis": "Betis",
    "betis": "Betis",
    "rayo vallecano": "Vallecano",
    "rayo": "Vallecano",
    "vallecano": "Vallecano",
    "deportivo alaves": "Alaves",
    "alaves": "Alaves",
    "alavés": "Alaves",
    "celta vigo": "Celta",
    "celta": "Celta",
    "real valladolid": "Valladolid",
    "valladolid": "Valladolid",
    "las palmas": "Las Palmas",
    "ud las palmas": "Las Palmas",
    "leganes": "Leganes",
    "leganés": "Leganes",
    "cd leganes": "Leganes",
    "girona fc": "Girona",
    "girona": "Girona",
    "villarreal cf": "Villarreal",
    "villarreal": "Villarreal",
    "real sociedad": "Sociedad",
    "sociedad": "Sociedad",
    "cadiz": "Cadiz",
    "cádiz": "Cadiz",
    "cadiz cf": "Cadiz",
    "espanyol": "Espanol",
    "rcd espanyol": "Espanol",
    "espanol": "Espanol",
    "osasuna": "Osasuna",
    "ca osasuna": "Osasuna",
    "getafe cf": "Getafe",
    "getafe": "Getafe",
    "mallorca": "Mallorca",
    "rcd mallorca": "Mallorca",
    "real madrid": "Real Madrid",
    "barcelona": "Barcelona",
    "fc barcelona": "Barcelona",
    "sevilla fc": "Sevilla",
    "sevilla": "Sevilla",
    "valencia cf": "Valencia",
    "valencia": "Valencia",
    # Segunda División (mutuos comunes)
    "racing santander": "Racing Santander",
    "real zaragoza": "Zaragoza",
    "zaragoza": "Zaragoza",
    "sd eibar": "Eibar",
    "eibar": "Eibar",
    "sporting gijon": "Sp Gijon",
    "sp gijon": "Sp Gijon",
    "real oviedo": "Oviedo",
    "oviedo": "Oviedo",
    "huesca": "Huesca",
    "sd huesca": "Huesca",
    "real burgos": "Burgos",
    "burgos": "Burgos",
    "eldense": "Eldense",
    "mirandes": "Mirandes",
    "sd mirandes": "Mirandes",
}

# ── Colores UI ────────────────────────────────────────────────────────────────
COLOR_VALUE_GREEN = "#00d4aa"
COLOR_VALUE_RED = "#ff4b4b"
COLOR_NEUTRAL = "#8b9ab0"
COLOR_BG_CARD = "#1a1f2e"
COLOR_BG_APP = "#0e1117"

# ── Disclaimer ────────────────────────────────────────────────────────────────
DISCLAIMER = (
    "⚠️ Las apuestas conllevan riesgo. Juega responsablemente. "
    "Analista Pro proporciona análisis histórico, no garantías de resultados futuros. "
    "Si el juego te causa problemas, llama al 900 200 225 (gratuito, 24h)."
)
