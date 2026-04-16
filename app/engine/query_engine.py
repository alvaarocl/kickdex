"""
Query Engine — El motor de cálculo dinámico de KICKDEX.
Permite realizar consultas complejas sobre equipos y jugadores con múltiples filtros.
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional

class QueryEngine:
    def __init__(self, df_matches: pd.DataFrame, df_players: pd.DataFrame):
        self.df = df_matches
        self.df_p = df_players

    def get_team_stats(
        self, 
        team: str, 
        venue: str = "All", 
        last_n: Optional[int] = None,
        league: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calcula estadísticas profundas para un equipo bajo ciertas condiciones."""
        df = self.df.copy()
        
        if league:
            df = df[df["Div"] == league]
            
        if venue == "Home":
            m = df[df["HomeTeam"] == team]
            prefix = "H"
        elif venue == "Away":
            m = df[df["AwayTeam"] == team]
            prefix = "A"
        else:
            m = df[(df["HomeTeam"] == team) | (df["AwayTeam"] == team)]
            prefix = "Both"

        if m.empty:
            return {}

        if last_n:
            m = m.sort_values("Date").tail(last_n)

        # Helper para extraer métricas según el lado
        def _get_metric(row, metric_base):
            is_home = row["HomeTeam"] == team
            col = f"H{metric_base}" if is_home else f"A{metric_base}"
            return row.get(col, 0)

        # Diccionario de resultados
        results = {
            "n_matches": len(m),
            "avg_goals_scored": 0.0,
            "avg_goals_conceded": 0.0,
            "avg_corners": 0.0,
            "avg_shots": 0.0,
            "avg_sot": 0.0,
            "avg_cards": 0.0,
            "btts_pct": 0.0,
            "over25_pct": 0.0,
            "clean_sheet_pct": 0.0,
            "win_pct": 0.0
        }

        scored = []
        conceded = []
        corners = []
        shots = []
        sot = []
        cards = []
        wins = 0
        btts = 0
        o25 = 0
        cs = 0

        for _, r in m.iterrows():
            is_home = r["HomeTeam"] == team
            gs = r["FTHG"] if is_home else r["FTAG"]
            gc = r["FTAG"] if is_home else r["FTHG"]
            res = r["FTR"]
            
            scored.append(gs)
            conceded.append(gc)
            corners.append(r["HC"] if is_home else r["AC"])
            shots.append(r["HS"] if is_home else r["AS"])
            sot.append(r["HST"] if is_home else r["AST"])
            cards.append((r["HY"] or 0) + (r["HR"] or 0) if is_home else (r["AY"] or 0) + (r["AR"] or 0))
            
            if (is_home and res == "H") or (not is_home and res == "A"):
                wins += 1
            if gs > 0 and gc > 0:
                btts += 1
            if gs + gc > 2.5:
                o25 += 1
            if gc == 0:
                cs += 1

        results.update({
            "avg_goals_scored": np.mean(scored),
            "std_goals_scored": np.std(scored), # Volatilidad
            "avg_goals_conceded": np.mean(conceded),
            "std_goals_conceded": np.std(conceded),
            "avg_corners": np.mean(corners),
            "std_corners": np.std(corners),
            "avg_shots": np.mean(shots),
            "avg_sot": np.mean(sot),
            "avg_cards": np.mean(cards),
            "win_pct": (wins / len(m)) * 100,
            "btts_pct": (btts / len(m)) * 100,
            "over25_pct": (o25 / len(m)) * 100,
            "clean_sheet_pct": (cs / len(m)) * 100,
            # Data raw para histogramas
            "raw_corners": corners,
            "raw_goals_scored": scored
        })

        return results

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
