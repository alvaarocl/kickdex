"""
Motor de detección de value bets.
Compara la probabilidad matemática calculada por el motor interno
con la probabilidad implícita de las cuotas de Bet365.
Solo usa cuotas reales de los CSVs — nunca cuotas simuladas.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.config import MIN_SAMPLE_VALUE, MIN_ACCURACY_VALUE, VALUE_EDGE_THRESHOLD
from app.engine.probability import MatchProbabilities

logger = logging.getLogger(__name__)


@dataclass
class ValueResult:
    market: str          # "1X2 Local", "Over 2.5", etc.
    our_prob: float      # Probabilidad interna (motor)
    implied_prob: float  # Probabilidad implícita de la cuota
    odds: float          # Cuota de la casa
    edge: float          # Ventaja: our_prob - implied_prob
    is_value: bool       # True si edge > VALUE_EDGE_THRESHOLD
    label: str           # "VALUE ✓", "Precio Justo", "Sobrevalorado"

    @property
    def ev(self) -> float:
        """Expected Value: (prob * cuota) - 1."""
        return round(self.our_prob * self.odds - 1, 4)

    @property
    def kelly(self) -> float:
        """
        Cálculo del Criterio de Kelly (Stake sugerido).
        f* = (Prob * Cuota - 1) / (Cuota - 1)
        Aplicamos un Kelly fraccional del 25% para mayor seguridad.
        """
        if self.odds <= 1.0 or not self.is_value or self.our_prob <= 0:
            return 0.0
        
        b = self.odds - 1
        f_star = (self.our_prob * self.odds - 1) / b
        
        # Kelly fraccional (0.25) para reducir volatilidad
        fractional_kelly = f_star * 0.25
        
        # Limitar a un máximo del 5% del bankroll por apuesta para seguridad
        return round(min(max(0, fractional_kelly), 0.05), 4)

    @property
    def color(self) -> str:
        if self.is_value:
            return "#00d4aa"
        if self.edge < -0.05:
            return "#ff4b4b"
        return "#8b9ab0"


def _implied(odds: float) -> float:
    """Probabilidad implícita de una cuota (sin ajuste de margen)."""
    if odds <= 1.0:
        return 0.99
    return round(1 / odds, 4)


def calculate_value(
    probs: MatchProbabilities,
    b365h: float | None,
    b365d: float | None,
    b365a: float | None,
    b365_over25: float | None = None,
) -> list[ValueResult]:
    """
    Calcula el value para cada mercado disponible.

    Args:
        probs: Probabilidades calculadas por el motor.
        b365h: Cuota Bet365 victoria local (o None si no disponible).
        b365d: Cuota Bet365 empate.
        b365a: Cuota Bet365 victoria visitante.
        b365_over25: Cuota Bet365 Over 2.5 goles.

    Returns:
        Lista de ValueResult para cada mercado con cuota disponible.
    """
    results = []

    def _make(market: str, our_prob: float, odds: float | None) -> None:
        if odds is None or not np.isfinite(odds) or odds < 1.01 or odds > 50:
            return
        implied = _implied(odds)
        edge = round(our_prob - implied, 4)
        is_value = edge >= VALUE_EDGE_THRESHOLD
        label = "🟢 VALUE" if is_value else ("🔴 Caro" if edge < -0.05 else "⚪ Justo")
        results.append(ValueResult(
            market=market,
            our_prob=our_prob,
            implied_prob=implied,
            odds=odds,
            edge=edge,
            is_value=is_value,
            label=label,
        ))

    _make("1X2 — Local", probs.home, b365h)
    _make("1X2 — Empate", probs.draw, b365d)
    _make("1X2 — Visitante", probs.away, b365a)
    if b365_over25 is not None:
        _make("Over 2.5 Goles", probs.over25, b365_over25)

    # Ordenar: value primero, luego por edge desc
    results.sort(key=lambda r: (r.is_value, r.edge), reverse=True)
    return results


# ─── Scanner histórico de patrones de valor ──────────────────────────────────

def scan_value_patterns(
    df: pd.DataFrame,
    min_sample: int = MIN_SAMPLE_VALUE,
    min_accuracy: float = MIN_ACCURACY_VALUE,
) -> pd.DataFrame:
    """
    Busca automáticamente patrones históricos con valor esperado positivo.
    Solo funciona con partidos que tengan cuotas reales de Bet365.

    Args:
        df: DataFrame procesado con rolling metrics y columnas B365.
        min_sample: Tamaño mínimo de muestra.
        min_accuracy: Probabilidad real mínima para considerar el patrón.

    Returns:
        DataFrame de oportunidades ordenadas por EV descendente.
    """
    # Filtrar solo partidos con cuotas reales
    required = ["FTHG", "FTAG", "FTR", "B365H", "B365D", "B365A"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        logger.warning("Columnas faltantes para value scan: %s", missing)
        return pd.DataFrame()

    working = df.dropna(subset=["FTHG", "FTAG", "B365H", "B365D", "B365A"]).copy()

    # Asegurar que las cuotas sean numéricas y válidas
    for col in ["B365H", "B365D", "B365A"]:
        working[col] = pd.to_numeric(working[col], errors="coerce")
    working = working[
        (working["B365H"] >= 1.01) & (working["B365H"] <= 50) &
        (working["B365D"] >= 1.01) & (working["B365D"] <= 50) &
        (working["B365A"] >= 1.01) & (working["B365A"] <= 50)
    ]

    if len(working) < min_sample:
        logger.info("Muestra insuficiente para value scan (%d partidos)", len(working))
        return pd.DataFrame()

    metric_thresholds = {
        "Home_Roll_Goals":   [0.5, 1.0, 1.5, 2.0, 2.5],
        "Home_Roll_Shots":   [8, 10, 12, 14],
        "Home_Roll_ShoT":    [3, 4, 5, 6],
        "Away_Roll_Goals":   [0.5, 1.0, 1.5, 2.0],
        "Away_Roll_Shots":   [8, 10, 12],
        "Away_Roll_ShoT":    [3, 4, 5],
    }

    events = [
        {"name": "Victoria Local",     "cond": lambda d: d["FTR"] == "H",                          "odds": "B365H"},
        {"name": "Empate",             "cond": lambda d: d["FTR"] == "D",                          "odds": "B365D"},
        {"name": "Victoria Visitante", "cond": lambda d: d["FTR"] == "A",                          "odds": "B365A"},
        {"name": "Más de 2.5 goles",   "cond": lambda d: (d["FTHG"] + d["FTAG"]) > 2.5,           "odds": "B365H"},
        {"name": "Ambos marcan",       "cond": lambda d: (d["FTHG"] > 0) & (d["FTAG"] > 0),        "odds": "B365H"},
    ]
    # Para Over 2.5 y BTTS usamos B365>2.5 si existe
    if "B365>2.5" in working.columns:
        events[3]["odds"] = "B365>2.5"
        events[4]["odds"] = "B365>2.5"

    opportunities = []

    for metric_col, thresholds in metric_thresholds.items():
        if metric_col not in working.columns:
            continue
        for threshold in thresholds:
            filtered = working[working[metric_col] >= threshold].copy()
            if len(filtered) < min_sample:
                continue
            for event in events:
                odds_col = event["odds"]
                if odds_col not in filtered.columns:
                    continue
                try:
                    occurred = event["cond"](filtered)
                    n_matches = len(filtered)
                    n_success = int(occurred.sum())
                    if n_matches < min_sample:
                        continue
                    real_prob = n_success / n_matches
                    if real_prob < min_accuracy:
                        continue
                    valid_odds = pd.to_numeric(filtered[odds_col], errors="coerce").dropna()
                    valid_odds = valid_odds[(valid_odds >= 1.01) & (valid_odds <= 50)]
                    if len(valid_odds) == 0:
                        continue
                    avg_odds = float(valid_odds.mean())
                    ev = (real_prob * avg_odds) - 1
                    if ev <= 0:
                        continue
                    opportunities.append({
                        "Condición": f"{metric_col} ≥ {threshold}",
                        "Evento": event["name"],
                        "Partidos (n)": n_matches,
                        "Aciertos": n_success,
                        "Prob. Real": f"{real_prob*100:.1f}%",
                        "Cuota Media": round(avg_odds, 2),
                        "EV": round(ev, 4),
                        "EV %": f"+{ev*100:.1f}%",
                        "_ev_raw": ev,
                    })
                except Exception as e:
                    logger.debug("Error en patrón %s/%s: %s", metric_col, event["name"], e)
                    continue

    if not opportunities:
        return pd.DataFrame()

    result = pd.DataFrame(opportunities)
    result = result.sort_values("_ev_raw", ascending=False).drop(columns=["_ev_raw"])
    return result.reset_index(drop=True)
