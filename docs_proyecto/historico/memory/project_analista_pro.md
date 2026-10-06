---
name: Analista Pro - Estado del Proyecto
description: Contexto del proyecto Analista Pro - plataforma Big Data fútbol gratuita, alternativa a ValueStats
type: project
---

Proyecto "Analista Pro": plataforma web gratuita de estadísticas de fútbol y detección de value bets, alternativa a ValueStats.com.

**Why:** El objetivo es cruzar estadísticas avanzadas con cuotas de casas de apuestas en tiempo real para encontrar "Value Bets" sin pagar subscripciones premium.

**Estado actual (Abril 2026):** Base funcional en Streamlit con problemas de arquitectura. Plan de refactorización radical creado en PLAN.md.

**Stack actual:** Python + Pandas + Streamlit. Datos de football-data.co.uk (CSV).

**Archivos clave:**
- `main.py` (a crear) → punto de entrada único
- `app.py` / `app_new.py` → versiones descoordinadas, consolidar
- `data_processor.py` → lógica buena de rolling metrics y EV, mantener
- `player_engine.py` → scraping FBref via soccerdata
- `data_updater.py` → descarga CSVs históricos SP1/SP2 desde 2004
- `PRD.md` → requisitos del producto
- `PLAN.md` → plan técnico de desarrollo por sprints

**Problemas críticos identificados:**
- Cuotas simuladas aleatoriamente en data_processor.py:115 (peligroso)
- Dos apps (app.py y app_new.py) descoordinadas, 3 tabs vacíos
- Fechas de temporada hardcodeadas ('2025-08-01')
- Sin separación de capas (UI + lógica + datos mezclados)
- Case sensitivity DATOS/ vs datos/

**How to apply:** Seguir el orden de sprints del PLAN.md: S0 limpieza → S1 data layer → S2 engine → S3 UI → S4 value detection → S5 deploy.
