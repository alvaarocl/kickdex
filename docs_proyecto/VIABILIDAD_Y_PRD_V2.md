# Análisis de Viabilidad y Nuevo PRD: KICKDEX V2 (The plataformas de an?lisis estad?stico Killer)

Este documento evalúa la viabilidad técnica y económica de implementar las características premium de plataformas de an?lisis estad?stico en KICKDEX, seguido de un PRD (Product Requirements Document) actualizado para ejecutar esta visión.

---

## 1. Análisis de Viabilidad (Feasibility Study)

Para competir con plataformas de an?lisis estad?stico, debemos ser realistas sobre qué datos son accesibles gratuitamente o a bajo coste, y cuáles son prohibitivos.

### 🟢 Altamente Viable (Implementación Inmediata / Coste Cero)
*   **Estadísticas de Árbitros:** **100% Viable.** Los CSVs actuales de *football-data.co.uk* ya incluyen la columna del árbitro. Solo requiere crear una lógica en Pandas para agrupar tarjetas por árbitro y mostrarlo en la UI.
*   **Bot de Telegram (Push Notifications):** **100% Viable.** La librería `python-telegram-bot` es gratuita. Se puede crear un script (`bot.py`) que corra cada 24h, lea los *Value Bets* del día y los envíe al canal de Telegram.
*   **Gestión de Banca (Criterio de Kelly):** **100% Viable.** Es pura matemática. Si KICKDEX detecta una probabilidad matemática del 55% y la dato externo paga 2.00, la fórmula de Kelly dirá exactamente qué % del dinero analizar.

### 🟡 Viabilidad Media (Requiere Inversión Moderada e Infraestructura Nueva)
*   **Live Match Tracker (Tiempo Real):** **Viable con cambios.** Streamlit no está hecho para actualizaciones cada 30 segundos (consume mucha memoria recargando la app).
    *   *Solución:* Migrar el Frontend a React o Vue.js, y usar WebSockets con un backend FastAPI.
    *   *Coste Datos:* Requiere pagar una API como **API-Football** o **Sportmonks** (~$20 a $50/mes).
*   **Expansión a 40+ Ligas:** **Viable.** Las APIs mencionadas arriba cubren cientos de ligas.
    *   *Solución:* Implica abandonar los CSVs y migrar a una base de datos relacional robusta (**PostgreSQL**) alojada en la nube (ej. Supabase, Railway o AWS).
*   **Tracking de Dropping Odds (Caídas de Cuotas):** **Viable.**
    *   *Solución:* Usar "The Odds API" (tiene un plan gratuito de 500 requests/mes, que se puede quedar corto). KICKDEX necesitará un "Cron Job" (tarea programada) que guarde la dato externo cada hora en la base de datos para poder dibujar la gráfica de la caída.

### 🔴 Baja Viabilidad (Prohibitivo para un proyecto gratuito)
*   **Mapas de Calor (Heat Maps) y Tracking Posicional:** **No Viable.** Los datos de coordenadas X/Y de los jugadores en el campo (provistos por empresas como Opta o StatsPerform) cuestan miles de dólares mensuales.
    *   *Alternativa:* Enfocarse en "Gráficos de Presión" (Momentum) basados en ataques peligrosos y tiros por minuto, que sí están incluidos en las APIs de $20/mes.
*   **xG (Expected Goals) en ligas menores:** Las APIs económicas ofrecen xG para las 5 grandes ligas, pero no para la 2ª división de Suecia. En esas ligas menores habrá que seguir usando el "xG Proxy" (Tiros a puerta * 0.35).

---

## 2. Nuevo PRD: KICKDEX V2

**Visión:** Evolucionar KICKDEX de una herramienta de análisis estático en CSVs a una plataforma dinámica en tiempo real impulsada por bases de datos relacionales, integraciones API y notificaciones Push.

### FASE 1.5: "Exprimir el CSV" (Próximos 15 días)
Antes de pagar APIs, debemos maximizar lo que ya tenemos gratis.

*   **Epic 1: El Factor Disciplinario (Árbitros)**
    *   **Requisito:** Nueva pestaña `arbitros.py`.
    *   **Funcionalidad:** Tabla ordenable con todos los árbitros de la liga. Columnas: Partidos pitados, Promedio Amarillas, Promedio Rojas, Faltas/Partido, % Penaltis pitados.
    *   **Cruce de datos:** En la pestaña de un partido (Ej: Madrid vs Barça), mostrar un widget de "Árbitro Asignado" indicando si es un árbitro "Over" (saca muchas tarjetas) o "Under".
*   **Epic 2: El Ecosistema Telegram**
    *   **Requisito:** Script autónomo que publique en un canal de Telegram.
    *   **Funcionalidad:** Cada mañana a las 10:00 AM, el bot publica las "Smart Alerts" más fuertes del día y los Value Bets detectados por el motor matemático.
*   **Epic 3: Optimización del Value Detector**
    *   **Requisito:** Integrar el Criterio de Kelly.
    *   **Funcionalidad:** En la tabla de Value Bets, añadir la columna "prioridad Sugerido (%)".

### FASE 2: "The Real-Time Jump" (Meses 2 a 4)
El gran salto tecnológico para igualar a plataformas de an?lisis estad?stico.

*   **Epic 4: Arquitectura Cloud y Base de Datos**
    *   **Requisito:** Abandonar los CSVs locales.
    *   **Funcionalidad:** Levantar una base de datos PostgreSQL. Crear un script que inicialice la DB descargando todo el histórico de football-data.co.uk a tablas SQL relacionales (`matches`, `teams`, `referees`).
*   **Epic 5: Integración de The-Odds-API (Dropping Odds)**
    *   **Requisito:** Motor de rastreo de datos externos.
    *   **Funcionalidad:** Un script en el servidor hace ping a la API de datos externos cada 2 horas. Guarda el valor de la victoria local/visitante.
    *   **UI:** Si la dato externo cae más de un 10%, lanza una alerta en la web y en Telegram: 🚨 *"Dropping Odd: Mucho dinero entrando a favor del equipo X"*.
*   **Epic 6: Live Match Dashboard (API-Football)**
    *   **Requisito:** Contratar API-Football (Plan Básico).
    *   **Funcionalidad:** Nueva pestaña "Directo". Lista de partidos jugándose ahora.
    *   **Métricas en Vivo:** Posesión, Tiros, Ataques Peligrosos actualizados cada minuto.
    *   **Gráfico de Momentum:** Gráfico de barras que pinta de verde/rojo qué equipo domina los últimos 10 minutos (calculado con `(Ataques Peligrosos * 2) + Tiros a puerta`).

### FASE 3: "La Bestia Analítica" (Meses 5 a 8)
*   **Epic 7: Migración a React/Next.js**
    *   **Requisito:** Reemplazar Streamlit.
    *   **Por qué:** Streamlit será demasiado lento para soportar gráficos en vivo de decenas de partidos para miles de usuarios.
    *   **Funcionalidad:** Backend en FastAPI sirviendo JSON. Frontend en React para máxima fluidez, "Zero Refreshes" y experiencia de aplicación móvil (PWA).
*   **Epic 8: Expansión Global (40+ Ligas)**
    *   **Requisito:** Escalar el pipeline de datos.
    *   **Funcionalidad:** Inyectar ligas sudamericanas, asiáticas y segundas divisiones europeas al PostgreSQL. El motor de Value Bets correrá sobre miles de partidos semanales, encontrando los errores de las fuentes externas en mercados oscuros.

---

## 3. Stack Tecnológico Actualizado para V2

Para lograr esto, la arquitectura de KICKDEX debe evolucionar:

**Paso 1: (Situación Actual - MVP)**
*   Python + Pandas + Streamlit + CSVs Locales.

**Paso 2: (Transición - Medio Plazo)**
*   Python + Pandas + Streamlit + **PostgreSQL** + **Python-Telegram-Bot** + **Cron Jobs**.

**Paso 3: (Destino Final - plataformas de an?lisis estad?stico Killer)**
*   **Backend:** FastAPI (Python) para servir la API.
*   **Base de Datos:** PostgreSQL (alojado en Supabase/Railway).
*   **Background Workers:** Celery o Redis Queue para procesar miles de datos de APIs en segundo plano sin colgar la web.
*   **Frontend:** Next.js (React) + Tailwind CSS + Recharts (para gráficas).
*   **Proveedores de Datos:** API-Football (partidos) + The-Odds-API (datos externos).