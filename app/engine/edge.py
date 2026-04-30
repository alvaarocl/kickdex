"""Value/edge helpers shared by the batch pipeline and tests."""

from __future__ import annotations

import math


def implied_probability(odds: float | int | str | None) -> float | None:
    """Return bookmaker implied probability for decimal odds."""
    try:
        value = float(odds)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value) or value <= 1:
        return None
    return 1 / value


def calculate_edge(prob_real: float | int | str | None, odds: float | int | str | None) -> float | None:
    """Return edge in percentage points: (model probability - implied probability) * 100."""
    implied = implied_probability(odds)
    if implied is None:
        return None
    try:
        probability = float(prob_real)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(probability) or probability <= 0 or probability >= 1:
        return None
    return (probability - implied) * 100


def edge_confidence(edge_pct: float | None, home_matches: int = 0, away_matches: int = 0) -> str:
    """Coarse confidence label for UI display, not a betting recommendation."""
    if edge_pct is None:
        return "unknown"
    sample = min(home_matches or 0, away_matches or 0)
    if sample >= 5 and edge_pct >= 5:
        return "medium"
    if sample >= 3 and edge_pct >= 2:
        return "low"
    return "watch"
