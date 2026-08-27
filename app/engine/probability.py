"""
Motor de probabilidades matemáticas.
Calcula la probabilidad de cada resultado basándose en:
- Forma reciente de ambos equipos (últimos 5 partidos)
- Historial H2H
- Factor local/visitante global de La Liga
"""

from __future__ import annotations

import math
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Factor de ventaja local en La Liga (basado en histórico largo plazo)
_HOME_ADVANTAGE = 1.15   # El equipo local gana ~15% más de lo que marcaría sin ventaja
_LEAGUE_AVG_GOALS = 2.52  # Media de goles por partido en La Liga (histórico)
_DIXON_COLES_RHO = -0.12  # Ajuste por subestimación de marcadores bajos (0-0, 1-0, 0-1, 1-1)
_H2H_WEIGHT = 0.30
_H2H_MIN_TOTAL = 5
_OVER25_WEIGHTS = (0.4, 0.25, 0.25, 0.10)  # base_poisson, home_rate, away_rate, h2h_rate
_BTTS_WEIGHTS = (0.35, 0.35, 0.30)          # home_rate, away_rate, h2h_rate

# Estas mismas constantes se publican en docs/data/model_config.json (ver
# build_model_config() en scripts/build_data.py) para que el modelo
# equivalente en JavaScript (docs/js/app.js calcProbabilities) no diverja.


@dataclass
class MatchProbabilities:
    home: float    # P(victoria local)
    draw: float    # P(empate)
    away: float    # P(victoria visitante)
    over25: float  # P(más de 2.5 goles)
    btts: float    # P(ambos marcan)

    def as_dict(self) -> dict:
        return {
            "home": self.home,
            "draw": self.draw,
            "away": self.away,
            "over25": self.over25,
            "btts": self.btts,
        }

def _poisson_prob(lam: float, k: int) -> float:
    """P(X = k) para distribución de Poisson con parámetro lam."""
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def _dixon_coles_adjustment(hg: int, ag: int, lam_h: float, lam_a: float, rho: float = -0.10) -> float:
    """
    Ajuste de Dixon-Coles para corregir la subestimación de empates (0-0, 1-1) 
    y resultados 1-0, 0-1. Rho suele estar entre -0.1 y -0.2.
    """
    if rho == 0: return 1.0
    if hg == 0 and ag == 0:
        return 1 - (lam_h * lam_a * rho)
    if hg == 1 and ag == 0:
        return 1 + (lam_a * rho)
    if hg == 0 and ag == 1:
        return 1 + (lam_h * rho)
    if hg == 1 and ag == 1:
        return 1 - rho
    return 1.0


def _poisson_matrix(lam_home: float, lam_away: float, max_goals: int = 8) -> tuple[float, float, float]:
    """
    Calcula matriz de probabilidades con ajuste Dixon-Coles.
    """
    p_home = p_draw = p_away = 0.0

    for hg in range(max_goals + 1):
        p_h = _poisson_prob(lam_home, hg)
        for ag in range(max_goals + 1):
            p_a = _poisson_prob(lam_away, ag)
            prob = p_h * p_a * _dixon_coles_adjustment(hg, ag, lam_home, lam_away, _DIXON_COLES_RHO)
            
            if hg > ag:
                p_home += prob
            elif hg == ag:
                p_draw += prob
            else:
                p_away += prob
    
    total = p_home + p_draw + p_away
    return p_home / total, p_draw / total, p_away / total


def _estimate_lambda(
    team_avg_goals: float,
    opp_avg_conceded: float,
    league_avg: float = _LEAGUE_AVG_GOALS / 2,
    advantage_factor: float = 1.0,
) -> float:
    """
    Estima el lambda de Poisson para los goles esperados de un equipo.
    Fórmula: (ataque_equipo / promedio_liga) × (defensa_rival / promedio_liga) × promedio_liga × factor
    """
    if league_avg <= 0:
        league_avg = 1.26
    attack = team_avg_goals / league_avg if league_avg > 0 else 1.0
    defense = opp_avg_conceded / league_avg if league_avg > 0 else 1.0
    lam = attack * defense * league_avg * advantage_factor
    return max(0.1, round(lam, 4))


def calculate_probabilities(
    home_stats: dict,
    away_stats: dict,
    h2h_summary: dict | None = None,
) -> MatchProbabilities:
    """
    Calcula las probabilidades de un partido dado los stats de ambos equipos.

    Args:
        home_stats: Dict de get_recent_form() para el equipo local.
        away_stats: Dict de get_recent_form() para el equipo visitante.
        h2h_summary: Dict de get_h2h_summary() (opcional, mejora la estimación).

    Returns:
        MatchProbabilities con P(home), P(draw), P(away), P(over25), P(btts).
    """
    # Extraer medias de goles (con fallback al promedio de liga)
    half_avg = _LEAGUE_AVG_GOALS / 2

    home_attack = home_stats.get("avg_goals", half_avg)
    home_defend = home_stats.get("avg_goals_against", half_avg)
    away_attack = away_stats.get("avg_goals", half_avg)
    away_defend = away_stats.get("avg_goals_against", half_avg)

    # Lambdas esperados
    lam_home = _estimate_lambda(home_attack, away_defend, half_avg, _HOME_ADVANTAGE)
    lam_away = _estimate_lambda(away_attack, home_defend, half_avg, 1.0)

    # Probabilidades Poisson
    p_home, p_draw, p_away = _poisson_matrix(lam_home, lam_away)

    # Si hay H2H, ponderar (30% H2H, 70% forma reciente). Si el resumen trae
    # tasas ponderadas por antigüedad (get_weighted_h2h_summary), se prefieren
    # sobre los conteos crudos wins_team1/draws/wins_team2.
    if h2h_summary and h2h_summary.get("total", 0) >= _H2H_MIN_TOTAL:
        n = h2h_summary["total"]
        if "weighted_win_rate1" in h2h_summary:
            h2h_home = h2h_summary["weighted_win_rate1"]
            h2h_draw = h2h_summary["weighted_draw_rate"]
            h2h_away = h2h_summary["weighted_win_rate2"]
        else:
            h2h_home = h2h_summary["wins_team1"] / n
            h2h_draw = h2h_summary["draws"] / n
            h2h_away = h2h_summary["wins_team2"] / n
        w_h2h = _H2H_WEIGHT
        p_home = round(p_home * (1 - w_h2h) + h2h_home * w_h2h, 4)
        p_draw = round(p_draw * (1 - w_h2h) + h2h_draw * w_h2h, 4)
        p_away = round(p_away * (1 - w_h2h) + h2h_away * w_h2h, 4)
        # Re-normalizar
        total = p_home + p_draw + p_away
        if total > 0:
            p_home = round(p_home / total, 4)
            p_draw = round(p_draw / total, 4)
            p_away = round(p_away / total, 4)

    # Over 2.5: basado en lambdas (probabilidad de que hg + ag > 2.5)
    p_over25_base = sum(
        _poisson_prob(lam_home, hg) * _poisson_prob(lam_away, ag)
        for hg in range(8)
        for ag in range(8)
        if hg + ag > 2
    )
    # Ponderar con tasas históricas de ambos equipos si disponibles
    home_o25 = home_stats.get("over25_rate", p_over25_base)
    away_o25 = away_stats.get("over25_rate", p_over25_base)
    h2h_o25 = h2h_summary.get("over25_rate", p_over25_base) if h2h_summary else p_over25_base
    w_base, w_home_o25, w_away_o25, w_h2h_o25 = _OVER25_WEIGHTS
    p_over25 = round((p_over25_base * w_base + home_o25 * w_home_o25 + away_o25 * w_away_o25 + h2h_o25 * w_h2h_o25), 4)

    # BTTS: promedio ponderado de tasas históricas
    w_home_btts, w_away_btts, w_h2h_btts = _BTTS_WEIGHTS
    home_btts = home_stats.get("btts_rate", 0.50)
    away_btts = away_stats.get("btts_rate", 0.50)
    h2h_btts = h2h_summary.get("btts_rate", 0.50) if h2h_summary else 0.50
    p_btts = round((home_btts * w_home_btts + away_btts * w_away_btts + h2h_btts * w_h2h_btts), 4)

    # Clamp todo a [0.01, 0.99]
    def _clamp(x):
        return max(0.01, min(0.99, x))

    return MatchProbabilities(
        home=_clamp(p_home),
        draw=_clamp(p_draw),
        away=_clamp(p_away),
        over25=_clamp(p_over25),
        btts=_clamp(p_btts),
    )
