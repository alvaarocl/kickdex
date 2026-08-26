/**
 * Canonical -> display name overrides for team labels shown in the UI.
 *
 * Team records everywhere else in the app (URLs, dataset keys, crest/player
 * asset manifests, dropdown values, CSV joins) keep using the short
 * football-data.co.uk-style canonical name (e.g. "Sociedad", "Ath Madrid").
 * That name must never change - renaming it would break every join across
 * the static JSON files. This map only swaps the TEXT shown to users for
 * the small set of canonical names that read as abbreviations, misspellings
 * or incomplete club names (e.g. "Sociedad" -> "Real Sociedad").
 * Teams not listed here already display fine using their canonical name.
 */
"use strict";

window.TEAM_DISPLAY_NAMES = {
  // España - La Liga / Segunda
  "Ath Madrid": "Atlético de Madrid",
  "Betis": "Real Betis",
  "Vallecano": "Rayo Vallecano",
  "Alaves": "Deportivo Alavés",
  "Celta": "Celta de Vigo",
  "Celta B": "Celta de Vigo B",
  "Valladolid": "Real Valladolid",
  "Las Palmas": "UD Las Palmas",
  "Leganes": "CD Leganés",
  "Girona": "Girona FC",
  "Villarreal": "Villarreal CF",
  "Sociedad": "Real Sociedad",
  "Sociedad B": "Real Sociedad B",
  "Cadiz": "Cádiz CF",
  "Espanol": "RCD Espanyol",
  "Osasuna": "CA Osasuna",
  "Getafe": "Getafe CF",
  "Mallorca": "RCD Mallorca",
  "Barcelona": "FC Barcelona",
  "Sevilla": "Sevilla FC",
  "Valencia": "Valencia CF",
  "Malaga": "Málaga CF",
  "Dep. A Coruna": "Deportivo de La Coruña",
  "Santander": "Racing de Santander",
  "Eibar": "SD Eibar",
  "Sp Gijon": "Sporting de Gijón",
  "Oviedo": "Real Oviedo",
  "Burgos": "Burgos CF",
  "Eldense": "CD Eldense",
  "Castellon": "CD Castellón",
  "Cordoba": "Córdoba CF",
  "Ceuta": "AD Ceuta FC",
  "Albacete": "Albacete Balompié",
  "Almeria": "UD Almería",
  "Elche": "Elche CF",
  "Andorra": "FC Andorra",
  "Sabadell": "CE Sabadell FC",
  "Tenerife": "CD Tenerife",
  "Granada": "Granada CF",
  "Levante": "Levante UD",

  // Inglaterra - Premier League / Championship
  "Man City": "Manchester City",
  "Man United": "Manchester United",
  "Nott'm Forest": "Nottingham Forest",
  "West Ham": "West Ham United",
  "West Brom": "West Bromwich Albion",
  "QPR": "Queens Park Rangers",
  "Leeds": "Leeds United",
  "Newcastle": "Newcastle United",
  "Wolves": "Wolverhampton Wanderers",
  "Tottenham": "Tottenham Hotspur",
  "Brighton": "Brighton & Hove Albion",
  "Stoke": "Stoke City",
  "Hull": "Hull City",
  "Cardiff": "Cardiff City",
  "Derby": "Derby County",
  "Birmingham": "Birmingham City",
  "Blackburn": "Blackburn Rovers",
  "Bolton": "Bolton Wanderers",
  "Coventry": "Coventry City",
  "Preston": "Preston North End",
  "Charlton": "Charlton Athletic",
  "Norwich": "Norwich City",
  "Swansea": "Swansea City",
  "Bournemouth": "AFC Bournemouth",
  "Ipswich": "Ipswich Town",
  "Lincoln": "Lincoln City",

  // Alemania - Bundesliga / 2. Bundesliga
  "Dortmund": "Borussia Dortmund",
  "Leverkusen": "Bayer Leverkusen",
  "Ein Frankfurt": "Eintracht Frankfurt",
  "FC Koln": "1. FC Köln",
  "Hamburg": "Hamburger SV",
  "M'gladbach": "Borussia Mönchengladbach",
  "Mainz": "Mainz 05",
  "St Pauli": "FC St. Pauli",
  "Stuttgart": "VfB Stuttgart",
  "Union Berlin": "1. FC Union Berlin",
  "Wolfsburg": "VfL Wolfsburg",
  "Freiburg": "SC Freiburg",
  "Augsburg": "FC Augsburg",
  "Hoffenheim": "TSG Hoffenheim",
  "Heidenheim": "1. FC Heidenheim",
  "Hertha": "Hertha BSC",
  "Bielefeld": "Arminia Bielefeld",
  "Bochum": "VfL Bochum",
  "Braunschweig": "Eintracht Braunschweig",
  "Cottbus": "Energie Cottbus",
  "Darmstadt": "SV Darmstadt 98",
  "Dresden": "Dynamo Dresden",
  "Elversberg": "SV Elversberg",
  "Greuther Furth": "SpVgg Greuther Fürth",
  "Hannover": "Hannover 96",
  "Kaiserslautern": "1. FC Kaiserslautern",
  "Karlsruhe": "Karlsruher SC",
  "Magdeburg": "1. FC Magdeburg",
  "Nurnberg": "1. FC Nürnberg",
  "Osnabruck": "VfL Osnabrück",
  "Paderborn": "SC Paderborn 07",

  // Italia - Serie A / B / C
  "Milan": "AC Milan",
  "Roma": "AS Roma",
  "Lazio": "SS Lazio",
  "Verona": "Hellas Verona",
  "Sudtirol": "FC Südtirol",
  "Avellino": "US Avellino",
  "Arezzo": "SS Arezzo",
  "Ascoli": "Ascoli Calcio",
  "Benevento": "Benevento Calcio",
  "Carrarese": "Carrarese Calcio",
  "Catanzaro": "US Catanzaro",
  "Cesena": "Cesena FC",
  "Cremonese": "US Cremonese",
  "Frosinone": "Frosinone Calcio",
  "Mantova": "Mantova 1911",
  "Modena": "Modena FC",
  "Padova": "Calcio Padova",
  "Palermo": "Palermo FC",
  "Pisa": "Pisa SC",
  "Sampdoria": "UC Sampdoria",
  "Sassuolo": "US Sassuolo",
  "Venezia": "Venezia FC",
  "Vicenza": "LR Vicenza",
  "Como": "Como 1907",
  "Cagliari": "Cagliari Calcio",
  "Empoli": "Empoli FC",
  "Genoa": "Genoa CFC",
  "Torino": "Torino FC",
  "Udinese": "Udinese Calcio",
  "Fiorentina": "ACF Fiorentina",
  "Bologna": "Bologna FC 1909",
  "Atalanta": "Atalanta BC",
  "Lecce": "US Lecce",
  "Monza": "AC Monza",
  "Parma": "Parma Calcio 1913",

  // Francia - Ligue 1 / Ligue 2
  "PSG": "Paris Saint-Germain",
  "Marseille": "Olympique de Marsella",
  "Lyon": "Olympique Lyonnais",
  "Lille": "LOSC Lille",
  "Lens": "RC Lens",
  "Rennes": "Stade Rennais",
  "Nice": "OGC Nice",
  "Nantes": "FC Nantes",
  "Monaco": "AS Monaco",
  "Montpellier": "Montpellier HSC",
  "Strasbourg": "RC Strasbourg",
  "Toulouse": "Toulouse FC",
  "Reims": "Stade de Reims",
  "Brest": "Stade Brestois",
  "Angers": "Angers SCO",
  "Auxerre": "AJ Auxerre",
  "Clermont": "Clermont Foot",
  "Metz": "FC Metz",
  "St Etienne": "AS Saint-Étienne",
  "Troyes": "ES Troyes AC",
  "Guingamp": "EA Guingamp",
  "Sochaux": "FC Sochaux-Montbéliard",
  "Nancy": "AS Nancy-Lorraine",
  "Dijon": "Dijon FCO",
  "Grenoble": "Grenoble Foot 38",
  "Le Mans": "Le Mans FC",
  "Laval": "Stade Lavallois",
  "Rodez": "Rodez AF",
  "Annecy": "FC Annecy",
  "Boulogne": "US Boulogne",
  "Dunkerque": "USL Dunkerque",
  "Red Star": "Red Star FC",

  // Países Bajos - Eredivisie / Eerste Divisie
  "Ajax": "AFC Ajax",
  "Twente": "FC Twente",
  "Utrecht": "FC Utrecht",
  "Groningen": "FC Groningen",
  "Heerenveen": "SC Heerenveen",
  "Zwolle": "PEC Zwolle",
  "Den Haag": "FC Den Haag",
  "Cambuur": "SC Cambuur",
  "Excelsior": "SBV Excelsior",
  "For Sittard": "Fortuna Sittard",
  "Nijmegen": "NEC Nijmegen",
  "Telstar": "SC Telstar",
};

/**
 * Returns the display label for a canonical team name. Falls back to the
 * canonical name itself when no override exists.
 */
function teamDisplayName(name) {
  if (!name) return name;
  return window.TEAM_DISPLAY_NAMES[name] || name;
}

const TEAM_SHORT_LABEL_GENERIC_WORDS = new Set([
  "real", "club", "deportivo", "cd", "ca", "ud", "rcd", "sd", "rc", "ac",
  "as", "sc", "fc", "cf", "afc", "ss", "us", "uc", "ssd", "1", "vfl", "vfb",
  "tsg", "sv", "ea", "og", "ogc", "aj", "fco", "de", "la", "los", "del",
]);

/**
 * Short, collision-safe label for tight-width UI slots (e.g. a comparator
 * column header). Strips generic club-type prefixes ("Real", "CA", "1. FC")
 * so "Real Sociedad" and "Real Madrid" don't both collapse to "Real".
 * Teams without a display-name override keep their already-short canonical
 * name untouched.
 */
function teamShortLabel(name) {
  if (!name) return name;
  const display = teamDisplayName(name);
  if (display === name) return name;
  const words = display.replace(/[.']/g, "").split(/\s+/).filter(Boolean);
  const distinctive = words.find(w => !TEAM_SHORT_LABEL_GENERIC_WORDS.has(w.toLowerCase()));
  return distinctive || words[words.length - 1] || display;
}
