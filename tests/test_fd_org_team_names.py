import json
from pathlib import Path

from app.config import FOOTBALL_DATA_ORG_COMPETITION_CODES, FOOTBALL_DATA_ORG_TEAM_ALIASES
from app.data.loader import normalize_fd_org_team_name

ROOT = Path(__file__).resolve().parents[1]


def test_known_collisions_resolve_correctly():
    # Casos reales donde un fuzzy-match generico fallaria por colision de
    # substring (ver comentario en app/config.py junto a
    # FOOTBALL_DATA_ORG_TEAM_ALIASES). Verificados contra la API real.
    assert normalize_fd_org_team_name("RCD Espanyol de Barcelona") == "Espanol"
    assert normalize_fd_org_team_name("FC Barcelona") == "Barcelona"
    assert normalize_fd_org_team_name("FC Internazionale Milano") == "Inter"
    assert normalize_fd_org_team_name("AC Milan") == "Milan"
    assert normalize_fd_org_team_name("Paris Saint-Germain FC") == "PSG"
    assert normalize_fd_org_team_name("Stade Rennais FC 1901") == "Rennes"
    assert normalize_fd_org_team_name("Paris FC") == "Paris FC"
    assert normalize_fd_org_team_name("NEC") == "Nijmegen"


def test_unmapped_name_passes_through_unchanged():
    assert normalize_fd_org_team_name("Some Unknown Club FC") == "Some Unknown Club FC"


def test_non_string_passes_through():
    assert normalize_fd_org_team_name(None) is None


def test_all_aliases_map_to_a_canonical_team_asset_name():
    """Guardia de regresion: si team_assets.json cambia de nombre canonico
    para algun equipo (ej. tras un fix de escudos), este test avisa de que
    el alias football-data.org ha quedado desfasado."""
    team_assets = json.loads((ROOT / "docs" / "data" / "team_assets.json").read_text(encoding="utf-8"))
    canonical = set(team_assets.get("teams", {}).keys())
    if not canonical:
        return  # entorno sin docs/data/ construido; no bloquear
    stale = {
        fd_name: canon
        for fd_name, canon in FOOTBALL_DATA_ORG_TEAM_ALIASES.items()
        if canon not in canonical
    }
    assert stale == {}, f"Alias apuntando a un nombre canonico que ya no existe: {stale}"
