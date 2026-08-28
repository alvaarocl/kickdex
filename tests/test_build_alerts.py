"""
Tests para la generación de alerts.json (Fase 0.4).
Verifican que _write_alerts_json produce un JSON con la forma esperada
y que el dict de alertas tiene los campos obligatorios.
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.engine.smart_alerts import generate_alerts, AlertStrength

# ── Fixtures de stats reutilizables ──────────────────────────────────────────

HOME_STATS = {
    "team": "Racing",
    "matches_analyzed": 10,
    "over25_rate": 0.70,
    "btts_rate": 0.65,
    "avg_goals": 2.1,
    "avg_goals_against": 1.0,
    "avg_shots": 14,
    "avg_shots_on": 5,
    "avg_corners": 6,
    "avg_cards": 1.8,
    "win_rate": 0.60,
    "clean_sheet_rate": 0.30,
}

AWAY_STATS = {
    "team": "Elche",
    "matches_analyzed": 8,
    "over25_rate": 0.55,
    "btts_rate": 0.50,
    "avg_goals": 1.3,
    "avg_goals_against": 1.6,
    "avg_shots": 10,
    "avg_shots_on": 3,
    "avg_corners": 4,
    "avg_cards": 2.1,
    "win_rate": 0.35,
    "clean_sheet_rate": 0.15,
}

H2H_SUMMARY = {
    "total": 8,
    "wins_team1": 4,
    "draws": 2,
    "wins_team2": 2,
    "over25_rate": 0.625,
    "btts_rate": 0.50,
}


def _alert_as_dict(a) -> dict:
    return {
        "type": a.type.value,
        "strength": a.strength.value,
        "text": a.text,
        "emoji": a.emoji,
        "color": a.color,
        "confidence": round(a.confidence, 3),
        "source": a.source,
    }


def test_alert_dict_has_required_fields():
    """Cada alerta serializada tiene los 7 campos que espera el frontend."""
    alerts = generate_alerts(HOME_STATS, AWAY_STATS, H2H_SUMMARY)
    assert len(alerts) > 0, "Deben generarse alertas para estos stats"
    required = {"type", "strength", "text", "emoji", "color", "confidence", "source"}
    for a in alerts:
        d = _alert_as_dict(a)
        assert required.issubset(d.keys()), f"Faltan campos: {required - d.keys()}"


def test_alerts_json_top_level_structure(tmp_path, monkeypatch):
    """_write_alerts_json genera un JSON con 'updated_at' y 'matches'."""
    import scripts.build_data as bd

    # Preparar mocks mínimos
    team_stats = {
        "Racing": {"home": HOME_STATS, "away": AWAY_STATS},
        "Elche":  {"home": AWAY_STATS, "away": HOME_STATS},
    }
    h2h_data = {
        "Elche|Racing": {
            "summary": H2H_SUMMARY,
        }
    }

    fixtures_payload = {
        "upcoming": [
            {"league": "SP2", "date": "2026-09-05", "home": "Racing", "away": "Elche"},
        ]
    }

    monkeypatch.setattr(bd, "OUTPUT_DIR", tmp_path)

    def fake_read(filename):
        if filename == "team_stats.json":
            return team_stats
        if filename == "h2h.json":
            return h2h_data
        return None

    monkeypatch.setattr(bd, "_read_existing_json", fake_read)

    bd._write_alerts_json(fixtures_payload)

    out = json.loads((tmp_path / "alerts.json").read_text(encoding="utf-8"))
    assert "updated_at" in out
    assert "matches" in out
    assert isinstance(out["matches"], dict)


def test_alerts_json_match_key_format(tmp_path, monkeypatch):
    """La clave de cada partido sigue el formato 'league|date|home|away'."""
    import scripts.build_data as bd

    team_stats = {
        "Racing": {"home": HOME_STATS},
        "Elche":  {"away": AWAY_STATS},
    }
    fixtures_payload = {
        "upcoming": [
            {"league": "SP2", "date": "2026-09-05", "home": "Racing", "away": "Elche"},
        ]
    }

    monkeypatch.setattr(bd, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(bd, "_read_existing_json", lambda f: team_stats if f == "team_stats.json" else {})

    bd._write_alerts_json(fixtures_payload)

    out = json.loads((tmp_path / "alerts.json").read_text(encoding="utf-8"))
    keys = list(out["matches"].keys())
    if keys:
        parts = keys[0].split("|")
        assert len(parts) == 4, f"Clave con formato incorrecto: {keys[0]}"
