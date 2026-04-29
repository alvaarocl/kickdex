# KICKDEX — The Football Data Terminal

**Terminal gratuito de estadísticas de fútbol.** Comparador de equipos, H2H histórico, scouting de jugadores y datos de ligas europeas.

Free, independent, math-first.

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

---

## Disclaimer

KICKDEX proporciona análisis histórico y modelos estadísticos informativos, no garantías de resultados futuros.
