"""Fill missing crest URLs from the public football-logos SVG repository."""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path, PurePosixPath

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data"
TREE = "https://api.github.com/repos/JoseArroyave/football-logos/git/trees/main?recursive=1"
RAW = "https://raw.githubusercontent.com/JoseArroyave/football-logos/main/"
COUNTRIES = {"SP1":"spain","SP2":"spain","E0":"england","E1":"england","I1":"italy","I2":"italy","D1":"germany","D2":"germany","F1":"france","F2":"france","N1":"netherlands"}
ALIASES = {"Alaves":"Deportivo Alaves","Ath Madrid":"Atletico Madrid","Athletic Club":"Athletic Club Bilbao","Betis":"Real Betis","Dep. A Coruna":"Deportivo La Coruna","Espanol":"Espanyol","Santander":"Racing Santander","Sociedad":"Real Sociedad","Vallecano":"Rayo Vallecano","Sp Gijon":"Sporting Gijon","For Sittard":"Fortuna Sittard","AZ Alkmaar":"AZ","Den Haag":"ADO Den Haag","Nijmegen":"NEC Nijmegen","PSV Eindhoven":"PSV","Dortmund":"Borussia Dortmund","Ein Frankfurt":"Eintracht Frankfurt","M'gladbach":"Borussia Monchengladbach","Man City":"Manchester City","Man United":"Manchester United","Nott'm Forest":"Nottingham Forest","PSG":"Paris Saint-Germain","St Etienne":"Saint-Etienne","Lyon":"Olympique Lyonnais","Marseille":"Olympique Marseille"}

def norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "", text)

def score(left: str, right: str) -> float:
    a, b = norm(left), norm(right)
    if a == b: return 1.0
    if a in b or b in a: return .91
    return SequenceMatcher(None, a, b).ratio() * .86

def load_manifest() -> dict:
    return json.loads((DATA / "team_assets.json").read_text(encoding="utf-8"))

def find(team: str, league: str, paths: list[str]) -> tuple[str | None, float]:
    # crest source fallback
    country = COUNTRIES.get(league)
    target = ALIASES.get(team, team)
    candidates = [(PurePosixPath(p).stem.replace("_", " "), p) for p in paths if PurePosixPath(p).parts[:2] == ("logos", country)]
    ranked = sorted(((score(target, name), path) for name, path in candidates), reverse=True)
    if not ranked or ranked[0][0] < .70: return None, ranked[0][0] if ranked else 0
    return ranked[0][1], ranked[0][0]

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    manifest = load_manifest()
    payload = requests.get(TREE, timeout=45).json()
    paths = [x["path"] for x in payload.get("tree", []) if x.get("path", "").endswith(".svg")]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    updated = missing = preserved = 0
    for name, asset in manifest.get("teams", {}).items():
        if asset.get("crest") and not args.force:
            preserved += 1; continue
        path, value = find(name, asset.get("league", ""), paths)
        if not path:
            missing += 1; print(f"MISSING {asset.get('league')}:{name}"); continue
        print(f"MATCH {asset.get('league')}:{name} -> {path} ({value:.2f})")
        if not args.dry_run:
            asset.update({"crest": RAW + path, "source": "football-logos/JoseArroyave", "source_updated_at": now})
        updated += 1
    if not args.dry_run:
        manifest["updated_at"] = now
        (DATA / "team_assets.json").write_text(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"OK crests={updated} preserved={preserved} missing={missing}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
