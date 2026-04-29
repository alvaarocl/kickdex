"""
Script de migración masiva: CSV -> SQL.
Lee todos los archivos en datos/ y los vuelca en la base de datos SQL.
"""

import sys
import os
import pandas as pd
from pathlib import Path
from sqlalchemy.orm import Session

# Añadir raíz al path para importar app
sys.path.append(os.getcwd())

from app.data.database import engine, init_db, SessionLocal
from app.data.models import Team, Match, PlayerStat
from app.data.loader import normalize_team_name

def migrate():
    print("🚀 Iniciando migración masiva a SQL...")
    init_db()
    db = SessionLocal()
    
    data_path = Path("datos")
    csv_files = list(data_path.glob("*.csv"))
    
    teams_cache = {}

    def get_or_create_team(name, league=None):
        name = normalize_team_name(name)
        if name in teams_cache:
            return teams_cache[name]
        
        team = db.query(Team).filter(Team.name == name).first()
        if not team:
            team = Team(name=name, league=league)
            db.add(team)
            db.flush()
        teams_cache[name] = team.id
        return team.id

    # 1. Migrar Partidos
    match_files = [f for f in csv_files if "jugadores" not in f.name]
    print(f"📦 Procesando {len(match_files)} archivos de partidos...")
    
    for f in match_files:
        try:
            df = pd.read_csv(f, encoding="latin1")
            df.columns = [c.strip() for c in df.columns]
            
            for _, row in df.iterrows():
                if pd.isna(row.get("HomeTeam")) or pd.isna(row.get("AwayTeam")):
                    continue
                
                h_id = get_or_create_team(row["HomeTeam"], row.get("Div"))
                a_id = get_or_create_team(row["AwayTeam"], row.get("Div"))
                
                # Intentar parsear fecha
                date_str = str(row["Date"])
                try:
                    date_obj = pd.to_datetime(date_str, dayfirst=True).date()
                except:
                    continue

                match = Match(
                    date=date_obj,
                    div=str(row.get("Div", "SP1")),
                    home_team_id=h_id,
                    away_team_id=a_id,
                    fthg=int(row["FTHG"]) if pd.notna(row.get("FTHG")) else 0,
                    ftag=int(row["FTAG"]) if pd.notna(row.get("FTAG")) else 0,
                    ftr=str(row.get("FTR", "")),
                    hs=int(row["HS"]) if pd.notna(row.get("HS")) else 0,
                    as_=int(row["AS"]) if pd.notna(row.get("AS")) else 0,
                    hst=int(row["HST"]) if pd.notna(row.get("HST")) else 0,
                    ast=int(row["AST"]) if pd.notna(row.get("AST")) else 0,
                    hc=int(row["HC"]) if pd.notna(row.get("HC")) else 0,
                    ac=int(row["AC"]) if pd.notna(row.get("AC")) else 0,
                )
                db.add(match)
            db.commit()
            print(f"  ✅ {f.name} importado.")
        except Exception as e:
            print(f"  ❌ Error en {f.name}: {e}")

    # 2. Migrar Jugadores
    player_files = [f for f in csv_files if "jugadores" in f.name]
    print(f"⚽ Procesando {len(player_files)} archivos de jugadores...")
    
    for f in player_files:
        try:
            df = pd.read_csv(f)
            for _, row in df.iterrows():
                p_stat = PlayerStat(
                    player=row["player"],
                    team=row["team"],
                    gls=float(row.get("gls", 0)),
                    ast=float(row.get("ast", 0)),
                    sh=float(row.get("sh", 0)),
                    sot=float(row.get("sot", 0)),
                    fls=float(row.get("fls", 0)),
                    min_=int(row.get("min", 0))
                )
                db.add(p_stat)
            db.commit()
            print(f"  ✅ {f.name} importado.")
        except Exception as e:
            print(f"  ❌ Error en {f.name}: {e}")

    print("🎉 Migración completada con éxito.")
    db.close()

if __name__ == "__main__":
    migrate()
