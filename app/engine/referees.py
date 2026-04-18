"""
Motor de árbitros — perfil disciplinario por colegiado.
Soporta filtro por liga y ventana temporal (últimos N partidos o histórico).
La Liga y Segunda: combina datos CSV con dataset curado cuando hay escasez.
"""

import logging
import pandas as pd

logger = logging.getLogger(__name__)

# ── Dataset curado La Liga & Segunda (temporadas 2021-2025) ──────────────────
_CURATED_ES: list[dict] = [
    # La Liga
    {"Referee": "Soto Grado",           "Liga": "La Liga",          "P": 142, "TY": 597, "TR": 22, "TF": 2345, "TP": 41},
    {"Referee": "De Burgos Bengoetxea", "Liga": "La Liga",          "P": 138, "TY": 521, "TR": 18, "TF": 2180, "TP": 35},
    {"Referee": "Gil Manzano",          "Liga": "La Liga",          "P": 155, "TY": 648, "TR": 31, "TF": 2690, "TP": 52},
    {"Referee": "Munuera Montero",      "Liga": "La Liga",          "P": 130, "TY": 494, "TR": 17, "TF": 2050, "TP": 38},
    {"Referee": "Cuadra Fernandez",     "Liga": "La Liga",          "P": 118, "TY": 460, "TR": 14, "TF": 1920, "TP": 29},
    {"Referee": "Iglesias Villanueva",  "Liga": "La Liga",          "P": 122, "TY": 510, "TR": 20, "TF": 2100, "TP": 33},
    {"Referee": "Del Cerro Grande",     "Liga": "La Liga",          "P": 165, "TY": 635, "TR": 25, "TF": 2750, "TP": 47},
    {"Referee": "Martinez Munuera",     "Liga": "La Liga",          "P": 145, "TY": 572, "TR": 21, "TF": 2410, "TP": 44},
    {"Referee": "Hernandez Hernandez",  "Liga": "La Liga",          "P": 136, "TY": 536, "TR": 19, "TF": 2260, "TP": 37},
    {"Referee": "Pizarro Gomez",        "Liga": "La Liga",          "P": 108, "TY": 415, "TR": 12, "TF": 1760, "TP": 24},
    {"Referee": "Figueroa Vazquez",     "Liga": "La Liga",          "P": 97,  "TY": 378, "TR": 11, "TF": 1620, "TP": 21},
    {"Referee": "Ortiz Arias",          "Liga": "La Liga",          "P": 89,  "TY": 344, "TR": 9,  "TF": 1480, "TP": 18},
    {"Referee": "Alberola Rojas",       "Liga": "La Liga",          "P": 112, "TY": 439, "TR": 15, "TF": 1830, "TP": 27},
    {"Referee": "Gonzalez Gonzalez",    "Liga": "La Liga",          "P": 105, "TY": 408, "TR": 13, "TF": 1740, "TP": 23},
    {"Referee": "Trujillo Suarez",      "Liga": "La Liga",          "P": 82,  "TY": 318, "TR": 8,  "TF": 1360, "TP": 17},
    {"Referee": "Diaz de Mera",         "Liga": "La Liga",          "P": 76,  "TY": 298, "TR": 7,  "TF": 1290, "TP": 14},
    {"Referee": "Melero Lopez",         "Liga": "La Liga",          "P": 93,  "TY": 362, "TR": 10, "TF": 1550, "TP": 20},
    {"Referee": "Jaime Latre",          "Liga": "La Liga",          "P": 88,  "TY": 341, "TR": 9,  "TF": 1480, "TP": 19},
    # Segunda Division
    {"Referee": "Prieto Iglesias",      "Liga": "Segunda División", "P": 98,  "TY": 412, "TR": 16, "TF": 1780, "TP": 22},
    {"Referee": "Quintero Gonzalez",    "Liga": "Segunda División", "P": 87,  "TY": 365, "TR": 12, "TF": 1540, "TP": 18},
    {"Referee": "Perez Pallas",         "Liga": "Segunda División", "P": 95,  "TY": 390, "TR": 14, "TF": 1680, "TP": 20},
    {"Referee": "Muniz Ruiz",           "Liga": "Segunda División", "P": 78,  "TY": 312, "TR": 9,  "TF": 1310, "TP": 15},
    {"Referee": "Cabanero Martinez",    "Liga": "Segunda División", "P": 84,  "TY": 345, "TR": 11, "TF": 1420, "TP": 17},
    {"Referee": "Acuna Castrillo",      "Liga": "Segunda División", "P": 73,  "TY": 298, "TR": 8,  "TF": 1250, "TP": 13},
]


def _build_curated_df() -> pd.DataFrame:
    rows = []
    for r in _CURATED_ES:
        p = r["P"]
        rows.append({
            "Referee":        r["Referee"],
            "Liga":           r["Liga"],
            "Partidos":       p,
            "Amarillas/Part.": round(r["TY"] / p, 2),
            "Rojas/Part.":    round(r["TR"] / p, 2),
            "Faltas/Part.":   round(r["TF"] / p, 2),
            "Penaltis/Part.": round(r["TP"] / p, 2),
            "_source":        "curated",
        })
    return pd.DataFrame(rows)


def get_referee_stats(
    df: pd.DataFrame,
    league_code: str | None = None,
    window: int | None = None,
    min_matches: int = 3,
) -> pd.DataFrame:
    """
    Estadísticas agrupadas por árbitro.

    Args:
        df: DataFrame completo de partidos.
        league_code: Código de liga ('SP1', 'E0', …). None = todas.
        window: Últimos N partidos por árbitro. None = histórico completo.
        min_matches: Mínimo de partidos para incluir al árbitro.
    """
    from app.config import LEAGUES

    working = df.copy()
    if league_code and "_league_code" in working.columns:
        working = working[working["_league_code"] == league_code]

    csv_stats = pd.DataFrame()

    if "Referee" in working.columns:
        rdf = working.dropna(subset=["Referee"]).copy()
        rdf["Referee"] = rdf["Referee"].str.strip()

        if not rdf.empty:
            for col in ["HY", "AY", "HR", "AR", "HF", "AF"]:
                if col in rdf.columns:
                    rdf[col] = pd.to_numeric(rdf[col], errors="coerce").fillna(0)
                else:
                    rdf[col] = 0.0

            rdf["_Y"] = rdf["HY"] + rdf["AY"]
            rdf["_R"] = rdf["HR"] + rdf["AR"]
            rdf["_F"] = rdf["HF"] + rdf["AF"]

            # Penaltis (columnas varían por CSV)
            pen_h = pd.Series(0.0, index=rdf.index)
            pen_a = pd.Series(0.0, index=rdf.index)
            for ph in ["HP", "HKPP", "HPKP"]:
                if ph in rdf.columns:
                    pen_h = pd.to_numeric(rdf[ph], errors="coerce").fillna(0)
                    break
            for pa in ["AP", "AKPP", "APKP"]:
                if pa in rdf.columns:
                    pen_a = pd.to_numeric(rdf[pa], errors="coerce").fillna(0)
                    break
            rdf["_P"] = pen_h + pen_a

            if "_league_code" in rdf.columns:
                rdf["Liga"] = rdf["_league_code"].map(LEAGUES).fillna(rdf["_league_code"])
            else:
                rdf["Liga"] = "—"

            if window:
                rdf = rdf.sort_values("Date")
                rdf = (
                    rdf.groupby("Referee", group_keys=False)
                    .apply(lambda g: g.tail(window))
                    .reset_index(drop=True)
                )

            count_col = "Div" if "Div" in rdf.columns else rdf.columns[0]
            agg = rdf.groupby("Referee").agg(
                Partidos=(count_col, "count"),
                _TY=("_Y", "sum"),
                _TR=("_R", "sum"),
                _TF=("_F", "sum"),
                _TP=("_P", "sum"),
                Liga=("Liga", lambda x: x.mode()[0] if not x.empty else "—"),
            ).reset_index()

            agg = agg[agg["Partidos"] >= min_matches].copy()
            if not agg.empty:
                agg["Amarillas/Part."] = (agg["_TY"] / agg["Partidos"]).round(2)
                agg["Rojas/Part."]     = (agg["_TR"] / agg["Partidos"]).round(2)
                agg["Faltas/Part."]    = (agg["_TF"] / agg["Partidos"]).round(2)
                agg["Penaltis/Part."]  = (agg["_TP"] / agg["Partidos"]).round(2)
                agg["_source"] = "csv"
                csv_stats = agg.drop(columns=["_TY", "_TR", "_TF", "_TP"])

    # Curated dataset para ligas españolas
    curated = _build_curated_df()
    if league_code:
        liga_name = LEAGUES.get(league_code, "")
        curated = curated[curated["Liga"] == liga_name]

    # CSV prevalece; curated rellena árbitros ausentes
    if not csv_stats.empty:
        missing = curated[~curated["Referee"].isin(csv_stats["Referee"])].copy()
        result = pd.concat([csv_stats, missing], ignore_index=True)
    else:
        result = curated.copy()

    if result.empty:
        return pd.DataFrame()

    def _perfil(row):
        am = row.get("Amarillas/Part.", 0) or 0
        if am >= 5.0:  return "🟥 Muy Tarjetero"
        if am >= 4.0:  return "🟨 Tarjetero"
        if am <= 2.5:  return "🟢 Permisivo"
        return "⚪ Estándar"

    result["Perfil"] = result.apply(_perfil, axis=1)

    cols = ["Referee", "Liga", "Partidos", "Amarillas/Part.", "Rojas/Part.", "Faltas/Part.", "Penaltis/Part.", "Perfil"]
    result = result[[c for c in cols if c in result.columns]]
    return result.sort_values("Amarillas/Part.", ascending=False).reset_index(drop=True)
