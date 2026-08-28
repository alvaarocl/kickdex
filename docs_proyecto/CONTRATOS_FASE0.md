# Contratos de datos — Fase 0 (fixture-first)

Formas nuevas/modificadas que producen `scripts/build_data.py` + `app/engine/*`
y que consumirán las Fases 1-2. Generado tras la Fase 0.

---

## 1. `team_stats.json` — bloque `hit_rates` (NUEVO)

Por equipo, dentro del objeto de equipo, junto a `home`/`away`:

```json
"AZ Alkmaar": {
  "home": { ...medias existentes... },
  "away": { ... },
  "hit_rates": {
    "home": {
      "l5":  { "goals_over_25": {"hits": 3, "total": 5,  "rate": 0.6}, ... },
      "l10": { "goals_over_25": {"hits": 5, "total": 10, "rate": 0.5}, ... },
      "l20": { "goals_over_25": {"hits": 12,"total": 20, "rate": 0.6}, ... },
      "all": { "goals_over_25": {"hits": 228,"total": 366,"rate": 0.623}, ... }
    },
    "away": { "l5": {...}, "l10": {...}, "l20": {...}, "all": {...} }
  }
}
```

- Ventanas: `l5`, `l10`, `l20`, `all`. Si el equipo tiene menos partidos que la
  ventana, `total` refleja los reales (nunca se rellena).
- Cada métrica es `{hits:int, total:int, rate:float}` con `rate = hits/total` a 3 decimales.
- **15 métricas** por ventana:
  `goals_over_05/15/25/35`, `btts`, `clean_sheet` (el equipo no encaja),
  `team_no_score` (el equipo no marca), `team_over_05/15` (goles marcados por el
  equipo), `corners_over_85/95`, `cards_over_35/45` (amarillas+rojas de ambos),
  `fouls_over_205/245` (faltas de ambos).
- Los 216 equipos tienen `hit_rates`. Si una liga no tiene córners/faltas en
  origen (2ª div sin esa columna), esas métricas salen con `hits:0`.

**Regla de UI (plan):** mostrar siempre el `n/N` — `62% (12/20)` — nunca el
porcentaje solo. Es el eje diferenciador frente a ValueStats (ellos fijan `/20`).

---

## 2. Probabilidad — campos nuevos

### 2a. `app/engine/probability.py` → `MatchProbabilities.as_dict()`

```json
{
  "home": 0.81, "draw": 0.14, "away": 0.05,   // sin cambios
  "over25": 0.57, "btts": 0.45,               // sin cambios
  "lam_home": 2.70,   // goles esperados del modelo (local) — NUEVO
  "lam_away": 0.58,   // NUEVO
  "top_scores": [ {"score": "2-0", "prob": 0.137}, ... ],  // top 8 — NUEVO
  "ou_lines": {       // NUEVO, derivado de la misma matriz 8x8 con Dixon-Coles
    "0.5": {"over": 0.955, "under": 0.045},
    "1.5": {"over": 0.846, "under": 0.154},
    "2.5": {"over": 0.636, "under": 0.364},
    "3.5": {"over": 0.414, "under": 0.586},
    "4.5": {"over": 0.233, "under": 0.767}
  }
}
```

### 2b. `docs/js/probability.js` → retorno de `calcProbabilities()`

Mismos datos, **nombres camelCase** (uso interno, no se serializa):
`lambda_h`, `lambda_a`, `topScores`, `ouLines`. Los campos `home/draw/away/over25/btts` sin cambios.

- `top_scores` / `ou_lines` se calculan **antes** del blend H2H (el blend solo
  ajusta 1X2, no la matriz de goles). Python y JS coinciden en esto.
- **Corrección al inventario previo:** `probability.js` YA implementaba
  Dixon-Coles. No había divergencia estructural con Python.

---

## 3. `alerts.json` (NUEVO — antes no existía)

`smart_alerts.generate_alerts()` conectado al build vía `_write_alerts_json()`.

```json
{
  "updated_at": "2026-08-28T10:00:00Z",
  "matches": {
    "SP1|2026-08-28|Santander|Elche": [
      {
        "type": "GOALS",            // GOALS|BTTS|OVER_UNDER|CARDS|CORNERS|FORM|DEFENSE|H2H|CLEAN_SHEET
        "strength": "MEDIUM",       // HIGH|MEDIUM|LOW
        "text": "Local promedia 2.1 goles por partido como local (...)",
        "emoji": "🟡",              // 🟢 HIGH / 🟡 MEDIUM / ⚪ LOW
        "color": "#f0c040",
        "confidence": 0.707,
        "source": "home"            // home|away|combined|h2h
      }
    ]
  }
}
```

- Clave de partido: `"{league}|{date}|{home}|{away}"` con nombres canónicos
  (los mismos de `fixtures.json` / `team_stats.json`).
- ~152 de 160 próximos partidos tienen alertas. Los que no: sin muestra suficiente.
- `smart_alerts._clean_stats()` fuerza `None → 0.0` para equipos recién
  ascendidos (antes reventaba con `NoneType >= float`).

**Rugosidades conocidas para pulir en Fase 1/2:**
- El texto dice "Local"/"Visitante" en vez del nombre del equipo: las sub-claves
  `home`/`away` de `team_stats` no llevan campo `team`. Pasar el nombre a
  `generate_alerts` o inyectarlo en el dict antes de llamar.
- El texto dice "(últimos 60)" usando `matches_analyzed`, que con el motor
  ponderado es la muestra completa. Revisar el wording.

---

## 4. `fixtures.json` — campos `referee` (NUEVO, estructural)

Cada fixture (`recent`, `upcoming`, `calendar`) lleva ahora:

```json
{ "referee": null, "referee_yellows_per_match": null, ... }
```

- **Siempre `null` de momento.** football-data.co.uk solo asigna árbitro a
  partidos ya disputados; FixtureDownload no trae árbitro. La asignación previa
  es imposible con las fuentes actuales.
- Campo estructural para que la UI (fila de Inicio, ficha) pueda leerlo sin
  romperse. Rellenarlo requiere una fuente nueva de designaciones arbitrales
  (fuera de alcance de esta fase).
- La resolución en cliente que hacía `match.js:getAssignedReferee(f)` sigue
  siendo la única vía real hoy — no eliminarla.

---

## 5. `h2h.json` — `result` descompuesto

Cada partido del array `matches` de cada par:

```json
{
  "date": "2025-03-02",
  "home": "Santander", "away": "Elche",       // NUEVO
  "home_score": 2, "away_score": 0,            // NUEVO
  "result": "Santander 2-0 Elche",            // se mantiene (retrocompat, 1 versión)
  "league": "Segunda División"
}
```

- `docs/js/h2h.js` ya consume los campos nuevos y aplica `teamDisplayName()`.
  `parseResult()` y su regex, y las funciones muertas `initH2H`/`runH2H`,
  eliminadas.
- `buildH2HHTML(team1, team2, data, opts)` mantiene su firma — `comparador.js`
  la sigue llamando igual.

---

## Estado de validación (Fase 0)

- `python -m pytest tests -q` → **107 passed** (13 nuevos)
- `python scripts/validate_static_data.py` → **STATIC DATA OK**
- Build offline (`KICKDEX_SKIP_DOWNLOADS=1`) → exit 0, sin warnings de alertas
- `node --check` de los 10 módulos JS → OK

## Tab "Clasificación" — MANTENIDA (decisión del usuario, 2026-08-28)

Añadida fuera del plan por el agente de pipeline, pero funciona con la
`FOOTBALL_DATA_API_KEY` ya configurada (misma que `update_live_scores.py`) y
football-data.org sí sirve la temporada 2026/27. Cron diario propio
(`update_standings.py`), degrada a `enabled:false` sin key.

- Archivos: `standings.js`, `update_standings.py`, `standings.json`,
  `scorers.json`, `app/config.py` (`FOOTBALL_DATA_ORG_COMPETITION_CODES`),
  tab `#tab-clasificacion` en `index.html`, `test_standings.py`.
- Bug corregido: la columna `#` usaba `row.position` de football-data.org, que
  empata a inicio de temporada. Ahora usa el índice de fila (tabla ya ordenada).
- Reutiliza el sistema de diseño existente, sin CSS nuevo.

## `scorers.json`

Mismo contrato que `standings.json`. Por liga: `competition_name`, `scorers[]`
con `rank, player, team, goals, assists, penalties, played_matches`.
