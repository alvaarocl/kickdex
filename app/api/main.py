"""
Servidor FastAPI Core para KICKDEX.
Punto de entrada para la terminal de datos profesional.
"""

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.data.database import get_db, init_db
from app.data.models import Team, Match, PlayerStat
from pydantic import BaseModel
from datetime import date

from app.engine.metrics import calculate_player_percentiles
import pandas as pd

app = FastAPI(title="KICKDEX API", version="2.0.0")


class TeamSchema(BaseModel):
    id: int
    name: str
    league: str | None = None

    class Config:
        from_attributes = True


class MatchSchema(BaseModel):
    id: int
    date: date
    home_team: str
    away_team: str
    fthg: int | None = None
    ftag: int | None = None
    ftr: str | None = None

# ─── Endpoints de Análisis Pro ────────────────────────────────────────────────

@app.get("/scouting/players")
def get_player_scouting(min_minutes: int = 500, db: Session = Depends(get_db)):
    """Retorna ranking de jugadores basado en percentiles (Z-Score)."""
    query = db.query(PlayerStat).all()
    df_p = pd.DataFrame([{ "player": p.player, "team": p.team, "gls": p.gls, 
                           "ast": p.ast, "sh": p.sh, "sot": p.sot, "min": p.min_ } for p in query])
    
    if df_p.empty: return []
    
    # Filtrar por minutos y calcular percentiles
    df_filtered = df_p[df_p["min"] >= min_minutes]
    scouting_results = calculate_player_percentiles(df_filtered)
    return scouting_results.to_dict(orient="records")

# ─── Endpoints Core (Equipos y Partidos) ──────────────────────────────────────

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def read_root():
    return {"status": "KICKDEX API Operational", "version": "2.0.0"}

@app.get("/teams", response_model=List[TeamSchema])
def get_teams(db: Session = Depends(get_db)):
    return db.query(Team).all()

@app.get("/matches/{team_name}", response_model=List[MatchSchema])
def get_team_matches(team_name: str, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.name == team_name).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Unir con nombres de equipos para el esquema
    matches = db.query(Match).filter(
        (Match.home_team_id == team.id) | (Match.away_team_id == team.id)
    ).order_by(Match.date.desc()).limit(50).all()
    
    result = []
    for m in matches:
        result.append({
            "id": m.id,
            "date": m.date,
            "home_team": m.home_team.name,
            "away_team": m.away_team.name,
            "fthg": m.fthg,
            "ftag": m.ftag,
            "ftr": m.ftr
        })
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
