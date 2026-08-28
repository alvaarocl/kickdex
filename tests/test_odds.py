"""Fase 4 — cuotas de partidos futuros (update_odds.py + add_odds_based_edges)."""

import importlib
import os


def test_update_odds_writes_disabled_stub_without_key(tmp_path, monkeypatch):
    monkeypatch.delenv("THE_ODDS_API_KEY", raising=False)
    import scripts.update_odds as uo
    importlib.reload(uo)
    monkeypatch.setattr(uo, "ODDS_PATH", tmp_path / "odds.json")
    uo.update_odds()
    import json
    data = json.loads((tmp_path / "odds.json").read_text(encoding="utf-8"))
    assert data["enabled"] is False
    assert data["matches"] == {}
    assert "leagues_covered" in data


def test_add_odds_based_edges_is_noop_when_odds_disabled(monkeypatch):
    import scripts.build_data as bd
    monkeypatch.setattr(bd, "_read_existing_json", lambda name: {"enabled": False, "matches": {}} if name == "odds.json" else None)
    payload = {"items": [{"status": "settled"}], "stats": {"upcoming_edges": 0}, "status": "settled_only"}
    out = bd.add_odds_based_edges(payload, None, {"upcoming": []})
    assert out is payload
    assert out["stats"]["upcoming_edges"] == 0
