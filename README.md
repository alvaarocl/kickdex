# ⚽ Analista Pro

**Herramienta gratuita de Big Data futbolístico** — alternativa a ValueStats.com.

Cruza estadísticas avanzadas con cuotas históricas de Bet365 para identificar Value Bets, analizar jugadores para Fantasy y comparar equipos con datos reales desde 2004.

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

---

## 🚀 Arranque Rápido

```bash
pip install -r requirements.txt
streamlit run main.py
```

La app se abre en `http://localhost:8501`

---

## 📁 Estructura

```
analista-pro/
├── main.py                  ← Punto de entrada único
├── app/
│   ├── config.py            ← Configuración centralizada (temporada, ligas)
│   ├── data/
│   │   ├── loader.py        ← Carga y normalización de CSVs
│   │   └── updater.py       ← Descarga automática desde football-data.co.uk
│   ├── engine/
│   │   ├── metrics.py       ← Rolling metrics, forma reciente, H2H
│   │   ├── probability.py   ← Modelo Poisson para probabilidades
│   │   ├── smart_alerts.py  ← Generador de tendencias en lenguaje natural
│   │   └── value_detector.py← Detección de Value Bets con EV real
│   └── ui/
│       ├── styles.py        ← CSS modo oscuro
│       ├── comparador.py    ← Tab: comparativa de partido
│       ├── h2h.py           ← Tab: historial H2H
│       ├── jugadores.py     ← Tab: player scouting
│       └── valor.py         ← Tab: value detection
├── tests/                   ← Tests unitarios (pytest)
├── datos/                   ← CSVs (descargados automáticamente)
└── .streamlit/config.toml   ← Tema oscuro
```

---

## 🔧 Cambiar de Temporada

En `app/config.py`:

```python
CURRENT_SEASON_CODE = "2627"      # Nuevo código de temporada
CURRENT_SEASON_START = "2026-08-01"  # Fecha de inicio
CURRENT_SEASON_LABEL = "2026/27"
```

---

## 🧪 Tests

```bash
pytest tests/ -v
```

---

## 🌐 Deploy (Railway + Dominio Custom)

1. Fork este repo en GitHub
2. Ve a [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Selecciona este repo
4. Railway detecta `railway.json` automáticamente
5. **Dominio custom:** Settings → Custom Domain → `analista.alvarocarpintero.com`
6. Añade en tu DNS (alvarocarpintero.com): `CNAME analista → tu-app.railway.app`

---

## 📊 Fuentes de Datos

- **Resultados históricos:** [football-data.co.uk](https://www.football-data.co.uk) (gratuito, SP1 + SP2 desde 2004)
- **Stats de jugadores:** FBref via [soccerdata](https://github.com/probberechts/soccerdata)

---

## ⚠️ Disclaimer

Las apuestas conllevan riesgo. Analista Pro proporciona análisis histórico, no garantías de resultados futuros. Si el juego te causa problemas, llama al **900 200 225** (gratuito, 24h).
