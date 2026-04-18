# EL PLAN MAESTRO: KICKDEX "Zero Cost" Data Architecture

El objetivo de este documento es trazar la ruta exacta para construir el **100% de las funcionalidades premium posibles (incluyendo métricas avanzadas y live scores)** utilizando exclusivamente fuentes de datos **gratuitas**. 

Vamos a construir un ecosistema (un "Frankenstein" de datos) que extraiga de diferentes fuentes, lo unifique en nuestra base de datos, y nos permita ofrecer un nivel de detalle idéntico a plataformas de pago.

---

## 1. El Ecosistema de Datos Gratuitos (The "Free Stack")

Para lograr esto sin gastar un euro, KICKDEX consumirá de 4 fuentes distintas mediante *web scraping* ético y librerías de Python.

### Fuente A: `football-data.co.uk` (La Base Histórica)
*   **Coste:** 100% Gratis (CSVs).
*   **Ligas:** Top 5 Ligas (Premier, La Liga, Serie A, Bundesliga, Ligue 1) + Segundas Divisiones.
*   **Qué extraemos:** Resultados al descanso (HTHG/HTAG), Córners, Faltas, Tiros Totales, Árbitro asignado.
*   **Frecuencia de actualización:** 2 veces por semana.

### Fuente B: `Understat` (El Motor de xG y Mapas de Tiro)
*   **Coste:** 100% Gratis usando la librería Python `understatapi` o `UnderData`.
*   **Ligas:** Top 5 Ligas Europeas.
*   **Qué extraemos:** 
    *   **xG (Expected Goals) y xA (Expected Assists)** reales y precisos.
    *   **Mapas de tiro:** Coordenadas X/Y de desde dónde tira cada jugador.
    *   **Expected Points (xPTS):** Puntos que debería tener un equipo según sus ocasiones, útil para detectar equipos que están teniendo "mala suerte" (Value Bets ocultas).
*   **Frecuencia de actualización:** Diaria.

### Fuente C: `FBref` via `soccerdata` (El Scouting de Jugadores Profundo)
*   **Coste:** 100% Gratis (Scraping autorizado por la librería `soccerdata`).
*   **Qué extraemos:** 
    *   **Match Logs:** Minuto exacto de cada evento (Goles, Tarjetas). ¡Esto resuelve el problema de saber si el árbitro sacó tarjeta en la 1ª parte!
    *   **Estadísticas de Cirujano:** Pases clave, acciones de creación de tiro, recuperaciones de balón en el último tercio.
*   **Frecuencia de actualización:** Diaria.

### Fuente D: `API-Football` (El "Live Match Tracker" Básico)
*   **Coste:** Gratis (Plan de 100 peticiones al día).
*   **Cómo usarlo estratégicamente:** No podemos pedir datos cada segundo. Pero podemos llamar al endpoint `/fixtures?live=all` cada 5 minutos durante el fin de semana. Esto consume ~40 peticiones en 3 horas.
*   **Qué extraemos:** Marcador en vivo, minuto de juego, tarjetas rojas. Suficiente para tener una pestaña "En Directo" funcional sin pagar la API premium.

---

## 2. Nuevas Funcionalidades Premium (Viables y Gratuitas)

Con este stack de datos, estas son las "Killer Features" que KICKDEX va a incluir en el ámbito puramente estadístico:

### 🎯 1. Dashboard de Árbitros "Deep Dive"
Gracias a los Match Logs de FBref cruzados con el nombre del árbitro de football-data, KICKDEX ofrecerá una pestaña dedicada al árbitro del partido con:
*   Media de Tarjetas Amarillas y Rojas.
*   **Tarjetas al Descanso (1st Half Cards):** Porcentaje de partidos donde este árbitro saca al menos 1 tarjeta antes del minuto 45.
*   **Foul-to-Card Ratio:** Cuántas faltas necesita pitar este árbitro para sacar una amarilla (indica si es un árbitro "tarjetero" o permisivo).
*   **Sesgo Local/Visitante:** ¿Favorece al equipo de casa en sus decisiones históricas?

### 📈 2. Análisis de "Justicia del Marcador" (xG Timeline)
Usando Understat, en la ficha de un partido terminado o en la previa de uno futuro, mostraremos:
*   **Tabla de Clasificación de xPTS:** Una liga paralela que muestra dónde deberían estar los equipos si el fútbol fuera 100% matemático. Si un equipo va 15º pero es 7º en xPTS, es el equipo ideal para apostar a su favor (Value Bet por regresión a la media).
*   **Zonas de Peligro:** Desde dónde concede tiros el equipo local vs desde dónde tira el visitante.

### ⏱️ 3. Tiempos de Goles (Time-based Stats)
Crucial para apuestas en vivo. KICKDEX mostrará una gráfica de barras dividida en tramos de 15 minutos (0-15', 15-30', etc.):
*   ¿En qué minuto suele marcar el Real Madrid?
*   ¿El equipo visitante suele conceder goles en los últimos 15 minutos (75-90') por bajón físico?

### 🤖 4. Generador de "Smart Alerts" Ampliado
El motor de lenguaje natural leerá TODAS estas nuevas bases de datos y generará frases premium:
*   *"El árbitro Mateu Lahoz ha sacado +1.5 tarjetas en la primera parte en el 80% de sus últimos 10 partidos."*
*   *"El equipo local está sobre-rindiendo (Goles: 15, xG: 9.2). Es probable que empiecen a marcar menos."*

---

## 3. Arquitectura del Sistema (Cómo construir el Frankenstein)

Para que esto sea rápido para el usuario final y no consuma la web de Streamlit, necesitamos separar la "Cosecha de datos" de la "Visualización".

```text
[ SERVIDOR / BACKGROUND JOBS ] -- (Corre de madrugada)
  ├─ 1. script_football_data.py → Descarga Top 5 Ligas (CSVs)
  ├─ 2. script_understat.py     → Descarga xG y xPTS vía understatapi
  ├─ 3. script_fbref.py         → Descarga Match Logs (Minutos de tarjetas)
  │
  ▼
[ BASE DE DATOS CENTRAL (SQLite o DuckDB) ]
  ├─ Tabla: Matches (Resultados, Córners)
  ├─ Tabla: Events (Minutos de goles y tarjetas)
  ├─ Tabla: ExpectedGoals (xG por equipo y jugador)
  │
  ▼
[ FRONTEND KICKDEX (Streamlit / React) ] -- (Carga instantánea)
  ├─ Tab 1: Previa del Partido (H2H, xG, Árbitro)
  ├─ Tab 2: Smart Alerts
  ├─ Tab 3: En Directo (API-Football cada 5 mins)
  ├─ Tab 4: Player Scouting (Mapas de Tiro)
```

### El Reto del "Live" (Directo)
Mantendremos el "Live" básico y elegante. 
1. El usuario entra en la pestaña "Directo".
2. Ve una lista de partidos con un semáforo parpadeando.
3. KICKDEX consulta el marcador a *API-Football*.
4. Muestra: `[65'] Real Madrid 1 - 0 Sevilla`.
5. *Valor añadido:* Justo debajo del marcador en vivo, KICKDEX inyecta la Smart Alert histórica: *"Ojo: El Sevilla ha empatado el 40% de partidos que iba perdiendo al descanso este año"*. 

---

## 4. Próximos Pasos (Hoja de Ruta de Implementación)

**Fase A: Expandir la Base (1 semana)**
1.  Modificar el código actual para descargar las 5 Grandes Ligas de `football-data.co.uk`.
2.  Instalar `understatapi` e integrarlo para descargar la tabla de xPTS (Puntos Esperados).
3.  Crear la vista de "Clasificación de Justicia" (Clasificación Real vs Clasificación xG).

**Fase B: El Árbitro y el Minuto (2 semanas)**
1.  Integrar `soccerdata` para raspar los Match Logs de FBref (conseguir los minutos de las tarjetas).
2.  Desarrollar `referee_engine.py`.
3.  Crear la UI del "Dashboard del Árbitro" en la web.

**Fase C: El Directo "Free" (1 semana)**
1.  Crear una cuenta gratuita en API-Football.
2.  Programar una caché estricta para no pasarnos de 100 peticiones/día (ej. guardar el JSON del live cada 5 mins y que los usuarios lean de ese JSON guardado, no de la API directamente).
3.  Lanzar la pestaña "Live Tracker".

**Conclusión:** Con esta arquitectura, KICKDEX pasará de ser un "Excel bonito" a un **terminal de inteligencia deportiva de primer nivel**, sin pagar un solo euro en licencias de datos, y preparado para destrozar a plataformas de pago que cobran $30/mes por la misma información.
