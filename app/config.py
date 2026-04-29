"""
Configuración centralizada de KICKDEX.
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
    "E0": "Premier League",
    "E1": "Championship",
    "I1": "Serie A",
    "I2": "Serie B",
    "D1": "Bundesliga",
    "D2": "2. Bundesliga",
    "F1": "Ligue 1",
    "F2": "Ligue 2",
    "N1": "Eredivisie",
}

# Free-tier API-Football league ids. Used only when APIFOOTBALL_KEY is set.
APIFOOTBALL_LEAGUE_IDS = {
    "SP1": 140,  # La Liga
    "SP2": 141,  # Segunda Division
    "E0": 39,   # Premier League
    "E1": 40,   # Championship
    "I1": 135,  # Serie A
    "I2": 136,  # Serie B
    "D1": 78,   # Bundesliga
    "D2": 79,   # 2. Bundesliga
    "F1": 61,   # Ligue 1
    "F2": 62,   # Ligue 2
    "N1": 88,   # Eredivisie
}

# ── Parámetros de análisis ────────────────────────────────────────────────────
ROLLING_WINDOW_DEFAULT = 5       # Últimos N partidos para forma reciente
ROLLING_WINDOW_OPTIONS = [3, 5, 10]
MIN_MATCHES_FOR_STATS = 3        # Mínimo de partidos para mostrar métricas

# ── Descarga de datos ─────────────────────────────────────────────────────────
FOOTBALL_DATA_BASE_URL = "https://www.football-data.co.uk/mmz4281"
DATA_DIR = "DATOS"
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
    # Premier League
    "man city": "Man City",
    "manchester city": "Man City",
    "man united": "Man United",
    "manchester united": "Man United",
    "manchester utd": "Man United",
    "arsenal": "Arsenal",
    "liverpool": "Liverpool",
    "chelsea": "Chelsea",
    "tottenham": "Tottenham",
    "tottenham hotspur": "Tottenham",
    "leeds united": "Leeds",
    "newcastle united": "Newcastle",
    "nottingham forest": "Nott'm Forest",
    "west ham united": "West Ham",
    # Bundesliga
    "bayern munich": "Bayern Munich",
    "fc bayern": "Bayern Munich",
    "dortmund": "Dortmund",
    "borussia dortmund": "Dortmund",
    "leverkusen": "Leverkusen",
    "bayer leverkusen": "Leverkusen",
    "eintracht frankfurt": "Ein Frankfurt",
    "koln": "FC Koln",
    "fc koln": "FC Koln",
    "hamburger sv": "Hamburg",
    "gladbach": "M'gladbach",
    "borussia monchengladbach": "M'gladbach",
    "mainz 05": "Mainz",
    # Serie A
    "inter": "Inter",
    "inter milan": "Inter",
    "juventus": "Juventus",
    "ac milan": "Milan",
    "milan": "Milan",
    "napoli": "Napoli",
    "roma": "Roma",
    "hellas verona": "Verona",
    # Ligue 1
    "psg": "PSG",
    "paris sg": "PSG",
    "paris saint-germain": "PSG",
    "marseille": "Marseille",
    "lyon": "Lyon",
}

# ── Colores UI ────────────────────────────────────────────────────────────────
COLOR_VALUE_GREEN = "#2EE6A6"   # Turf
COLOR_VALUE_RED = "#FF5A6E"     # Red Card
COLOR_NEUTRAL = "#8A94AB"       # Concrete
COLOR_BG_CARD = "#0B0F1A"       # Midnight
COLOR_BG_APP = "#05070D"        # Pitch Black

# ── App identity ──────────────────────────────────────────────────────────────
APP_NAME = "KICKDEX"
APP_TAGLINE = "The football data terminal."

# ── Disclaimer ────────────────────────────────────────────────────────────────
DISCLAIMER = (
    "KICKDEX proporciona análisis histórico y modelos estadísticos informativos, "
    "no garantías de resultados futuros."
)
