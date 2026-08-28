"""
Normalización y scoring de nombres compartidos entre scripts de enriquecimiento
de identidad (escudos de equipo, fotos de jugadores). Extraído de
update_team_crests.py para no duplicar la misma lógica en
update_player_photos_wikidata.py.
"""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher


def norm(value: str) -> str:
    """NFKD sin diacríticos, minúsculas, solo alfanumérico — para comparar
    nombres que difieren en acentos, mayúsculas o puntuación."""
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "", text)


def score(left: str, right: str) -> float:
    """1.0 = coincidencia exacta tras normalizar; 0.91 = uno contiene al otro;
    si no, ratio de similitud de secuencia escalado a un máximo de 0.86 para
    que nunca compita con una coincidencia real."""
    a, b = norm(left), norm(right)
    if a == b:
        return 1.0
    if a in b or b in a:
        return 0.91
    return SequenceMatcher(None, a, b).ratio() * 0.86
