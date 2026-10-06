"""
Datos diarios desde el marcador público de ESPN (funciona desde GitHub Actions):
árbitros por partido, estadísticas por jugador y partido, próximos partidos y
mapa de equipos. Una sola pasada por los resúmenes de partido.

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
5. Del mismo resumen sale una fila por jugador que jugó (DATOS/espn_player_matches.csv):
   goles, asistencias, tiros, tiros a puerta, faltas, tarjetas y minutos
   (calculados con los cambios y expulsiones). Es la fuente de players.json.
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
UPCOMING_PATH = Path(DATA_DIR) / "espn_upcoming.json"
PLAYERS_PATH = Path(DATA_DIR) / "espn_player_matches.csv"
SYNC_PATH = Path(DATA_DIR) / "espn_sync.json"
STANDINGS_PATH = Path(DATA_DIR) / "espn_standings.json"
STANDINGS_URL = "https://site.api.espn.com/apis/v2/sports/soccer/{slug}/standings"
PLAYER_FIELDNAMES = [
    "event_id", "date", "league", "team", "opponent", "venue", "player_id", "player", "position",
    "starter", "minutes", "gls", "ast", "sh", "sot", "fls", "fld", "crdy", "crdr", "og", "saves", "gc",
]
PLAYER_STATS = {  # columna -> stat de ESPN
    "gls": "totalGoals", "ast": "goalAssists", "sh": "totalShots", "sot": "shotsOnTarget",
    "fls": "foulsCommitted", "fld": "foulsSuffered", "crdy": "yellowCards", "crdr": "redCards",
    "og": "ownGoals", "saves": "saves", "gc": "goalsConceded",
}
MATCH_MINUTES = 90
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


def _existing_players(path: Path) -> tuple[set[str], dict[str, str]]:
    ids: set[str] = set()
    last: dict[str, str] = {}
    if not path.exists():
        return ids, last
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ids.add(str(row.get("event_id")))
            lg, d = row.get("league", ""), row.get("date", "")
            if d > last.get(lg, ""):
                last[lg] = d
    return ids, last


def _append_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        if new_file:
            writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})


def _append(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        if new_file:
            writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in FIELDNAMES})


def _minute(event: dict[str, Any]) -> int | None:
    clock = event.get("clock") or {}
    try:
        return int(float(clock.get("value")) // 60)
    except (TypeError, ValueError):
        m = re.match(r"(\d+)", str(clock.get("displayValue") or ""))
        return int(m.group(1)) if m else None


def player_rows(league: str, event: dict[str, Any], summary: dict[str, Any], id_to_key: dict[str, str],
                teams: TeamMatcher) -> list[dict[str, Any]]:
    """Una fila por jugador que jugó. Minutos: titular 0→90, cambios y rojas
    con su minuto (ESPN no da minutos jugados directamente)."""
    rosters = summary.get("rosters") or []
    if len(rosters) != 2:
        return []
    sub_in: dict[str, int] = {}
    sub_out: dict[str, int] = {}
    sent_off: dict[str, int] = {}
    for k in summary.get("keyEvents") or []:
        kind = str((k.get("type") or {}).get("text", "")).lower()
        minute = _minute(k)
        parts = [str(((p or {}).get("athlete") or {}).get("id") or "") for p in k.get("participants") or []]
        if minute is None or not parts:
            continue
        minute = min(minute, MATCH_MINUTES)
        if kind == "substitution" and len(parts) >= 2:
            sub_in[parts[0]] = minute
            sub_out[parts[1]] = minute
        elif kind == "red card":
            sent_off[parts[0]] = minute

    def team_key(team: dict[str, Any]) -> str:
        return id_to_key.get(str(team.get("id"))) or teams.match(league, team.get("displayName"), team.get("location")) \
            or team.get("displayName", "")

    keys = [team_key(r.get("team") or {}) for r in rosters]
    kickoff = datetime.fromisoformat(event["date"].replace("Z", "+00:00"))
    rows = []
    for idx, side in enumerate(rosters):
        for entry in side.get("roster") or []:
            athlete = entry.get("athlete") or {}
            pid = str(athlete.get("id") or "")
            stats = {s.get("name"): s.get("displayValue") for s in entry.get("stats") or []}
            played = entry.get("starter") or entry.get("subbedIn") or str(stats.get("appearances", "0")) not in ("0", "")
            if not pid or not played:
                continue
            start = 0 if entry.get("starter") else sub_in.get(pid)
            if start is None:
                start = MATCH_MINUTES  # entró pero sin minuto conocido: 0 min estimados
            end = min(sub_out.get(pid, MATCH_MINUTES), sent_off.get(pid, MATCH_MINUTES))
            row = {
                "event_id": event["id"],
                "date": kickoff.date().isoformat(),
                "league": league,
                "team": keys[idx],
                "opponent": keys[1 - idx],
                "venue": "H" if side.get("homeAway") == "home" else "A",
                "player_id": pid,
                "player": athlete.get("displayName") or athlete.get("fullName") or "",
                "position": (entry.get("position") or {}).get("abbreviation", ""),
                "starter": 1 if entry.get("starter") else 0,
                "minutes": max(0, end - start),
            }
            for col, stat in PLAYER_STATS.items():
                try:
                    row[col] = int(float(stats.get(stat))) if stats.get(stat) not in (None, "") else ""
                except (TypeError, ValueError):
                    row[col] = ""
            rows.append(row)
    return rows


def write_team_map(teams: TeamMatcher, leagues: list[str]) -> int:
    """{liga: {id ESPN: clave canónica}} para el Directo (cruce exacto por id
    en vez de por nombre en el navegador)."""
    # Se parte del mapa anterior: si ESPN responde a medias en una ejecución,
    # no se pierden equipos (pasó: 142 de 216 con la API lenta).
    try:
        out = json.loads(TEAM_MAP_PATH.read_text(encoding="utf-8")).get("leagues", {})
    except (OSError, ValueError):
        out = {}
    out = {code: dict(v) for code, v in out.items()}
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
    return out


def zone_for(description: str | None) -> str:
    """Nota de zona de ESPN → zona de la UI (ver standings.js)."""
    d = str(description or "").lower()
    if not d:
        return ""
    if "relegation" in d:
        return "relpo" if "playoff" in d else "rel"
    if "promotion" in d:
        return "po" if "playoff" in d else "promo"
    if "champions league" in d:
        return "uclq" if "qualif" in d else "ucl"
    if "europa league" in d:
        return "uel"
    if "conference league" in d:
        return "uecl"
    return ""


def fetch_standings(leagues: list[str], team_map: dict[str, dict[str, str]], teams: TeamMatcher) -> dict[str, Any]:
    """Clasificación de cada liga (contrato de standings.json + zona por fila)."""
    out: dict[str, Any] = {}
    for code in leagues:
        slug = ESPN_SLUGS.get(code)
        try:
            r = requests.get(STANDINGS_URL.format(slug=slug), headers=HEADERS, timeout=20)
            data = r.json() if r.status_code == 200 else {}
        except (requests.RequestException, ValueError):
            data = {}
        children = data.get("children") or []
        entries = ((children[0] if children else {}).get("standings") or {}).get("entries") or []
        if not entries:
            continue
        table = []
        for e in entries:
            t = e.get("team") or {}
            st = {x.get("name"): x.get("value") for x in e.get("stats") or []}
            key = team_map.get(code, {}).get(str(t.get("id"))) or teams.match(code, t.get("displayName"), t.get("location")) \
                or t.get("displayName")
            num = lambda k: int(st[k]) if st.get(k) is not None else None
            table.append({
                "position": num("rank"), "team": key, "played": num("gamesPlayed"),
                "won": num("wins"), "draw": num("ties"), "lost": num("losses"),
                "goals_for": num("pointsFor"), "goals_against": num("pointsAgainst"),
                "goal_diff": num("pointDifferential"), "points": num("points"),
                "form": None, "zone": zone_for((e.get("note") or {}).get("description")),
                "zone_label": (e.get("note") or {}).get("description"),
            })
        table.sort(key=lambda x: (x["position"] or 99))
        out[code] = {
            "competition_name": (children[0] if children else {}).get("name"),
            "matchday": max((x["played"] or 0) for x in table),
            "source": "espn",
            "table": table,
        }
    STANDINGS_PATH.write_text(json.dumps({
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "leagues": out,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def fixture_item(code: str, ev: dict[str, Any], teams: TeamMatcher) -> dict[str, Any] | None:
    """Partido programado → contrato de fixtures.json (fecha/hora en Madrid)."""
    from zoneinfo import ZoneInfo

    comp = (ev.get("competitions") or [{}])[0]
    side = {c.get("homeAway"): c.get("team") or {} for c in comp.get("competitors", [])}
    home, away = side.get("home"), side.get("away")
    if not home or not away:
        return None
    kickoff = datetime.fromisoformat(ev["date"].replace("Z", "+00:00"))
    local = kickoff.astimezone(ZoneInfo("Europe/Madrid"))
    time_ok = comp.get("timeValid", True) and (kickoff.hour, kickoff.minute) != (0, 0)
    return {
        "league": code,
        "league_name": LEAGUES.get(code, code),
        "date": local.date().isoformat() if time_ok else kickoff.date().isoformat(),
        "time": local.strftime("%H:%M") if time_ok else "",
        "home": teams.match(code, home.get("displayName"), home.get("shortDisplayName"), home.get("location")) or home.get("displayName"),
        "away": teams.match(code, away.get("displayName"), away.get("shortDisplayName"), away.get("location")) or away.get("displayName"),
        "venue": (comp.get("venue") or {}).get("fullName", ""),
        "status": "scheduled",
        "source": "ESPN",
    }


def update(leagues: list[str], days_ahead: int = 3, workers: int = 8, max_seconds: float | None = None,
           fixture_days: int = 21) -> int:
    deadline = time.monotonic() + max_seconds if max_seconds else None
    teams = TeamMatcher()
    team_map = write_team_map(teams, leagues)
    print(f"OK mapa ESPN→equipos: {sum(len(v) for v in team_map.values())} equipos")
    standings = fetch_standings(leagues, team_map, teams)
    print(f"OK clasificaciones ESPN: {len(standings)} ligas")
    known, last_by_league = _existing(OUT_PATH)
    known_players, last_players = _existing_players(PLAYERS_PATH)
    # La ventana empieza en la fecha más antigua pendiente de árbitros o jugadores.
    for code in leagues:
        a, b = last_by_league.get(code), last_players.get(code)
        last_by_league[code] = min(a, b) if a and b else ""
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
        # Hasta `fixture_days` vista: calendario de las ligas sin FixtureDownload.
        while day <= today + timedelta(days=max(days_ahead, fixture_days)):
            jobs.append((code, slug, day))
            day += timedelta(days=1)

    def scoreboard(job):
        code, slug, day = job
        if deadline and time.monotonic() > deadline:
            return job, []
        return job, _get(slug, "scoreboard", {"dates": day.strftime("%Y%m%d")}).get("events", [])

    with ThreadPoolExecutor(max_workers=workers) as ex:
        boards = list(ex.map(scoreboard, jobs))

    finished, upcoming, fixtures = [], [], []
    for (code, slug, day), events in boards:
        for ev in events:
            state = ((ev.get("status") or {}).get("type") or {}).get("state")
            if state == "post" and (f"espn:{ev['id']}" not in known or str(ev["id"]) not in known_players):
                finished.append((code, slug, ev))
            elif state == "pre" and day >= today:
                if day <= today + timedelta(days=days_ahead):
                    upcoming.append((code, slug, ev))
                item = fixture_item(code, ev, teams)
                if item:
                    fixtures.append(item)
    if fixtures:
        UPCOMING_PATH.write_text(json.dumps({
            "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "items": sorted(fixtures, key=lambda f: (f["date"], f["time"], f["league"])),
        }, ensure_ascii=False, indent=1), encoding="utf-8")

    # 2) Resúmenes de partidos terminados nuevos + próximos (árbitro asignado).
    def summary(item):
        code, slug, ev = item
        if deadline and time.monotonic() > deadline:
            return item, {}
        return item, _get(slug, "summary", {"event": ev["id"]})

    with ThreadPoolExecutor(max_workers=workers) as ex:
        done = list(ex.map(summary, finished))
        ahead = list(ex.map(summary, upcoming))

    rows = [r for (code, _slug, ev), s in done
            if s and f"espn:{ev['id']}" not in known and (r := match_row(code, ev, s, teams))]
    rows.sort(key=lambda r: (r["league"], r["date"]))
    if rows:
        _append(OUT_PATH, rows)

    prows = []
    for (code, _slug, ev), s in done:
        if s and str(ev["id"]) not in known_players:
            prows.extend(player_rows(code, ev, s, team_map.get(code, {}), teams))
    prows.sort(key=lambda r: (r["league"], r["date"], r["team"]))
    if prows:
        _append_csv(PLAYERS_PATH, prows, PLAYER_FIELDNAMES)

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

    SYNC_PATH.write_text(json.dumps({
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scoreboards": len(jobs), "new_matches": len(finished),
        "referee_rows": len(rows), "player_rows": len(prows), "upcoming": len(fixtures),
        "complete": not (deadline and time.monotonic() > deadline),
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    unmatched = sorted({r[k] for r in rows for k in ("home", "away") if r[k] and not any(r[k] == key for key, _ in teams.by_league.get(r["league"], []))})
    print(f"OK ESPN árbitros: {len(jobs)} días-liga, {len(finished)} partidos nuevos, {len(rows)} con árbitro, "
          f"{len(assignments)} asignaciones próximas, {len(fixtures)} partidos programados, "
          f"{len(prows)} filas de jugador")
    if unmatched:
        print(f"   Equipos sin cruzar ({len(unmatched)}): {', '.join(unmatched[:15])}")
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--leagues", nargs="*", default=list(ESPN_SLUGS))
    parser.add_argument("--days-ahead", type=int, default=3)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--max-seconds", type=float, default=None)
    parser.add_argument("--fixture-days", type=int, default=21)
    args = parser.parse_args()
    update(args.leagues, args.days_ahead, args.workers, args.max_seconds, args.fixture_days)


if __name__ == "__main__":
    main()
