# KICKDEX — Football intelligence, indexed.

**La terminal de inteligencia futbolística.** Comparador de equipos, H2H histórico, scouting de jugadores y detección de edge en cuotas de ligas europeas.

> NO LOGIN. NO ADS. NO PICKS.

Brand system V3 → ver `brand/BRAND_GUIDE.md`.

---

## Arranque rápido (backend Streamlit)

```bash
pip install -r requirements.txt
streamlit run main.py
```

La app se abre en `http://localhost:8501`

**Frontend estático:** abre `docs/index.html` directamente en el navegador, o despliega via GitHub Pages.

---

## Estructura

```
kickdex/
├── docs/                    ← Frontend estático (GitHub Pages)
│   ├── index.html           ← App principal
│   ├── css/app.css          ← Sistema de diseño KICKDEX
│   ├── js/                  ← Módulos JS (comparador, h2h, jugadores, árbitros)
│   └── data/                ← JSON endpoints (generados por scripts/build_data.py)
├── main.py                  ← Punto de entrada Streamlit
├── app/
│   ├── config.py            ← Configuración centralizada (temporada, ligas, colores)
│   ├── data/
│   │   ├── loader.py        ← Carga y normalización de CSVs
│   │   └── updater.py       ← Descarga automática desde football-data.co.uk
│   ├── engine/
│   │   ├── metrics.py       ← Rolling metrics, forma reciente, H2H
│   │   ├── probability.py   ← Modelo Poisson para probabilidades
│   │   └── smart_alerts.py  ← Generador de tendencias en lenguaje natural
│   └── ui/
│       ├── styles.py        ← CSS modo oscuro Streamlit
│       ├── comparador.py    ← Tab: comparativa de partido
│       ├── h2h.py           ← Tab: historial H2H
│       ├── jugadores.py     ← Tab: player scouting
│       └── arbitros.py      ← Tab: perfiles disciplinarios
├── scripts/build_data.py    ← Pipeline: CSV → JSON para el frontend
├── tests/                   ← Tests unitarios (pytest)
├── datos/                   ← CSVs históricos (descargados automáticamente)
├── REBRANDING.md            ← Estudio de marca completo
└── .streamlit/config.toml  ← Tema oscuro Streamlit
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
