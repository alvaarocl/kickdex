---
name: KICKDEX - Estado del Proyecto y Rebrand
description: Plataforma Big Data de fútbol — rebrand de Analista Pro a KICKDEX, nuevo nombre + identidad completa documentada en REBRANDING.md
type: project
---

Proyecto rebrandeado de "Analista Pro" a **KICKDEX**: terminal de datos de fútbol gratuito, alternativa a ValueStats.com. Cubre La Liga + Segunda División con 18,249 partidos históricos desde 2004.

**Why:** REBRANDING.md creado el 2026-04-15 con estudio de mercado completo, estudio de marca, nombre nuevo, paleta refinada y checklist de migración de 23 archivos.

**Nuevo nombre: KICKDEX**
- kick (fútbol, universal) + dex (índice, terminal de datos)
- Tagline: "The football data terminal." / "Tu terminal de fútbol."
- Promesa de marca: "The edge, for free."

**Estado actual (Abril 2026):**
- Frontend estático funcional en `docs/` (GitHub Pages, analista.alvarocarpintero.com)
- Backend Streamlit en Railway (en consolidación)
- REBRANDING.md completado — Fase 0 y Fase 1 completadas
- Fases 2-5 (CSS tokens, logo, copy, config) pendientes de confirmación

**Stack:**
- Frontend: HTML5 + CSS3 + Vanilla JS + Chart.js
- Backend: Python 3.11 + Streamlit + Pandas + soccerdata
- Datos: football-data.co.uk (CSV), JSON pipeline a `docs/data/`
- Deploy: GitHub Pages (static) + Railway (Streamlit)

**Identidad visual nueva (definida en REBRANDING.md):**
- Paleta: #05070D (bg), #2EE6A6 Turf (brand), #F5B93C Edge Gold, #F1F5FB Stadium White
- Fuentes: IBM Plex Sans (UI) + JetBrains Mono (datos) — Space Grotesk a eliminar
- Logo: wordmark `kick` (IBM Plex Sans Bold) + `dex` (JetBrains Mono Bold, color Turf)
- Estilo: OLED dark, glassmorphism, trading-terminal aesthetic

**Archivos clave:**
- `REBRANDING.md` → source of truth del rebrand completo
- `docs/index.html` → frontend principal (GitHub Pages)
- `docs/css/app.css` → 1433 líneas, sistema de diseño
- `docs/js/` → app.js, comparador.js, h2h.js, jugadores.js, valor.js, animations.js
- `PRD.md`, `PLAN.md` → product requirements y plan técnico
- `app/config.py`, `main.py`, `.streamlit/config.toml` → config backend

**How to apply:** Para cambios de UI, leer REBRANDING.md §5 para tokens de color y tipografía. Para copy, seguir §6. Para ejecutar la migración, seguir el checklist de §7 en orden de fases.
