"""
API Manager — Conector profesional con proveedores de datos externos.
Gestiona The Odds API y API-Football con sistema de fallback y caché.
"""

import os
import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ExternalAPIManager:
    def __init__(self):
        self.odds_api_key = os.getenv("THE_ODDS_API_KEY")
        self.football_api_key = os.getenv("FOOTBALL_API_KEY")
        self.odds_base_url = "https://api.the-odds-api.com/v4/sports"
        self.football_base_url = "https://v3.football.api-sports.io"

    def get_live_odds(self, sport: str = "soccer_spain_la_liga") -> List[Dict]:
        """
        Obtiene cuotas en tiempo real de The Odds API.
        """
        if not self.odds_api_key:
            logger.warning("THE_ODDS_API_KEY no configurada. Usando datos simulados.")
            return self._get_mock_odds()

        try:
            url = f"{self.odds_base_url}/{sport}/odds/"
            params = {
                "apiKey": self.odds_api_key,
                "regions": "eu",
                "markets": "h2h,totals",
                "oddsFormat": "decimal"
            }
            res = requests.get(url, params=params)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            logger.error(f"Error fetching odds: {e}")
            return self._get_mock_odds()

    def get_live_scores(self, league_id: int = 140) -> List[Dict]:
        """
        Obtiene marcadores en vivo de API-Football (140 = La Liga).
        """
        if not self.football_api_key:
            logger.warning("FOOTBALL_API_KEY no configurada. Usando datos simulados.")
            return self._get_mock_scores()

        try:
            url = f"{self.football_base_url}/fixtures"
            headers = {"x-apisports-key": self.football_api_key}
            params = {"live": "all", "league": league_id}
            res = requests.get(url, headers=headers, params=params)
            res.raise_for_status()
            return res.json().get("response", [])
        except Exception as e:
            logger.error(f"Error fetching live scores: {e}")
            return self._get_mock_scores()

    def _get_mock_odds(self) -> List[Dict]:
        return [{
            "home_team": "Real Madrid",
            "away_team": "Barcelona",
            "bookmakers": [{
                "key": "bet365",
                "markets": [{"key": "h2h", "outcomes": [
                    {"name": "Real Madrid", "price": 1.95},
                    {"name": "Draw", "price": 3.60},
                    {"name": "Barcelona", "price": 3.80}
                ]}]
            }]
        }]

    def _get_mock_scores(self) -> List[Dict]:
        return [{
            "fixture": {"status": {"elapsed": 65}},
            "teams": {"home": {"name": "Atletico Madrid"}, "away": {"name": "Sevilla"}},
            "goals": {"home": 1, "away": 0}
        }]
