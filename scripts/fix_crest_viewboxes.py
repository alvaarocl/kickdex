"""
Fix crest SVGs whose declared viewBox clips the real artwork.

The public source (JoseArroyave/football-logos) is served as raw hotlinked
URLs (see update_team_crests.py) with no local processing. A meaningful
fraction of its SVGs declare a viewBox/width/height that is smaller than (or
offset from) the actual path geometry, so the browser renders/clips to that
wrong box and the badge appears cut off (reported by the user for Celta de
Vigo and others).

This script: downloads each affected crest, computes the REAL bounding box
of its path geometry with svgelements (not trusting the declared viewBox),
rewrites the viewBox to that real box (plus a small margin, matching the
project's existing anti-clip padding convention), strips the now-stale
width/height attributes so the corrected viewBox is authoritative, and saves
the fixed SVG locally under docs/img/crests/. docs/data/team_assets.json's
crest_local is then pointed at the local, corrected file — entityMedia()
already prefers crest_local over crest (app/js/app.js), so no frontend
change is needed.

Usage:
    python scripts/fix_crest_viewboxes.py            # fix known-broken teams
    python scripts/fix_crest_viewboxes.py --scan-all # re-detect broken teams first
    python scripts/fix_crest_viewboxes.py --team Celta Sevilla ...
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import requests
from svgelements import SVG

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data"
CRESTS_DIR = ROOT / "docs" / "img" / "crests"

VIEWBOX_RE = re.compile(r'viewBox="(-?[\d.]+) (-?[\d.]+) ([\d.]+) ([\d.]+)"')
WIDTH_RE = re.compile(r'\bwidth="([\d.]+)(?:px)?"')
HEIGHT_RE = re.compile(r'\bheight="([\d.]+)(?:px)?"')
SVG_OPEN_RE = re.compile(r"<svg\b[^>]*>")

CLIP_THRESHOLD = 0.05  # matches the detection threshold used when scanning

# Teams found broken via a full scan of all 212 crest URLs on 2026-08-27
# (real path geometry extends meaningfully outside the declared viewBox).
KNOWN_BROKEN = [
    "Getafe", "Derby", "Sevilla", "Nantes", "Bristol City", "Cardiff",
    "Celta", "Darmstadt", "Braunschweig", "Nurnberg", "Willem II",
    "Sudtirol", "Cagliari", "Crystal Palace", "Telstar", "Schalke 04",
    "Hannover", "Wolves", "Leverkusen", "Eldense", "Girona", "Sp Gijon",
    "Cambuur", "Sabadell", "Tenerife", "Zwolle", "Middlesbrough", "Pisa",
    "Guingamp", "Elche", "Heerenveen", "Cremonese", "Rennes", "Levante",
    "Watford", "Vicenza",
]


def slugify(name: str) -> str:
    text = unicodedata.normalize("NFKD", name)
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def declared_box(svg_text: str) -> tuple[float, float, float, float] | None:
    head = svg_text[:2000]
    vb = VIEWBOX_RE.search(head)
    if vb:
        return tuple(float(vb.group(i)) for i in (1, 2, 3, 4))
    wm, hm = WIDTH_RE.search(head), HEIGHT_RE.search(head)
    if wm and hm:
        return 0.0, 0.0, float(wm.group(1)), float(hm.group(1))
    return None


def real_bbox(svg_text: str) -> tuple[float, float, float, float] | None:
    svg = SVG.parse(BytesIO(svg_text.encode("utf-8")))
    xs: list[float] = []
    ys: list[float] = []
    for e in svg.elements():
        if not hasattr(e, "bbox"):
            continue
        try:
            b = e.bbox()
        except Exception:
            b = None
        if b:
            xs += [b[0], b[2]]
            ys += [b[1], b[3]]
    if not xs or not ys:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def clipped_fraction(declared, real) -> float:
    vb_minx, vb_miny, vbw, vbh = declared
    x0, y0, x1, y1 = real
    vb_maxx, vb_maxy = vb_minx + vbw, vb_miny + vbh
    out_x = max(0.0, vb_minx - x0, x1 - vb_maxx)
    out_y = max(0.0, vb_miny - y0, y1 - vb_maxy)
    return out_x / vbw + out_y / vbh


def fix_svg(svg_text: str, real: tuple[float, float, float, float], margin: float = 0.04) -> str:
    x0, y0, x1, y1 = real
    w, h = x1 - x0, y1 - y0
    pad_x, pad_y = w * margin, h * margin
    new_vb = f'{x0 - pad_x:.3f} {y0 - pad_y:.3f} {w + 2 * pad_x:.3f} {h + 2 * pad_y:.3f}'

    def _replace_open_tag(match: re.Match) -> str:
        tag = match.group(0)
        tag = VIEWBOX_RE.sub("", tag)
        tag = WIDTH_RE.sub("", tag)
        tag = HEIGHT_RE.sub("", tag)
        tag = re.sub(r"\s{2,}", " ", tag)
        tag = tag.replace("<svg ", f'<svg viewBox="{new_vb}" ', 1)
        return tag

    return SVG_OPEN_RE.sub(_replace_open_tag, svg_text, count=1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--team", nargs="*", help="Only fix these team names (must match team_assets.json keys)")
    args = parser.parse_args()

    manifest_path = DATA / "team_assets.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    teams = manifest.get("teams", {})

    targets = args.team if args.team else KNOWN_BROKEN
    CRESTS_DIR.mkdir(parents=True, exist_ok=True)

    fixed = skipped = failed = 0
    for name in targets:
        asset = teams.get(name)
        if not asset or not asset.get("crest"):
            print(f"  SKIP {name}: no crest URL in manifest")
            skipped += 1
            continue
        url = asset["crest"]
        try:
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()
            svg_text = resp.text

            declared = declared_box(svg_text)
            real = real_bbox(svg_text)
            if not declared or not real:
                print(f"  FAIL {name}: could not determine declared/real box")
                failed += 1
                continue

            frac = clipped_fraction(declared, real)
            if frac < CLIP_THRESHOLD:
                print(f"  OK   {name}: already fine (clipped_frac={frac:.2f}), leaving crest_local unset")
                skipped += 1
                continue

            fixed_svg = fix_svg(svg_text, real)
            slug = slugify(name)
            out_path = CRESTS_DIR / f"{slug}.svg"
            out_path.write_text(fixed_svg, encoding="utf-8")

            asset["crest_local"] = f"img/crests/{slug}.svg"
            asset["crest_fix_note"] = f"viewBox recomputed from real path geometry (clipped_frac was {frac:.2f})"
            asset["source_updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            print(f"  FIXED {name}: clipped_frac={frac:.2f} -> {out_path.relative_to(ROOT)}")
            fixed += 1
        except Exception as e:
            print(f"  FAIL {name}: {e}")
            failed += 1

    manifest["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    print(f"\nFixed {fixed}, skipped {skipped}, failed {failed}. Manifest updated: {manifest_path.relative_to(ROOT)}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
