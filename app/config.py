"""
Configuración centralizada de KICKDEX.
Un único lugar para cambiar temporadas, ligas y parámetros globales.
"""

# ── Temporada actual ──────────────────────────────────────────────────────────
CURRENT_SEASON_CODE = "2627"
CURRENT_SEASON_START = "2026-08-01"   # Cambiar cada año en pretemporada
CURRENT_SEASON_LABEL = "2026/27"
CURRENT_SEASON_YEAR = 2026

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

# Expected club count is used to label an early-season roster as partial. It
# does not block publication while a league feed is still being populated.
LEAGUE_TEAM_COUNTS = {
    "SP1": 20,
    "SP2": 22,
    "E0": 20,
    "E1": 24,
    "I1": 20,
    "I2": 20,
    "D1": 18,
    "D2": 18,
    "F1": 18,
    "F2": 18,
    "N1": 18,
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

# football-data.org (v4) competition codes — usados por update_live_scores.py
# para el marcador con retraso (plan gratuito: sin partidos en vivo, solo con
# retraso). Cubre 7 de las 11 ligas de KICKDEX; SP2/I2/D2/F2 quedan fuera
# porque el tier gratuito de football-data.org no las incluye.
FOOTBALL_DATA_ORG_COMPETITION_CODES = {
    "SP1": "PD",   # La Liga (Primera División)
    "E0": "PL",    # Premier League
    "E1": "ELC",   # Championship
    "I1": "SA",    # Serie A
    "D1": "BL1",   # Bundesliga
    "F1": "FL1",   # Ligue 1
    "N1": "DED",   # Eredivisie
}

# The Odds API (the-odds-api.com) sport keys — usados por scripts/update_odds.py
# para cuotas de partidos FUTUROS (Fase 4). Sin THE_ODDS_API_KEY el script
# escribe odds.json con enabled=false y el edge sigue siendo solo retrospectivo.
# Solo las 5 grandes de momento para no agotar el tier gratuito (500 req/mes):
# 5 ligas × 2 builds/día ≈ 300 req/mes. Ampliar a E1/N1 si se sube de plan.
THE_ODDS_API_SPORT_KEYS = {
    "SP1": "soccer_spain_la_liga",
    "E0":  "soccer_epl",
    "I1":  "soccer_italy_serie_a",
    "D1":  "soccer_germany_bundesliga",
    "F1":  "soccer_france_ligue_one",
}

# Public World Soccer Data paths for referee season aggregates.
# Used as a free fallback when per-match referee feeds are unavailable.
WORLDSOCCERDATA_REFEREE_PATHS = {
    "SP1": "spain/laliga",
    "SP2": "spain/la-liga2",
    "E0": "england/premier-league",
    "E1": "england/championship",
    "I1": "italy/seriea",
    "D1": "germany/bundesliga",
    "F1": "france/ligue-1",
    "N1": "netherlands/eredivisie",
}

# ── Parámetros de análisis ────────────────────────────────────────────────────
ROLLING_WINDOW_DEFAULT = 5       # Últimos N partidos para forma reciente
ROLLING_WINDOW_OPTIONS = [3, 5, 10]
MIN_MATCHES_FOR_STATS = 3        # Mínimo de partidos para mostrar métricas

# ── Forma ponderada por historial (get_weighted_form / get_weighted_h2h_summary) ──
# En vez de cortar a los últimos N partidos (arriba), estas funciones usan todo
# el historial disponible pero dan menos peso a los partidos más antiguos.
HALF_LIFE_DAYS = 270             # Un partido de hace ~9 meses pesa la mitad que uno de hoy
MAX_LOOKBACK_MATCHES = 60        # Tope de partidos por local/visitante (rendimiento; el peso ya los hace irrelevantes antes)

# ── Alias de árbitros (colisiones apellido+inicial que _referee_key no resuelve) ──
# Clave: nombre normalizado (NFKD sin diacríticos, minúsculas) tal como aparece
# en la fuente. Valor: la clave canónica a la que debe mapear en build_referees().
REFEREE_ALIASES: dict[str, str] = {}

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
    "atl. madrid": "Ath Madrid",
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
    "rcd espanyol de barcelona": "Espanol",
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
    "malaga cf": "Malaga",
    "malaga": "Malaga",
    "málaga cf": "Malaga",
    "málaga": "Malaga",
    "deportivo la coruna": "Dep. A Coruna",
    "deportivo de la coruna": "Dep. A Coruna",
    "dep. a coruna": "Dep. A Coruna",
    "la coruna": "Dep. A Coruna",
    "rc deportivo": "Dep. A Coruna",
    "r. racing club": "Santander",
    "racing club": "Santander",
    # Segunda División (mutuos comunes)
    "racing santander": "Santander",
    "santander": "Santander",
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

# ── Nombres de equipo football-data.org -> canonico KICKDEX ──────────────────
# football-data.org devuelve nombres legales/formales ("Real Madrid CF",
# "FC Internazionale Milano") en vez de los nombres cortos de
# football-data.co.uk que usa el resto del motor (TEAM_ALIASES arriba esta
# pensado al reves: de variantes coloquiales -> nombre corto). Un fuzzy-match
# generico falla aqui de forma peligrosa por colisiones de substring: p.ej.
# "RCD Espanyol de Barcelona" -> "Barcelona" (termina en "de Barcelona"),
# "FC Internazionale Milano" -> "Milan" (contiene "milan" dentro de
# "milano"), "Stade Rennais FC 1901"/"Paris Saint-Germain FC" -> "Paris FC"
# (los tres comparten "paris"/fragmentos), o "NEC" -> "Twente" (cadenas muy
# cortas, ratio de SequenceMatcher no fiable). Mapa fijo, verificado a mano
# contra docs/data/team_assets.json, para las 7 ligas cubiertas por el tier
# gratuito (ver FOOTBALL_DATA_ORG_COMPETITION_CODES).
FOOTBALL_DATA_ORG_TEAM_ALIASES: dict[str, str] = {
    # La Liga
    "Club Atlético de Madrid": "Ath Madrid",
    "Athletic Club": "Athletic Club",
    "CA Osasuna": "Osasuna",
    "RCD Espanyol de Barcelona": "Espanol",
    "FC Barcelona": "Barcelona",
    "Getafe CF": "Getafe",
    "Málaga CF": "Malaga",
    "Real Madrid CF": "Real Madrid",
    "Rayo Vallecano de Madrid": "Vallecano",
    "Levante UD": "Levante",
    "Real Betis Balompié": "Betis",
    "Real Sociedad de Fútbol": "Sociedad",
    "Villarreal CF": "Villarreal",
    "Valencia CF": "Valencia",
    "Deportivo Alavés": "Alaves",
    "Elche CF": "Elche",
    "RC Celta de Vigo": "Celta",
    "Sevilla FC": "Sevilla",
    "RC Deportivo La Coruña": "Dep. A Coruna",
    "Real Racing Club de Santander": "Santander",
    # Premier League
    "Arsenal FC": "Arsenal",
    "Aston Villa FC": "Aston Villa",
    "Chelsea FC": "Chelsea",
    "Everton FC": "Everton",
    "Fulham FC": "Fulham",
    "Liverpool FC": "Liverpool",
    "Manchester City FC": "Man City",
    "Manchester United FC": "Man United",
    "Newcastle United FC": "Newcastle",
    "Sunderland AFC": "Sunderland",
    "Tottenham Hotspur FC": "Tottenham",
    "Hull City AFC": "Hull",
    "Leeds United FC": "Leeds",
    "Ipswich Town FC": "Ipswich",
    "Nottingham Forest FC": "Nott'm Forest",
    "Crystal Palace FC": "Crystal Palace",
    "Brighton & Hove Albion FC": "Brighton",
    "Brentford FC": "Brentford",
    "AFC Bournemouth": "Bournemouth",
    "Coventry City FC": "Coventry",
    # Championship
    "Blackburn Rovers FC": "Blackburn",
    "Bolton Wanderers FC": "Bolton",
    "Norwich City FC": "Norwich",
    "Queens Park Rangers FC": "QPR",
    "Stoke City FC": "Stoke",
    "Swansea City AFC": "Swansea",
    "West Bromwich Albion FC": "West Brom",
    "Wolverhampton Wanderers FC": "Wolves",
    "Portsmouth FC": "Portsmouth",
    "Burnley FC": "Burnley",
    "Birmingham City FC": "Birmingham",
    "Southampton FC": "Southampton",
    "Derby County FC": "Derby",
    "Middlesbrough FC": "Middlesbrough",
    "Watford FC": "Watford",
    "Charlton Athletic FC": "Charlton",
    "Sheffield United FC": "Sheffield United",
    "Millwall FC": "Millwall",
    "Bristol City FC": "Bristol City",
    "Wrexham AFC": "Wrexham",
    "West Ham United FC": "West Ham",
    "Cardiff City FC": "Cardiff",
    "Preston North End FC": "Preston",
    "Lincoln City FC": "Lincoln",
    # Serie A
    "AC Milan": "Milan",
    "ACF Fiorentina": "Fiorentina",
    "AS Roma": "Roma",
    "Atalanta BC": "Atalanta",
    "Bologna FC 1909": "Bologna",
    "Cagliari Calcio": "Cagliari",
    "Genoa CFC": "Genoa",
    "FC Internazionale Milano": "Inter",
    "Juventus FC": "Juventus",
    "SS Lazio": "Lazio",
    "Parma Calcio 1913": "Parma",
    "SSC Napoli": "Napoli",
    "Udinese Calcio": "Udinese",
    "Venezia FC": "Venezia",
    "Frosinone Calcio": "Frosinone",
    "US Sassuolo Calcio": "Sassuolo",
    "Torino FC": "Torino",
    "US Lecce": "Lecce",
    "AC Monza": "Monza",
    "Como 1907": "Como",
    # Bundesliga
    "1. FC Köln": "FC Koln",
    "TSG 1899 Hoffenheim": "Hoffenheim",
    "Bayer 04 Leverkusen": "Leverkusen",
    "Borussia Dortmund": "Dortmund",
    "FC Bayern München": "Bayern Munich",
    "FC Schalke 04": "Schalke 04",
    "Hamburger SV": "Hamburg",
    "VfB Stuttgart": "Stuttgart",
    "SV Werder Bremen": "Werder Bremen",
    "1. FSV Mainz 05": "Mainz",
    "FC Augsburg": "Augsburg",
    "SC Freiburg": "Freiburg",
    "Borussia Mönchengladbach": "M'gladbach",
    "Eintracht Frankfurt": "Ein Frankfurt",
    "1. FC Union Berlin": "Union Berlin",
    "SC Paderborn 07": "Paderborn",
    "SV 07 Elversberg": "Elversberg",
    "RB Leipzig": "RB Leipzig",
    # Ligue 1
    "Toulouse FC": "Toulouse",
    "Stade Brestois 29": "Brest",
    "Olympique de Marseille": "Marseille",
    "AJ Auxerre": "Auxerre",
    "Lille OSC": "Lille",
    "OGC Nice": "Nice",
    "Olympique Lyonnais": "Lyon",
    "Paris Saint-Germain FC": "PSG",
    "FC Lorient": "Lorient",
    "Stade Rennais FC 1901": "Rennes",
    "ES Troyes AC": "Troyes",
    "Angers SCO": "Angers",
    "Le Havre AC": "Le Havre",
    "Le Mans FC": "Le Mans",
    "Racing Club de Lens": "Lens",
    "AS Monaco FC": "Monaco",
    "RC Strasbourg Alsace": "Strasbourg",
    "Paris FC": "Paris FC",
    # Eredivisie
    "FC Twente '65": "Twente",
    "SBV Excelsior": "Excelsior",
    "Willem II Tilburg": "Willem II",
    "SC Heerenveen": "Heerenveen",
    "PSV": "PSV Eindhoven",
    "Feyenoord Rotterdam": "Feyenoord",
    "FC Utrecht": "Utrecht",
    "FC Groningen": "Groningen",
    "AFC Ajax": "Ajax",
    "ADO Den Haag": "Den Haag",
    "AZ": "AZ Alkmaar",
    "PEC Zwolle": "Zwolle",
    "Go Ahead Eagles": "Go Ahead Eagles",
    "SC Cambuur-Leeuwarden": "Cambuur",
    "Telstar 1963": "Telstar",
    "NEC": "Nijmegen",
    "Fortuna Sittard": "For Sittard",
    "Sparta Rotterdam": "Sparta Rotterdam",
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
