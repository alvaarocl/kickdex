"""Verified club rosters for the active season.

Results feeds are intentionally not used as a roster source: at the start of a
season they only contain clubs that have already played.  These lists let the
UI expose every configured club while results, player and referee coverage are
reported independently.
"""

from __future__ import annotations

from app.config import CURRENT_SEASON_LABEL


ROSTER_VERIFIED_AT = "2026-08-24"

CURRENT_SEASON_ROSTERS: dict[str, dict[str, object]] = {
    "SP1": {
        "teams": [
            "Alaves", "Ath Madrid", "Athletic Club", "Barcelona", "Betis",
            "Celta", "Dep. A Coruna", "Elche", "Espanol", "Getafe",
            "Levante", "Malaga", "Osasuna", "Real Madrid", "Santander",
            "Sevilla", "Sociedad", "Valencia", "Vallecano", "Villarreal",
        ],
        "source": "https://www.laliga.com/en-US/laliga-easports/clubs",
    },
    "SP2": {
        "teams": [
            "Albacete", "Almeria", "Andorra", "Burgos", "Cadiz", "Castellon",
            "Celta B", "Ceuta", "Cordoba", "Eibar", "Eldense", "Girona",
            "Granada", "Las Palmas", "Leganes", "Mallorca", "Oviedo",
            "Sabadell", "Sociedad B", "Sp Gijon", "Tenerife", "Valladolid",
        ],
        "source": "https://www.laliga.com/en-US/laliga-hypermotion/clubs",
    },
    "E0": {
        "teams": [
            "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton",
            "Chelsea", "Coventry", "Crystal Palace", "Everton", "Fulham",
            "Hull", "Ipswich", "Leeds", "Liverpool", "Man City", "Man United",
            "Newcastle", "Nott'm Forest", "Sunderland", "Tottenham",
        ],
        "source": "https://www.premierleague.com/en/clubs",
    },
    "E1": {
        "teams": [
            "Birmingham", "Blackburn", "Bolton", "Bristol City", "Burnley",
            "Cardiff", "Charlton", "Derby", "Lincoln", "Middlesbrough",
            "Millwall", "Norwich", "Portsmouth", "Preston", "QPR",
            "Sheffield United", "Southampton", "Stoke", "Swansea", "Watford",
            "West Brom", "West Ham", "Wolves", "Wrexham",
        ],
        "source": "https://www.efl.com/competitions/championship/clubs",
    },
    "I1": {
        "teams": [
            "Atalanta", "Bologna", "Cagliari", "Como", "Fiorentina",
            "Frosinone", "Genoa", "Inter", "Juventus", "Lazio", "Lecce",
            "Milan", "Monza", "Napoli", "Parma", "Roma", "Sassuolo",
            "Torino", "Udinese", "Venezia",
        ],
        "source": "https://www.legaseriea.it/en/team",
    },
    "I2": {
        "teams": [
            "Arezzo", "Ascoli", "Avellino", "Benevento", "Carrarese",
            "Catanzaro", "Cesena", "Cremonese", "Empoli", "Juve Stabia",
            "Mantova", "Modena", "Padova", "Palermo", "Pisa", "Sampdoria",
            "Sudtirol", "Verona", "Vicenza", "Virtus Entella",
        ],
        "source": "https://www.legab.it/news/serie-bkt-2026-2027-curiosita-e-statistiche-delle-20-squadre",
    },
    "D1": {
        "teams": [
            "Augsburg", "Bayern Munich", "Dortmund", "Ein Frankfurt",
            "Elversberg", "FC Koln", "Freiburg", "Hamburg", "Hoffenheim",
            "Leverkusen", "Mainz", "M'gladbach", "Paderborn", "RB Leipzig",
            "Schalke 04", "Stuttgart", "Union Berlin", "Werder Bremen",
        ],
        "source": "https://www.bundesliga.com/en/bundesliga/clubs",
    },
    "D2": {
        "teams": [
            "Bielefeld", "Bochum", "Braunschweig", "Cottbus", "Darmstadt",
            "Dresden", "Greuther Furth", "Hannover", "Heidenheim", "Hertha",
            "Holstein Kiel", "Kaiserslautern", "Karlsruhe", "Magdeburg",
            "Nurnberg", "Osnabruck", "St Pauli", "Wolfsburg",
        ],
        "source": "https://www.bundesliga.com/en/2bundesliga/clubs",
    },
    "F1": {
        "teams": [
            "Angers", "Auxerre", "Brest", "Le Havre", "Le Mans", "Lens",
            "Lille", "Lorient", "Lyon", "Marseille", "Monaco", "Nice",
            "Paris FC", "PSG", "Rennes", "Strasbourg", "Toulouse", "Troyes",
        ],
        "source": "https://ligue1.com/fr/articles/l1_article_5293-les-dates-de-reprise-des-clubs-de-l1-2627",
    },
    "F2": {
        "teams": [
            "Annecy", "Boulogne", "Clermont", "Dijon", "Dunkerque", "Grenoble",
            "Guingamp", "Laval", "Metz", "Montpellier", "Nancy", "Nantes",
            "Pau FC", "Red Star", "Reims", "Rodez", "Sochaux", "St Etienne",
        ],
        "source": "https://ligue2.fr/fr/clubs",
    },
    "N1": {
        "teams": [
            "AZ Alkmaar", "Ajax", "Cambuur", "Den Haag", "Excelsior",
            "Feyenoord", "For Sittard", "Go Ahead Eagles", "Groningen",
            "Heerenveen", "Nijmegen", "PSV Eindhoven", "Sparta Rotterdam",
            "Telstar", "Twente", "Utrecht", "Willem II", "Zwolle",
        ],
        "source": "https://eredivisie.nl/meer/merk/logos-18-clubs/",
    },
}


def roster_for(league_code: str) -> dict[str, object] | None:
    roster = CURRENT_SEASON_ROSTERS.get(league_code)
    if not roster:
        return None
    return {
        **roster,
        "season": CURRENT_SEASON_LABEL,
        "verified_at": ROSTER_VERIFIED_AT,
    }


def all_roster_teams() -> list[str]:
    return sorted({
        team
        for roster in CURRENT_SEASON_ROSTERS.values()
        for team in roster["teams"]
    })
