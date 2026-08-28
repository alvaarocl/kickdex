"""
Fotos de jugadores vía Wikidata — gratis, sin clave, sin registro.

Contexto: igual que se hizo con los escudos de equipo (update_team_crests.py),
pero para jugadores. El pipeline API-Football (update_entity_assets.py) nunca
ha funcionado (0/2815 con foto) y su clave ya se usa para árbitros, así que
Wikidata evita chocar con esa cuota y no depende de ninguna clave.

Por cada equipo, una única consulta SPARQL con los nombres de esa plantilla
(en vez de una petición por jugador — 2815 peticiones individuales sería
excesivo para un endpoint público). Busca personas marcadas como futbolista
(wdt:P106 wd:Q937857) cuya etiqueta o alias coincida con alguno de los
nombres, y trae su foto (wdt:P18) y equipo(s) conocido(s) (wdt:P54) para
desambiguar cuando el nombre no es único (frecuente en jugadores hispanos que
Wikidata etiqueta con el nombre completo pero usan un alias corto, ej.
"Rodri" -> "Rodrigo Hernández Cascante").

Guarda el resultado en player_assets.json vía el campo `photo` (mismo campo
que ya usa update_entity_assets.py) usando build_player_assets(), que ya
preserva valores existentes entre ejecuciones.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

if hasattr(sys.stdout, "reconfigure"):
    # Nombres de jugadores/etiquetas de Wikidata traen acentos, diéresis, etc.
    # — en la consola de Windows (cp1252) un print() sin esto puede reventar
    # con UnicodeEncodeError a mitad de un run.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.data.assets import build_player_assets
from scripts._fuzzy_match import score

DATA_DIR = ROOT / "docs" / "data"
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
COMMONS_FILEPATH = "https://commons.wikimedia.org/wiki/Special:FilePath/{name}?width=300"
# Wikidata pide un User-Agent descriptivo con contacto (política de la
# Wikimedia Foundation) — usamos la URL pública del producto, no un dato
# personal.
USER_AGENT = "KICKDEX-PlayerPhotos/1.0 (https://kickdex.alvarocarpintero.com)"

FOOTBALLER_QID = "wd:Q937857"
MIN_TEAM_SCORE = 0.55
AMBIGUITY_MARGIN = 0.12


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _escape_literal(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _build_query(names: list[str]) -> str:
    values = " ".join(
        f'"{_escape_literal(n)}"@{lang}'
        for n in names
        for lang in ("en", "es", "mul")
    )
    return f"""
SELECT ?person ?name ?personLabel ?image ?teamLabel WHERE {{
  VALUES ?name {{ {values} }}
  {{ ?person rdfs:label ?name . }} UNION {{ ?person skos:altLabel ?name . }}
  ?person wdt:P106 {FOOTBALLER_QID} .
  OPTIONAL {{ ?person wdt:P18 ?image . }}
  OPTIONAL {{ ?person wdt:P54 ?team . }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,es,mul". }}
}}
"""


def _qid_from_uri(uri: str) -> str:
    return uri.rsplit("/", 1)[-1]


def _photo_url_from_image_uri(uri: str) -> str | None:
    # P18 se representa en el RDF de Wikidata ya como una URL de
    # Special:FilePath de Commons — la reutilizamos directamente.
    if "Special:FilePath/" not in uri:
        return None
    filename = uri.rsplit("Special:FilePath/", 1)[-1]
    return COMMONS_FILEPATH.format(name=filename)


def query_wikidata(names: list[str], timeout: int = 30) -> list[dict[str, Any]]:
    if not names:
        return []
    query = _build_query(names)
    res = requests.get(
        SPARQL_ENDPOINT,
        params={"query": query, "format": "json"},
        headers={"User-Agent": USER_AGENT, "Accept": "application/sparql-results+json"},
        timeout=timeout,
    )
    res.raise_for_status()
    return res.json().get("results", {}).get("bindings", [])


def match_players(names: list[str], team: str, bindings: list[dict[str, Any]]) -> dict[str, dict[str, Any] | None]:
    """Agrupa los resultados SPARQL por nombre solicitado y por QID, y aplica
    la guardia de ambigüedad usando el equipo real como desempate.

    Returns: {name: {"qid", "person_label", "photo"} | None}
    """
    # candidates[name][qid] = {"person_label", "images": set, "teams": set}
    candidates: dict[str, dict[str, dict[str, Any]]] = {}
    for row in bindings:
        name = row.get("name", {}).get("value")
        person_uri = row.get("person", {}).get("value")
        if not name or not person_uri:
            continue
        qid = _qid_from_uri(person_uri)
        bucket = candidates.setdefault(name, {}).setdefault(qid, {
            "person_label": row.get("personLabel", {}).get("value") or qid,
            "images": set(),
            "teams": set(),
        })
        image = row.get("image", {}).get("value")
        if image:
            bucket["images"].add(image)
        team_label = row.get("teamLabel", {}).get("value")
        if team_label:
            bucket["teams"].add(team_label)

    result: dict[str, dict[str, Any] | None] = {}
    for name in names:
        qids = candidates.get(name, {})
        with_photo = {qid: c for qid, c in qids.items() if c["images"]}
        if not with_photo:
            result[name] = None
            continue
        if len(with_photo) == 1:
            qid, c = next(iter(with_photo.items()))
            photo = _photo_url_from_image_uri(next(iter(c["images"])))
            result[name] = {"qid": qid, "person_label": c["person_label"], "photo": photo} if photo else None
            continue

        ranked = []
        for qid, c in with_photo.items():
            team_score = max((score(team, t) for t in c["teams"]), default=-1.0)
            ranked.append((team_score, qid, c))
        ranked.sort(key=lambda x: x[0], reverse=True)
        top_score, top_qid, top_c = ranked[0]
        second_score = ranked[1][0] if len(ranked) > 1 else -1.0
        if top_score < MIN_TEAM_SCORE or (top_score - second_score) < AMBIGUITY_MARGIN:
            result[name] = "AMBIGUOUS"
            continue
        photo = _photo_url_from_image_uri(next(iter(top_c["images"])))
        result[name] = {"qid": top_qid, "person_label": top_c["person_label"], "photo": photo} if photo else None

    return result


def update_player_photos(
    team_filter: str | None = None,
    dry_run: bool = False,
    sleep_seconds: float = 1.0,
    force: bool = False,
) -> dict[str, int]:
    players = json.loads((DATA_DIR / "players.json").read_text(encoding="utf-8"))
    existing_path = DATA_DIR / "player_assets.json"
    existing = json.loads(existing_path.read_text(encoding="utf-8")) if existing_path.exists() else {}
    manifest = build_player_assets(players, existing)

    teams = [team_filter] if team_filter else sorted(players.keys())
    stats = {"matched": 0, "missing": 0, "ambiguous": 0, "skipped_existing": 0}
    now = _now()

    for i, team in enumerate(teams):
        rows = players.get(team) or []
        names = []
        for row in rows if isinstance(rows, list) else []:
            name = str(row.get("player") or "").strip()
            if not name:
                continue
            key = f"{team}::{name}"
            asset = manifest["players"].get(key)
            if asset and asset.get("photo") and not force:
                stats["skipped_existing"] += 1
                continue
            names.append(name)
        if not names:
            continue

        try:
            bindings = query_wikidata(names)
        except Exception as exc:
            print(f"SKIP team={team}: {exc}")
            continue

        matches = match_players(names, team, bindings)
        for name in names:
            key = f"{team}::{name}"
            outcome = matches.get(name)
            if outcome == "AMBIGUOUS":
                stats["ambiguous"] += 1
                print(f"AMBIGUOUS {key} (candidatos empatados o sin equipo claro)")
            elif not outcome:
                stats["missing"] += 1
                print(f"MISSING {key}")
            else:
                stats["matched"] += 1
                print(f"MATCH {key} -> {outcome['qid']} (\"{outcome['person_label']}\")")
                if not dry_run:
                    manifest["players"][key].update({
                        "id": outcome["qid"],
                        "photo": outcome["photo"],
                        "source": "wikidata",
                        "source_updated_at": now,
                    })

        if i < len(teams) - 1:
            time.sleep(sleep_seconds)

    if not dry_run:
        manifest["updated_at"] = now
        existing_path.write_text(
            json.dumps(manifest, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )

    print(
        f"OK player photos matched={stats['matched']} missing={stats['missing']} "
        f"ambiguous={stats['ambiguous']} skipped_existing={stats['skipped_existing']}"
    )
    return stats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--team", default=None, help="Procesar un único equipo (para probar antes de lanzar todos)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Reconsultar jugadores que ya tienen foto")
    parser.add_argument("--sleep", type=float, default=1.0, help="Pausa entre consultas por equipo")
    args = parser.parse_args()
    update_player_photos(
        team_filter=args.team,
        dry_run=args.dry_run,
        sleep_seconds=args.sleep,
        force=args.force,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
