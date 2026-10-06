"""
Apercibidos y sancionados calculados a partir de las tarjetas registradas
partido a partido (DATOS/espn_player_matches.csv).

No es el dato oficial del comité de competición: es la aplicación de la regla
de acumulación de cada liga a las tarjetas conocidas. El feed oficial/verificado
(DATOS/suspensions_manual.csv + fuentes oficiales) tiene prioridad cuando existe.

Reglas (temporada 2026/27). `confidence` se muestra en la UI:
- SP1/SP2 (RFEF): 1 partido cada 5 amarillas (5, 10, 15...).
- E0 (Premier League): 5 amarillas antes de que el club juegue 19 partidos → 1;
  10 antes de 32 → 2; 15 → 3.
- E1 (EFL Championship): 5 antes de 19 partidos → 1; 10 antes de 46 → 2; 15 → 3.
- D1/D2 (DFB): 5ª, 10ª y 15ª amarilla → 1 partido.
- I1/I2 (Lega): 5ª, 10ª, 14ª, 17ª y cada una a partir de ahí → 1 partido.
- F1/F2 (LFP): 3 amarillas en un periodo de 10 partidos del club → 1 partido.
- N1 (KNVB): 5ª, 10ª, 15ª amarilla → 1 partido (regla simplificada).
- Doble amarilla → 1 partido (esas amarillas no acumulan). Roja directa → al
  menos 1 partido (la duración la fija el comité).
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

RULES: dict[str, dict[str, Any]] = {
    "SP1": {"type": "cycle", "every": 5, "confidence": "alta", "text": "1 partido cada 5 amarillas"},
    "SP2": {"type": "cycle", "every": 5, "confidence": "alta", "text": "1 partido cada 5 amarillas"},
    "D1": {"type": "list", "at": [5, 10, 15], "confidence": "alta", "text": "5ª, 10ª y 15ª amarilla: 1 partido"},
    "D2": {"type": "list", "at": [5, 10, 15], "confidence": "alta", "text": "5ª, 10ª y 15ª amarilla: 1 partido"},
    "E0": {"type": "england", "steps": [(5, 19, 1), (10, 32, 2), (15, None, 3)], "confidence": "alta",
           "text": "5 amarillas antes de la jornada 19: 1 partido · 10 antes de la 32: 2 · 15: 3"},
    "E1": {"type": "england", "steps": [(5, 19, 1), (10, 46, 2), (15, None, 3)], "confidence": "alta",
           "text": "5 amarillas antes del partido 19: 1 partido · 10 antes del 46: 2 · 15: 3"},
    "I1": {"type": "list_then_each", "at": [5, 10, 14, 17], "confidence": "media",
           "text": "5ª, 10ª, 14ª, 17ª y cada amarilla posterior: 1 partido"},
    "I2": {"type": "list_then_each", "at": [5, 10, 14, 17], "confidence": "media",
           "text": "5ª, 10ª, 14ª, 17ª y cada amarilla posterior: 1 partido"},
    "F1": {"type": "window", "cards": 3, "matches": 10, "confidence": "media",
           "text": "3 amarillas en 10 partidos: 1 partido"},
    "F2": {"type": "window", "cards": 3, "matches": 10, "confidence": "media",
           "text": "3 amarillas en 10 partidos: 1 partido"},
    "N1": {"type": "list", "at": [5, 10, 15], "confidence": "media", "text": "5ª, 10ª y 15ª amarilla: 1 partido"},
    "CL": {"type": "odd_from", "first": 3, "confidence": "alta",
           "text": "3ª amarilla y cada amarilla impar posterior (5ª, 7ª…): 1 partido"},
}


def _thresholds(rule: dict, upto: int) -> list[int]:
    t = rule["type"]
    if t == "cycle":
        return list(range(rule["every"], upto + rule["every"] + 1, rule["every"]))
    if t == "list":
        return list(rule["at"])
    if t == "list_then_each":
        last = rule["at"][-1]
        return list(rule["at"]) + list(range(last + 1, max(upto, last) + 2))
    if t == "odd_from":
        return list(range(rule["first"], upto + 3, 2))
    return []


def _next_threshold(rule: dict, yellows: int, club_played: int) -> tuple[int | None, int]:
    """(próximo umbral, partidos de sanción) desde el recuento actual."""
    if rule["type"] == "england":
        for cards, before, ban in rule["steps"]:
            if yellows < cards and (before is None or club_played < before):
                return cards, ban
        return None, 0
    for th in _thresholds(rule, yellows + 1):
        if th > yellows:
            return th, 1
    return None, 0


def compute_discipline(rows: list[dict], upcoming: list[dict] | None = None,
                       today: str | None = None) -> list[dict]:
    """rows: filas jugador-partido (league, event_id, date, team, opponent, venue,
    player_id, player, crdy, crdr, red_type). Devuelve items con status
    "suspended" (se pierde el próximo partido) o "at_risk" (a una amarilla)."""
    # Calendario jugado por equipo y competición (para contar partidos cumplidos).
    team_matches: dict[tuple, list[str]] = defaultdict(list)
    seen = set()
    for r in rows:
        key = (r["league"], r["team"], r["event_id"])
        if key not in seen:
            seen.add(key)
            team_matches[(r["league"], r["team"])].append(r["date"])
    for k in team_matches:
        team_matches[k].sort()

    upcoming_by_team: dict[tuple, list[dict]] = defaultdict(list)
    for f in sorted(upcoming or [], key=lambda f: (f.get("date", ""), f.get("time", ""))):
        if today and f.get("date", "") < today:
            continue
        for side, opp in (("home", "away"), ("away", "home")):
            upcoming_by_team[(f.get("league"), f.get(side))].append({
                "date": f.get("date"), "time": f.get("time") or "", "opponent": f.get(opp),
                "venue": "H" if side == "home" else "A",
            })

    by_player: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        if r["league"] in RULES:
            by_player[(r["league"], r["player_id"])].append(r)

    items = []
    for (league, pid), matches in by_player.items():
        rule = RULES[league]
        matches.sort(key=lambda r: (r["date"], r["event_id"]))
        team = matches[-1]["team"]
        name = matches[-1]["player"]
        played_dates = team_matches[(league, team)]
        yellows = 0
        window_dates: list[str] = []          # amarillas vigentes (regla de ventana)
        bans: list[dict] = []
        for m in matches:
            y = int(float(m.get("crdy") or 0))
            red = int(float(m.get("crdr") or 0))
            red_type = m.get("red_type") or ("direct" if red else "")
            before = yellows
            yellows += y
            club_played = sum(1 for d in team_matches[(league, m["team"])] if d <= m["date"])
            if rule["type"] == "england":
                for cards, cutoff, ban in rule["steps"]:
                    if before < cards <= yellows and (cutoff is None or club_played <= cutoff):
                        bans.append({"date": m["date"], "matches": ban, "reason": f"{cards}ª amarilla",
                                     "opponent": m.get("opponent"), "team": m["team"]})
            elif rule["type"] == "window":
                club = team_matches[(league, m["team"])]
                idx = {d: i for i, d in enumerate(club)}
                for _ in range(y):
                    window_dates.append(m["date"])
                cur = idx.get(m["date"], 0)
                window_dates = [d for d in window_dates if cur - idx.get(d, cur) < rule["matches"]]
                if len(window_dates) >= rule["cards"]:
                    bans.append({"date": m["date"], "matches": 1,
                                 "reason": f"{rule['cards']} amarillas en {rule['matches']} partidos",
                                 "opponent": m.get("opponent"), "team": m["team"]})
                    window_dates = []
            else:
                for th in _thresholds(rule, yellows):
                    if before < th <= yellows:
                        bans.append({"date": m["date"], "matches": 1, "reason": f"{th}ª amarilla",
                                     "opponent": m.get("opponent"), "team": m["team"]})
            if red:
                bans.append({"date": m["date"], "matches": 1,
                             "reason": "doble amarilla" if red_type == "2y" else "roja directa",
                             "min_only": red_type != "2y", "opponent": m.get("opponent"), "team": m["team"]})

        base = {
            "player": name, "player_id": pid, "team": team, "league": league,
            "cards": yellows, "rule": rule["text"], "confidence": rule["confidence"],
            "source_name": "Calculado por KICKDEX (tarjetas registradas)", "source": "calculated",
            "official": False, "verified": False,
        }
        # ¿Sanción pendiente? Partidos del club en la competición tras la expulsión/acumulación.
        pending = None
        for ban in bans:
            if ban["team"] != team:
                continue
            served = sum(1 for d in played_dates if d > ban["date"])
            if served < ban["matches"]:
                pending = {**ban, "remaining": ban["matches"] - served}
        if not pending and bans and bans[-1]["team"] == team:
            # Sanción ya cumplida: no se muestra, pero sirve para descartar
            # avisos oficiales desfasados (artículos sin fecha).
            items.append({**base, "status": "served", "status_label": "Cumplida",
                          "reason": bans[-1]["reason"], "trigger_date": bans[-1]["date"]})
        if pending:
            misses = upcoming_by_team.get((league, team), [])[: pending["remaining"]]
            items.append({**base, "status": "suspended", "status_label": "Sancionado",
                          "reason": pending["reason"], "ban_matches": pending["matches"],
                          "remaining": pending["remaining"], "min_only": pending.get("min_only", False),
                          "trigger_date": pending["date"], "trigger_opponent": pending.get("opponent"),
                          "misses": misses, "threshold": None})
            continue

        if rule["type"] == "window":
            if len(window_dates) == rule["cards"] - 1:
                items.append({**base, "status": "at_risk", "status_label": "Apercibido",
                              "threshold": rule["cards"], "ban_matches": 1,
                              "window_cards": len(window_dates),
                              "next": (upcoming_by_team.get((league, team)) or [None])[0]})
            continue
        nxt, ban = _next_threshold(rule, yellows, len(played_dates))
        if nxt is not None and yellows == nxt - 1:
            items.append({**base, "status": "at_risk", "status_label": "Apercibido",
                          "threshold": nxt, "ban_matches": ban,
                          "next": (upcoming_by_team.get((league, team)) or [None])[0]})
    items.sort(key=lambda i: (i["league"], i["team"], i["status"] != "suspended", i["player"]))
    return items
