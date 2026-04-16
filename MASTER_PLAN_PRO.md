# 🏆 KICKDEX — MASTER PLAN PRO (FULL-STACK TERMINAL)

Este documento es la única fuente de verdad para la evolución de KICKDEX de una web estática a una terminal de datos profesional.

---

## 🏗️ FASE 1: INFRAESTRUCTURA CORE (BACKEND & SQL)
- [x] **Migración SQL (SQLite/Postgres):** Volcar 20 años de historia a una base de datos relacional.
- [x] **FastAPI Migration:** Crear el servidor de API para desacoplar lógica de visualización.
- [x] **Data Normalization v2:** Diccionario maestro de equipos y jugadores para cruzar fuentes.
- [x] **Query Engine SQL:** Estructura base de API para consultas rápidas.

## ⚡ FASE 2: TIEMPO REAL & APIS PRO
- [x] **External API Manager:** Conector listo para The Odds API y API-Football.
- [x] **Live Odds & Scores:** Endpoints `/market/odds` y `/market/live` operativos.
- [ ] **xG Real Engine:** Integración de Goles Esperados reales basados en la posición del tiro (FBref).
- [ ] **Dropping Odds:** Sistema de detección de caídas de cuotas drásticas.

## 🎨 FASE 3: FRONTEND TERMINAL (NEXT.JS)
- [x] **Arquitectura Next.js:** Estructura de carpetas y cliente de API listo.
- [x] **Dashboard OLED Dark:** UI base diseñada con Tailwind y Lucide.
- [x] **Match Components:** Componentes reactivos para partidos y cuotas.
- [ ] **Interactive Charts:** Mapas de calor de tiros y gráficos de momentum.

## 🤖 FASE 4: AUTOMATIZACIÓN & ALERTAS
- [ ] **Telegram Bot Integration:** Recibir alertas de valor configuradas directamente en el chat.
- [ ] **Backtesting en la Nube:** Permitir que los backtests corran en el servidor y guarden resultados.
- [ ] **Daily Market Report:** Informe automático matutino con las mejores oportunidades detectadas.

---

## 🛠️ STACK TÉCNICO DEFINITIVO
- **Backend:** Python (FastAPI) + SQLAlchemy.
- **Base de Datos:** PostgreSQL (Producción) / SQLite (Dev).
- **Frontend:** React (Next.js) + TailwindCSS + Lucide Icons.
- **Gráficos:** Recharts / Plotly.js.
- **DevOps:** Docker + GitHub Actions + Railway/Vercel.

*Plan consolidado: Abril 2026*
