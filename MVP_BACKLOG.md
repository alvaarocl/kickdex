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

- [x] **P0.2 · Tests de edge math** *(✓ codex+claude · 2026-05-01)*
  - 15 tests: implied prob, calculate_edge, edge_confidence, contrato edges.json. Pasan en 0.05s.

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

- [x] **P1.2 · Banner/badge de cobertura visible en tabs** *(✓ claude · 2026-05-01)*
  - `coverage-strip` global bajo tabs, lee `data_status.json` + `meta.json`. Linkea a `/coverage`. i18n.

- [x] **P1.3 · Fallback decente cuando un partido no tiene jugadores** *(✓ claude · 2026-05-01)*
  - `comparador.js`: mensaje explica feed (FBref/soccerdata) + link a `coverage.html`.

- [x] **P1.4 · Logos SVG con tagline V3** *(✓ claude · 2026-05-01)*
  - Verificado: ambos SVG ya dicen "Football intelligence, indexed.". No hay rastro de la tagline antigua.

- [x] **P1.5 · README alineado con stack estático-first** *(✓ claude · 2026-05-01)*
  - Reescrito con arquitectura, comandos locales, estructura completa. Streamlit marcado como interno.

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

- [x] **P2.4 · Limpieza de tokens CSS duplicados** *(✓ claude · 2026-05-01)*
  - `--green/yellow/blue` ahora son alias de `--brand/gold/brand2`. Una única fuente de verdad.

---

## P3 · Pulido pre-launch

> Mapeado a Sprint 4 de CLAUDE.md.

- [x] **P3.1 · `robots.txt` y `sitemap.xml`** *(✓ claude · 2026-05-01)*
  - `docs/robots.txt` y `docs/sitemap.xml` con 8 URLs (raíz, methodology, coverage, report, legales).

- [x] **P3.2 · Canonicals + mejores titles/descriptions en legales** *(✓ claude · 2026-05-01)*
  - Canonical + meta description añadidos en index, methodology, coverage, aviso-legal, privacidad, cookies, terminos.

- [x] **P3.3 · Lazy-load `h2h.json` (4.4 MB)** *(✓ claude · 2026-05-01)*
  - H2H sale del Promise.all crítico. Carga en background tras initial render. Evento `kdx:h2h-ready` notifica. H2H tab muestra spinner mientras carga.
  - **Pendiente futuro:** particionado real por liga (post-MVP).

- [x] **P3.4 · Botón "Reportar error / sugerir mejora"** *(✓ claude · 2026-05-01)*
  - `mailto:hola@kickdex.com` en footer (i18n `footer_feedback`). Reemplazar email cuando esté el real.

- [x] **P3.5 · Onboarding microcopy en primera entrada al app** *(✓ claude · 2026-05-01)*
  - `cmp_prompt` reescrito como pasos 1-2-3 ES/EN.

- [x] **P3.6 · Match Report linkeado desde Comparador** *(✓ claude · 2026-05-01)*
  - `buildExportReport()` en `comparador.js` añade card final con CTA `> export report_` que abre `report.html` con params.

- [ ] **P3.7 · Lighthouse / a11y / mobile audit** *(skip · requiere herramientas externas)*

- [x] **P3.8 · Hero counters leen `meta.json`** *(✓ codex · 2026-04-30)*
  - `updateLandingMetrics()` actualiza el primer contador con `meta.total_matches` real.

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
