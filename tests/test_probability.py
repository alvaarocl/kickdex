"""Tests para el motor de probabilidades."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from app.engine.probability import calculate_probabilities, MatchProbabilities

STRONG_HOME = {
    "avg_goals": 2.5, "avg_goals_against": 0.8, "avg_shots": 15,
    "avg_shots_on": 6, "avg_corners": 7, "over25_rate": 0.8, "btts_rate": 0.6,
    "clean_sheet_rate": 0.5, "win_rate": 0.75,
}
WEAK_AWAY = {
    "avg_goals": 0.8, "avg_goals_against": 2.2, "avg_shots": 8,
    "avg_shots_on": 2, "avg_corners": 3, "over25_rate": 0.6, "btts_rate": 0.45,
    "clean_sheet_rate": 0.1, "win_rate": 0.20,
}
BALANCED = {
    "avg_goals": 1.4, "avg_goals_against": 1.4, "avg_shots": 12,
    "avg_shots_on": 4, "avg_corners": 5, "over25_rate": 0.50, "btts_rate": 0.50,
    "clean_sheet_rate": 0.30, "win_rate": 0.40,
}


def test_probabilities_sum_to_one():
    probs = calculate_probabilities(BALANCED, BALANCED)
    total = probs.home + probs.draw + probs.away
    assert abs(total - 1.0) < 0.02, f"Probabilities sum to {total}, not 1.0"


def test_strong_home_favors_home():
    probs = calculate_probabilities(STRONG_HOME, WEAK_AWAY)
    assert probs.home > probs.away, "Home should be favored"
    assert probs.home > 0.45, "Strong home should have >45% win prob"


def test_all_probs_in_valid_range():
    probs = calculate_probabilities(STRONG_HOME, WEAK_AWAY)
    for attr in ["home", "draw", "away", "over25", "btts"]:
        val = getattr(probs, attr)
        assert 0.0 <= val <= 1.0, f"{attr}={val} out of range"


def test_over25_prob_range():
    probs = calculate_probabilities(STRONG_HOME, WEAK_AWAY)
    assert 0.0 <= probs.over25 <= 1.0


def test_h2h_weighting_influences_result():
    """Con H2H donde el visitante domina, las probabilidades deben ajustarse."""
    away_dominant_h2h = {"total": 10, "wins_team1": 2, "draws": 2, "wins_team2": 6,
                          "over25_rate": 0.6, "btts_rate": 0.5, "avg_goals": 2.1}
    probs_no_h2h = calculate_probabilities(STRONG_HOME, WEAK_AWAY)
    probs_with_h2h = calculate_probabilities(STRONG_HOME, WEAK_AWAY, away_dominant_h2h)
    # Con H2H que favorece al visitante, la prob del visitante debe ser mayor
    assert probs_with_h2h.away > probs_no_h2h.away
