"""
Generador de Smart Alerts — frases de tendencia en lenguaje natural.
Analiza los stats de un partido y genera alertas ordenadas por relevancia.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

logger = logging.getLogger(__name__)


class AlertType(str, Enum):
    GOALS = "GOALS"
    BTTS = "BTTS"
    OVER_UNDER = "OVER_UNDER"
    CARDS = "CARDS"
    CORNERS = "CORNERS"
    FORM = "FORM"
    DEFENSE = "DEFENSE"
    H2H = "H2H"
    CLEAN_SHEET = "CLEAN_SHEET"


class AlertStrength(str, Enum):
    HIGH = "HIGH"      # ≥70% → Verde brillante
    MEDIUM = "MEDIUM"  # 55-69% → Amarillo
    LOW = "LOW"        # <55% → Gris, apenas se muestra


@dataclass
class Alert:
    text: str
    type: AlertType
    strength: AlertStrength
    confidence: float   # 0.0–1.0
    source: str         # "home", "away", "h2h", "combined"

    @property
    def emoji(self) -> str:
        return {"HIGH": "🟢", "MEDIUM": "🟡", "LOW": "⚪"}.get(self.strength.value, "⚪")

    @property
    def color(self) -> str:
        return {
            "HIGH": "#00d4aa",
            "MEDIUM": "#f0c040",
            "LOW": "#8b9ab0",
        }.get(self.strength.value, "#8b9ab0")


def _strength(rate: float) -> AlertStrength:
    if rate >= 0.70:
        return AlertStrength.HIGH
    if rate >= 0.55:
        return AlertStrength.MEDIUM
    return AlertStrength.LOW


def _pct(rate: float) -> str:
    return f"{int(round(rate * 100))}%"


def _clean_stats(stats: dict | None) -> dict:
    """Coerce None numeric values to 0.0 so comparisons don't blow up.

    team_stats.json stores explicit nulls for teams with thin history
    (recién ascendidos, filiales); ``dict.get(k, default)`` doesn't help
    because the key is present with value None.
    """
    if not stats:
        return {}
    cleaned = dict(stats)
    for key, value in stats.items():
        if value is None and key != "team":
            cleaned[key] = 0.0
    return cleaned


# ─── Generadores de alertas ──────────────────────────────────────────────────

def _home_alerts(home: dict, n: int) -> list[Alert]:
    alerts = []
    team = home.get("team", "Local")

    # Over 2.5 como local
    r = home.get("over25_rate", 0.0)
    if r >= 0.55:
        alerts.append(Alert(
            text=f"{team} ha jugado con más de 2.5 goles en el {_pct(r)} de sus partidos como local (muestra {n}, peso reciente)",
            type=AlertType.OVER_UNDER, strength=_strength(r), confidence=r, source="home"
        ))

    # BTTS como local
    r = home.get("btts_rate", 0.0)
    if r >= 0.55:
        alerts.append(Alert(
            text=f"Ambos equipos han marcado en el {_pct(r)} de los partidos de {team} (muestra {n}, peso reciente)",
            type=AlertType.BTTS, strength=_strength(r), confidence=r, source="home"
        ))

    # Racha goleadora
    r = home.get("avg_goals", 0.0)
    if r >= 2.0:
        alerts.append(Alert(
            text=f"{team} promedia {r:.1f} goles por partido como local (muestra {n}, peso reciente)",
            type=AlertType.GOALS, strength=AlertStrength.HIGH if r >= 2.5 else AlertStrength.MEDIUM,
            confidence=min(r / 3, 0.99), source="home"
        ))

    # Portería a cero
    r = home.get("clean_sheet_rate", 0.0)
    if r >= 0.50:
        alerts.append(Alert(
            text=f"{team} mantiene la portería a cero en el {_pct(r)} de sus partidos como local",
            type=AlertType.CLEAN_SHEET, strength=_strength(r), confidence=r, source="home"
        ))

    # Tarjetas
    r = home.get("avg_cards", 0.0)
    if r >= 2.5:
        alerts.append(Alert(
            text=f"{team} recibe una media de {r:.1f} tarjetas amarillas por partido",
            type=AlertType.CARDS, strength=AlertStrength.MEDIUM, confidence=min(r / 4, 0.99), source="home"
        ))

    # Tasa de victoria
    wr = home.get("win_rate", 0.0)
    if wr >= 0.60:
        alerts.append(Alert(
            text=f"{team} gana el {_pct(wr)} de sus partidos como local (muestra {n}, peso reciente)",
            type=AlertType.FORM, strength=_strength(wr), confidence=wr, source="home"
        ))

    return alerts


def _away_alerts(away: dict, n: int) -> list[Alert]:
    alerts = []
    team = away.get("team", "Visitante")

    r = away.get("over25_rate", 0.0)
    if r >= 0.55:
        alerts.append(Alert(
            text=f"Más de 2.5 goles en el {_pct(r)} de los partidos de {team} como visitante",
            type=AlertType.OVER_UNDER, strength=_strength(r), confidence=r, source="away"
        ))

    r = away.get("btts_rate", 0.0)
    if r >= 0.55:
        alerts.append(Alert(
            text=f"Ambos marcan en el {_pct(r)} de los partidos de {team} fuera de casa",
            type=AlertType.BTTS, strength=_strength(r), confidence=r, source="away"
        ))

    r = away.get("avg_goals_against", 0.0)
    if r >= 1.5:
        alerts.append(Alert(
            text=f"{team} concede {r:.1f} goles de media como visitante (muestra {n}, peso reciente)",
            type=AlertType.DEFENSE, strength=_strength(r / 3), confidence=min(r / 3, 0.99), source="away"
        ))

    r = away.get("avg_goals", 0.0)
    if r >= 1.5:
        alerts.append(Alert(
            text=f"{team} anota {r:.1f} goles de media como visitante (muestra {n}, peso reciente)",
            type=AlertType.GOALS, strength=AlertStrength.HIGH if r >= 2.0 else AlertStrength.MEDIUM,
            confidence=min(r / 3, 0.99), source="away"
        ))

    wr = away.get("win_rate", 0.0)
    if wr >= 0.50:
        alerts.append(Alert(
            text=f"{team} gana el {_pct(wr)} de sus partidos fuera de casa (muestra {n}, peso reciente)",
            type=AlertType.FORM, strength=_strength(wr), confidence=wr, source="away"
        ))

    return alerts


def _h2h_alerts(h2h: dict, team1: str, team2: str) -> list[Alert]:
    alerts = []
    n = h2h.get("total", 0)
    if n < 3:
        return alerts

    r = h2h.get("over25_rate", 0.0)
    if r >= 0.55:
        alerts.append(Alert(
            text=f"Más de 2.5 goles en el {_pct(r)} de los {n} enfrentamientos directos ({team1} vs {team2})",
            type=AlertType.H2H, strength=_strength(r), confidence=r, source="h2h"
        ))

    r = h2h.get("btts_rate", 0.0)
    if r >= 0.55:
        alerts.append(Alert(
            text=f"Ambos equipos marcan en el {_pct(r)} de sus encuentros directos",
            type=AlertType.H2H, strength=_strength(r), confidence=r, source="h2h"
        ))

    wins1 = h2h.get("wins_team1", 0)
    wins2 = h2h.get("wins_team2", 0)
    if wins1 / n >= 0.60:
        alerts.append(Alert(
            text=f"{team1} gana el {_pct(wins1/n)} de los enfrentamientos directos ({wins1} de {n})",
            type=AlertType.H2H, strength=_strength(wins1 / n), confidence=wins1 / n, source="h2h"
        ))
    elif wins2 / n >= 0.60:
        alerts.append(Alert(
            text=f"{team2} domina el H2H: gana el {_pct(wins2/n)} de los encuentros ({wins2} de {n})",
            type=AlertType.H2H, strength=_strength(wins2 / n), confidence=wins2 / n, source="h2h"
        ))

    return alerts


def _combined_alerts(home: dict, away: dict) -> list[Alert]:
    """Alertas que combinan stats de ambos equipos."""
    alerts = []

    # Partido de muchos goles: ambos equipos atacan mucho
    combined_goals = home.get("avg_goals", 0) + away.get("avg_goals", 0)
    if combined_goals >= 3.0:
        rate = min(combined_goals / 5, 0.95)
        alerts.append(Alert(
            text=f"Partido potencialmente goleador: suma de promedios de goles = {combined_goals:.1f}/partido",
            type=AlertType.GOALS,
            strength=AlertStrength.HIGH if combined_goals >= 3.5 else AlertStrength.MEDIUM,
            confidence=rate, source="combined"
        ))

    # BTTS combinado
    home_btts = home.get("btts_rate", 0.0)
    away_btts = away.get("btts_rate", 0.0)
    combined_btts = (home_btts + away_btts) / 2
    if combined_btts >= 0.60:
        alerts.append(Alert(
            text=f"Alta probabilidad de que ambos equipos marquen (tasas: {_pct(home_btts)} / {_pct(away_btts)})",
            type=AlertType.BTTS, strength=_strength(combined_btts), confidence=combined_btts, source="combined"
        ))

    return alerts


# ─── API pública ─────────────────────────────────────────────────────────────

def generate_alerts(
    home_stats: dict,
    away_stats: dict,
    h2h_summary: dict | None = None,
    n: int = 5,
    min_strength: AlertStrength = AlertStrength.MEDIUM,
) -> list[Alert]:
    """
    Genera todas las alertas para un partido, ordenadas por relevancia.

    Args:
        home_stats: Resultado de get_recent_form() para el local.
        away_stats: Resultado de get_recent_form() para el visitante.
        h2h_summary: Resultado de get_h2h_summary() (opcional).
        n: Número de partidos analizados (para textos).
        min_strength: Filtro mínimo de fuerza (default: MEDIUM).

    Returns:
        Lista de Alert ordenada por confidence desc.
    """
    home_stats = _clean_stats(home_stats)
    away_stats = _clean_stats(away_stats)
    h2h_summary = _clean_stats(h2h_summary) or None

    team1 = home_stats.get("team", "Local")
    team2 = away_stats.get("team", "Visitante")

    alerts: list[Alert] = []
    alerts.extend(_home_alerts(home_stats, n))
    alerts.extend(_away_alerts(away_stats, n))
    alerts.extend(_combined_alerts(home_stats, away_stats))
    if h2h_summary:
        alerts.extend(_h2h_alerts(h2h_summary, team1, team2))

    # Filtrar por fuerza mínima
    strength_order = {AlertStrength.LOW: 0, AlertStrength.MEDIUM: 1, AlertStrength.HIGH: 2}
    min_val = strength_order[min_strength]
    alerts = [a for a in alerts if strength_order[a.strength] >= min_val]

    # Ordenar: HIGH primero, luego por confidence
    alerts.sort(key=lambda a: (strength_order[a.strength], a.confidence), reverse=True)

    # Limitar a las 8 más relevantes para no saturar la UI
    return alerts[:8]
