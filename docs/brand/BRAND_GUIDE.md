# KICKDEX — Brand System V3

**Football intelligence, indexed.**

KICKDEX no es una web de stats. Es una **terminal de inteligencia futbolística**. Cada decisión de marca refuerza esa categoría — densa, matemática, sin ruido de casa de apuestas.

---

## 1. Posicionamiento

- **Categoría propia:** Football Intelligence Terminal.
- **Antagonista:** ValueStats (funcional pero opaco), tipsters, casas de apuestas.
- **Promesa:** edges en verde, riesgo en rojo, el resto es ruido. Gratis. Independiente. Matemático.

### Manifiesto (60 palabras)

> Las casas de apuestas venden suerte. Los blogs venden picks. KICKDEX no vende nada. Indexamos cada partido, cada jugador y cada cuota en una sola terminal y dejamos que el dato hable. Si hay edge, lo ves en verde. Si hay riesgo, lo ves en rojo. El resto es ruido. Gratis. Independiente. Matemático.

### Tagline system

| Nivel | Línea |
|---|---|
| Master | *Football intelligence, indexed.* |
| Producto | *The terminal for football edges.* |
| Marketing | *Read the match before it's played.* |
| Status (CLI) | `> NO LOGIN. NO ADS. NO PICKS.` |

---

## 2. Logo

Asset oficial: monograma `K▌` dentro de tile + wordmark `kickdex▌` con cursor de terminal.

- `brand/kickdex-logo-dark.svg` — fondo Pitch Black.
- `brand/kickdex-logo-light.svg` — fondo Report White.
- `brand/kickdex-monogram.svg` — solo tile, para favicon / app icon / avatar social.

### Reglas

- Wordmark en **un solo color** (Report White en dark, Pitch Black en light). El acento de marca vive en el **cursor `▌`** después de `dex`.
- Cursor parpadea (1s, opacity 1↔0.2) en web. En estático, fijo en Turf.
- Padding mínimo alrededor del logo = altura de la `K`.
- Tamaño mínimo wordmark: 96px ancho. Por debajo, usar monograma.
- Prohibido: degradados sobre el wordmark, sombras, outlines, rotación, distorsión.

---

## 3. Paleta — 4 + 2 con jerarquía estricta

### Modo oscuro (producto)

| Token | Hex | Rol | Cuándo usar |
|---|---|---|---|
| `--bg` Pitch Black | `#05070D` | Lienzo | Fondo único |
| `--surface` Midnight | `#0B0F1A` | Superficie | Cards, tablas |
| `--edge` Turf | `#2EE6A6` | **Acento primario** | Acción, selección, estado activo, value en verde |
| `--gold` Edge Gold | `#F5B93C` | **Señal de valor** | SOLO para edge detectado / KPI héroe |
| `--risk` Red Card | `#FF5A6E` | Riesgo | Solo alertas, drops fuertes, lesiones |
| `--live` Data Cyan | `#5BD6FF` | Dato vivo | SOLO streaming / actualizaciones en tiempo real |

### Modo claro (informes y exportables)

| Token | Hex | Rol |
|---|---|---|
| Report White | `#F8FAF7` | Lienzo |
| Field Mist | `#E8F1EC` | Superficie |
| Deep Turf | `#087B61` | Acento primario |
| Value Ochre | `#C77C00` | Señal de valor |
| Alert Red | `#D94357` | Riesgo |
| Data Blue | `#2B8FD9` | Dato vivo |

### Reglas de paleta

1. **Cyan y Gold son escasos.** Si una pantalla los usa los dos, uno sobra.
2. Turf domina la jerarquía secundaria; Gold es el "uno y único" reservado al value.
3. Para nuevos estados, usar opacidades de los 6 tokens — **no añadir colores**.
4. Light mode SOLO para reports/exportables/deck comercial. Dark es la identidad del producto.

---

## 4. Tipografía

| Uso | Familia | Pesos |
|---|---|---|
| Marca, métricas, número-héroe | `IBM Plex Mono` | 500 / 700 |
| UI y lectura | `Inter` (fallback `IBM Plex Sans`) | 400 / 500 / 600 |
| Datos densos en producto | `JetBrains Mono` | 400 / 600 |

### Escala "Edge Display"

Reservada para el número-héroe (probabilidad, edge %, KPI principal).

```
edge-xxl  96px / 0.9 / -0.04em / IBM Plex Mono 700
edge-xl   64px / 0.95 / -0.03em / IBM Plex Mono 700
edge-lg   48px / 1 / -0.02em / IBM Plex Mono 700
```

Siempre con `font-feature-settings: "tnum" "ss01"`.

### Escala UI

```
display   40px / 1.1
h1        32px / 1.2
h2        24px / 1.3
h3        20px / 1.4
body      15.5px / 1.6
caption   13px / 1.4 / uppercase / +0.08em tracking
mono-data 14px / 1.4 / IBM Plex Mono
```

---

## 5. El Edge Number — activo de marca

Tu Bloomberg-moment. **Cada captura de KICKDEX en redes debe tener UN Edge Number.**

Anatomy:

```
    ┌──────────────────────────────┐
    │ EDGE                         │
    │                              │
    │   +12.8%                     │  ← IBM Plex Mono 96px, gold
    │   ━━━━━━━━━━━━━━━━━━━━       │  ← sparkline 1px Turf
    │                              │
    │ Real Madrid · ML · Bet365    │  ← caption Inter 13px muted
    └──────────────────────────────┘
```

Aparece en: hero de landing, card principal de cada match, OG images, loading screens, posts sociales.

Ver implementación en `docs/css/app.css` (sección `EDGE NUMBER — V3`) y `docs/js/edge.js`.

---

## 6. Lenguaje visual — "Terminal grid"

- Retícula hairline 1px Turf @ 8% opacity como fondo de hero.
- Todo número live entre `[ ]` o con prefijo `> ` cuando provenga del feed en vivo.
- Tablas con `tabular-nums` + zebra muy sutil (3% blanco).
- Cursor `▌` parpadeante (1s) como firma de marca.
- Esquinas: 16px en cards, 10px en chips, 24px solo en hero/dashboard exterior.
- Iconografía: lineal, 1.5px stroke, jamás rellena.
- Micro-anim: números que "tipean" al cargar (200ms stagger). Nada decorativo.

---

## 7. Voz y tono

Directa, numérica, segura. Una terminal experta, no una casa de apuestas.

### Sí

- "Edge detectado"
- "Forma subiendo"
- "Riesgo alto"
- "Señal de valor"
- "Confianza media"
- `> reading market…`

### No

- "Apuesta segura"
- "Gana fijo"
- "Dinero fácil"
- "Pick infalible"
- Emojis de dinero, fuego, cohete

### Disclaimer (también marca)

```
> RISK NOTICE: edges are estimates, not guarantees. Play responsibly.
```

No legalese — es una línea de status de terminal.

---

## 8. Aplicaciones

| Activo | Reglas |
|---|---|
| **Landing** | Una sola pantalla. Hero con Edge Number. CTA único: `> launch terminal_`. Cero scroll-marketing. |
| **Match Report (PDF/PNG)** | Light mode. Una página. Edge Number arriba, tabla de stats abajo. Footer con methodology link. Activo viral compartible. |
| **OG image dinámica** | `/og?match=xxx` — dark, Edge Number central, escudos opcionales en mono. |
| **Social posts** | 3 plantillas (1:1, 9:16, 16:9). Plex Mono, Pitch Black, Edge en gold. 1 al día durante lanzamiento. |
| **Newsletter "The Edge Brief"** | Domingo, 5 partidos + 5 edges. Header con cursor parpadeante. |
| **Status badge** | Header del producto: `> NO LOGIN. NO ADS. NO PICKS.` |

---

## 9. Qué NO hacer

- No añadir colores fuera de los 6 tokens.
- No usar fotografía de jugadores ni ilustraciones figurativas.
- No copiar la densidad sin jerarquía de ValueStats.
- No usar la palabra "apuesta" en marketing — siempre "edge", "valor", "señal".
- No registrarse en directorios de tipsters.
- No degradar el wordmark con efectos.

---

## 10. Tokens de implementación

CSS variables ya definidas en `docs/css/app.css`:

```css
--bg --surface --edge --gold --risk --live
--text --text2 --muted --muted2
--font-ui --font-data --font-mono
--radius --radius-sm --radius-lg
--shadow --shadow-brand --shadow-gold
```

Componentes V3:

- `.edge-number` — número-héroe.
- `.edge-number--xl/lg/md` — variantes de tamaño.
- `.edge-cursor` — cursor parpadeante reutilizable.
- `.terminal-status` — barra de status CLI.
- `.kbd-grid` — fondo retícula hairline.

---

**Versión:** 3.0 · 2026-04-30
