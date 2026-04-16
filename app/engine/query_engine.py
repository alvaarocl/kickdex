"""
Query Engine — El motor de cálculo dinámico de KICKDEX.
Permite realizar consultas complejas sobre equipos y jugadores con múltiples filtros.
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
from app.data.models import Team, Match, PlayerStat
from sqlalchemy import or_, func

class QueryEngine:
    def __init__(self, db: Session):
        self.db = db

    def get_team_stats(self, team_name: str, venue: str = "All", last_n: int = 10):
        """Consulta estadísticas de equipo directamente desde SQL."""
        team = self.db.query(Team).filter(Team.name == team_name).first()
        if not team: return {}

        query = self.db.query(Match).filter(
            or_(Match.home_team_id == team.id, Match.away_team_id == team.id)
        )
        
        if venue == "Home":
            query = query.filter(Match.home_team_id == team.id)
        elif venue == "Away":
            query = query.filter(Match.away_team_id == team.id)

        matches = query.order_by(Match.date.desc()).limit(last_n).all()
        if not matches: return {}

        # Cálculos SQL-style
        scored = [m.fthg if m.home_team_id == team.id else m.ftag for m in matches]
        conceded = [m.ftag if m.home_team_id == team.id else m.fthg for m in matches]
        corners = [m.hc if m.home_team_id == team.id else m.ac for m in matches]
        
        return {
            "n_matches": len(matches),
            "avg_goals_scored": sum(scored) / len(scored),
            "avg_goals_conceded": sum(conceded) / len(conceded),
            "avg_corners": sum(corners) / len(corners),
            "raw_corners": corners,
            "win_pct": (sum(1 for m in matches if (m.ftr == 'H' and m.home_team_id == team.id) or (m.ftr == 'A' and m.away_team_id == team.id)) / len(matches)) * 100
        }

    def get_player_stats(self, player: str, last_n: Optional[int] = None) -> Dict[str, Any]:
        """Calcula estadísticas profundas para un jugador."""
        df = self.df_p[self.df_p["player"] == player].copy()
        if df.empty:
            return {}
        
        if last_n:
            df = df.sort_values("date").tail(last_n)
            
        return {
            "n_matches": len(df),
            "avg_goals": df["gls"].mean(),
            "avg_assists": df["ast"].mean(),
            "avg_shots": df["sh"].mean(),
            "avg_sot": df["sot"].mean(),
            "avg_cards": df["crdy"].mean(),
            "avg_fouls": df["fls"].mean(),
            "total_goals": df["gls"].sum(),
            "total_assists": df["ast"].sum()
        }
