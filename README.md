# KICKDEX — Football intelligence, indexed.

**La terminal de inteligencia futbolística.** Comparador de equipos, H2H histórico, scouting de jugadores y detección de edge en cuotas de ligas europeas.

> NO LOGIN. NO ADS. NO PICKS.

Brand system V3 → ver `brand/BRAND_GUIDE.md`.

---

## Arquitectura

KICKDEX es **estático-first**: el producto público es la carpeta `docs/`, servida por GitHub Pages en `kickdex.alvarocarpintero.com`. El backend Python en `app/` es un **pipeline batch**, no un servidor en producción.

```
CSVs (football-data.co.uk, FBref) ──► app/data + app/engine ──► scripts/build_data.py ──► docs/data/*.json ──► docs/ (GitHub Pages)
```

El cron diario en `.github/workflows/` ejecuta el pipeline y commitea los JSONs.

---

## Arranque local (frontend)

Sin dependencias:

```bash
cd docs && python -m http.server 8080
# → http://localhost:8080
```

## Regenerar datos

```bash
pip install -r requirements.txt
python scripts/build_data.py
```

Saltar descargas para iterar rápido:

```bash
KICKDEX_SKIP_DOWNLOADS=1 KICKDEX_SKIP_PLAYER_DOWNLOADS=1 python scripts/build_data.py
```

---

## Estructura

```
kickdex/
├── docs/                    ← Producto público (GitHub Pages)
│   ├── index.html           ← App SPA + landing
│   ├── methodology.html     ← Cómo funciona el modelo
│   ├── coverage.html        ← Qué ligas cubrimos
│   ├── report.html          ← Match report PDF (light mode)
│   ├── og.html              ← Plantilla OG navegable
│   ├── og.png               ← OG estático para previews
│   ├── robots.txt + sitemap.xml
│   ├── brand/               ← Logos SVG + brand guide
│   ├── css/app.css          ← Sistema V3 (Edge Number, terminal-status, brand mark)
│   ├── js/                  ← Vanilla JS modular (sin frameworks)
│   │   ├── app.js           ← Core: i18n, tabs, datos, hero edge wiring
│   │   ├── edge.js          ← Componente Edge Number (auto-mount)
│   │   ├── inicio.js, comparador.js, h2h.js, jugadores.js, arbitros.js
│   │   └── animations.js
│   └── data/                ← JSONs generados (no editar a mano)
│       ├── meta.json, leagues.json, teams.json
│       ├── fixtures.json, team_stats.json, h2h.json
│       ├── players.json, players_detail.json, player_coverage.json
│       ├── referees.json, data_status.json
│       └── edges.json       ← Edges Bet365 (closing odds)
├── app/
│   ├── data/{loader,updater}.py    ← Carga y descarga de CSVs
│   ├── engine/
│   │   ├── probability.py          ← Poisson bivariante + Dixon-Coles
│   │   ├── metrics.py              ← Forma reciente, H2H, rolling
│   │   ├── smart_alerts.py         ← Tendencias en lenguaje natural
│   │   └── edge.py                 ← implied_probability, calculate_edge
│   └── og.py                       ← Renderer Pillow para OG
├── scripts/build_data.py           ← Pipeline CSV → docs/data/*.json
├── tests/                          ← pytest
├── DATOS/                          ← CSVs históricos
├── AGENTS.md                       ← Guía para agentes IA (puntero a CLAUDE.md)
├── CLAUDE.md                       ← Playbook compartido (sprints, brand, voice)
└── MVP_BACKLOG.md                  ← Backlog priorizado y trackeable
```

---

## Cambiar de temporada

En `app/config.py`:

```python
CURRENT_SEASON_CODE = "2627"
CURRENT_SEASON_START = "2026-08-01"
CURRENT_SEASON_LABEL = "2026/27"
```

---

## Tests

```bash
pytest tests/ -v
```

---

## Fuentes de datos

- **Resultados históricos:** [football-data.co.uk](https://www.football-data.co.uk) (gratuito, SP1 + SP2 desde 2004)
- **Stats de jugadores:** FBref via [soccerdata](https://github.com/probberechts/soccerdata)
- **Árbitros:** World Soccer Data actualiza `DATOS/referees_season.csv` en el workflow para la vista de temporada actual; football-data/manual quedan como histórico/fallback. Si configuras `APIFOOTBALL_KEY`, el workflow también intenta añadir partidos recientes a `DATOS/referees_matches.csv`.

---

## Generar OG images

Cada partido puede tener su PNG Open Graph dinámico:

```bash
python -m app.og --home "Real Madrid" --away "Barcelona" \
                 --edge 12.8 --league "LA LIGA · J30" \
                 --caption "Real Madrid · ML · Bet365 1.92"
```

Se guarda en `docs/og/<home>-vs-<away>.png`. Para previsualización web sin servidor: abre `docs/og.html?home=...&away=...&edge=12.8`.

Para fuentes correctas en el render Pillow, coloca los TTF en `app/fonts/` (`IBMPlexMono-Bold.ttf`, `IBMPlexMono-Medium.ttf`).

## Match Report PDF

`docs/report.html?home=...&away=...&edge=...&caption=...&league=...` genera un report en light mode con botón "Export PDF" (html2canvas + jsPDF, todo en cliente).

## Disclaimer

> RISK NOTICE: edges are estimates, not guarantees. Play responsibly.

KICKDEX proporciona análisis histórico y modelos estadísticos informativos, no garantías de resultados futuros.
