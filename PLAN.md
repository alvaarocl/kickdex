# 🗺️ PLAN DE DESARROLLO — KICKDEX
## Plan Técnico Estructurado

**Fecha:** Abril 2026  
**Versión del Plan:** 1.0  
**Referencia:** PRD.md v1.0

---

## 0. Diagnóstico del Estado Actual

Antes de construir, hay que entender qué tenemos y qué está mal.

### ✅ Lo que existe y vale la pena mantener

| Módulo | Archivo | Por qué vale |
|--------|---------|--------------|
| Rolling Metrics (tendencia) | `data_processor.py` | Algoritmo sólido: shift(1), find_value_opportunities, tendencia calculation |
| Descarga histórica | `data_updater.py` | Funcional: descarga SP1/SP2 desde 2004 |
| Scraping jugadores | `player_engine.py` | Integración FBref via soccerdata |
| H2H histórico | `app.py` (Tab 2) | Lógica correcta, bien filtrada |

### ❌ Problemas críticos que hay que corregir

| Problema | Archivo | Impacto |
|----------|---------|---------|
| **Cuotas simuladas aleatoriamente** | `data_processor.py:115` | Los tendencia calculados con datos externos fake son inútiles y engañosos |
| **Dos apps descoordinadas** | `app.py` y `app_new.py` | 3 de 5 tabs en `app_new.py` dicen "coming soon" |
| **Fechas hardcodeadas** | `app.py:107,190` | `'2025-08-01'` deja de funcionar cada temporada |
| **Case sensitivity** | `DATOS/` vs `datos/` | Rota en Linux/Mac |
| **Sin separación de capas** | `app.py` | UI + lógica + datos mezclados en un solo archivo |
| **Sin arquitectura de módulos** | Raíz del proyecto | Todo suelto, sin estructura |
| **news_engine depende de scraping** | `news_engine.py` | Frágil, se rompe si el site cambia |
| **app_new.py `run_updater()` como `@st.cache_resource`** | `app_new.py:11` | Descarga datos en cada sesión, mata rendimiento |
| **Sin normalización de ligas** | Todos | La app no distingue SP1 de SP2 visualmente |
| **Sin tests** | Todos | Imposible detectar regresiones al cambiar código |

---

## 1. Decisión de Arquitectura: Refactorizar vs Rehacer

### Veredicto: **Refactorización radical con arquitectura nueva**

No empezamos de cero (se pierde el trabajo de data_processor.py), pero sí rehacemos la estructura completa.

```
MANTENER:   Lógica de data_processor.py (rolling metrics, tendencia detection)
REHACER:    Estructura de archivos, organización en módulos, app principal
ELIMINAR:   app_new.py (se absorbe en nueva app), news_engine.py (reemplazar)
AÑADIR:     Capa de servicios, config centralizada, tests, Smart Alerts engine
```

### Nueva Estructura de Carpetas

```
kickdex/
│
├── 📁 app/                     ← Módulos de la aplicación
│   ├── __init__.py
│   ├── config.py               ← Configuración centralizada (temporadas, fechas)
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py           ← Carga y caché de datos
│   │   ├── updater.py          ← Descarga desde football-data.co.uk
│   │   └── player_scraper.py   ← FBref via soccerdata
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── metrics.py          ← Rolling metrics, forma reciente (de data_processor.py)
│   │   ├── trend_detector.py   ← tendencia calculation (de data_processor.py)
│   │   ├── smart_alerts.py     ← Generador de frases de tendencia (NUtendenciaO)
│   │   └── probability.py      ← Cálculo de probabilidades matemáticas (NUtendenciaO)
│   └── ui/
│       ├── __init__.py
│       ├── comparador.py       ← Tab de comparativa de equipos
│       ├── h2h.py              ← Tab de historial H2H
│       ├── jugadores.py        ← Tab de player scouting
│       └── jugadores.py            ← Tab de statistical trend detection
│
├── 📁 datos/                   ← CSVs históricos (lowercase, consistente)
│   ├── SP1_0405.csv
│   ├── SP1_2526.csv
│   └── jugadores_raw.csv
│
├── 📁 tests/                   ← Tests unitarios
│   ├── test_metrics.py
│   ├── test_trend_detector.py
│   └── test_smart_alerts.py
│
├── main.py                     ← Punto de entrada único (streamlit run main.py)
├── requirements.txt
├── PRD.md
├── PLAN.md
└── README.md
```

---

## 2. Stack Tecnológico

### Fase 1 (MVP Mejorado) — Lo que usamos ahora y lo que se añade

```
BACKEND / DATA:
├── Python 3.11+
├── pandas 2.x           — Procesamiento de datos
├── numpy                — Cálculos numéricos
├── soccerdata           — Scraping FBref para jugadores
└── requests             — Descarga CSVs de football-data.co.uk

FRONTEND:
├── streamlit 1.3x+      — Dashboard principal
├── plotly               — Gráficos interactivos (añadir)
└── streamlit-extras     — Componentes adicionales (añadir)

TESTING:
└── pytest               — Tests unitarios

CONFIGURACIÓN:
└── python-dotenv        — Variables de entorno
```

### Fase 2 (Tiempo Real) — Lo que se añadirá

```
BACKEND:
├── FastAPI              — API REST para separar backend/frontend
├── SQLite → PostgreSQL  — Persistencia real
├── Redis                — Caché de datos externos en tiempo real
└── APScheduler          — Jobs de actualización automática

APIs EXTERNAS:
├── The Odds API         — Cuotas en tiempo real (gratuita: 500 req/mes)
├── API-Football         — Datos de partidos en tiempo real
└── [FBref via fbref.com]— Datos históricos avanzados (xG)

FRONTEND:
└── React + TailwindCSS  — Reemplaza Streamlit para UI de producción
```

---

## 3. Roadmap de Desarrollo — Sprints Detallados

---

### SPRINT 0: Limpieza y Fundamentos
**Duración:** 3-5 días  
**Objetivo:** Eliminar deuda técnica antes de construir encima

#### Tareas

**S0-01 — Consolidar estructura de carpetas**
- Crear estructura `app/data/`, `app/engine/`, `app/ui/`
- Renombrar `DATOS/` → `datos/` (consistente lowercase)
- Eliminar `app_new.py` (su lógica se redistribuye)
- Crear `app/__init__.py` y demás `__init__.py`

**S0-02 — Config centralizada (`app/config.py`)**
```python
# En vez de fechas hardcodeadas dispersas por el código:
CURRENT_SEASON_START = "2025-08-01"   # Solo cambiar aquí cada año
CURRENT_SEASON_CODE = "2526"
LEAGUES = {"SP1": "La Liga", "SP2": "Segunda División"}
ROLLING_WINDOW_DEFAULT = 5
```

**S0-03 — Migrar `data_processor.py` → `app/engine/metrics.py`**
- Mantener `FootballDataProcessor` (lógica válida)
- Eliminar `_ensure_odds_columns()` con datos externos random (peligroso)
- Separar `find_statistical_trends()` → `app/engine/trend_detector.py`

**S0-04 — Migrar `data_updater.py` → `app/data/updater.py`**
- Añadir encoding correcto (`latin1` para archivos antiguos)
- Añadir logging estructurado en vez de prints

**S0-05 — Crear `main.py`**
- Único punto de entrada: `streamlit run main.py`
- Eliminar confusión entre `app.py` / `app_new.py`

**Criterio de éxito:** `streamlit run main.py` arranca con la misma funcionalidad que `app.py`, sin errores, con la nueva estructura de carpetas.

---

### SPRINT 1: Data Layer Robusto
**Duración:** 5-7 días  
**Objetivo:** Base de datos sólida, limpia, confiable

#### Tareas

**S1-01 — Loader unificado (`app/data/loader.py`)**
```python
@st.cache_data(ttl=3600)  # Caché de 1 hora, no infinita
def load_matches(data_dir="datos") -> pd.DataFrame:
    """
    Carga y normaliza TODOS los CSVs.
    Garantías:
    - Encoding: intenta utf-8, fallback a latin1
    - Fechas: parser robusto, sin hardcodear formato
    - Columnas: normalización a nombres estándar
    - Sin duplicados
    """
```

**S1-02 — Normalización de nombres de equipos**
- El problema: "Atletico Madrid" / "Atlético Madrid" / "Ath Madrid" son el mismo equipo
- Solución: `TEAM_ALIASES` dict en `config.py` + función `normalize_team_name()`
- Aplicar en carga, no en pantalla

**S1-03 — Filtro de temporada dinámico**
- Eliminar `'2025-08-01'` hardcodeado
- Usar `config.CURRENT_SEASON_START` en todos los filtros
- Añadir selector de temporada en UI ("Temporada actual / Histórico")

**S1-04 — Pipeline de validación de datos**
```python
def validate_dataframe(df: pd.DataFrame) -> DataValidationResult:
    """
    Comprueba:
    - Filas sin fecha → eliminar
    - Nombres de equipo vacíos → flag
    - Columnas de goles negativas → flag
    - Duplicados exactos → eliminar
    Devuelve resultado con warnings, no lanza excepciones
    """
```

**S1-05 — Actualización inteligente de datos**
- `data_updater.py`: Añadir verificación de hash de archivo
- Si el CSV de temporada actual no ha cambiado desde ayer → no re-procesar
- Logs de última actualización en `datos/.last_update.json`

**Criterio de éxito:** Los datos cargan correctamente en <2 segundos. Equipos normalizados consistentemente. Sin datos duplicados. Tests pasando.

---

### SPRINT 2: Engine de Métricas y Smart Alerts
**Duración:** 7-10 días  
**Objetivo:** El corazón analítico de la app — métricas fiables + insights estad?sticos

#### Tareas

**S2-01 — Refactorizar `metrics.py` (de `data_processor.py`)**
- Mantener `calculate_rolling_metrics()` con shift(1) anti-leakage
- Optimizar: el loop actual es O(n*m) — usar `groupby().rolling()` de pandas
- Añadir métricas nuevas:
  - `xG_proxy`: (tiros_a_puerta * 0.35) — aproximación sin datos xG reales
  - `clean_sheets`: % partidos sin conceder
  - `btts_rate`: % partidos donde ambos marcan
  - `over25_rate`: % partidos con más de 2.5 goles

**S2-02 — `smart_alerts.py` — El Generador de Tendencias (NUtendenciaO)**

Este es uno de los módulos más valiosos del PRD. Genera frases en lenguaje natural.

```python
ALERT_TEMPLATES = [
    # Goles
    {
        "condition": lambda stats, n: stats['over25_rate_last_n'] >= 0.70,
        "text": "Más de 2.5 goles en el {pct}% de sus últimos {n} partidos",
        "type": "GOALS", "strength": "HIGH"
    },
    # BTTS
    {
        "condition": lambda stats, n: stats['btts_rate_last_n'] >= 0.65,
        "text": "Ambos equipos han marcado en el {pct}% de los últimos {n} partidos",
        "type": "BTTS", "strength": "MEDIUM"
    },
    # Tarjetas
    {
        "condition": lambda stats, n: stats['avg_cards'] >= 3.5,
        "text": "Promedio de {avg} tarjetas por partido en los últimos {n} encuentros",
        "type": "CARDS", "strength": "MEDIUM"
    },
    # Forma como local/visitante
    {
        "condition": lambda stats, n: stats['win_rate_home'] >= 0.70,
        "text": "{team} gana el {pct}% de partidos en casa",
        "type": "FORM", "strength": "HIGH"
    },
    # ... 20+ templates más
]

def generate_match_alerts(home_stats: dict, away_stats: dict, h2h_stats: dict) -> list[Alert]:
    """
    Para un partido dado, devuelve lista de alertas ordenadas por relevancia.
    Cada Alert tiene: texto, tipo, fuerza (HIGH/MEDIUM/LOW), confidence_pct
    """
```

**S2-03 — `probability.py` — Probabilidades Matemáticas (NUtendenciaO)**
```python
def calculate_match_probabilities(home_stats: dict, away_stats: dict, h2h_stats: dict) -> dict:
    """
    Calcula:
    - P(Victoria Local): Basado en forma reciente (últimos 5) + historial H2H
    - P(Empate): Derivada de los anteriores
    - P(Victoria Visitante): Basada en forma reciente visitante
    - P(Over 2.5): Basado en over25_rate de ambos equipos
    - P(BTTS): Basado en btts_rate de ambos equipos
    
    Método: Modelo de Dixon-Coles simplificado + pesos de forma reciente
    Returns: {"home": 0.45, "draw": 0.28, "away": 0.27, "over25": 0.62, "btts": 0.55}
    """
```

**S2-04 — Tests para engine (`tests/`)**
```python
# tests/test_metrics.py
def test_no_data_leakage():
    """Verificar que rolling metrics usen shift(1)"""

def test_rolling_window_5():
    """Los promedios de los últimos 5 son correctos"""

# tests/test_smart_alerts.py  
def test_over25_alert_triggers_above_70pct():
    ...

def test_btts_alert_strength():
    ...
```

**Criterio de éxito:** `pytest tests/` pasa 100%. Smart Alerts genera mínimo 3 frases relevantes para cualquier partido de La Liga.

---

### SPRINT 3: UI/UX Profesional
**Duración:** 7-10 días  
**Objetivo:** Interfaz que parezca plataformas de an?lisis estad?stico, no un script universitario

#### Tareas

**S3-01 — Layout global y tema visual**
```python
# main.py - Configuración visual
st.set_page_config(
    page_title="KICKDEX",
    layout="wide",
    page_icon="⚽",
    initial_sidebar_state="collapsed"  # Priorizar contenido
)

# CSS personalizado en modo oscuro
CUSTOM_CSS = """
<style>
    .stApp { background-color: #0e1117; }
    .metric-card { background: #1a1f2e; border-radius: 8px; padding: 16px; }
    .value-green { color: #00d4aa; font-weight: bold; }
    .value-red { color: #ff4b4b; font-weight: bold; }
    .alert-high { border-left: 3px solid #00d4aa; padding-left: 12px; }
    ...
</style>
"""
```

**S3-02 — Tab 1: Comparador de Partido (Rehacer)**

Layout objetivo:
```
┌─────────────────────────────────────────────────────┐
│  [Real Madrid]   vs   [Barcelona]      [ANALIZAR]   │
├──────────────────────┬──────────────────────────────┤
│   REAL MADRID        │        BARCELONA              │
│   (En Casa)          │        (Fuera)                │
├──────────────────────┴──────────────────────────────┤
│  ✅ 3-1 vs Atletico  │  ✅ 2-0 vs Sevilla           │
│  ✅ 2-0 vs Getafe    │  ❌ 0-1 vs Villarreal         │
│  ❌ 0-1 vs Man City  │  ✅ 3-2 vs Valencia           │
├──────────────────────┬──────────────────────────────┤
│  Goles/partido: 2.1  │  Goles/partido: 1.8           │
│  Tiros/partido: 14.2 │  Tiros/partido: 13.6          │
│  Corners/partido: 6  │  Corners/partido: 5.2         │
├──────────────────────┴──────────────────────────────┤
│  🔔 SMART ALERTS                                     │
│  🟢 Real Madrid gana el 80% en casa (últimos 10)    │
│  🟡 Más de 2.5 goles en 70% de clásicos             │
│  🟢 Ambos marcan en 75% de encuentros directos      │
├─────────────────────────────────────────────────────┤
│  📊 PROBABILIDADES MATEMÁTICAS                       │
│  🏠 Real Madrid: 52%    Empate: 25%    Barça: 23%   │
│  Over 2.5: 65%          BTTS: 60%                   │
└─────────────────────────────────────────────────────┘
```

Detalles de implementación:
- Métricas en `st.metric()` con delta (↑/↓ respecto a su promedio de temporada)
- `plotly` bar chart comparativo horizontal (radar chart opcional)
- Smart Alerts con color coding (verde/amarillo/rojo según fuerza)
- Probabilidades como progress bars con colores

**S3-03 — Tab 2: Historial H2H (Mejorar)**
- Mantener lógica actual (funciona bien)
- Añadir: resumen estadístico (X victorias locales, Y empates, Z visitante)
- Añadir: gráfico de timeline de resultados
- Añadir: datos externos históricas con tendencia

**S3-04 — Tab 3: Player Scouting (Rehacer)**

Layout objetivo:
```
┌──────────────────────────────────────────────────────┐
│  Equipo: [Real Madrid ▼]   Liga: [La Liga ▼]         │
├──────────────────────────────────────────────────────┤
│  TOP REMATADORES          │  TOP ASISTENTES           │
│  ┌────────────────────┐   │  ┌────────────────────┐  │
│  │ Mbappé      3.2 sh │   │  │ Valverde    2.1 kp │  │
│  │ Bellingham  2.8 sh │   │  │ Modric      1.8 kp │  │
│  └────────────────────┘   │  └────────────────────┘  │
├──────────────────────────────────────────────────────┤
│  BUSCADOR OPORTUNIDADES PLAYER PROPS                  │
│  Mercado: [Tiros Totales ▼]  Línea: [1.5]  Min: 70% │
│  [BUSCAR]                                             │
│  ┌──────────────────────────────────────────────────┐│
│  │ Jugador     Equipo    %Acierto  Últimos 5        ││
│  │ Mbappé      R.Madrid  85%      ✅✅✅✅✅         ││
│  └──────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────┘
```

**S3-05 — Tab 4: Value Detection (NUtendenciaO)**

Este es el diferenciador principal del PRD.

```
┌──────────────────────────────────────────────────────┐
│  🎯 RADAR DE VALUE BETS — Jornada 32                  │
├──────────────────────────────────────────────────────┤
│  Partido              Prob.Mat.  Cuota  Implied  tendencia   │
│  ──────────────────────────────────────────────────  │
│  🟢 Real Madrid (W)    52%      1.80    55.5%  +12%  │
│  🟢 Barça Over 2.5     65%      1.75    57.1%  +8%   │
│  ⚪ Atlético (W)       45%      2.10    47.6%  -3%   │
│  🔴 Sevilla (W)        25%      1.90    52.6%  -28%  │
├──────────────────────────────────────────────────────┤
│  ⚠️ Las an?lisis conllevan riesgo. Juega responsable │
└──────────────────────────────────────────────────────┘
```

Nota: Las datos externos en esta fase vienen de los CSVs históricos (datos externos de los partidos ya jugados para validar el algoritmo), no de una API en tiempo real. El objetivo de Fase 1 es validar que el algoritmo de probabilidades funciona ANTES de conectar datos externos reales.

**Criterio de éxito:** App visualmente profesional en modo oscuro. Tablas ordenables. Smart Alerts visibles y con color. Probabilidades en cada partido. Sin errores de UX obvios.

---

### SPRINT 4: Value Detection Engine
**Duración:** 5-7 días  
**Objetivo:** Motor de detección de valor funcional con datos históricos

#### Tareas

**S4-01 — Refactorizar `trend_detector.py` (de `data_processor.py`)**
- Mantener `find_statistical_trends()` — lógica sólida
- **ELIMINAR** la dependencia de datos externos simuladas — si no hay datos externos reales en el CSV, no calcular tendencia
- Añadir: filtro por temporada (solo calcular con datos de la temporada donde hay datos externos reales)
- Añadir: backtesting — "si hubieras apostado €10 en cada Value Bet, habrías ganado X"

**S4-02 — Value Score por partido**
```python
def calculate_value_score(match_row: pd.Series, team_stats: dict) -> ValueScore:
    """
    Para un partido con datos externos (B365H, B365D, B365A):
    1. Calcula probabilidades matemáticas del motor
    2. Calcula probabilidades implícitas de las datos externos
    3. Detecta discrepancias (value)
    4. Devuelve: home_value, draw_value, away_value, over25_value, btts_value
    """
```

**S4-03 — Backtesting de la temporada**
```
Usando datos históricos de temporadas con datos externos reales (SP1_2324.csv tiene B365H/D/A):
- Validar: cuando el modelo dice "Value Bet", ¿ganó el apostador históricamente?
- Mostrar en UI: "Rendimiento histórico del modelo: +X% ROI en 2023/24"
- Transparencia total — si el modelo no predice bien, que se vea
```

**Criterio de éxito:** El scanner de value funciona con datos históricos reales de temporadas anteriores (las que tienen datos externos en el CSV). ROI histórico calculado y visible en UI.

---

### SPRINT 5: Testing, Performance y Deploy
**Duración:** 5 días  
**Objetivo:** Producción lista

#### Tareas

**S5-01 — Test suite completo**
```
tests/
├── test_metrics.py       — Anti-leakage, rolling window correcto
├── test_smart_alerts.py  — Alertas se generan con las condiciones correctas
├── test_trend_detector.py — tendencia calculado correctamente
├── test_probability.py   — Probabilidades suman 100%, rango válido
├── test_data_loader.py   — Carga sin errores, normalización correcta
└── test_h2h.py           — H2H correcto, sin duplicados
```

**S5-02 — Optimización de rendimiento**
- Medir tiempo de carga actual
- Cachear agresivamente: `@st.cache_data(ttl=3600)` en carga de datos
- Pre-computar rolling metrics al cargar, no al filtrar
- Target: <1s al cambiar de equipo (actualmente puede ser 2-5s)

**S5-03 — README.md profesional**
- Instrucciones de instalación
- Instrucciones de actualización de datos
- Screenshot de la app
- Descripción de cada módulo

**S5-04 — Deploy en Streamlit Cloud** (gratuito)
- `streamlit.io/cloud` — deploy directo desde GitHub
- Configurar secrets para variables de entorno
- Workflow de actualización de datos (manual o cron)

**Criterio de éxito:** `pytest` 100% pass. Carga <1s. Deploy funcionando en URL pública.

---

## 4. Fase 2 — Tiempo Real (Plan de Alto Nivel)

Una vez el MVP funcione bien, estos son los pasos para la Fase 2.

### 4.1 Integración de The Odds API (Cuotas Reales)

```
Plan:
1. Registrarse en The Odds API (500 requests/mes gratuitas)
2. Crear app/data/odds_fetcher.py
3. Cachear datos externos en SQLite para no gastar requests
4. Mostrar datos externos reales en Tab 4 (Value Detection)
5. Marcar claramente cuándo las datos externos son "en tiempo real" vs "históricas"
```

### 4.2 Datos de Partidos en Vivo

```
Opción A (Gratuita, delay de 5 min):
- API-Football: Plan gratuito con delay
- Suficiente para Smart Alerts pre-partido

Opción B (De pago, real-time):
- Sportradar / Opta: Profesional, webhooks
- Necesario para Live Match Center real
```

### 4.3 Migración de Frontend (Streamlit → React)

```
Timeline: Solo cuando la app tenga >10,000 usuarios activos mensuales

Razones para migrar:
- Streamlit no permite componentes custom complejos
- Sin control sobre JS, animaciones, PWA
- Límites en interactividad (no WebSockets nativas)

Plan de migración:
- Mantener backend Python (FastAPI)
- Reemplazar solo la capa de presentación (React + TailwindCSS)
- Reutilizar todos los engines (metrics, smart_alerts, trend_detector)
```

---

## 5. Tabla de Prioridades y Dependencias

```
SPRINT 0 → SPRINT 1 → SPRINT 2 → SPRINT 3 → SPRINT 4 → SPRINT 5
  │          │          │           │           │
  │          └──────────┤           │           │
  │                     └───────────┤           │
  │                                 └───────────┘
  └─── Bloqueante para todo lo demás
```

| Sprint | Depende de | Bloquea | Duración |
|--------|-----------|---------|----------|
| Sprint 0 | — | Todos | 3-5 días |
| Sprint 1 | Sprint 0 | Sprint 2, 3, 4 | 5-7 días |
| Sprint 2 | Sprint 1 | Sprint 3, 4 | 7-10 días |
| Sprint 3 | Sprint 1, 2 | Sprint 5 | 7-10 días |
| Sprint 4 | Sprint 2, 3 | Sprint 5 | 5-7 días |
| Sprint 5 | Todos | Deploy | 5 días |

**Total estimado MVP completo: 32-44 días de trabajo**

---

## 6. Criterios de Calidad — Non-Negotiable

Estos son los estándares mínimos que deben cumplirse antes de dar por completado cualquier sprint:

### Datos
- [ ] No hay datos externos simuladas/aleatorias en ningún cálculo visible
- [ ] Nombres de equipos normalizados consistentemente
- [ ] Ninguna columna de fecha hardcodeada con año concreto
- [ ] La carpeta de datos es `datos/` (lowercase) en todos los archivos

### Código
- [ ] Cero lógica de negocio en archivos de UI (`app/ui/`)
- [ ] Cada función tiene docstring con parámetros y return type
- [ ] Tests pasan al 100% antes de cualquier merge
- [ ] Sin `print()` en producción (usar `logging`)

### UX
- [ ] Modo oscuro activado por defecto
- [ ] Ningún spinner dura más de 2 segundos
- [ ] Cada cálculo de probabilidad muestra el tamaño de muestra (n)
- [ ] Disclaimer de juego responsable visible en Value Detection

### Integridad analítica
- [ ] Cada métrica explica su base de cálculo (tooltip o caption)
- [ ] Si no hay suficiente muestra (<10 partidos), no se muestra la métrica
- [ ] Las probabilidades matemáticas suman 100% (home + draw + away)
- [ ] El tendencia solo se calcula cuando hay datos externos reales, nunca simuladas

---

## 7. Decisiones de Diseño Documentadas

### ¿Por qué Streamlit y no React ahora?
Streamlit permite iterar 10x más rápido en MVP. El riesgo es UX limitada, pero es aceptable mientras no tengamos usuarios reales. Migrar cuando tengamos 10k MAU.

### ¿Por qué no usar xG real desde fbref?
FBref tiene xG desde ~2017/18 para La Liga. Es posible, pero añade complejidad al scraper. Fase 1 usa `xG_proxy = tiros_a_puerta * 0.35` como aproximación. Se añade xG real en Fase 2.

### ¿Por qué no guardar datos en base de datos SQL ahora?
Los CSV de football-data.co.uk son archivos pequeños (~500KB cada temporada). Con 20 temporadas son ~10MB. SQLite añadiría complejidad sin beneficio real hasta Fase 2. PostgreSQL cuando tengamos datos en tiempo real.

### ¿Por qué eliminar el news_engine basado en scraping?
El scraping de DuckDuckGo + trafilatura es frágil (se rompe si cambia el HTML del sitio, puede dar timeout, puede devolver contenido irrelevante). En Fase 2 se reemplaza por una API de noticias deportivas (NewsAPI.org gratuita o similar). En Fase 1: eliminar la feature de noticias o ponerla detrás de un flag.

---

## 8. Checklist de Inicio (Próximas 48 horas)

Antes de empezar a codificar, completar esto:

- [ ] **Verificar datos disponibles**: ¿Qué CSVs hay en `datos/`? ¿Tienen columnas de datos externos (B365H)?
- [ ] **Verificar que `player_engine.py` funciona**: Ejecutar `python player_engine.py` y confirmar que genera `datos/jugadores_raw.csv`
- [ ] **Instalar dependencias faltantes**: `pip install plotly pytest python-dotenv`
- [ ] **Crear branch de desarrollo**: `git checkout -b refactor/arquitectura-nueva` (si hay git)
- [ ] **Definir criterio de "listo"** para el Sprint 0: ¿Cuándo decimos que la estructura base está lista?

---

**FIN DEL PLAN**
