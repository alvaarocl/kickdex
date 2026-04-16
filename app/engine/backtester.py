"""
Backtester Engine — El simulador de estrategias de KICKDEX.
Permite validar reglas de apuestas sobre el histórico real de datos.
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Callable

class BacktestResult:
    def __init__(self, trades: List[Dict]):
        self.trades = pd.DataFrame(trades)
        
    def get_summary(self) -> Dict[str, Any]:
        if self.trades.empty:
            return {}
            
        wins = self.trades[self.trades["profit"] > 0]
        losses = self.trades[self.trades["profit"] < 0]
        
        total_staked = len(self.trades)
        total_profit = self.trades["profit"].sum()
        
        return {
            "total_bets": len(self.trades),
            "win_rate": (len(wins) / len(self.trades)) * 100,
            "total_profit": total_profit,
            "yield_roi": (total_profit / total_staked) * 100,
            "max_drawdown": self._calculate_drawdown(),
            "avg_odds": self.trades["odds"].mean(),
            "equity_curve": self.trades["balance"].tolist()
        }
    
    def _calculate_drawdown(self) -> float:
        balance = self.trades["balance"]
        peak = balance.cummax()
        drawdown = (balance - peak)
        return float(drawdown.min())

class Backtester:
    def __init__(self, df: pd.DataFrame):
        # Aseguramos que los datos tengan métricas rolling para evitar leakage
        from app.engine.metrics import calculate_rolling_metrics
        self.df = calculate_rolling_metrics(df)
        self.initial_balance = 100.0

    def run_strategy(
        self, 
        market: str, # "1", "X", "2", "Over 2.5", "BTTS"
        min_metric_val: float,
        metric_col: str, # Ej: "Home_Roll_Goals"
        min_odds: float = 1.0,
        max_odds: float = 10.0
    ) -> BacktestResult:
        """
        Ejecuta una simulación: apuesta 1 unidad cada vez que se cumple la condición.
        Market mapping:
        - "1": Victoria Local (FTR == 'H', Odds: B365H)
        - "X": Empate (FTR == 'D', Odds: B365D)
        - "2": Victoria Visitante (FTR == 'A', Odds: B365A)
        """
        trades = []
        current_balance = self.initial_balance
        
        # Solo partidos con cuotas disponibles
        work_df = self.df.dropna(subset=["B365H", "B365D", "B365A", "FTR"])
        
        for _, row in work_df.iterrows():
            # 1. Verificar condición de la estrategia
            val = row.get(metric_col, 0)
            if val < min_metric_val:
                continue
            
            # 2. Determinar cuota y resultado según mercado
            odds = 0.0
            won = False
            
            if market == "1":
                odds = row["B365H"]
                won = row["FTR"] == "H"
            elif market == "X":
                odds = row["B365D"]
                won = row["FTR"] == "D"
            elif market == "2":
                odds = row["B365A"]
                won = row["FTR"] == "A"
            elif market == "Over 2.5":
                odds = row.get("B365>2.5", 1.85) # Fallback si no hay
                won = (row["FTHG"] + row["FTAG"]) > 2.5
            
            if odds < min_odds or odds > max_odds:
                continue
                
            # 3. Calcular profit (Stake plano de 1 unidad)
            profit = (odds - 1) if won else -1.0
            current_balance += profit
            
            trades.append({
                "date": row["Date"],
                "match": f"{row['HomeTeam']} vs {row['AwayTeam']}",
                "metric_val": val,
                "odds": odds,
                "won": won,
                "profit": profit,
                "balance": current_balance
            })
            
        return BacktestResult(trades)
