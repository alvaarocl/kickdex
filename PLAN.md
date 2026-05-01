# KICKDEX Product Plan

## Objetivo

Convertir KICKDEX en una web funcional y competitiva para analisis futbolistico, con profundidad real de datos, buena experiencia de uso y una propuesta diferencial frente a herramientas como ValueStats.

El usuario objetivo no necesita solo "datos rapidos". Un tipster, analista o usuario avanzado necesita variedad, contexto, fiabilidad y trazabilidad. La lectura rapida ayuda, pero solo si debajo hay datos suficientes y bien organizados.

## Posicionamiento

ValueStats funciona como una suite amplia de estadisticas: partidos, live, cuotas, arbitros, jugadores, apercibidos, perfiles, alineaciones, tendencias y detalle partido a partido.

KICKDEX debe competir como una terminal profesional de analisis:

- muchos datos, no solo resumen;
- estructura clara por partido;
- fuentes visibles;
- metodologia explicada;
- historico fuerte;
- edge propio;
- tendencias calculadas;
- comparador de equipos, jugadores y arbitros;
- experiencia mas limpia y directa para tomar decisiones informadas.

La diferenciacion no debe ser "menos datos". Debe ser:

> Datos profundos, ordenados y accionables, con modelo propio y explicacion clara.

## Principios De Producto

1. Cada dato debe tener contexto.
   No basta con mostrar una media; hay que mostrar ventana, competicion, local/visitante y muestra.

2. Cada partido debe tener una ficha completa.
   El calendario no debe ser solo una lista. Cada partido debe abrir un analisis completo.

3. El edge debe ser una capa extra, no el unico producto.
   El edge ayuda a detectar discrepancias, pero el usuario debe poder validar con forma, H2H, arbitro, jugadores, tendencias y cuotas.

4. La cobertura debe ser honesta.
   Si una liga tiene jugadores incompletos o arbitros parciales, se muestra. Eso genera confianza.

5. Primero datos estables, despues live.
   El directo es atractivo, pero sin fuente fiable puede romper el producto. Primero hay que dominar prepartido, historico y postpartido.

## Analisis De ValueStats

### Pagina De Partidos

ValueStats muestra:

- partidos por dia;
- partidos en directo;
- filtros por liga;
- logos de competiciones;
- estado del partido;
- ultimos 5;
- goles a favor;
- goles en contra;
- tarjetas por partido;
- arbitro asignado;
- cuotas 1X2;
- comparador de cuotas por casa.

Lecciones para KICKDEX:

- el calendario debe mostrar mas informacion sin obligar a entrar al comparador;
- cada tarjeta de partido debe incluir senales utiles;
- las cuotas y el arbitro deben estar visibles si existen;
- los partidos deben estar agrupados por liga y fecha de forma clara.

### Detalle De Partido

ValueStats tiene una pagina por partido con:

- cabecera de equipos;
- competicion;
- fecha/hora;
- estadio;
- arbitro;
- pestanas;
- previa;
- alineaciones;
- comparativa local/visitante;
- filtros ultimos 5/10/15/20;
- filtros por competicion;
- medias de goles, tiros, posesion, corners, faltas, amarillas, rojas, penaltis y paradas;
- H2H;
- ultimos partidos;
- tendencias;
- jugadores;
- suplentes;
- jugadores apercibidos.

Lecciones para KICKDEX:

- necesitamos una pagina `match.html`;
- el analisis no puede vivir solo dentro de tabs generales;
- todo lo que sabemos de un partido debe agruparse en una ficha unica;
- la ficha debe poder compartirse.

### Tendencias

ValueStats muestra tendencias tipo:

- `+1.5 goles L5/6 local`;
- `BTTS L6/7 global`;
- `9+ corners L5/6 global`;
- equipo recibe gol;
- equipo gana/pierde/no pierde;
- local/visitante/global.

Lecciones para KICKDEX:

- esto es muy viable con nuestro historico;
- da mucho valor visual;
- ayuda al usuario a detectar patrones rapidamente;
- debe ser calculado y no escrito manualmente.

### Arbitros

ValueStats ofrece:

- directorio de arbitros;
- filtro por liga;
- mostrar solo arbitros con proximo partido;
- amarillas;
- rojas;
- faltas;
- VAR;
- penaltis;
- ultimos 5 partidos;
- proximo partido;
- perfil individual por arbitro;
- estadisticas por temporada y liga.

Lecciones para KICKDEX:

- ya tenemos parte de la base;
- falta convertir arbitros en producto propio;
- hay que crear perfil de arbitro;
- hay que comparar cada arbitro contra la media de su liga.

### Jugadores

ValueStats tiene:

- jugadores por partido;
- stats P90;
- valoracion;
- goles;
- asistencias;
- tiros;
- tiros a puerta;
- pases;
- entradas;
- faltas cometidas;
- faltas recibidas;
- amarillas;
- fueras de juego;
- partidos jugados;
- titulares y suplentes;
- tendencias de jugador.

Lecciones para KICKDEX:

- nuestra pestaña de jugadores debe evolucionar a perfiles;
- necesitamos stats partido a partido;
- P90 debe ser una vista principal;
- las tendencias de jugador pueden ser una ventaja muy potente.

### Jugadores Apercibidos

ValueStats muestra jugadores a una tarjeta de sancion.

Lecciones para KICKDEX:

- es una funcionalidad muy valiosa para tipsters;
- requiere cuidado porque las reglas cambian por competicion;
- debe empezar por ligas donde podamos verificar reglas y acumulaciones;
- debe marcarse como "posible apercibido" si no tenemos fuente oficial.

## Roadmap Recomendado

## Sprint 1 - Pagina De Partido

Objetivo: que cada partido tenga una ficha completa y compartible.

Crear `match.html` con:

- cabecera: equipos, liga, fecha, hora, estadio si existe, arbitro si existe;
- estado: proximo, en juego si la fuente lo permite, finalizado;
- cuotas disponibles;
- edge KICKDEX si existe;
- probabilidades 1X2;
- forma local/visitante;
- ultimos 5/10/20;
- H2H;
- tarjetas y arbitro;
- jugadores destacados;
- tendencias disponibles;
- boton para exportar informe.

Cambios tecnicos:

- crear identificador estable por partido;
- hacer que calendario enlace a `match.html?id=...`;
- generar `matches_index.json` o ampliar `fixtures.json`;
- reutilizar `team_stats.json`, `h2h.json`, `referees.json`, `edges.json` y jugadores.

Prioridad: muy alta.

## Sprint 2 - Motor De Tendencias

Objetivo: detectar patrones automaticamente con historico.

Generar `trends.json` con tendencias de:

- goles a favor;
- goles en contra;
- over/under 1.5, 2.5, 3.5;
- BTTS;
- resultado: gana, empata, pierde, no pierde;
- corners si hay columnas disponibles;
- tarjetas;
- local;
- visitante;
- global;
- H2H.

Formato ejemplo:

- `Girona +1.5 goles L5/6 local`;
- `Mallorca recibe +1.5 goles L7/8 visitante`;
- `BTTS L6/7 global`;
- `9+ corners L5/6 global`.

Cambios tecnicos:

- crear `app/engine/trends.py`;
- generar `docs/data/trends.json`;
- mostrar tendencias en calendario y `match.html`;
- anadir tests para reglas principales.

Prioridad: muy alta.

## Sprint 3 - Arbitros Pro

Objetivo: llevar arbitros al nivel de una herramienta profesional.

Crear:

- `referee.html`;
- perfil individual;
- pais;
- partidos arbitrados;
- media amarillas;
- media rojas;
- media faltas;
- penaltis si hay fuente;
- VAR si hay fuente;
- ultimos 5 partidos;
- tabla por temporada y liga;
- proximo partido;
- comparacion contra media de liga.

Cambios tecnicos:

- ampliar `referees.json`;
- generar indice de arbitros;
- enlazar arbitros desde calendario y match page.

Prioridad: alta.

## Sprint 4 - Jugadores Pro

Objetivo: convertir jugadores en una herramienta real de scouting y props.

Crear:

- `player.html`;
- buscador global de jugadores;
- stats partido a partido;
- P90;
- goles;
- asistencias;
- tiros;
- tiros a puerta;
- faltas cometidas;
- faltas recibidas si existe;
- amarillas;
- minutos;
- tendencia ultimos partidos;
- comparacion contra companeros.

Cambios tecnicos:

- mejorar `players_detail.json`;
- crear indice global de jugadores;
- anadir posicion si la fuente la trae;
- usar avatar inicial/escudo si no hay foto fiable.

Prioridad: alta.

## Sprint 5 - Jugadores Apercibidos

Objetivo: detectar jugadores cerca de sancion por acumulacion de tarjetas.

MVP:

- empezar por La Liga y Segunda;
- calcular amarillas acumuladas por jugador en temporada actual;
- definir umbrales por competicion;
- marcar `posible apercibido`;
- mostrar en match page;
- mostrar pagina global `apercibidos.html`.

Precaucion:

- no afirmar sancion oficial si no tenemos fuente oficial;
- incluir fecha de actualizacion y competicion;
- permitir reglas configurables por liga.

Prioridad: media-alta.

## Sprint 6 - Cuotas Y Edge Para Proximos Partidos

Objetivo: que el edge sea prepartido real.

Ahora:

- tenemos edge historico con cuotas Bet365 de football-data;
- no siempre hay cuotas futuras en el feed.

Siguiente:

- integrar una API de cuotas live/prepartido;
- empezar con pocas ligas;
- guardar snapshot diario;
- calcular edge para partidos futuros;
- mostrar mejor cuota;
- mostrar probabilidad implicita;
- mostrar diferencia contra modelo.

Cambios tecnicos:

- crear `odds.json`;
- crear `edges_upcoming.json` o ampliar `edges.json`;
- separar `historical`, `upcoming`, `live`;
- mantener UI igual.

Prioridad: media-alta.

## Sprint 7 - Live Y Eventos

Objetivo: tener datos en directo cuando exista fuente fiable.

No hacerlo primero.

Requisitos:

- fuente estable;
- coste asumible;
- limites claros;
- fallback si falla;
- cache para no romper la web.

Funciones:

- marcador en directo;
- minuto;
- eventos;
- tarjetas;
- cambios;
- estadisticas por parte si la fuente lo permite.

Prioridad: media, despues de consolidar prepartido.

## Sprint 8 - Visual Y UX

Objetivo: que KICKDEX parezca una herramienta lista para mercado.

Mejoras:

- logos de ligas;
- escudos de equipos si hay fuente fiable;
- avatares de jugadores;
- iconos por metrica;
- badges de estado;
- comparativas mas visuales;
- filtros persistentes;
- buscador global;
- paginas compartibles;
- mejor mobile;
- tablas densas pero legibles.

Prioridad: continua.

## Datos Necesarios Por Area

### Partido

- fecha;
- hora;
- liga;
- temporada;
- local;
- visitante;
- estadio;
- arbitro;
- estado;
- marcador;
- cuotas;
- edge;
- probabilidades;
- H2H;
- forma;
- tendencias.

### Jugador

- equipo;
- posicion;
- minutos;
- goles;
- asistencias;
- tiros;
- tiros a puerta;
- faltas;
- amarillas;
- rojas;
- partido a partido;
- P90.

### Arbitro

- pais;
- ligas;
- partidos;
- amarillas;
- rojas;
- faltas;
- penaltis;
- VAR;
- ultimos partidos;
- proximo partido.

### Cuotas

- casa;
- mercado;
- cuota;
- timestamp;
- partido;
- probabilidad implicita;
- edge.

## Orden Practico De Ejecucion

1. Crear `match.html`.
2. Enlazar calendario a `match.html`.
3. Generar `trends.json`.
4. Mostrar tendencias en match page.
5. Crear perfiles de arbitro.
6. Crear perfiles de jugador.
7. Crear apercibidos.
8. Integrar cuotas futuras.
9. Mejorar visual con logos/escudos/avatares.
10. Explorar live.

## Diferenciacion Final

KICKDEX no debe posicionarse como una web de datos rapidos ni como un clon de ValueStats.

Debe posicionarse como:

> Una terminal de inteligencia futbolistica para analizar partidos con datos profundos, tendencias, arbitros, jugadores, cuotas y edge propio.

La ventaja no es tener menos datos. La ventaja debe ser ordenar mejor los datos, explicar mejor el contexto y conectar todo con una lectura accionable del partido.

## Riesgos

- Fuentes gratuitas inestables.
- Datos de jugadores incompletos por bloqueos de FBref.
- Reglas de apercibidos distintas por liga.
- Cuotas futuras limitadas sin API.
- Live caro o poco fiable.
- Exceso de funcionalidades sin buena estructura.

## Mitigacion

- Documentar cobertura real.
- Preservar ultimo JSON bueno si falla una fuente.
- Crear tests para generadores.
- Separar datos historicos, actuales y live.
- Lanzar por capas, no todo a la vez.
- Priorizar match page y tendencias antes que live.

