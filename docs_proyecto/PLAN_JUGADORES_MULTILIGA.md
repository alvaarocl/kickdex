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

## Siguiente implementacion

- Mostrar en el frontend una etiqueta de cobertura por liga/equipo.
- Anadir alias de equipos a medida que aparezcan diferencias entre FBref y football-data.
