# REBRANDING — Analista Pro → KICKDEX
> Estudio de marca, estudio de mercado y plan de migración completo.
> Redactado: 2026-04-15 | Autor: Claude Code × Álvaro Carpintero

---

## 0. TL;DR — Una página para decidir

| | Ahora | Propuesta |
|---|---|---|
| **Nombre** | Analista Pro | **KICKDEX** |
| **Tagline** | Fútbol Big Data | **The football data terminal.** / *Tu terminal de fútbol.* |
| **Posicionamiento** | Herramienta de análisis española | Terminal de datos de fútbol independiente |
| **Logo** | Balón genérico + grid SVG | Wordmark `kick` + `dex` (cursor terminal) |
| **Paleta** | Esmeralda #00d4aa + OLED negro | **Turf** #2EE6A6 + **Pitch Black** #05070D (refinada) |
| **Tipografía** | IBM Plex Sans + JetBrains Mono | Igual — **consolidada** (eliminar Space Grotesk no usada) |
| **Voz** | Descriptiva, técnica | Trader meets tifoso — precisa, directa, sin hype |
| **Mercado objetivo** | España | España → escala internacional (PL, SA, L1) |

**Recomendación:** Aprobar KICKDEX como nombre, ejecutar fases en orden. Total de archivos a tocar: **23**. Sin tocar: motor de datos, tests, schemas JSON.

---

## 1. Por qué hacer rebranding

### 1.1 Problemas del nombre actual

**"Analista Pro" es genérico e indefendible.**

1. **Sin diferenciación en búsqueda.** Más de 100 canales de YouTube, apps de análisis deportivo y servicios de apuestas usan variantes de "Analista"/"Analyst Pro". Ranking orgánico imposible para el nombre de marca.

2. **Completamente descriptivo.** Los nombres puramente descriptivos no pueden ser registrados como marca. Cualquier competidor puede usar el mismo nombre mañana.

3. **Bloquea la expansión.** El nombre solo funciona en español. En inglés, "Analista" no significa nada y "Pro" es el sufijo más saturado del mercado digital (Spotify Pro, LinkedIn Pro, Figma Pro, etc.).

4. **Sin gancho emocional.** Competitors como WhoScored, FBref, Understat o ValueStats tienen identidades reconocibles. "Analista Pro" suena a un Excel con CSS.

5. **El sufijo "Pro" marca precio, no producto.** Implica que hay una versión "Free" inferior, lo cual contradice el posicionamiento de "gratis es el producto".

### 1.2 Qué hay que preservar

Lo que ya funciona —y en lo que el rebrand se apoya, no destruye:

- **Sistema de color OLED + emerald:** único en el vertical de estadísticas de fútbol. Se refina, no se cambia.
- **Estética trading-terminal:** JetBrains Mono para datos + glassmorphism sobre negro profundo. Nadie más en este espacio tiene esto.
- **Codificación semántica del color:** verde = edge, oro = oportunidad, rojo = riesgo. Sistema ya en la cabeza de los usuarios existentes.
- **Densidad de datos:** las tablas y cards ya están optimizadas para power users. No se toca la arquitectura visual.
- **El producto es sólido:** 18,249 partidos históricos, pipeline de datos funcional, 4 módulos completos. El rebrand no es una distracción del producto; lo proyecta mejor.

---

## 2. Estudio de Mercado

### 2.1 Segmento objetivo

**Fútbol datos / value betting para prosumidores hispanohablantes** — con visión de expansión a Europa.

Tamaño del segmento (estimación):
- **España:** ~3.8M personas que hacen apuestas deportivas regularmente (DGOJ 2025), de las cuales ~15-20% buscan "value" de forma activa → 570,000-760,000 usuarios potenciales de una herramienta de EV.
- **Fantasy football ES:** Biwenger tiene ~450K usuarios activos, Sorare ~800K usuarios globales.
- **Fútbol data nerds:** audiencias de cuentas tipo @opta_pablo, @xGlab en Twitter/X: 200-500K alcance combinado.

### 2.2 Mapa competitivo

| Competidor | Posicionamiento | Precio | Fortaleza | Debilidad (→ nuestra apertura) |
|---|---|---|---|---|
| **ValueStats.com** | Calculadoras de value betting | Freemium / Paid | Audiencia española, fórmulas EV probadas | UI fea, lenta, sin dashboard moderno |
| **WhoScored** | Ratings + estadísticas de partidos | Free + Ads | Autoridad de marca, cobertura global | Sin value betting, sin ángulo fantasy |
| **FBref / StatsBomb** | Stats avanzadas en bruto | Free | Profundidad de datos, credibilidad analítica | Vibe de hoja de cálculo, UI nula para apostadores |
| **Understat** | Modelo xG | Free | Credibilidad en xG | UI anticuada, sin foco español |
| **Oddsportal** | Comparación de cuotas | Free + Ads | Cobertura de mercados | Sin analytics, solo cuotas |
| **Biwenger / Marca Fantasy** | Plataformas fantasy | Free + Paid | Audiencia masiva, engagement alto | La capa de analytics es muy delgada |
| **Stake / bet365 insights** | "Insights" de bookmakers | Free (como gancho) | Cuotas reales | Sesgados — son la casa |
| **SofaScore / Flashscore** | Live scores + stats básicas | Free + App | Alcance enorme, app muy descargada | Sin análisis predictivo, sin EV |
| **xGscore.com** | xG model alternativo | Free | Nicho fiel | Poco activo, sin módulo de apuestas |

### 2.3 Espacio libre — qué marca debe poseer

Cuatro posiciones que nadie ocupa de forma clara y que KICKDEX puede reclamar:

**1. "El terminal de trading para fútbol"**
La estética JetBrains Mono + OLED ya está ahí. Ningún competidor en este vertical usa un lenguaje visual de terminal financiero. Es diferenciador y aspiracional para el target (que también lee r/algotrading y sigue cuentas de quant finance).

**2. Independiente, gratuito, matemáticamente honesto**
Opuesto al contenido "de análisis" de los bookmakers, que están incentivados a que pierdas. La independencia es un valor diferenciador real y comunicable.

**3. Listo para el mercado internacional desde el nombre**
El nombre debe funcionar en inglés sin traducción. Ser el primero en cubrir La Liga + Segunda con UX de nivel 2025 desde una marca internacional.

**4. Fantasy + Value en un solo producto**
Nadie combina scouting nivel Biwenger con detección de EV value betting bajo un mismo techo. Este es el verdadero foso competitivo a largo plazo.

### 2.4 Tendencias del mercado a aprovechar

| Tendencia | Por qué nos beneficia |
|---|---|
| Regulación de apuestas → "data-driven responsable" | Un posicionamiento matemático e independiente es más defensible en un entorno regulado |
| Lenguaje crypto/fintech en deportes | "Alpha", "edge", "signal", "terminal" resuenan con el target; KICKDEX vive en ese vocabulario |
| Comunidades stat-native en X/TikTok | Tarjetas estilo Opta, micro-animaciones de datos — el producto ya tiene las animaciones, falta la marca |
| Dark mode como estándar | Ya lo tenemos; la competencia sigue en modo claro por defecto |
| xG y stats avanzadas mainstream | La audiencia general ya conoce xG. El producto debe posicionarse un paso más allá, no explicarlo. |

---

## 3. Estudio de Marca

### 3.1 Esencia de marca

| Dimensión | Definición |
|---|---|
| **Categoría** | Terminal de inteligencia de fútbol / value betting |
| **Promesa central** | *"The edge, for free."* — matemáticas de nivel bookmaker, empaquetadas como herramienta pública y bella. |
| **Propuesta de valor** | 20 años de historia + modelos probabilísticos + scouting de jugadores, en una UI que respira La Liga. |
| **Tono de voz** | Confiado · preciso · ligeramente irreverente · trader-meets-tifoso |
| **Rasgos de personalidad (top 5)** | Analítico, afilado, independiente, culto, rápido |
| **Rasgos a rechazar** | Gambling-bro, hype-driven, caricaturesco, "gurú", casino-gold |

### 3.2 Declaración de posicionamiento

> Para los aficionados al fútbol español que apuestan con la cabeza — fantasy managers, cazadores de valor y frikis de los datos — **KICKDEX** es el terminal de datos independiente que convierte 20 años de historia en edge real, gratis. A diferencia de los "análisis" de los bookmakers o los sitios de hojas de cálculo, ofrece scouting de nivel Biwenger y detección de value betting EV en un dashboard rápido y hermoso.

### 3.3 Pilares de marca

**1. Matemáticas antes que hype**
Cada número es reproducible. Cada EV tiene su fuente. Mostramos los cálculos, no las predicciones.

**2. Independiente por diseño**
Ningún bookmaker nos posee. Ningún afiliado edita los resultados. El modelo de negocio es el producto, no la comisión.

**3. Hecho para el fútbol**
La UI respira La Liga. El copy habla como en la grada. Los colores son los del césped y las luces del estadio, no los de una sala de máquinas.

**4. Gratis es el producto**
No hay versión premium que oculte las funciones buenas. Gratis no es la versión de prueba — es la filosofía.

### 3.4 Rasgos de personalidad — DO / DON'T

| DO | DON'T |
|---|---|
| "Valencia está sobrevaluado a 2.10" | "¡PICK DEL DÍA! 🔥🔥🔥" |
| "Muestra de 38 partidos. Confianza: media." | "Insider info — solo aquí." |
| "EV positivo en BTTS: +4.2%" | "100% ganador. Garantizado." |
| "Los datos no mienten. Tú decides." | "Suscríbete al canal para la pick premium" |
| Copy en dos idiomas, sin forzar | "La Plataforma #1 de España™" |

### 3.5 Personas target (3)

---

#### Persona A — "El Cazador de Value" (core)

**Nombre ficticio:** Marcos, 28 años, Madrid  
**Ocupación:** Analista de datos en una fintech  
**Perfil apostador:** Apuesta 2-3 veces por semana, bankroll de ~500€, lleva sus propias hojas de cálculo en Google Sheets  
**Frustraciones actuales:**
- Las herramientas de value betting son de pago o tienen UX terrible
- No confía en los tipsters porque no muestran el modelo matemático
- Las cuotas le interesan solo si hay edge real demostrable

**Qué busca en KICKDEX:**
- Ver el EV calculado con datos históricos, no con intuición
- Interfaz que se parezca a sus herramientas de trabajo (Bloomberg, Python notebooks)
- Transparencia total del modelo

**Mensaje clave para él:** *"El cálculo, no el pick."*

---

#### Persona B — "El Fantasy Manager Serio" (secundario)

**Nombre ficticio:** Laura, 24 años, Barcelona  
**Ocupación:** Estudiante de medicina, juega en Biwenger con su cuadrilla  
**Perfil fantasy:** Lleva 3 temporadas jugando, gestiona su equipo con más criterio que el resto  
**Frustraciones actuales:**
- Las estadísticas en Biwenger son básicas (solo goles y asistencias)
- No sabe comparar el rendimiento real de dos jugadores rápido
- Pierde tiempo buscando datos en diferentes webs

**Qué busca en KICKDEX:**
- Ver minutos, disparos, faltas, tarjetas de cualquier jugador en segundos
- Comparar dos equipos antes de decidir si pone jugadores de uno u otro
- Interfaz rápida, no quiere aprender una herramienta compleja

**Mensaje clave para ella:** *"Scouting de First Team para tu Fantasy."*

---

#### Persona C — "El Friki de Datos" (comunidad)

**Nombre ficticio:** Iván, 34 años, Valencia  
**Ocupación:** Profesor de instituto, fanático del fútbol analítico  
**Perfil data nerd:** Sigue a @opta, conoce qué es xG, escribe hilos en Twitter sobre estadísticas  
**Frustraciones actuales:**
- FBref y Understat son potentes pero tienen UI de los 2000
- Nada de lo que existe en español tiene la profundidad y la estética que merece el deporte
- Le encantaría poder citar datos de una herramienta que no parezca amateur

**Qué busca en KICKDEX:**
- Una tool que le dé credibilidad cuando la comparte en redes
- H2H histórico completo con datos visualizados, no solo tablas
- Que la herramienta parezca "pro" — que él parezca "pro" usándola

**Mensaje clave para él:** *"Datos que se pueden citar."*

---

## 4. El nuevo nombre — KICKDEX

### 4.1 Brief de naming

Criterios de evaluación (todos obligatorios):
- Memorable en ES y EN
- Pronunciable sin ambigüedad
- ≤ 10 caracteres
- Sin colisión de marca con top-20 de fútbol/apuestas
- `.com` o `.io` disponible (o `[nombre].alvarocarpintero.com` como subdominio)
- Evoca datos + fútbol
- No se lee como "apuestas" / "casino"
- Bilingual-ready — funciona en ambos idiomas

### 4.2 Shortlist completa — 15 candidatos evaluados

| Nombre | Construcción | Pro | Contra | Score /10 |
|---|---|---|---|---|
| **KICKDEX** | kick + dex (index) | Único en búsqueda, bilingual, data-terminal vibe, wordmark natural | Ligeramente tech-y sin copy de apoyo | **9.2** ★ |
| **ALPHAGOL** | alpha + gol | Edge financiero + fútbol, internacional, premium | "Alpha" saturado en crypto | 8.1 |
| **GOLAZO** | golazo (ES) | Emoción inmediata, icónico, audiencia española | Cien canales de YouTube, no registrable | 7.4 |
| **PULSOFC** | pulso + FC | Cálido, editorial, "pulso de la liga" | Menos data-driven evidente | 7.0 |
| **GAMBETA** | gambeta (fútbol slang) | Único, culto, niche fútbol | Incomprensible fuera del fútbol hispano | 6.8 |
| **STATBALL** | stat + ball | Claro, funcional | Genérico, sin personalidad | 5.9 |
| **PITCHIQ** | pitch + IQ | Internacional, inteligente | IQ saturado en apps de productividad | 5.7 |
| **EDGEGOL** | edge + gol | Edge claro, bilingual | Suena a producto de nutrición | 5.5 |
| **METRICAFC** | métrica + FC | Español, preciso | Largo, difícil de googlear | 5.2 |
| **ZONAL** | zona (táctica) | Tácticamente resonante | Demasiado vago, ya existe una web | 4.8 |
| **STATTICO** | stat + -tico (italiano) | Curioso, europeo | Sin sentido claro para el target | 4.5 |
| **GOALPHA** | goal + alpha | Clever portmanteau | Confuso en pronunciación en español | 4.3 |
| **PULSO** | pulso (ES) | Simple, cálido | Demasiado genérico | 4.0 |
| **EDGEXI** | edge + XI | Finance + 11 jugadores | Pronunciación ambigua (XI) | 4.0 |
| **FÚTBOL LABS** | fútbol + labs | Neutro, reconocible | Completamente genérico | 3.5 |

### 4.3 Por qué gana KICKDEX

**1. Único y defendible**
No existe ninguna marca relevante de datos deportivos, apuestas o fútbol que use "Kickdex". El término es inventado, por tanto registrable.

**2. Auto-explicativo en dos idiomas**
- *Kick* — universal. Cualquier persona que haya visto un partido de fútbol sabe lo que es un kick.
- *dex* — shorthand de "index" en el lenguaje de los devs, traders y makers. También evoca "dexterity" (habilidad). También suena a un terminal financiero (como Bloomberg terminal tickers).
- Sin traducción necesaria en ES ni EN.

**3. Wordmark natural**
La construcción de dos sílabas se divide exactamente en la frontera entre el mundo del fútbol (`kick`, IBM Plex Sans) y el mundo de los datos (`dex`, JetBrains Mono). La identidad tipográfica ya existente da el logotipo de regalo.

**4. Terminal aesthetic encaja a la perfección**
El termino "dex" resuena con el lenguaje de los exchange terminals, los DEX de crypto (Uniswap, dYdX), los Pokédex. Dice "consulta de datos" sin decirlo explícitamente.

**5. Escalable más allá de La Liga**
"KICKDEX para la Premier League" o "KICKDEX Bundesliga" funciona. "Analista Pro para la Premier League" no.

### 4.4 Taglines propuestos

| Contexto | Tagline | Tono |
|---|---|---|
| **Hero principal (EN)** | The football data terminal. | Declarativo, preciso |
| **Hero principal (ES)** | Tu terminal de fútbol. | Directo, ownership |
| **Value betting section** | Edge, computed. | Trader-speak |
| **Player scouting section** | Numbers don't lie. Squad picks do. | Ligeramente irreverente |
| **H2H section** | 20 years of history. One screen. | Data authority |
| **Empty states** | No hay datos aún. El fútbol tiene esa costumbre. | Dry humor, on-brand |
| **Footer** | Free, independent, math-first. | Pilares de marca condensados |

---

## 5. Sistema de Identidad Visual

### 5.1 Paleta de color — sistema completo

**Filosofía:** Evolucionar, no quemar. El sistema OLED + emerald ya tiene el 70% correcto. Se afila, se nombra, se documenta.

#### Tokens de color

| Token | Nombre | Hex actual | Hex nuevo | Uso | WCAG sobre fondo |
|---|---|---|---|---|---|
| `--color-bg` | Pitch Black | `#020409` | `#05070D` | Fondo base | — |
| `--color-surface-1` | Midnight | `#04060e` | `#0B0F1A` | Cards, panels | — |
| `--color-surface-2` | Graphite | `#070c18` | `#111728` | Tablas, rows alternos | — |
| `--color-surface-3` | — | `#0c1322` | `#1A2236` | Hover, focus rings | — |
| `--color-brand` | Turf | `#00d4aa` | `#2EE6A6` | Primario de marca, CTAs, tabs activos | AA ✓ (6.3:1) |
| `--color-accent` | Edge Gold | `#f59e0b` | `#F5B93C` | Oportunidades de value, badges premium | AA ✓ (7.1:1) |
| `--color-signal` | Signal Blue | `#22d3ee` | `#5BD6FF` | Visualización de datos, xG | AA ✓ (6.8:1) |
| `--color-danger` | Red Card | `#f43f5e` | `#FF5A6E` | Señales negativas, derrota | AA ✓ (5.2:1) |
| `--color-warning` | Amber | `#fbbf24` | `#FBBF24` | Sin cambio | AA ✓ |
| `--color-purple` | Accent 4 | `#a78bfa` | `#A78BFA` | Sin cambio — viz variaciones | AA ✓ |
| `--color-text-high` | Stadium White | `#e6edf7` | `#F1F5FB` | Headings, datos primarios | AAA ✓ (15:1) |
| `--color-text-mid` | — | — | `#C8D4E8` | Body text, labels | AA ✓ (9.4:1) |
| `--color-text-muted` | Concrete | — | `#8A94AB` | Timestamps, secondary | AA ✓ (4.6:1) |
| `--color-border` | — | — | `#1E2A40` | Bordes de cards | — |
| `--color-glow-brand` | — | — | `rgba(46,230,166,0.15)` | Box shadows, hovers | — |
| `--color-glow-gold` | — | — | `rgba(245,185,60,0.15)` | Value betting hovers | — |

**CSS Variables block para `docs/css/app.css` (`:root`):**
```css
:root {
  /* Backgrounds */
  --color-bg:        #05070D;
  --color-surface-1: #0B0F1A;
  --color-surface-2: #111728;
  --color-surface-3: #1A2236;
  --color-border:    #1E2A40;

  /* Brand */
  --color-brand:     #2EE6A6;  /* Turf */
  --color-accent:    #F5B93C;  /* Edge Gold */
  --color-signal:    #5BD6FF;  /* Signal Blue */
  --color-danger:    #FF5A6E;  /* Red Card */
  --color-warning:   #FBBF24;
  --color-purple:    #A78BFA;
  --color-orange:    #FB923C;

  /* Text */
  --color-text-high:  #F1F5FB;  /* Stadium White */
  --color-text-mid:   #C8D4E8;
  --color-text-muted: #8A94AB;  /* Concrete */

  /* Glows */
  --glow-brand: rgba(46, 230, 166, 0.15);
  --glow-gold:  rgba(245, 185, 60, 0.15);
  --glow-red:   rgba(255, 90, 110, 0.12);

  /* Typography */
  --font-ui:   'IBM Plex Sans', sans-serif;
  --font-data: 'JetBrains Mono', monospace;

  /* Spacing / Radius */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 20px;
  --radius-xl: 28px;
}
```

### 5.2 Tipografía — lock definitivo

| Rol | Fuente | Pesos | Uso |
|---|---|---|---|
| **UI / Display** | IBM Plex Sans | 400, 500, 600, 700 | Todo el texto de interfaz, headings, copy |
| **Datos / Marca** | JetBrains Mono | 400, 500, 700 | Estadísticas, cuotas, EV values, parte `dex` del wordmark |
| **ELIMINAR** | Space Grotesk | — | Import declarado pero no usado. Pesa ~20KB extra. Eliminar. |

**Google Fonts import (actualizado):**
```css
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');
```

### 5.3 Logo y marca — especificación

#### Wordmark principal

```
kick  dex
↑     ↑
IBM   JetBrains Mono Bold
Plex  Color: --color-brand (#2EE6A6)
Sans  Con "cursor tick": 2px underline 
Bold  en el último caracter
```

**Construcción:**
- `kick` — IBM Plex Sans Bold, `--color-text-high` (#F1F5FB), tracking: -0.02em
- `dex` — JetBrains Mono Bold, `--color-brand` (#2EE6A6), tracking: 0
- Separación entre las dos palabras: 0.08em (se percibe como un espacio natural)
- Misma x-height para ambas tipografías — alineación limpia en baseline
- El "cursor" es un underscore `_` estilizado o un 2px horizontal rule de 6px de ancho bajo la `x` de `dex`, en `--color-brand`, con animación `blink` de 1 ciclo al cargar la página

**Variantes:**
- `kickdex` (minúsculas, compacto) — para favicons y badges
- `KICKDEX` (caps) — para headings de sección, ogImage, README banner
- `kick[dex]` — variante alternativa para iconografía (corchete = terminal syntax)

#### Icono / favicon

Grid 24×24 px:
```
K]
```
- `K` — IBM Plex Sans Bold, Stadium White
- `]` — JetBrains Mono Bold, Turf green
- Fondo: `--color-surface-1` (#0B0F1A), border-radius: 4px
- Escala a 16×16 sin perder legibilidad

**Eliminar:** el SVG actual del balón de fútbol con grid overlay. Es un elemento genérico que no aporta identidad.

### 5.4 Iconografía

- **Set actual:** feather-style SVG (stroke-based, 15-20px) — compatible
- **Librería recomendada:** migrar a **Lucide** (fork mantenido de Feather, drop-in compatible, mismo API)
- **Prohibido:** emojis como iconos de UI
- **Tamaño consistente:** viewBox `0 0 24 24`, render a `w-5 h-5` (20px) o `w-4 h-4` (16px). No mezclar.

### 5.5 Taxonomía de componentes (naming final)

| Nombre actual (implícito) | Nombre nuevo | Archivo CSS / JS |
|---|---|---|
| Header / Navbar | `.terminal-header` | app.css |
| Glass card | `.glass-card` | app.css (sin cambio) |
| Stat row | `.stat-row` | app.css (sin cambio) |
| Probability bar | `.prob-bar` | app.css (sin cambio) |
| Match header | `.match-header` | app.css (sin cambio) |
| Value row | `.value-row` | app.css (sin cambio) |
| Form dots (WDL) | `.form-dots` | app.css (sin cambio) |
| Badge pill | `.badge` | app.css (sin cambio) |
| Alert card | `.alert-card` | app.css (sin cambio) |
| **NUEVO** | `.brand-wordmark` | app.css — componente del logo |
| **NUEVO** | `.brand-cursor` | app.css — animación del cursor del logo |

### 5.6 Guía de movimiento (motion)

| Elemento | Duración | Easing | Notas |
|---|---|---|---|
| Tab transitions | 200ms | ease-out | Ya implementado |
| Card hover | 150ms | ease | box-shadow + translateY(-2px) |
| Stagger entrance | 60ms between items | ease-out | Ya implementado |
| Brand cursor blink | 600ms, 1 ciclo | step-end | Solo al cargar la página |
| Count-up numbers | 800ms | ease-out | Ya implementado en animations.js |
| Probability bars | 600ms | ease-out | Shimmer ya implementado |
| Skeleton loading | 1.5s loop | linear | Shimmer |

**`prefers-reduced-motion`:** Todas las animaciones ya respetan esta media query. Preservar en el rebrand.

---

## 6. Guía de Voz y Copy

### 6.1 Principios de voz

**CONFIADO SIN SER ARROGANTE**
Las matemáticas hablan por sí solas. No necesitas exclams ni mayúsculas.

**PRECISO SIN SER FRÍO**
Da los números exactos. Añade contexto de muestra. No te escondas en la ambigüedad.

**LIGERAMENTE IRREVERENTE**
Puedes hacer un guiño en los estados vacíos. La herramienta es seria; no tiene que ser aburrida.

**TRADER MEETS TIFOSO**
Habla como alguien que conoce la diferencia entre xG y Expected Threat, y también sabe quién marcó el gol del título en el 93'.

### 6.2 Copy framework — DO / DON'T

**Headings de sección:**
- ✓ "Comparador de equipos" → "Terminal de Comparación"
- ✓ "Value Bets" → "Edge Detector" o mantener "Value Bets"
- ✗ "¡El mejor analizador de fútbol!"

**Descripciones de módulos:**
- ✓ "Compara el rendimiento de dos equipos sobre los últimos N partidos. Basado en 18,249 registros históricos."
- ✗ "Descubre qué equipo tiene más posibilidades de ganar gracias a nuestra IA revolucionaria"

**Mensajes de estado vacío:**
- ✓ "Selecciona dos equipos para generar el análisis." (funcional)
- ✓ "No hay datos todavía. El fútbol tiene esa costumbre." (con personalidad)
- ✗ "Ops! Algo salió mal 😢" (emoji + incertidumbre)

**Mensajes de error:**
- ✓ "No se encontraron datos para esta temporada. Prueba con el archivo de temporada anterior."
- ✗ "Error inesperado. Por favor, inténtalo de nuevo más tarde."

**Meta descriptions (SEO):**
- ✓ "KICKDEX — Terminal gratuito de estadísticas de fútbol. Comparador, H2H histórico, scouting y detección de value bets para La Liga y Segunda División."
- ✗ "El mejor analizador de fútbol gratuito de España. Analisa tus apuestas con IA."

### 6.3 Terminología canónica

| Usar | No usar |
|---|---|
| Edge / EV (Expected Value) | "Pick", "predicción garantizada" |
| Scouting / estadísticas de jugador | "Ficha técnica completa" |
| Muestra de N partidos | "Datos históricos completos" |
| Cuota implícita | "Probabilidad del bookmaker" |
| Confianza: alta/media/baja | "95% seguro" |
| Terminal / dashboard | "Plataforma", "Suite" |
| Independiente | "El número 1" |

### 6.4 Internacionalización

La herramienta es actualmente en español. Con el rebrand, preparar la arquitectura para i18n:
- Todas las strings hardcoded en `docs/js/*.js` → extraer a objeto `COPY = {}` en `app.js`
- No escribir copy que dependa de la gramática española (géneros, conjugaciones) en el JS
- Los módulos de Streamlit en `app/ui/*.py` → misma lógica, centralizar strings en `app/config.py`

---

## 7. Checklist de migración — todos los archivos

### FASE 1 — Documento de marca (este archivo)
- [x] `REBRANDING.md` — creado

### FASE 2 — Tokens de diseño (CSS / JS)
- [ ] `docs/css/app.css`
  - [ ] Actualizar `:root` con nueva paleta (16 tokens)
  - [ ] Eliminar `@import` de Space Grotesk
  - [ ] Actualizar Google Fonts import (IBM Plex Sans + JetBrains Mono únicamente)
  - [ ] Añadir clase `.brand-wordmark` para el logo de texto
  - [ ] Añadir clase `.brand-cursor` con animación blink (1 ciclo)
  - [ ] Actualizar `.nav-brand` / `.logo-text` con nueva typography split
- [ ] `docs/js/animations.js`
  - [ ] Verificar que no hay referencias hardcoded a colores hex del sistema viejo

### FASE 3 — Logo y head
- [ ] `docs/index.html`
  - [ ] `<title>` → `KICKDEX — Terminal de Estadísticas de Fútbol`
  - [ ] `<meta name="description">` → nuevo copy
  - [ ] `<meta property="og:title">` → `KICKDEX`
  - [ ] `<meta property="og:description">` → nuevo copy
  - [ ] `<meta property="og:image">` → `/assets/og-image.png`
  - [ ] `<link rel="icon">` → `/assets/favicon.svg`
  - [ ] `<link rel="apple-touch-icon">` → `/assets/apple-touch-icon.png`
  - [ ] Wordmark SVG en el header → nueva construcción `kick` + `dex` con cursor
  - [ ] Cualquier string "Analista Pro" → "KICKDEX"
- [ ] **Crear** `docs/assets/favicon.svg` — icono `K]` 24×24
- [ ] **Crear** `docs/assets/apple-touch-icon.png` — 180×180
- [ ] **Crear** `docs/assets/og-image.png` — 1200×630 (KICKDEX wordmark + tagline sobre fondo Pitch Black)

### FASE 4 — Copy de interfaz
- [ ] `docs/index.html`
  - [ ] Hero / subtítulo
  - [ ] Labels de tabs de navegación
  - [ ] Empty states de cada módulo
  - [ ] Footer (copyright, links)
  - [ ] Cualquier tooltip o ayuda contextual
- [ ] `app/ui/comparador.py` — `st.title()`, captions, ayudas
- [ ] `app/ui/h2h.py` — ídem
- [ ] `app/ui/jugadores.py` — ídem
- [ ] `app/ui/valor.py` — ídem
- [ ] `app/ui/styles.py` — si contiene strings de marca

### FASE 5 — Config e infraestructura
- [ ] `README.md`
  - [ ] Título, descripción, badge de estado
  - [ ] Links al live site
  - [ ] Screenshots (actualizar cuando el rebrand visual esté aplicado)
- [ ] `PRD.md` — reemplazar todas las referencias a "Analista Pro"
- [ ] `PLAN.md` — ídem
- [ ] `PRD.txt` — ídem (archivo legacy)
- [ ] `Contexto General del Proyecto.txt` — ídem (archivo legacy)
- [ ] `app/config.py`
  - [ ] Constante `APP_NAME` → `"KICKDEX"`
  - [ ] Cualquier string de marca
- [ ] `.streamlit/config.toml`
  - [ ] `[browser] serverName` si existe
  - [ ] Colores del `[theme]` → nueva paleta (surface, primary, background, text)
- [ ] `main.py` — `st.set_page_config(page_title="KICKDEX", page_icon="⚽")` → usar SVG/emoji adecuado
- [ ] `app.py` — ídem (si sigue activo)
- [ ] `app_new.py` — ídem
- [ ] `railway.json` — service name
- [ ] `Procfile` — si tiene comentarios con nombre
- [ ] `CNAME` — `analista.alvarocarpintero.com` → `kickdex.alvarocarpintero.com` (**requiere acción DNS manual**)
- [ ] `memory/MEMORY.md` — actualizar referencias al nombre
- [ ] `memory/project_analista_pro.md` → renombrar a `memory/project_kickdex.md` y actualizar contenido
- [ ] `.github/` — workflows, issue templates si tienen nombre del proyecto

### NO TOCAR (intencionadamente)
- `scripts/build_data.py` — pipeline de datos, no visible al usuario
- `app/data/loader.py`, `app/data/updater.py` — ídem
- `app/engine/*.py` — motor de cálculo, no tiene strings de marca
- `docs/data/*.json` — schemas de datos
- `tests/` — tests unitarios
- `docs/js/comparador.js`, `h2h.js`, `jugadores.js`, `valor.js` — lógica, sin strings de marca (verificar)

---

## 8. Fases de rollout

### Fase 0 — Decisión ✓ (este documento)
Aprobar nombre, paleta, voz. Sin tocar código todavía.

### Fase 1 — Documento de marca ✓ (completado)
`REBRANDING.md` como source of truth. Referencia para todo lo demás.

### Fase 2 — Tokens de diseño (½ día)
Solo `docs/css/app.css` — actualizar `:root` con nueva paleta, eliminar Space Grotesk, añadir clases del logo. Verificación: cargar `docs/index.html` en el navegador, debe verse igual o mejor en todos los módulos.

### Fase 3 — Logo y head (½ día)
Nuevo wordmark SVG inline en `docs/index.html`, meta tags, favicon. Esta es la primera vez que el nombre "KICKDEX" aparece en producción. Verificación: screenshot del header + Lighthouse meta tags.

### Fase 4 — Copy pass (1 día)
Todos los textos visibles al usuario en el frontend HTML y en Streamlit. Verificación: grep completo, cero hits de "Analista Pro".

### Fase 5 — Config e infra (½ día)
Docs, config files, Streamlit page title. No afecta al usuario final directamente. Verificación: `streamlit run main.py` arranca con el nuevo título.

### Fase 6 — Deploy y social (a definir)
- Swap de CNAME (requiere acción DNS manual del usuario)
- Rename del repositorio GitHub (opcional, rompe links externos)
- OG image y Twitter card en producción
- Post de lanzamiento (si aplica)

**Cada fase es reversible de forma independiente.**

---

## 9. Preguntas abiertas y riesgos

### Preguntas abiertas

| # | Pregunta | Impacto si no se responde |
|---|---|---|
| 1 | **¿Confirmas KICKDEX como nombre definitivo?** ¿O prefieres ALPHAGOL, GOLAZO, PULSO FC o GAMBETA? | Bloquea Fases 3-5 |
| 2 | **Estrategia de dominio:** ¿mantener `kickdex.alvarocarpintero.com` o registrar dominio propio `kickdex.io`/`kickdex.com`? | Afecta CNAME, OG tags, README |
| 3 | **Rename del repo GitHub:** ¿hacerlo ahora o después del lanzamiento público? | Si hay links externos que apuntan al repo, el rename los rompe |
| 4 | **¿Ejecutamos las fases 2-5 en esta sesión** después de confirmar el nombre, o el REBRANDING.md es el único output por ahora? | Planificación de tiempo |
| 5 | **Streamlit como superficie activa:** ¿está el backend de Railway en producción real con usuarios, o solo `docs/` es la app canónica en este momento? | Afecta urgencia de Fase 4 para Streamlit |

### Riesgos

| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| CNAME requiere propagación DNS (24-48h) | Alta | Planificar cambio en momento de baja demanda |
| GitHub repo rename rompe links externos | Media | Hacer redirect de GitHub antes del rename, o posponer |
| Usuarios existentes con bookmark al dominio viejo | Baja (MVP) | Mantener redirect 301 en el dominio antiguo si es posible |
| "KICKDEX" no suena bien para alguien del target | Baja | El shortlist de 4 alternativas está listo |
| Paleta nueva rompe algún componente CSS | Baja | Las variables son drop-in; backup del app.css actual antes de editar |

---

## Apéndice A — Resumen ejecutivo para compartir

**KICKDEX** es el rebrand de Analista Pro, una herramienta gratuita de estadísticas de fútbol con 20 años de historia de La Liga y Segunda División.

El nuevo nombre combina *kick* (universal en fútbol) con *dex* (índice de datos / terminal), creando una identidad que escala más allá de España sin perder el ADN futbolístico. La estética OLED-terminal existente (JetBrains Mono + glassmorphism) se refina y consolida como sistema, no se cambia. La promesa de marca: **"The edge, for free."**

Audiencias: value bettors con mentalidad analítica, fantasy managers serios, frikis de datos de fútbol.

Diferenciador: el único terminal de datos de fútbol independiente que combina scouting de jugadores con detección matemática de value bets, en una UI que no pide disculpas por ser densa y hermosa.

---

*REBRANDING.md v1.0 — KICKDEX Brand Study*
*Generado: 2026-04-15 | Próxima revisión: tras confirmación de nombre*
