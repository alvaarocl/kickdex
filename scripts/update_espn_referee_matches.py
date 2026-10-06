"""
Árbitro + tarjetas + faltas por partido desde el marcador público de ESPN.

Por qué: World Soccer Data bloquea las IPs de GitHub Actions (403/406, tanto
directo como vía lector), así que desde CI no se podía actualizar la temporada
de los árbitros. ESPN sí responde desde CI y su resumen de partido trae el
árbitro (gameInfo.officials) y, por equipo, amarillas, rojas y faltas.

Funcionamiento (incremental, apto para el workflow diario):
1. Por liga y día (desde la última fecha registrada - 3 días, o desde el inicio
   de temporada en la primera ejecución) se lee el scoreboard.
2. Para cada partido terminado que no esté ya en el CSV se pide el resumen.
3. Se AÑADEN filas a DATOS/referees_matches.csv (mismo contrato que
   update_referee_data.py, que build_data.py ya consume), source=espn.
4. Para partidos de los próximos días, si ESPN ya publica el árbitro, se
   guarda en DATOS/referee_assignments.json (lo usa build_fixtures).
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import CURRENT_SEASON_START, DATA_DIR, LEAGUES

BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/{endpoint}"
ESPN_SLUGS = {
    "SP1": "esp.1", "SP2": "esp.2", "E0": "eng.1", "E1": "eng.2", "I1": "ita.1", "I2": "ita.2",
    "D1": "ger.1", "D2": "ger.2", "F1": "fra.1", "F2": "fra.2", "N1": "ned.1",
}
OUT_PATH = Path(DATA_DIR) / "referees_matches.csv"
ASSIGNMENTS_PATH = Path(DATA_DIR) / "referee_assignments.json"
TEAM_MAP_PATH = ROOT / "docs" / "data" / "espn_teams.json"
FIELDNAMES = [
    "fixture_id", "date", "league", "league_name", "referee", "home", "away",
    "home_score", "away_score", "yellow_cards", "red_cards", "fouls", "penalties",
    "source", "updated_at",
]
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
}
NOISE = {"fc", "cf", "afc", "sc", "cd", "ud", "sd", "rc", "rcd", "club", "de", "del", "la", "el", "the",
         "ac", "as", "ss", "us", "sv", "vfb", "vfl", "tsg", "1", "fk", "calcio", "city", "town"}


def _get(slug: str, endpoint: str, params: dict[str, Any], timeout: int = 20) -> dict[str, Any]:
    url = BASE.format(slug=slug, endpoint=endpoint)
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 500, 502, 503):
                time.sleep(2 * (attempt + 1))
                continue
            return {}
        except requests.RequestException:
            time.sleep(2 * (attempt + 1))
    return {}


# ── Nombres ESPN → claves canónicas del dataset ───────────────────────────

# Nombres de ESPN que no se parecen al canónico.
ESPN_ALIASES = {"fc cologne": "koln", "cologne": "koln", "deportivo": "deportivo coruna"}


def _tokens(name: str | None) -> list[str]:
    text = unicodedata.normalize("NFKD", str(name or ""))
    text = "".join(c for c in text if not unicodedata.combining(c)).lower().strip()
    text = ESPN_ALIASES.get(text, text)
    return [t for t in re.sub(r"[^a-z0-9\s]", " ", text).split() if t and t not in NOISE]


def _display_names() -> dict[str, str]:
    path = ROOT / "docs" / "js" / "team_names.js"
    try:
        return dict(re.findall(r'"([^"]+)":\s*"([^"]+)"', path.read_text(encoding="utf-8")))
    except OSError:
        return {}


class TeamMatcher:
    def __init__(self) -> None:
        try:
            leagues = json.loads((ROOT / "docs" / "data" / "leagues.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            leagues = {}
        display = _display_names()
        self.by_league = {
            code: [(key, [_tokens(key), _tokens(display.get(key, key))]) for key in info.get("teams", [])]
            for code, info in leagues.items()
        }

    def match(self, league: str, *names: str | None) -> str | None:
        best, best_score = None, 0.0
        for key, variants in self.by_league.get(league, []):
            for v in variants:
                for n in (_tokens(x) for x in names if x):
                    if not v or not n:
                        continue
                    if v == n:
                        score = 1.0
                    else:
                        inter = len([t for t in v if t in n])
                        fuzzy = len([t for t in v if any(len(t) >= 3 and len(u) >= 3 and (u.startswith(t) or t.startswith(u)) for u in n)])
                        score = max(inter, 0.9 * fuzzy) / max(len(v), len(n))
                    if score > best_score:
                        best, best_score = key, score
        return best if best_score >= 0.5 else None


# ── Extracción ────────────────────────────────────────────────────────────

def _stat(team_box: dict[str, Any], name: str) -> int | None:
    for s in team_box.get("statistics", []) or []:
        if s.get("name") == name:
            try:
                return int(float(s.get("displayValue")))
            except (TypeError, ValueError):
                return None
    return None


def _referee(summary: dict[str, Any]) -> str | None:
    for o in (summary.get("gameInfo") or {}).get("officials") or []:
        if (o.get("position") or {}).get("name", "").lower() == "referee" or o.get("order") == 1:
            return (o.get("displayName") or o.get("fullName") or "").strip() or None
    return None


def match_row(league: str, event: dict[str, Any], summary: dict[str, Any], teams: TeamMatcher) -> dict[str, Any] | None:
    referee = _referee(summary)
    comp = (event.get("competitions") or [{}])[0]
    competitors = {c.get("homeAway"): c for c in comp.get("competitors", [])}
    home, away = competitors.get("home"), competitors.get("away")
    if not referee or not home or not away:
        return None
    box = {str((t.get("team") or {}).get("id")): t for t in (summary.get("boxscore") or {}).get("teams", [])}
    hb, ab = box.get(str(home["team"]["id"]), {}), box.get(str(away["team"]["id"]), {})

    def total(stat: str) -> int | str:
        a, b = _stat(hb, stat), _stat(ab, stat)
        return "" if a is None or b is None else a + b

    # Tarjetas = eventos mostrados por el árbitro (keyEvents). El boxscore de
    # ESPN omite la amarilla de una doble amarilla; contamos cada tarjeta una vez.
    card_events = [str((k.get("type") or {}).get("text", "")) for k in summary.get("keyEvents") or []]
    yellows = sum(1 for t in card_events if t.lower() == "yellow card")
    reds = sum(1 for t in card_events if t.lower() == "red card")
    has_events = bool(summary.get("keyEvents"))

    def team_name(c: dict[str, Any]) -> str:
        t = c.get("team") or {}
        return teams.match(league, t.get("displayName"), t.get("shortDisplayName"), t.get("name"), t.get("location")) or t.get("displayName", "")

    kickoff = datetime.fromisoformat(event["date"].replace("Z", "+00:00"))
    return {
        "fixture_id": f"espn:{event['id']}",
        "date": kickoff.date().isoformat(),
        "league": league,
        "league_name": LEAGUES.get(league, league),
        "referee": referee,
        "home": team_name(home),
        "away": team_name(away),
        "home_score": home.get("score", ""),
        "away_score": away.get("score", ""),
        "yellow_cards": yellows if has_events else total("yellowCards"),
        "red_cards": reds if has_events else total("redCards"),
        "fouls": total("foulsCommitted"),
        "penalties": "",  # ESPN no lo da a nivel de partido: vacío = sin dato
        "source": "espn",
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def _existing(path: Path) -> tuple[set[str], dict[str, str]]:
    ids: set[str] = set()
    last_by_league: dict[str, str] = {}
    if not path.exists():
        return ids, last_by_league
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ids.add(str(row.get("fixture_id")))
            if row.get("source") == "espn":
                lg, d = row.get("league", ""), row.get("date", "")
                if d > last_by_league.get(lg, ""):
                    last_by_league[lg] = d
    return ids, last_by_league


def _append(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        if new_file:
            writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in FIELDNAMES})


def write_team_map(teams: TeamMatcher, leagues: list[str]) -> int:
    """{liga: {id ESPN: clave canónica}} para el Directo (cruce exacto por id
    en vez de por nombre en el navegador)."""
    out: dict[str, dict[str, str]] = {}
    for code in leagues:
        slug = ESPN_SLUGS.get(code)
        data = _get(slug, "teams", {}) if slug else {}
        league_teams = ((data.get("sports") or [{}])[0].get("leagues") or [{}])[0].get("teams") or []
        for item in league_teams:
            t = item.get("team") or {}
            key = teams.match(code, t.get("displayName"), t.get("shortDisplayName"), t.get("name"), t.get("location"))
            if key and t.get("id"):
                out.setdefault(code, {})[str(t["id"])] = key
    if out:
        TEAM_MAP_PATH.write_text(json.dumps({
            "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "leagues": out,
        }, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return sum(len(v) for v in out.values())


def update(leagues: list[str], days_ahead: int = 3, workers: int = 8, max_seconds: float | None = None) -> int:
    deadline = time.monotonic() + max_seconds if max_seconds else None
    teams = TeamMatcher()
    mapped = write_team_map(teams, leagues)
    print(f"OK mapa ESPN→equipos: {mapped} equipos")
    known, last_by_league = _existing(OUT_PATH)
    today = date.today()
    season_start = date.fromisoformat(CURRENT_SEASON_START)

    # 1) Scoreboards por (liga, día) — en paralelo.
    jobs = []
    for code in leagues:
        slug = ESPN_SLUGS.get(code)
        if not slug:
            continue
        start = season_start
        if last_by_league.get(code):
            start = max(season_start, date.fromisoformat(last_by_league[code]) - timedelta(days=3))
        day = start
        while day <= today + timedelta(days=days_ahead):
            jobs.append((code, slug, day))
            day += timedelta(days=1)

    def scoreboard(job):
        code, slug, day = job
        if deadline and time.monotonic() > deadline:
            return job, []
        return job, _get(slug, "scoreboard", {"dates": day.strftime("%Y%m%d")}).get("events", [])

    with ThreadPoolExecutor(max_workers=workers) as ex:
        boards = list(ex.map(scoreboard, jobs))

    finished, upcoming = [], []
    for (code, slug, day), events in boards:
        for ev in events:
            state = ((ev.get("status") or {}).get("type") or {}).get("state")
            if state == "post" and f"espn:{ev['id']}" not in known:
                finished.append((code, slug, ev))
            elif state == "pre" and day >= today:
                upcoming.append((code, slug, ev))

    # 2) Resúmenes de partidos terminados nuevos + próximos (árbitro asignado).
    def summary(item):
        code, slug, ev = item
        if deadline and time.monotonic() > deadline:
            return item, {}
        return item, _get(slug, "summary", {"event": ev["id"]})

    with ThreadPoolExecutor(max_workers=workers) as ex:
        done = list(ex.map(summary, finished))
        ahead = list(ex.map(summary, upcoming))

    rows = [r for (code, _slug, ev), s in done if s and (r := match_row(code, ev, s, teams))]
    rows.sort(key=lambda r: (r["league"], r["date"]))
    if rows:
        _append(OUT_PATH, rows)

    assignments = []
    for (code, _slug, ev), s in ahead:
        ref = _referee(s) if s else None
        if not ref:
            continue
        comp = (ev.get("competitions") or [{}])[0]
        side = {c.get("homeAway"): c.get("team") or {} for c in comp.get("competitors", [])}
        assignments.append({
            "league": code,
            "date": datetime.fromisoformat(ev["date"].replace("Z", "+00:00")).date().isoformat(),
            "home": teams.match(code, side.get("home", {}).get("displayName")) or side.get("home", {}).get("displayName"),
            "away": teams.match(code, side.get("away", {}).get("displayName")) or side.get("away", {}).get("displayName"),
            "referee": ref,
            "source": "espn",
        })
    ASSIGNMENTS_PATH.write_text(json.dumps({
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "items": assignments,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    unmatched = sorted({r[k] for r in rows for k in ("home", "away") if r[k] and not any(r[k] == key for key, _ in teams.by_league.get(r["league"], []))})
    print(f"OK ESPN árbitros: {len(jobs)} días-liga, {len(finished)} partidos nuevos, {len(rows)} con árbitro, "
          f"{len(assignments)} asignaciones próximas")
    if unmatched:
        print(f"   Equipos sin cruzar ({len(unmatched)}): {', '.join(unmatched[:15])}")
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--leagues", nargs="*", default=list(ESPN_SLUGS))
    parser.add_argument("--days-ahead", type=int, default=3)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--max-seconds", type=float, default=None)
    args = parser.parse_args()
    update(args.leagues, args.days_ahead, args.workers, args.max_seconds)


if __name__ == "__main__":
    main()
