# Plan Jugadores Multi-Liga

## Objetivo

Completar estadisticas de jugadores para todas las ligas soportadas por KICKDEX, manteniendo los datos de LaLiga que ya existen y permitiendo incorporar el resto por fases.

## Estado actual

- El frontend consume `docs/data/players.json` y `docs/data/players_detail.json`.
- El build diario de GitHub Actions ejecuta `python scripts/build_data.py`.
- `build_data.py` protege los JSON de jugadores: si FBref falla y la cobertura nueva es menor que la existente, conserva los JSON publicados.
- `docs/data/player_coverage.json` registra la cobertura por liga cuando se genera el build.
- El backend espera datos normalizados con estas columnas: `date`, `team`, `player`, `sh`, `sot`, `gls`, `ast`, `fls`, `crdy`, `min`, `league`.
- El cargador soporta `datos/jugadores_raw.csv`, `datos/players/*.csv` y `datos/jugadores/*.csv`.

## Fuente recomendada

Fuente primaria: FBref via `soccerdata`.

Motivo: `soccerdata.FBref.read_player_match_stats(stat_type="summary")` devuelve match logs por jugador con goles, asistencias, tiros, tiros a puerta, faltas y tarjetas. Es el grano que necesita KICKDEX para player props y tendencias recientes.

## Formato de CSV por liga

Cada CSV manual o generado debe normalizarse a:

```csv
date,team,player,sh,sot,gls,ast,fls,crdy,min,league
2025-09-01,Real Madrid,Jugador Uno,3,2,1,0,1,0,90,SP1
```

Se puede cargar un archivo por liga:

- `datos/players/SP1.csv`
- `datos/players/E0.csv`
- `datos/players/I1.csv`
- `datos/players/D1.csv`

## Automatizacion diaria

GitHub Actions corre todos los dias a las 6:00 UTC y un extra los miercoles. El flujo instala `requirements.txt`, ejecuta el build y despues imprime cobertura de jugadores con:

```bash
python scripts/check_player_coverage.py
```

Regla de seguridad: los datos de jugadores solo se reemplazan si la cobertura nueva no es menor que la publicada. Esto evita que un bloqueo puntual de FBref borre jugadores en produccion.

## Fases

1. Mantener LaLiga como CSV local validado.
2. Generar `datos/jugadores_raw.csv` y `datos/players/{liga}.csv` con `app/data/player_scraper.py`.
3. Si una liga falla por scraping, usar cache local de esa liga cuando exista.
4. Regenerar `docs/data/players.json`, `docs/data/players_detail.json` y `docs/data/player_coverage.json` con `python scripts/build_data.py`.
5. Revisar cobertura con `python scripts/check_player_coverage.py`.

## Riesgos

- FBref puede limitar scraping si se hacen demasiadas peticiones seguidas.
- Algunas segundas divisiones pueden no tener el mismo nivel de match logs.
- Los nombres de equipos entre football-data y FBref necesitan alias adicionales.

## Bloqueo de FBref/Selenium y mitigacion con Understat (2026-08-26)

`soccerdata.FBref` hereda de `BaseSeleniumReader` y depende de `seleniumbase`
en modo `uc=True` (Chrome no detectado) sin ninguna via alternativa por
requests puro. En esta maquina esa llamada cuelga de forma indefinida (se
confirmo de nuevo: >1min30s sin resolver ni lanzar excepcion), consistente
con el bloqueo ya diagnosticado en sesiones anteriores. Ademas, en CI
(`update_data.yml`) el scraping de jugadores nunca se ejecuta: el paso
"Update player data" siempre corre con `--skip-scrape`, asi que la cobertura
de jugadores lleva tiempo congelada en cualquier entorno, no solo en local.

Mitigacion aplicada: `app/data/player_scraper.py` ahora intenta primero
`soccerdata.Understat` (lector HTTP puro, sin navegador) para las 5 ligas que
cubre — SP1, E0, I1, D1, F1 — y solo si falla o la liga no esta soportada cae
al camino FBref existente. Understat solo aporta **equipos que faltan** en la
cache local (`_merge_missing_teams`); nunca sobreescribe un equipo que ya
tenga datos, para no perder columnas que Understat no expone a nivel de
temporada (tiros a puerta, faltas cometidas quedan en 0.0 para las filas que
vengan de Understat).

Ejecutado y verificado para **SP1**: anadidos Deportivo, Malaga y Racing
Santander (los 3 ascendidos que faltaban) sin tocar los 17 equipos ya
cubiertos por FBref — verificado byte a byte que esas filas no cambiaron.
`docs/data/players.json` regenerado; `check_player_coverage.py` ahora marca
SP1 en 100% (era 85%, 17/20).

**No aplicado a E0/I1/D1/F1 en esta sesion** — motivo: la cache existente de
esas 4 ligas usa nombres de equipo sin normalizar de una version anterior del
pipeline (p. ej. "Leeds United"/"Manchester Utd"/"Newcastle United" en vez de
las claves canonicas "Leeds"/"Man United"/"Newcastle" que ya existen en
`TEAM_ALIASES`). Al comparar contra los nombres de Understat ("Leeds", "Man
United", "Newcastle"...) el merge por nombre-no-visto los trata como equipos
nuevos y crea duplicados. Los equipos realmente nuevos que si detecto
Understat (Coventry/Hull/Ipswich en E0, Frosinone/Monza/Venezia en I1,
Le Mans/Troyes en F1) coinciden con el roster oficial de la app, asi que la
fuente es correcta — el problema es solo de normalizacion de nombres
heredados. D1/Bundesliga ademas devolvio 0 filas en Understat para la
temporada 2026 (la liga probablemente aun no esta indexada alli).

## Siguiente implementacion

- Normalizar las cache CSV heredadas de E0/I1/D1/F1 con `normalize_team_name`
  (o regenerarlas desde cero) antes de activar el relleno automatico de
  Understat en esas 4 ligas — evita los duplicados descritos arriba.
- Confirmar si D1 necesita esperar a que Understat indexe la temporada
  2026/27 de Bundesliga, o si hace falta otra fuente para esa liga.
- Extender la automatizacion diaria (`update_data.yml`) para dejar de correr
  siempre `--skip-scrape`, ahora que existe una via sin Selenium para las 5
  ligas grandes.
- Mostrar en el frontend una etiqueta de cobertura por liga/equipo.
- Anadir alias de equipos a medida que aparezcan diferencias entre
  FBref/Understat y football-data.
