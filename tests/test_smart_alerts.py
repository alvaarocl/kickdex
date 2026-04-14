"""Tests para el generador de Smart Alerts."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.engine.smart_alerts import generate_alerts, AlertStrength, AlertType

HIGH_OVER25_STATS = {
    "team": "TestFC", "over25_rate": 0.80, "btts_rate": 0.70,
    "avg_goals": 2.8, "avg_goals_against": 1.2, "avg_shots": 15,
    "avg_shots_on": 6, "avg_corners": 7, "avg_cards": 1.5,
    "win_rate": 0.75, "clean_sheet_rate": 0.30,
}
LOW_STATS = {
    "team": "LoserFC", "over25_rate": 0.20, "btts_rate": 0.25,
    "avg_goals": 0.5, "avg_goals_against": 0.8, "avg_shots": 6,
    "avg_shots_on": 2, "avg_corners": 3, "avg_cards": 1.2,
    "win_rate": 0.10, "clean_sheet_rate": 0.05,
}


def test_generates_alerts_for_high_stats():
    alerts = generate_alerts(HIGH_OVER25_STATS, LOW_STATS)
    assert len(alerts) > 0


def test_high_over25_triggers_alert():
    alerts = generate_alerts(HIGH_OVER25_STATS, HIGH_OVER25_STATS)
    types = [a.type for a in alerts]
    assert AlertType.OVER_UNDER in types or AlertType.GOALS in types or AlertType.BTTS in types


def test_alerts_respect_min_strength_filter():
    """Con filtro HIGH, solo deben aparecer alertas HIGH."""
    alerts = generate_alerts(HIGH_OVER25_STATS, HIGH_OVER25_STATS, min_strength=AlertStrength.HIGH)
    for a in alerts:
        assert a.strength == AlertStrength.HIGH


def test_alert_confidence_in_range():
    alerts = generate_alerts(HIGH_OVER25_STATS, LOW_STATS)
    for a in alerts:
        assert 0.0 <= a.confidence <= 1.0, f"Confidence {a.confidence} out of range"


def test_max_alerts_limit():
    """No debe generar más de 8 alertas."""
    alerts = generate_alerts(HIGH_OVER25_STATS, HIGH_OVER25_STATS)
    assert len(alerts) <= 8


def test_no_alerts_for_low_stats():
    """Equipo con stats bajos no debería generar alertas HIGH."""
    alerts = generate_alerts(LOW_STATS, LOW_STATS, min_strength=AlertStrength.HIGH)
    assert len(alerts) == 0


def test_h2h_alerts_require_minimum_matches():
    """H2H con menos de 3 partidos no genera alertas."""
    small_h2h = {"total": 2, "wins_team1": 1, "draws": 0, "wins_team2": 1,
                 "over25_rate": 0.80, "btts_rate": 0.75}
    alerts = generate_alerts(HIGH_OVER25_STATS, HIGH_OVER25_STATS, h2h_summary=small_h2h)
    h2h_types = [a for a in alerts if a.source == "h2h"]
    assert len(h2h_types) == 0
