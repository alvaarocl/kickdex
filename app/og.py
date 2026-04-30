"""
KICKDEX — OG image renderer (V3 brand)

Genera imágenes Open Graph 1200x630 con la identidad de KICKDEX:
fondo Pitch Black + grid hairline + Edge Number gold + cursor turf + match copy.

Uso CLI:
    python -m app.og --home "Real Madrid" --away "Barcelona" \
                     --edge 12.8 --league "LA LIGA · J30" \
                     --caption "Real Madrid · ML · Bet365 1.92" \
                     --out docs/og/real-madrid-vs-barcelona.png

Uso programático:
    from app.og import render_og
    render_og(home="Real Madrid", away="Barcelona", edge=12.8, ...)

Tipografías:
    Requiere IBM Plex Mono y Inter en TTF. Por defecto busca en
    `app/fonts/` o cae a la fuente por defecto de Pillow.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Optional

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
except ImportError as e:
    raise ImportError(
        "Pillow no está instalado. Instala con: pip install Pillow"
    ) from e


# ── Brand tokens (V3) ───────────────────────────────────────────────────────
BG_PITCH = (5, 7, 13)
BG_MIDNIGHT = (11, 15, 26)
TEXT = (241, 245, 251)
TEXT2 = (200, 212, 232)
MUTED = (138, 148, 171)
BRAND_TURF = (46, 230, 166)
EDGE_GOLD = (245, 185, 60)
DATA_CYAN = (91, 214, 255)
RED_CARD = (255, 90, 110)

W, H = 1200, 630

FONT_DIR = Path(__file__).parent / "fonts"


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    """Try local TTFs first, fall back to default."""
    candidates = [
        FONT_DIR / name,
        Path(name),
        Path("/usr/share/fonts/truetype") / name,
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    # Fallback: Pillow default (pixel font, will look basic)
    return ImageFont.load_default()


def _draw_grid(draw: ImageDraw.ImageDraw) -> None:
    """Hairline retícula sobre el fondo, con desvanecido radial."""
    for x in range(0, W, 64):
        draw.line([(x, 0), (x, H)], fill=(46, 230, 166, 18), width=1)
    for y in range(0, H, 64):
        draw.line([(0, y), (W, y)], fill=(46, 230, 166, 18), width=1)


def _format_edge(value: float) -> str:
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.1f}%"


def render_og(
    home: str = "Home",
    away: str = "Away",
    edge: float = 0.0,
    league: str = "LA LIGA",
    caption: str = "",
    out: Optional[str] = None,
) -> Image.Image:
    """Render OG image. Returns PIL Image; if `out` provided, saves to disk."""

    # Base canvas
    img = Image.new("RGB", (W, H), BG_PITCH)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Grid hairlines
    _draw_grid(draw)

    # Soft brand glow (top-left + bottom-right)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse([-300, -300, 700, 400], fill=(46, 230, 166, 38))
    gdraw.ellipse([700, 350, 1500, 950], fill=(245, 185, 60, 28))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    img.paste(glow, (0, 0), glow)

    img.paste(overlay, (0, 0), overlay)
    draw = ImageDraw.Draw(img)

    # Fonts
    f_brand = _font("IBMPlexMono-Bold.ttf", 30)
    f_status = _font("IBMPlexMono-Medium.ttf", 14)
    f_label = _font("IBMPlexMono-Medium.ttf", 16)
    f_value = _font("IBMPlexMono-Bold.ttf", 200)
    f_match = _font("IBMPlexMono-Bold.ttf", 28)
    f_league = _font("IBMPlexMono-Medium.ttf", 14)
    f_cap = _font("IBMPlexMono-Medium.ttf", 18)
    f_foot = _font("IBMPlexMono-Medium.ttf", 14)

    # Header — brand tile + wordmark
    tile_x, tile_y = 64, 56
    draw.rounded_rectangle(
        [tile_x, tile_y, tile_x + 52, tile_y + 52],
        radius=12, fill=BRAND_TURF,
    )
    draw.text((tile_x + 14, tile_y + 4), "K", fill=(2, 26, 18), font=f_brand)
    draw.text((tile_x + 70, tile_y + 8), "kickdex", fill=TEXT, font=f_brand)

    # Status pill (top-right)
    status_text = "● LIVE · TERMINAL"
    sw = draw.textlength(status_text, font=f_status)
    sx = W - 64 - sw - 28
    sy = 64
    draw.rounded_rectangle(
        [sx, sy, sx + sw + 28, sy + 36],
        radius=999, outline=(255, 255, 255, 30), width=1,
    )
    draw.text((sx + 14, sy + 10), status_text, fill=MUTED, font=f_status)

    # Edge label
    draw.text((64, 200), "EDGE DETECTED", fill=MUTED, font=f_label)

    # Edge number — the hero
    edge_text = _format_edge(edge)
    draw.text((60, 230), edge_text, fill=EDGE_GOLD, font=f_value)

    # Cursor next to edge value
    val_w = draw.textlength(edge_text, font=f_value)
    cur_x = 60 + val_w + 12
    draw.rectangle([cur_x, 250, cur_x + 24, 380], fill=BRAND_TURF)

    # Sparkline
    spark_y = 460
    for i in range(0, 360, 2):
        a = max(0, min(255, int(255 * (1 - abs(i - 180) / 180))))
        draw.line([(64 + i, spark_y), (64 + i + 2, spark_y)], fill=(46, 230, 166, a))

    # Caption
    if caption:
        draw.text((64, 478), caption, fill=TEXT2, font=f_cap)

    # Right column — league + match
    league_x = W - 64
    draw.text(
        (league_x - draw.textlength(league.upper(), font=f_league), 220),
        league.upper(), fill=DATA_CYAN, font=f_league,
    )
    match_text = f"{home}  vs  {away}"
    mw = draw.textlength(match_text, font=f_match)
    draw.text((league_x - mw, 250), match_text, fill=TEXT, font=f_match)

    # Footer
    draw.line([(64, H - 70), (W - 64, H - 70)], fill=(255, 255, 255, 20), width=1)
    draw.text(
        (64, H - 50),
        "Football intelligence, indexed.  ·  kickdex.com",
        fill=BRAND_TURF, font=f_foot,
    )
    foot_right = "> NO LOGIN. NO ADS. NO PICKS."
    fw = draw.textlength(foot_right, font=f_foot)
    draw.text((W - 64 - fw, H - 50), foot_right, fill=MUTED, font=f_foot)

    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        img.save(out, format="PNG", optimize=True)

    return img


def _slug(s: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in s.lower()).strip("-")


def _cli() -> None:
    ap = argparse.ArgumentParser(description="KICKDEX OG image renderer")
    ap.add_argument("--home", default="Home")
    ap.add_argument("--away", default="Away")
    ap.add_argument("--edge", type=float, default=0.0)
    ap.add_argument("--league", default="LA LIGA")
    ap.add_argument("--caption", default="")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    out = args.out or f"docs/og/{_slug(args.home)}-vs-{_slug(args.away)}.png"
    render_og(
        home=args.home, away=args.away, edge=args.edge,
        league=args.league, caption=args.caption, out=out,
    )
    print(f"OG saved → {out}")


if __name__ == "__main__":
    _cli()
