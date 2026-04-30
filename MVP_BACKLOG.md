# MVP Backlog — KICKDEX

Backlog accionable y trackeable. Convenciones:

- `[ ]` pendiente · `[~]` en progreso · `[x]` completado
- Al empezar un item, cámbialo a `[~]` y añade `(WIP: <agente>)`. Commitea ese cambio.
- Al terminar, márcalo `[x]` con `(✓ <agente> · YYYY-MM-DD)`.
- **Owner:** `claude` / `codex` / `any`. Sugerencia, no ley.
- Cada item enlaza al sprint correspondiente de [`CLAUDE.md`](CLAUDE.md).
- Si descubres deuda nueva, añádela en P3 — no la dejes como TODO en código.

Última auditoría: 2026-04-30 (Claude + Codex).

---

## P0 · Bloqueadores de lanzamiento

> Sin esto, lanzar es vender humo. Mapeado a Sprint 1 de CLAUDE.md.

- [x] **P0.1 · Edge Number real con cuotas Bet365 históricas** *(✓ codex · 2026-04-30)*
  - `app/engine/edge.py` ✓ · `docs/data/edges.json` ✓ · `scripts/build_data.py` integra ✓
  - Hero conectado vía `updateHeroEdge()` en `docs/js/app.js` ✓
  - Etiquetado como `histórico · Bet365` / `live · Bet365` según `status` ✓

- [ ] **P0.2 · Tests de edge math** *(Owner: codex · Sprint 1)*
  - `tests/test_edge.py`: positivo, negativo, cuota inválida (≤1), no-edge.
  - Validar contrato JSON de `edges.json` con muestra fija.
  - Depende de: P0.1.
  - Archivos: `tests/test_edge.py` (nuevo).

- [x] **P0.3 · Calendar fixture cards muestran edge** *(✓ codex · 2026-04-30)*
  - `inicio.js:154-159` usa `getFixtureEdges(f)` + `formatEdgePercent`. Badge `.fx-edge-badge`.

- [x] **P0.4 · OG image existe y se sirve 200** *(✓ codex · 2026-04-30)*
  - `docs/og.png` generado y commiteado.

- [x] **P0.5 · Página `/methodology.html`** *(✓ codex · 2026-04-30)*
  - Linkeada desde nav (`methodology.html`) y desde "Read methodology".

- [x] **P0.6 · Página `/coverage.html`** *(✓ codex · 2026-04-30)*
  - `docs/coverage.html` + `data_status.json` + `player_coverage.json` + `leagues.json`.

- [ ] **P0.7 · Datos legales reales en aviso/privacidad/términos** *(Owner: codex + humano · Sprint 2)*
  - Pedir al humano: titular, NIF/CIF, domicilio, email contacto.
  - Reescribir `docs/aviso-legal.html`, `docs/privacidad.html`, `docs/terminos.html`, `docs/cookies.html`.
  - Voz consistente con marca; sin legalese innecesario, pero cumpliendo LSSI/GDPR.

---

## P1 · Honestidad y ajuste de expectativas

> Mapeado a Sprint 2 de CLAUDE.md.

- [x] **P1.1 · Auditar y corregir copy que sobrepromete** *(✓ claude · 2026-05-01)*
  - i18n keys actualizadas en ES/EN: `leagues_h2`, `leagues_eyebrow`, `feat_calendar_desc`, `feat_scout_desc`, `landing_f4_body`.
  - Fallback HTML en `index.html` actualizado.
  - Counter hero ya lee `meta.json` vía `updateLandingMetrics()` (codex).

- [ ] **P1.2 · Banner/badge de cobertura visible en tabs** *(Owner: any)*
  - Cada tab (Calendario, Comparador, Jugadores, Árbitros) muestra discreta línea: "Cobertura: SP1, SP2, E0… · Actualizado YYYY-MM-DD".
  - Componente reutilizable `coverage-strip` en CSS.
  - Archivos: `docs/index.html`, `docs/css/app.css`, `docs/js/app.js`.

- [ ] **P1.3 · Fallback decente cuando un partido no tiene jugadores** *(Owner: any)*
  - En `comparador.js` y `jugadores.js`, si la liga no tiene player stats, mostrar mensaje breve explicando origen y enlace a `/coverage`.
  - No mostrar "sin datos" pelado.
  - Archivos: `docs/js/comparador.js`, `docs/js/jugadores.js`.

- [x] **P1.4 · Logos SVG con tagline V3** *(✓ claude · 2026-05-01)*
  - Verificado: ambos SVG ya dicen "Football intelligence, indexed.". No hay rastro de la tagline antigua.

- [ ] **P1.5 · README alineado con stack estático-first** *(Owner: codex)*
  - Eliminar referencias a Streamlit como punto de entrada principal.
  - Documentar pipeline batch + GitHub Pages.
  - Archivos: `README.md`.

---

## P2 · Decisión de stack y limpieza

> Mapeado a Sprint 3 de CLAUDE.md. **Requiere aprobación humana antes de borrar.**

- [ ] **P2.1 · Decisión humana: ¿matar Streamlit/FastAPI o conservar como interno?** *(Owner: humano)*
  - Bloquea P2.2 y P2.3.

- [ ] **P2.2 · Si matamos: archivar Streamlit/FastAPI** *(Owner: claude · espera P2.1)*
  - Mover `main.py`, `Procfile`, `Dockerfile`, `railway.json`, `app/ui/`, `app/api/` a `archive/` o eliminar.
  - Limpiar `requirements.txt` de deps innecesarias (streamlit, fastapi, uvicorn).
  - Actualizar README.

- [ ] **P2.3 · Si los conservamos: documentar como admin interno** *(Owner: codex · espera P2.1)*
  - Header en `main.py` indicando "internal only, not public".
  - Quitar de `Procfile`/`railway.json` o señalar que no es public-facing.
  - Documentar acceso en `docs_proyecto/INTERNAL.md`.

- [ ] **P2.4 · Limpieza de tokens CSS duplicados** *(Owner: any)*
  - `--green` = `--brand`, `--green2` = `--blue`, etc. Consolidar.
  - Archivos: `docs/css/app.css`.

---

## P3 · Pulido pre-launch

> Mapeado a Sprint 4 de CLAUDE.md.

- [ ] **P3.1 · `robots.txt` y `sitemap.xml`** *(Owner: codex)*
  - `robots.txt` permite todo, sitemap apunta a `/`, `/methodology`, `/coverage`, legales.
  - `sitemap.xml` válido con `lastmod`.
  - Archivos: `docs/robots.txt` (nuevo), `docs/sitemap.xml` (nuevo).

- [ ] **P3.2 · Canonicals + mejores titles/descriptions en legales** *(Owner: codex)*
  - `<link rel="canonical">` en cada página.
  - Title/description únicos por página legal.
  - Archivos: `docs/{aviso-legal,privacidad,terminos,cookies}.html`.

- [ ] **P3.3 · Lazy-load + partition de `h2h.json` (4.4 MB)** *(Owner: claude)*
  - Particionar por liga (`h2h-SP1.json`, `h2h-E0.json`…) o por equipo (`h2h/<team-slug>.json`).
  - `h2h.js` carga el shard correspondiente al entrar en la pestaña.
  - Archivos: `scripts/build_data.py`, `docs/js/h2h.js`, `docs/data/h2h*.json`.

- [ ] **P3.4 · Botón "Reportar error / sugerir mejora"** *(Owner: any)*
  - `mailto:` o formulario simple (Formspree/Tally) en footer.
  - Archivos: `docs/index.html`, `docs/js/app.js` (i18n keys).

- [ ] **P3.5 · Onboarding microcopy en primera entrada al app** *(Owner: any)*
  - Cuando se cierra la landing por primera vez, las tabs muestran 1-2 palabras de hint sobre la cabecera ("Elige liga", "Selecciona equipos", "Analiza"). Dismissable.
  - Archivos: `docs/js/app.js`, `docs/css/app.css`.

- [ ] **P3.6 · Match Report linkeado desde Comparador** *(Owner: any)*
  - Cuando el comparador muestra resultado, botón "Export report" abre `report.html?home=...&away=...&edge=...`.
  - Archivos: `docs/js/comparador.js`.

- [ ] **P3.7 · Lighthouse / a11y / mobile audit** *(Owner: claude)*
  - Pasar Lighthouse, anotar issues, abrir items P3.x específicos.
  - Sin entregable de código directo, sólo backlog.

- [ ] **P3.8 · Hero counters leen `meta.json`** *(Owner: any)*
  - Sustituir `data-counter="85000"` por fetch a `meta.json` y rendering dinámico.
  - Archivos: `docs/index.html`, `docs/js/animations.js`.

---

## Backlog idea (post-MVP)

Items aún sin priorizar; sólo si el lanzamiento va bien.

- [ ] Integración con TheOddsAPI (free tier 500 req/mes) → live odds.
- [ ] Bot de Twitter/X publicando 3 edges del día con OG image.
- [ ] Newsletter "The Edge Brief" semanal.
- [ ] Cobertura player stats discontinua: investigar fuentes alternativas (Sofascore, Understat).
- [ ] CI: validación de calidad de `docs/data/*.json` antes de commit.
- [ ] Plausible (cookieless analytics) si llega tracking real.
- [ ] Modo deck/exportable para creadores (PDF marca + 1 partido + edges + comparativa).

---

## Changelog (items completados)

> Mover aquí items con `[x]` cuando se cierran. Mantiene la lista activa limpia.

- *(vacío hasta que se cierre el primer item)*
