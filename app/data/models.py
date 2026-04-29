"""
Modelos de base de datos SQLAlchemy para KICKDEX.
Define la estructura de tablas para partidos y estadísticas de jugadores.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    league = Column(String) # SP1, SP2
    
    # Relaciones
    home_matches = relationship("Match", foreign_keys="Match.home_team_id", back_populates="home_team")
    away_matches = relationship("Match", foreign_keys="Match.away_team_id", back_populates="away_team")

class Match(Base):
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    div = Column(String, nullable=False)
    
    home_team_id = Column(Integer, ForeignKey("teams.id"))
    away_team_id = Column(Integer, ForeignKey("teams.id"))
    
    fthg = Column(Integer) # Full Time Home Goals
    ftag = Column(Integer) # Full Time Away Goals
    ftr = Column(String(1)) # Full Time Result (H, D, A)
    
    # Stats
    hs = Column(Integer) # Home Shots
    as_ = Column(Integer, name="as") # Away Shots
    hst = Column(Integer) # Home Shots on Target
    ast = Column(Integer) # Away Shots on Target
    hc = Column(Integer) # Home Corners
    ac = Column(Integer) # Away Corners
    hf = Column(Integer) # Home Fouls
    af = Column(Integer) # Away Fouls
    hy = Column(Integer) # Home Yellow Cards
    ay = Column(Integer) # Away Yellow Cards
    hr = Column(Integer) # Home Red Cards
    ar = Column(Integer) # Away Red Cards
    
    # Relaciones
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")

class PlayerStat(Base):
    __tablename__ = "player_stats"
    
    id = Column(Integer, primary_key=True)
    player = Column(String, nullable=False)
    team = Column(String, nullable=False)
    date = Column(Date)
    
    gls = Column(Float) # Goles
    ast = Column(Float) # Asistencias
    sh = Column(Float)  # Tiros
    sot = Column(Float) # Tiros a puerta
    fls = Column(Float) # Faltas cometidas
    crdy = Column(Float) # Amarillas
    min_ = Column(Integer, name="min") # Minutos
