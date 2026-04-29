# 📋 PRD - KICKDEX
## Product Requirements Document

**Versión:** 1.0  
**Última Actualización:** Abril 2026  
**Estado:** En Desarrollo (MVP)

---

## 🎯 Visión del Producto

**Convertirse en la herramienta gratuita de referencia para el análisis estadístico y táctico de fútbol**, combinando la profundidad del Big Data con una interfaz intuitiva que permita identificar ventajas competitivas (value bets o chollos Fantasy) en segundos.

### Diferenciación Competitiva

Somos la **alternativa 100% gratuita, moderna y en tiempo real** a plataformas de pago como **plataformas de an?lisis estad?stico.com**.

**Objetivo Diferenciador:** No solo mostrar datos históricos estáticos, sino crear un **"radar de an?lisis y rendimiento"** que cruce:
- Estadísticas avanzadas (xG, tiros, posesión)
- Cuotas de fuentes externas en tiempo real
- Datos de partidos en vivo

Permitiendo a los usuarios encontrar **"Value Bets"** (an?lisis de valor) y oportunidades en **Fantasy Football** sin pagar suscripciones premium.

---

## 👥 Públic Objetivo (User Personas)

### 1. El Apostador Inteligente ("Value Hunter")
- **Descripción:** No an?lisis por impulso. Busca discrepancias entre lo que dicen las fuentes externas (datos externos) y lo que dicen las matemáticas (xG, tiros, rachas).
- **Necesidades:**
  - Comparar equipos rápidamente
  - Identificar tendencias estad?sticas relevantes
  - Recibir alertas de caídas de datos externos
  - Acceso a probabilidades matemáticas precisas

### 2. El Manager de Fantasy (Biwenger, Sorare, Marca)
- **Descripción:** Busca identificar tendencias antes que el resto.
- **Necesidades:**
  - Saber qué jugador está tirando más a puerta aunque aún no haya marcado
  - Identificar quién está cometiendo menos faltas
  - Perfiles detallados de jugadores por métrica
  - Recomendaciones de alineación

### 3. El "Nerd" del Fútbol
- **Descripción:** Aficionados, periodistas o creadores de contenido que necesitan datos duros y rápidos.
- **Necesidades:**
  - Respaldar debates o análisis previos a un partido
  - Acceso a estadísticas históricas profundas
  - Comparativas H2H detalladas
  - Datos visualmente atractivos para contenido

---

## 📌 Casos de Uso Principales

### 1. Comparativa H2H Quirúrgica
**Descripción:** Enfrentar a dos equipos (Local vs. Visitante) y ver de un vistazo quién llega mejor basándose en métricas subyacentes reales, no solo en la tabla de clasificación.

**Flujo:**
1. Usuario ingresa dos equipos
2. Sistema muestra:
   - Tiros a puerta (últimos 5 partidos)
   - Córners
   - Presión ofensiva/defensiva
   - xG (Goles Esperados)
   - Posesión promedio
   - Historial directo (H2H)
3. Indicadores visuales (Verde/Rojo) para fortalezas/debilidades

### 2. Scouting de Jugadores
**Descripción:** Entrar a la plantilla de un equipo específico y aislar a los líderes en métricas concretas.

**Flujo:**
1. Usuario selecciona equipo
2. Sistema muestra tabla de jugadores con:
   - Goles marcados
   - Asistencias
   - Tiros realizados
   - Faltas cometidas
   - Tarjetas amarillas/rojas
   - Minutos jugados
3. Ordenable por cualquier columna
4. Filtros por rango de minutos, últimos N partidos

### 3. Detección de Valor en Cuotas (Visión Futura)
**Descripción:** Observar un partido en directo o pre-partido, ver la probabilidad matemática de victoria generada por la app y contrastarla automáticamente con las datos externos.

**Flujo:**
1. Usuario abre un partido
2. Sistema calcula:
   - Probabilidad matemática de victoria local (basada en xG, historial)
   - Probabilidad matemática de empate
   - Probabilidad matemática de victoria visitante
3. Sistema compara contra datos externos de Bet365, Bwin, etc.
4. Marca en VERDE si hay "Value" (dato externo paga más que probabilidad real)
5. Alerta si cae drásticamente la dato externo (dinero del mercado)

---

## 🎬 Análisis de Competencia (Benchmark: plataformas de an?lisis estad?stico)

Para entender lo que estamos construyendo, hemos analizado el núcleo de **valuestats.com**. Nuestra plataforma debe replicar y superar los siguientes pilares que ellos monetizan:

### 1. Motor de Tendencias Automáticas ("Trends")
**Qué hace plataformas de an?lisis estad?stico:**
- Detecta patrones rentables automáticamente
- Ejemplo: "El Equipo A ha tenido -2.5 goles en sus últimos 5 partidos como local"
- Ejemplo: "El Equipo B recibe +1.5 tarjetas amarillas como visitante"

**Nuestro Objetivo:** 
Implementar un generador inteligente que expulse insights estad?sticos en lenguaje natural en lenguaje natural.

### 2. Comparador de Cuotas (Odds Comparison)
**Qué hace plataformas de an?lisis estad?stico:**
- Rastreador que compara datos externos (1-X-2 y otros mercados) entre casas principales
- Cubre: Bet365, Betfair, Bwin, WilliamHill, 888Sport

**Nuestro Objetivo:**
Integración en tiempo real de APIs de datos externos (Fase 2 del roadmap).

### 3. Live Match Tracker (Directo)
**Qué hace plataformas de an?lisis estad?stico:**
- Sigue partidos en vivo
- Actualiza rendimiento ofensivo/defensivo de equipos
- Estadísticas individuales de jugadores al minuto (faltas, tarjetas, sustituciones, goles)

**Nuestro Objetivo:**
Implementar gráficos de momentum y actualizaciones en tiempo real (Fase 2).

### 4. Base de Datos Global
**Qué hace plataformas de an?lisis estad?stico:**
- Cubre desde grandes ligas europeas (Premier, La Liga, Champions) hasta ligas menores y sudamericanas
- Listados de máximos goleadores y próximos partidos

**Nuestro Objetivo:**
Expandir cobertura gradualmente desde Liga Española → Ligas Top 5 → Ligas Menores.

---

## 🔧 Requisitos Funcionales - Stack Funcional

### **Pila A: Pre-Match & Predictive Analytics (Análisis Previo)**

#### A1. Fichas de Partido (Match Hub)
- **Descripción:** Vista detallada de un encuentro futuro
- **Debe incluir:**
  - Historial H2H (Head-to-Head)
  - Estado de forma reciente (W-D-L últimos 5-10 partidos)
  - Métricas avanzadas promedio:
    - xG (Goles Esperados)
    - Tiros a puerta
    - Posesión
    - Córners
    - Faltas
  - Alineaciones esperadas (si disponible)
  - Información de bajas/lesiones (si disponible)

#### A2. Generador de Tendencias (Smart Alerts)
- **Descripción:** Algoritmo que lee la base de datos y expulsa insights estad?sticos
- **Ejemplo de salida:**
  - "Hay un 80% de probabilidad de que ambos equipos marquen basándonos en los últimos 10 partidos"
  - "El equipo visitante ha concedido +2 goles en el 70% de partidos como visitante"
  - "Más de 2.5 goles en el 75% de enfrentamientos directos"
- **Lógica:** Basada en patrones históricos + forma reciente

#### A3. Player Scouting (Fantasy & Prop Bets)
- **Descripción:** Perfiles de jugadores con estadísticas desglosadas
- **Debe incluir:**
  - Promedios exactos por partido:
    - Faltas cometidas
    - Tiros realizados
    - Pases clave
    - Goles
    - Asistencias
    - Minutos jugados
  - Últimos 5/10 partidos individual
  - Tendencias de forma (mejorando/empeorando)
  - Recomendaciones para Fantasy

---

### **Pila B: Real-Time Odds & Value Detection (Cuotas en Vivo)**

#### B1. Integración de Cuotas API
- **Descripción:** Conexión en tiempo real para mostrar datos externos del mercado
- **Tipos de datos externos a mostrar:**
  - 1X2 (Victoria local / Empate / Victoria visitante)
  - Over/Under de goles
  - Ambos marcan (GG - Both Teams to Score)
  - Goles exactos
- **Casas de an?lisis:** Bet365, Bwin, Betfair, WilliamHill, 888Sport
- **Actualización:** Cada 5-10 minutos (fase actual), cada minuto (fase 2)

#### B2. Buscador de Valor (The "Edge")
- **Descripción:** El corazón de la app. El sistema debe comparar:
  - **Probabilidad Matemática** = basada en histórico de stats (xG, form)
  - **Probabilidad Implícita** = derivada de la dato externo de la casa
- **Indicador Visual:**
  - 🟢 **VERDE:** Value Bet encontrado (casa paga MÁS de lo que debería)
  - 🔴 **ROJO:** Apuesta de riesgo (casa paga MENOS de lo que debería)
  - ⚪ **GRIS:** Precio justo
- **Fórmula Básica:**
  - Prob. Implícita = 1 / Cuota
  - Si (Prob. Implícita < Prob. Matemática) → VALUE

#### B3. Seguimiento de Caídas de Cuotas (Dropping Odds)
- **Descripción:** Alertas visuales si la dato externo cae drásticamente
- **Indicador:** Si la dato externo de un equipo en Bet365 cae >5% en últimas 2 horas
- **Interpretación:** Dinero del mercado se mueve hacia esa opción (información privilegiada del mercado)
- **Visualización:** Gráfico de línea que muestra evolución de dato externo en tiempo real

---

### **Pila C: Live Match Center (El Partido en Directo)**

#### C1. Gráfico de Momentum (Live Pressure)
- **Descripción:** Gráfico dinámico que muestre qué equipo ataca más
- **Granularidad:** Tramos de 5-10 minutos durante el partido
- **Métrica:** 
  - Tiros a puerta realizados en ese tramo
  - Presión ofensiva (relación tiros/corners)
  - Posesión aproximada
- **Visualización:** Gráfico de barras apiladas, color local vs color visitante

#### C2. Actualización de Stats en Vivo
- **Descripción:** Modificación en tiempo real de estadísticas
- **Stats en vivo:**
  - Tiros / Tiros a puerta
  - Córners
  - Tarjetas (amarillas/rojas)
  - Faltas
  - Posesión
  - Substituciones
  - Goles (marcador en vivo)
- **Frecuencia:** Actualización cada 30-60 segundos
- **Propósito:** Apoyar a usuarios que hacen an?lisis en directo (In-Play Betting)

---

### **Pila D: Experiencia de Usuario (UX/UI)**

#### D1. Filosofía "Zero Friction"
- **Requisito:** La web es 100% gratuita
- **No hay:**
  - Muros de pago
  - Registros obligatorios
  - Anuncios tipo banner molestos
  - Pop-ups intrusivos
- **Monetización Futura:** Freemium (datos avanzados/API) o afiliación de an?lisis (sin obligar a usar la plataforma)

#### D2. Diseño Pro-Analista
- **Modo Oscuro:** Obligatorio por defecto
- **Tablas:** Alta densidad de datos (estilo Excel moderno)
  - Ordenables por cualquier columna
  - Filtros inline
  - Columnas configurables
- **Jerarquía Visual:**
  - Datos más importantes destacan (Goles, Tiros)
  - Métricas secundarias en segundo plano
- **Semáforo de Colores:**
  - 🟢 VERDE: Fortaleza
  - 🔴 ROJO: Debilidad
  - ⚪ GRIS: Neutral

---

## 📅 Roadmap de Fases

### **FASE 1: MVP Actual (Análisis Estático Avanzado)** ✅ En Desarrollo
**Timeline:** Año 1 (Dic 2025 - Dic 2026)

**Objetivo:** Crear la base sólida de análisis histórico que supere a competencia en densidad de datos y UX

**Deliverables:**
- ✅ Cobertura total de la temporada actual (1ª y 2ª División Española)
- ✅ Panel comparativo de equipos con selección dinámica de número de partidos (últimos 5, 10, etc.)
- ✅ Fichas individuales de equipos con promedios de rendimiento
- ✅ Buscador de jugadores con desglose de estadísticas por partido (minutos, goles, tiros, faltas, tarjetas)
- ✅ Historial de enfrentamientos directos desde años anteriores
- ✅ Dashboard interactivo en Streamlit
- ✅ Generador básico de tendencias (Smart Alerts)
- ✅ Data normalization y limpieza

**Stack Técnico:**
- Backend: Python (Pandas, NumPy)
- Frontend: Streamlit
- Base de Datos: CSV + Caché en memoria (Fase 1)
- Source de Datos: football-data.co.uk (histórico gratuito)

---

### **FASE 2: Expansión a Tiempo Real (El Siguiente Gran Paso)** 📋 Planned
**Timeline:** Año 2 (Ene 2027 - Dic 2027)

**Objetivo:** Integrar datos en tiempo real y datos externos vivas para crear ventaja competitiva real

**Realidad del Mercado:** Para lograr un "100% tiempo real", el sistema deberá transicionar de extraer datos gratuitos (que tienen retraso de 1-2 días) a consumir webhooks de una API deportiva profesional.

**Deliverables:**
1. **Live Match Tracker**
   - Calendario de la jornada con marcador en directo
   - Estadísticas actualizándose minuto a minuto
   - Gráfico de momentum en tiempo real

2. **Integración de Cuotas (Odds API)**
   - Módulo que rastree datos externos de pre-partido y en directo
   - Cobertura de Bet365, Bwin, Betfair, WilliamHill, 888Sport
   - Histórico de movimientos de datos externos

3. **Motor de Value Detection**
   - Cálculo automático de probabilidades matemáticas
   - Comparación contra datos externos del mercado
   - Alertas visuales cuando hay "Value Bets"
   - Ranking de mejores oportunidades del día

4. **Push Notifications**
   - Alertas cuando se detecta Value
   - Alertas de caídas de datos externos significativas
   - Notificaciones de cambios en equipo/lesiones

**Stack Técnico a Agregar:**
- API Deportiva Profesional: ScoresBCI, Flashscore API, o similar
- API de Cuotas: Odds API, BetsAPI
- Backend: FastAPI o Django (mayor escalabilidad)
- Base de Datos: PostgreSQL + Redis (caché)
- WebSockets: Para actualizaciones en tiempo real
- Frontend: React/Vue.js (Streamlit → webapp moderna)

---

### **FASE 3: Global & Advanced Features** (Backlog)
**Timeline:** Año 3+ (2028+)

**Deliverables:**
- Expansión geográfica: Ligas Top 5 europeas + Sudamérica
- Machine Learning: Predictor de resultados basado en xG
- Análisis de Arbitraje: Tendencias de tarjetas por árbitro
- Community Features: Leaderboard de predictores, compartir análisis
- Mobile App: iOS/Android nativa
- API Pública: Para desarrolladores (con afiliación)

---

## 📊 Requisitos No Funcionales

### 🚀 Rendimiento
- **Carga de Datos:** Cambiar entre equipos debe ser prácticamente instantáneo (<500ms)
- **No Interrumpir:** El flujo de análisis del usuario no debe verse interrumpido
- **Caché Agresivo:** Resultados de cálculos frecuentes deben estar cacheados
- **Base de Datos:** Queries complejos deben optimizarse con índices

### 🎨 Usabilidad (UX/UI)
- **Modo Oscuro:** Obligatorio por defecto (protege vista, reduce cansancio)
- **Jerarquía Visual Clara:** Datos importantes destacan sobre secundarios
- **Zero Ads:** Ausencia total de publicidad intrusiva
  - ❌ Banners flotantes
  - ❌ Pop-ups intersticiales
  - ❌ Auto-play de vídeos
- **Accesibilidad:** Contraste suficiente, fonts legibles, navegación intuitiva

### 🔒 Fiabilidad
- **Normalización de Datos:**
  - Sin nombres de equipos duplicados o mal escritos
  - Nombres de jugadores consistentes
- **Sin Registros Fantasma:** Que inflen estadísticas individuales
- **Integridad:** Verificación cruzada de datos antes de mostrar
- **Mantenimiento:** Actualización automática de datos (diaria)

### 🌐 Escalabilidad
- **Fase 1:** Millones de registros históricos en caché
- **Fase 2:** Handling de miles de solicitudes/segundo durante match events
- **Arquitectura:** Separación de frontend/backend para escalar independientemente

### 📱 Compatibilidad
- **Desktop First:** Prioridad en pantallas amplias (16:9, 21:9)
- **Responsive:** Funcional en tablets (iPad)
- **Navegadores:** Chrome, Firefox, Safari, Edge (últimas 2 versiones)

---

## 🛠️ Especificaciones Técnicas

### Stack Recomendado (Fase 1)

```
Frontend:
├── Streamlit (actual) → React (Fase 2)
├── Pandas DataFrames para visualización
└── Plotly para gráficos interactivos

Backend:
├── Python 3.9+
├── Pandas (procesamiento)
├── NumPy (cálculos)
└── SQLite (caché local)

Data:
├── CSV (histórico gratuito)
├── Source: football-data.co.uk
├── Updates: Diarios
└── Backup: GitHub

Infrastructure:
├── Cloud: Vercel/Netlify (frontend)
├── Backend: Heroku / AWS Lambda
└── Database: Managed PostgreSQL (Fase 2)
```

### Formato de Datos Esperado

Los archivos CSV deben contener:
```
Obligatorias:
- Date: Fecha del partido
- HomeTeam: Equipo local
- AwayTeam: Equipo visitante
- FTHG: Goles del equipo local
- FTAG: Goles del equipo visitante
- Div: División/Liga

Opcionales (si no existen, se crean con NaN):
- HS: Tiros local
- AS: Tiros visitante
- HST: Tiros a puerta local
- AST: Tiros a puerta visitante
- HF: Faltas local
- AF: Faltas visitante
- HC: Córners local
- AC: Córners visitante
- HY: Tarjetas amarillas local
- AY: Tarjetas amarillas visitante
- B365H, B365D, B365A: Cuotas Bet365
```

---

## 📈 KPIs y Métricas de Éxito

### Fase 1 (MVP)
| KPI | Meta | Método |
|-----|------|--------|
| Usuarios únicos/mes | 10,000 | Google Analytics |
| Tiempo en sesión promedio | >10 min | Streamlit Analytics |
| Tasa de rebote | <40% | GA |
| Velocidad de carga | <2s | Lighthouse |
| Cobertura de datos | 100% (Liga Española) | Manual review |
| Precisión de stats | 99%+ | Validación cruzada |

### Fase 2 (Real-Time)
| KPI | Meta | Método |
|-----|------|--------|
| Uptime | 99.9% | Monitoring |
| Latencia de actualización | <1s | WebSocket logs |
| Precisión de Value Detection | >80% | Backtesting |
| Usuarios activos diarios | 50,000+ | GA |
| Conversión a premium (futuro) | 5%+ | Stripe |

---

## 🔐 Seguridad y Cumplimiento

### Requisitos Mínimos
- ✅ HTTPS obligatorio (SSL/TLS)
- ✅ No almacenar datos sensibles (contraseñas) en Fase 1
- ✅ Respetar ToS de fuentes de datos (football-data.co.uk)
- ✅ Respetar APIs de datos externos (rate limits)
- ✅ GDPR: Privacidad de usuario (no tracking sin consentimiento)
- ✅ Afiliación responsable: Advertencia de riesgos de juego

### Disclaimer
La plataforma debe mostrar claramente:
- "Las an?lisis conllevan riesgo. Juega responsablemente."
- "KICKDEX proporciona análisis histórico, no garantías de futuro."
- "No somos asesores financieros. Haz tus propias investigaciones."

---

## 📝 Tareas Inmediatas (Next Sprint)

### Priority 1 (Semana 1-2)
- [ ] Consolidar estructura de datos (limpieza de duplicados)
- [ ] Implementar caché en disco para queries frecuentes
- [ ] Añadir test unitarios para data_processor.py
- [ ] Documentar formato de datos esperado

### Priority 2 (Semana 3-4)
- [ ] Mejorar UX/UI del dashboard (tablas ordenables)
- [ ] Implementar generador de tendencias básico
- [ ] Agregar filtros avanzados (por fecha, liga, equipo)
- [ ] Crear perfiles de jugadores detallados

### Priority 3 (Semana 5+)
- [ ] Preparar integración con API de datos externos (pruebas)
- [ ] Diseñar arquitectura para Fase 2
- [ ] Crear documentación para desarrolladores
- [ ] Plan de monetización (freemium model)

---

## 📞 Contacto y Escalación

- **Product Owner:** [Tu nombre]
- **Slack Channel:** #kickdex
- **Issues/Bugs:** GitHub Issues
- **Retrospective:** Bi-weekly (Jueves 4pm CET)

---

## 📚 Apéndices

### A. Referencias y Benchmarks
- **Competencia Directa:** plataformas de an?lisis estad?stico.com, WhoScored, Understat
- **Datos Históricos:** football-data.co.uk
- **APIs de Referencia:** Odds API, Flashscore API

### B. Glosario
- **xG (Expected Goals):** Goles esperados basados en calidad de ocasiones
- **Value Bet:** Apuesta donde la dato externo paga más que la probabilidad real
- **H2H (Head-to-Head):** Enfrentamientos históricos entre dos equipos
- **Smart Alert:** Tendencia automática detectada por el sistema
- **Live Pressure:** Gráfico de presión/momentum en tiempo real
- **Odds Dropping:** Caída significativa de dato externo (=dinero fluyendo)

### C. Casos de Uso Expandidos

#### Caso 1: Usuario "Value Hunter" busca an?lisis
1. Entra a KICKDEX
2. Ve calendario de hoy (Real Madrid vs Barcelona)
3. Clica en el partido
4. Ve fichas de ambos equipos (H2H, forma reciente)
5. Lee Smart Alerts: "Real Madrid marca el primer gol en el 65% de clásicos"
6. Sistema calcula prob. matemática: 55% Madrid gana
7. Cuota de Bet365: 1.90 (prob. implícita = 52%)
8. 🟢 Marcado como VALUE ✓
9. Usuario coloca an?lisis

#### Caso 2: Manager de Fantasy busca diferencial
1. Abre Fantasy League
2. Entra a KICKDEX → Buscador de Jugadores
3. Filtra: "Delanteros Centro, últimos 5 partidos"
4. Ordena por "Tiros a Puerta" descendente
5. Ve jugador emergente con promedio alto pero bajo precio de fantasy
6. Clica en perfil, ve historial + tendencia
7. Decide incluirlo en alineación (diferencial respecto a otros managers)

---

**FIN DEL DOCUMENTO**
