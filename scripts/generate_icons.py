#!/usr/bin/env python3
"""Generate lo-fi pixel-art SVG weather icons for wxmeow.

Run from project root:
    python3 scripts/generate_icons.py

Outputs 44 SVGs to wxmeow/static/icons/
Icons are 160x160px (16x16 grid, 10px per cell).
"""

import math
import os

OUTPUT_DIR = "wxmeow/static/icons"
GRID = 16
CELL = 10
SIZE = GRID * CELL

# ── Colour palette ────────────────────────────────────────────────────────────
SUN      = '#f0c030'
MOON     = '#eeddaa'
CLOUD    = '#888888'
CLOUD_L  = '#bbbbbb'
CLOUD_D  = '#445566'
RAIN     = '#4466aa'
RAIN_L   = '#7799cc'
SNOW_DOT = '#334466'
SNOW_ARM = '#aabbcc'
BOLT     = '#ffee00'
DARK     = '#333333'
FOG_C    = '#aaaaaa'
HOT_C    = '#cc3322'
COLD_C   = '#3388bb'
DUST_C   = '#cc9955'
SMOKE_C  = '#777777'
WIND_C   = '#999999'
SKY_N    = '#223344'
HAZE_C   = '#ddcc88'


# ── SVG serialiser ────────────────────────────────────────────────────────────
def make_svg(pixels: dict, bg: str = None) -> str:
    rects = []
    if bg:
        rects.append(f'<rect x="0" y="0" width="{SIZE}" height="{SIZE}" fill="{bg}"/>')
    for (r, c), color in sorted(pixels.items()):
        if 0 <= r < GRID and 0 <= c < GRID:
            rects.append(
                f'<rect x="{c*CELL}" y="{r*CELL}" width="{CELL}" height="{CELL}" fill="{color}"/>'
            )
    body = '\n'.join(rects)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{SIZE}" height="{SIZE}" viewBox="0 0 {SIZE} {SIZE}">\n'
        f'{body}\n</svg>\n'
    )


# ── Drawing primitives ────────────────────────────────────────────────────────
def circle(p, cr, cc, radius, color):
    for r in range(GRID):
        for c in range(GRID):
            if math.hypot(r + 0.5 - cr, c + 0.5 - cc) < radius:
                p[(r, c)] = color


def sun(p, cr=7.5, cc=7.5, radius=3.8, color=SUN):
    circle(p, cr, cc, radius, color)
    for deg in range(0, 360, 45):
        ang = math.radians(deg)
        for t in (radius + 1.2, radius + 2.2):
            r = cr + math.sin(ang) * t - 0.5
            c = cc + math.cos(ang) * t - 0.5
            pr, pc = int(r), int(c)
            if 0 <= pr < GRID and 0 <= pc < GRID:
                p[(pr, pc)] = color


def moon(p, cr=7.5, cc=7.5, outer=4.2, color=MOON):
    cut_r, cut_c = cr - 1.5, cc + 2.2
    cut_rad = outer - 0.8
    for r in range(GRID):
        for c in range(GRID):
            in_outer = math.hypot(r + 0.5 - cr, c + 0.5 - cc) < outer
            in_cut   = math.hypot(r + 0.5 - cut_r, c + 0.5 - cut_c) < cut_rad
            if in_outer and not in_cut:
                p[(r, c)] = color


def stars(p, pos=None, color=MOON):
    for r, c in (pos or [(1, 2), (2, 13), (0, 8), (4, 5)]):
        if 0 <= r < GRID and 0 <= c < GRID:
            p[(r, c)] = color


def cloud(p, base_r=9.0, center_c=8.0, color=CLOUD, scale=1.0):
    s = scale
    for br, bc, br_r in [
        (base_r - 2.0*s, center_c - 2.5*s, 2.2*s),
        (base_r - 3.5*s, center_c + 0.0*s, 2.8*s),
        (base_r - 2.5*s, center_c + 3.0*s, 2.0*s),
    ]:
        circle(p, br, bc, br_r, color)
    for r in range(int(base_r - 3.2*s), int(base_r) + 1):
        for c in range(int(center_c - 4.0*s), int(center_c + 4.5*s) + 1):
            if 0 <= r < GRID and 0 <= c < GRID:
                p[(r, c)] = color


def rain(p, start_r=11, cols=None, color=RAIN, stagger=True):
    for i, c in enumerate(cols or [3, 5, 7, 9, 11]):
        r_off = (i % 2) if stagger else 0
        for dr in range(2):
            r = start_r + r_off + dr
            if 0 <= r < GRID and 0 <= c < GRID:
                p[(r, c)] = color


def snowflakes(p, start_r=11, cols=None, dot=SNOW_DOT, arm=SNOW_ARM):
    for i, c in enumerate(cols or [3, 7, 11]):
        r = start_r + (i % 2)
        for dr in (-1, 0, 1):
            nr = r + dr
            if 0 <= nr < GRID and 0 <= c < GRID:
                p[(nr, c)] = dot if dr == 0 else arm
        for dc in (-1, 1):
            if 0 <= r < GRID and 0 <= c + dc < GRID:
                p[(r, c + dc)] = arm


def lightning(p, cr=10, cc=9, color=BOLT):
    for r, c in [
        (cr,   cc),  (cr,   cc-1),
        (cr+1, cc-2),(cr+1, cc-1),
        (cr+2, cc),  (cr+2, cc+1),(cr+2, cc+2),
        (cr+3, cc+2),(cr+3, cc+3),
        (cr+4, cc+1),(cr+4, cc+2),
    ]:
        if 0 <= r < GRID and 0 <= c < GRID:
            p[(r, c)] = color


def windlines(p, rows, sc=1, ec=14, color=WIND_C):
    for r in rows:
        for c in range(sc, ec):
            if c % 5 != 4 and 0 <= r < GRID and 0 <= c < GRID:
                p[(r, c)] = color


def foglines(p, rows=None, color=FOG_C):
    for r in (rows or [4, 6, 8, 10, 12]):
        for c in range(2, 15):
            if c % 4 != 3 and 0 <= r < GRID:
                p[(r, c)] = color


def thermometer(p, stem=HOT_C, bulb=HOT_C):
    for r in range(3, 12):
        p[(r, 7)] = stem
        p[(r, 8)] = stem
    circle(p, 12.5, 7.5, 2.5, bulb)


# ── Icon definitions ──────────────────────────────────────────────────────────
def skc():
    p = {}; sun(p, 7.5, 7.5, 4.2); return p

def skc_night():
    p = {}; moon(p, 7.5, 7.5); stars(p); return p

def few():
    p = {}
    sun(p, 5.0, 5.0, 3.5)
    cloud(p, 11.5, 10.0, CLOUD_L, scale=0.75)
    return p

def few_night():
    p = {}
    moon(p, 5.0, 5.5, 3.0)
    cloud(p, 11.5, 10.0, CLOUD_L, scale=0.75)
    return p

def sct():
    p = {}
    sun(p, 5.0, 4.5, 3.2)
    cloud(p, 11.0, 9.5, CLOUD, scale=0.9)
    return p

def sct_night():
    p = {}
    moon(p, 5.0, 5.0, 2.8)
    cloud(p, 11.0, 9.5, CLOUD, scale=0.9)
    return p

def bkn():
    p = {}
    sun(p, 4.0, 4.0, 2.8)
    cloud(p, 10.0, 9.0, CLOUD)
    return p

def bkn_night():
    p = {}
    moon(p, 4.0, 4.5, 2.5)
    cloud(p, 10.0, 9.0, CLOUD)
    return p

def ovc():
    p = {}
    cloud(p, 7.0, 8.0, CLOUD, scale=1.1)
    cloud(p, 11.0, 9.0, CLOUD_L, scale=0.8)
    return p

def wind_skc():
    p = {}
    sun(p, 5.5, 7.5, 3.5)
    windlines(p, [10, 12, 14])
    return p

def wind_skc_night():
    p = {}
    moon(p, 5.0, 7.5, 3.0)
    windlines(p, [10, 12, 14])
    return p

def wind_few():
    p = {}
    sun(p, 3.5, 4.0, 2.5)
    cloud(p, 9.0, 9.0, CLOUD_L, scale=0.7)
    windlines(p, [12, 14])
    return p

def wind_few_night():
    p = {}
    moon(p, 3.5, 4.5, 2.2)
    cloud(p, 9.0, 9.0, CLOUD_L, scale=0.7)
    windlines(p, [12, 14])
    return p

def wind_sct():
    p = {}
    sun(p, 4.0, 4.0, 2.8)
    cloud(p, 9.5, 9.0, CLOUD, scale=0.85)
    windlines(p, [13, 15])
    return p

def wind_sct_night():
    p = {}
    moon(p, 4.0, 4.5, 2.5)
    cloud(p, 9.5, 9.0, CLOUD, scale=0.85)
    windlines(p, [13, 15])
    return p

def wind_bkn():
    p = {}
    sun(p, 3.5, 3.5, 2.2)
    cloud(p, 8.5, 8.0, CLOUD)
    windlines(p, [13, 15])
    return p

def wind_bkn_night():
    p = {}
    moon(p, 3.5, 4.0, 2.0)
    cloud(p, 8.5, 8.0, CLOUD)
    windlines(p, [13, 15])
    return p

def wind_ovc():
    p = {}
    cloud(p, 7.0, 8.0, CLOUD)
    windlines(p, [11, 13, 15])
    return p

def snow():
    p = {}
    cloud(p, 7.5, 8.0, CLOUD)
    snowflakes(p, 11, [3, 7, 11])
    return p

def rain_snow():
    p = {}
    cloud(p, 7.5, 8.0, CLOUD)
    rain(p, 11, [2, 6, 10], RAIN)
    snowflakes(p, 12, [4, 12])
    return p

def snow_sleet():
    p = {}
    cloud(p, 7.5, 8.0, CLOUD)
    snowflakes(p, 10, [2, 8])
    for r, c in [(12, 5), (13, 6), (12, 10), (13, 11)]:
        if 0 <= r < GRID and 0 <= c < GRID:
            p[(r, c)] = RAIN_L
    return p

def snow_fzra():
    p = {}
    cloud(p, 7.5, 8.0, CLOUD)
    rain(p, 11, [3, 7, 11], RAIN_L)
    snowflakes(p, 13, [5, 9])
    return p

def sleet():
    p = {}
    cloud(p, 7.5, 8.0, CLOUD)
    for i in range(5):
        r, c = 11 + i // 2, 2 + i * 2
        if 0 <= r < GRID and 0 <= c < GRID:
            p[(r, c)] = RAIN
        if 0 <= r + 1 < GRID and 0 <= c + 1 < GRID:
            p[(r + 1, c + 1)] = RAIN_L
    return p

def blizzard():
    p = {}
    cloud(p, 5.5, 8.0, CLOUD_D)
    cloud(p, 8.5, 9.0, CLOUD, scale=0.8)
    snowflakes(p, 11, [2, 6, 10, 13])
    windlines(p, [14], sc=1, ec=15, color=SNOW_ARM)
    return p

def icon_rain():
    p = {}
    cloud(p, 7.5, 8.0, CLOUD)
    rain(p, 11, [3, 5, 7, 9, 11])
    return p

def rain_sleet():
    p = {}
    cloud(p, 7.5, 8.0, CLOUD)
    rain(p, 11, [3, 7, 11], RAIN)
    for r, c in [(12, 5), (13, 6), (12, 10), (13, 11)]:
        if 0 <= r < GRID and 0 <= c < GRID:
            p[(r, c)] = RAIN_L
    return p

def fzra():
    p = {}
    cloud(p, 7.5, 8.0, CLOUD)
    rain(p, 11, [3, 5, 7, 9, 11], RAIN_L)
    for c in [4, 7, 10]:
        for r in [14, 15]:
            if 0 <= r < GRID:
                p[(r, c)] = SNOW_ARM
    return p

def rain_fzra():
    p = {}
    cloud(p, 7.5, 8.0, CLOUD)
    rain(p, 11, [3, 7, 11], RAIN)
    rain(p, 13, [5, 9], RAIN_L, stagger=False)
    return p

def rain_showers():
    p = {}
    cloud(p, 6.5, 8.0, CLOUD, scale=1.1)
    cloud(p, 9.0, 9.5, CLOUD_L, scale=0.7)
    rain(p, 12, [4, 7, 10])
    return p

def rain_showers_hi():
    p = {}
    cloud(p, 7.5, 8.0, CLOUD_L)
    rain(p, 11, [4, 8, 12])
    return p

def tsra():
    p = {}
    cloud(p, 5.5, 8.0, CLOUD_D)
    cloud(p, 8.5, 9.0, CLOUD, scale=0.8)
    lightning(p, 10, 8)
    rain(p, 11, [3, 12])
    return p

def tsra_sct():
    p = {}
    sun(p, 3.5, 3.5, 2.5)
    cloud(p, 8.5, 9.0, CLOUD)
    lightning(p, 10, 8)
    return p

def tsra_sct_night():
    p = {}
    moon(p, 3.5, 4.0, 2.2)
    cloud(p, 8.5, 9.0, CLOUD)
    lightning(p, 10, 8)
    return p

def tsra_hi():
    p = {}
    sun(p, 4.5, 4.0, 3.0)
    cloud(p, 10.0, 10.0, CLOUD_L, scale=0.7)
    lightning(p, 11, 9)
    return p

def tsra_hi_night():
    p = {}
    moon(p, 4.5, 4.5, 2.5)
    cloud(p, 10.0, 10.0, CLOUD_L, scale=0.7)
    lightning(p, 11, 9)
    return p

def tornado():
    p = {}
    for r in range(4):
        for c in range(GRID):
            p[(r, c)] = CLOUD_D
    for r, cols in [
        (4,  range(3, 13)), (5,  range(4, 12)),
        (6,  range(5, 11)), (7,  range(5, 11)),
        (8,  range(6, 10)), (9,  range(6, 10)),
        (10, range(7,  9)), (11, range(7,  9)),
        (12, [7, 8]),       (13, [7]),
        (14, [8]),
    ]:
        for c in cols:
            if 0 <= r < GRID and 0 <= c < GRID:
                p[(r, c)] = DARK
    for c in [2, 5, 11, 14]:
        p[(15, c)] = DARK
    return p

def hurricane():
    p = {(r, c): SKY_N for r in range(GRID) for c in range(GRID)}
    cr, cc = 7.5, 7.5
    for deg in range(0, 720, 10):
        a = math.radians(deg)
        t = (deg / 360.0) * 5.5
        pr = int(cr + math.sin(a) * t - 0.5)
        pc = int(cc + math.cos(a) * t - 0.5)
        if 0 <= pr < GRID and 0 <= pc < GRID:
            p[(pr, pc)] = CLOUD
    circle(p, 7.5, 7.5, 2.0, '#6688aa')
    circle(p, 7.5, 7.5, 1.0, '#99bbcc')
    return p

def tropical_storm():
    p = {(r, c): SKY_N for r in range(GRID) for c in range(GRID)}
    cr, cc = 7.5, 7.5
    for deg in range(0, 540, 15):
        a = math.radians(deg)
        t = (deg / 360.0) * 4.5
        pr = int(cr + math.sin(a) * t - 0.5)
        pc = int(cc + math.cos(a) * t - 0.5)
        if 0 <= pr < GRID and 0 <= pc < GRID:
            p[(pr, pc)] = CLOUD_L
    circle(p, 7.5, 7.5, 1.5, '#aaccdd')
    return p

def fog():
    p = {}; foglines(p); return p

def dust():
    p = {}
    for r in range(4, 15):
        for c in range(1, 15):
            if (r * 3 + c * 7) % 11 < 4:
                p[(r, c)] = DUST_C
            elif (r * 5 + c * 3) % 13 < 3:
                p[(r, c)] = '#aa8844'
    return p

def smoke():
    p = {}
    for col_base in [4, 8, 12]:
        for r in range(2, 15):
            offset = int(math.sin(r * 1.2 + col_base * 0.5) * 1.5)
            c = col_base + offset
            if 0 <= c < GRID:
                p[(r, c)] = SMOKE_C
            if r < 8 and 0 <= c + 1 < GRID:
                p[(r, c + 1)] = '#aaaaaa'
    return p

def haze():
    p = {}
    sun(p, 7.5, 7.5, 3.5, '#e8c040')
    # Horizontal haze bands overwrite every other row
    for r in range(GRID):
        if r % 2 == 1:
            for c in range(GRID):
                if (r, c) in p:
                    p[(r, c)] = '#ccaa44'
                else:
                    p[(r, c)] = HAZE_C
    return p

def hot():
    p = {}
    thermometer(p, '#ee4422', HOT_C)
    sun(p, 3.5, 12.5, 2.8)
    windlines(p, [5, 7], sc=0, ec=5, color='#ff8855')
    return p

def cold():
    p = {}
    thermometer(p, '#5599bb', COLD_C)
    snowflakes(p, 4,  [12], '#66aacc', '#99ccee')
    snowflakes(p, 9,  [13], '#66aacc', '#99ccee')
    return p

def unknown():
    p = {}
    cloud(p, 6.0, 8.0, CLOUD_L, scale=0.9)
    for r in [9, 10]:
        p[(r, 7)] = DARK; p[(r, 8)] = DARK
    p[(12, 7)] = DARK; p[(12, 8)] = DARK
    return p


# ── Registry & runner ─────────────────────────────────────────────────────────
ICONS = {
    'skc':             skc,
    'skc_night':       skc_night,
    'few':             few,
    'few_night':       few_night,
    'sct':             sct,
    'sct_night':       sct_night,
    'bkn':             bkn,
    'bkn_night':       bkn_night,
    'ovc':             ovc,
    'wind_skc':        wind_skc,
    'wind_skc_night':  wind_skc_night,
    'wind_few':        wind_few,
    'wind_few_night':  wind_few_night,
    'wind_sct':        wind_sct,
    'wind_sct_night':  wind_sct_night,
    'wind_bkn':        wind_bkn,
    'wind_bkn_night':  wind_bkn_night,
    'wind_ovc':        wind_ovc,
    'snow':            snow,
    'rain_snow':       rain_snow,
    'snow_sleet':      snow_sleet,
    'snow_fzra':       snow_fzra,
    'sleet':           sleet,
    'blizzard':        blizzard,
    'rain':            icon_rain,
    'rain_sleet':      rain_sleet,
    'fzra':            fzra,
    'rain_fzra':       rain_fzra,
    'rain_showers':    rain_showers,
    'rain_showers_hi': rain_showers_hi,
    'tsra':            tsra,
    'tsra_sct':        tsra_sct,
    'tsra_sct_night':  tsra_sct_night,
    'tsra_hi':         tsra_hi,
    'tsra_hi_night':   tsra_hi_night,
    'tornado':         tornado,
    'hurricane':       hurricane,
    'tropical_storm':  tropical_storm,
    'fog':             fog,
    'dust':            dust,
    'smoke':           smoke,
    'haze':            haze,
    'hot':             hot,
    'cold':            cold,
    'unknown':         unknown,
}

if __name__ == '__main__':
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for name, fn in ICONS.items():
        pixels = fn()
        svg = make_svg(pixels)
        path = os.path.join(OUTPUT_DIR, f'{name}.svg')
        with open(path, 'w') as f:
            f.write(svg)
    print(f'Generated {len(ICONS)} icons → {OUTPUT_DIR}/')
