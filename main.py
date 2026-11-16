#!/usr/bin/env python3
"""makefun ai-excited-01 — "A Galaxy in a Seed".

One original image, drawn procedurally with the Python standard library only.

The idea (the surprise is the scale twist): the smallest thing in the
picture — one tiny seed resting at the bottom-left — is cracking open,
and an entire spiral galaxy is bursting out of it, racing diagonally
up-right so hard it smashes through the picture's own gold frame and
spills out of the corner. One focal point (the crack), one strong
diagonal, one bold limited palette (deep indigo night, warm gold,
star-white, cyan). No text: the image has to hit at a glance, and at
300 px the bright diagonal galaxy band and the glowing seed still read.

Deterministic: fixed RNG seed, no clock, no network, no dict-order
dependence. Writes $MAKEFUN_OUTPUT_DIR/entry.png (default
/output/entry.png), 800x800 RGB PNG, stdlib zlib encoding.
"""

import math
import os
import random
import struct
import zlib

W = H = 800
SEED = 20261116

# ---------------------------------------------------------------- canvas

canvas = bytearray(W * H * 3)


def _i(x, y):
    return (y * W + x) * 3


def put(x, y, r, g, b):
    if 0 <= x < W and 0 <= y < H:
        i = _i(x, y)
        canvas[i] = r
        canvas[i + 1] = g
        canvas[i + 2] = b


def blend(x, y, r, g, b, a):
    """Alpha-blend colour (r, g, b) over pixel (x, y); a in [0, 1]."""
    if 0 <= x < W and 0 <= y < H and a > 0.0:
        i = _i(x, y)
        if a >= 1.0:
            canvas[i] = r
            canvas[i + 1] = g
            canvas[i + 2] = b
        else:
            canvas[i] = int(canvas[i] + (r - canvas[i]) * a + 0.5)
            canvas[i + 1] = int(canvas[i + 1] + (g - canvas[i + 1]) * a + 0.5)
            canvas[i + 2] = int(canvas[i + 2] + (b - canvas[i + 2]) * a + 0.5)


def add(x, y, r, g, b, a):
    """Additive light: add colour * a to pixel (x, y), clamped."""
    if 0 <= x < W and 0 <= y < H and a > 0.0:
        i = _i(x, y)
        canvas[i] = min(255, canvas[i] + int(r * a + 0.5))
        canvas[i + 1] = min(255, canvas[i + 1] + int(g * a + 0.5))
        canvas[i + 2] = min(255, canvas[i + 2] + int(b * a + 0.5))


def disc(cx, cy, rad, rgb, alpha=1.0, soft=1.0):
    """Filled circle with a soft edge (soft px of falloff)."""
    r, g, b = rgb
    x0 = max(0, int(cx - rad - soft))
    x1 = min(W - 1, int(cx + rad + soft) + 1)
    y0 = max(0, int(cy - rad - soft))
    y1 = min(H - 1, int(cy + rad + soft) + 1)
    for y in range(y0, y1 + 1):
        dy = y - cy
        for x in range(x0, x1 + 1):
            dx = x - cx
            d = math.sqrt(dx * dx + dy * dy)
            if d <= rad:
                a = alpha
            elif d <= rad + soft:
                a = alpha * (1.0 - (d - rad) / soft)
            else:
                continue
            blend(x, y, r, g, b, a)


def glow(cx, cy, rad, rgb, strength=1.0):
    """Additive radial glow, brightest at the centre, fading out."""
    r, g, b = rgb
    x0 = max(0, int(cx - rad))
    x1 = min(W - 1, int(cx + rad) + 1)
    y0 = max(0, int(cy - rad))
    y1 = min(H - 1, int(cy + rad) + 1)
    for y in range(y0, y1 + 1):
        dy = (y - cy) / rad
        for x in range(x0, x1 + 1):
            dx = (x - cx) / rad
            d2 = dx * dx + dy * dy
            if d2 >= 1.0:
                continue
            fall = (1.0 - d2) * (1.0 - d2)
            add(x, y, r, g, b, strength * fall)


def line(x0, y0, x1, y1, rgb, width=1.0, alpha=1.0):
    """Thick straight segment, drawn as a chain of soft discs."""
    steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 2
    for k in range(steps + 1):
        t = k / steps
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t
        disc(x, y, width / 2.0, rgb, alpha, soft=0.8)


def sparkle(cx, cy, size, rgb, alpha=1.0):
    """Four-point star: bright core plus horizontal/vertical spikes."""
    disc(cx, cy, size * 0.28, (255, 255, 255), alpha, soft=1.0)
    line(cx - size, cy, cx + size, cy, rgb, width=1.6, alpha=alpha * 0.9)
    line(cx, cy - size, cx, cy + size, rgb, width=1.6, alpha=alpha * 0.9)
    line(cx - size * 0.55, cy - size * 0.55, cx + size * 0.55,
         cy + size * 0.55, rgb, width=1.0, alpha=alpha * 0.5)
    line(cx - size * 0.55, cy + size * 0.55, cx + size * 0.55,
         cy - size * 0.55, rgb, width=1.0, alpha=alpha * 0.5)


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_rgb(c1, c2, t):
    return (int(lerp(c1[0], c2[0], t) + 0.5),
            int(lerp(c1[1], c2[1], t) + 0.5),
            int(lerp(c1[2], c2[2], t) + 0.5))


# ---------------------------------------------------------------- palette

NAVY_DEEP = (4, 5, 15)
NAVY_MID = (13, 18, 48)
NAVY_GLOW = (24, 32, 74)
GOLD = (212, 175, 90)
GOLD_BRIGHT = (255, 205, 92)
AMBER = (242, 169, 59)
SEED_DARK = (122, 66, 18)
SEED_DEEP = (58, 30, 5)
WHITE = (255, 255, 255)
CYAN = (140, 220, 255)
VIOLET = (178, 140, 255)
MAGENTA = (255, 120, 200)

rng = random.Random(SEED)

# The burst axis: from the seed's crack toward the top-right corner.
CRACK = (300.0, 556.0)
DIAG = (0.719, -0.695)  # unit vector along the diagonal
DIAG_LEN = 560.0  # long enough for the arms to reach the broken corner


def along(t, perp=0.0):
    """Point t (0..1) along the burst diagonal, offset perp px sideways."""
    px = -DIAG[1]
    py = DIAG[0]
    return (CRACK[0] + DIAG[0] * DIAG_LEN * t + px * perp,
            CRACK[1] + DIAG[1] * DIAG_LEN * t + py * perp)


# ---------------------------------------------------------------- background

def paint_background():
    # Radial night gradient: lighter indigo around the burst, near-black
    # at the corners, plus a gentle vignette.
    cx, cy = 430.0, 380.0
    for y in range(H):
        dy = y - cy
        row = y * W * 3
        for x in range(W):
            dx = x - cx
            d = math.sqrt(dx * dx + dy * dy) / 620.0
            if d > 1.0:
                d = 1.0
            t = d * d * (3.0 - 2.0 * d)  # smoothstep
            r = int(lerp(NAVY_GLOW[0], NAVY_DEEP[0], t) + 0.5)
            g = int(lerp(NAVY_GLOW[1], NAVY_DEEP[1], t) + 0.5)
            b = int(lerp(NAVY_GLOW[2], NAVY_DEEP[2], t) + 0.5)
            i = row + x * 3
            canvas[i] = r
            canvas[i + 1] = g
            canvas[i + 2] = b


def paint_nebula():
    # Three huge, very faint colour washes so the night is not flat.
    glow(620, 180, 260, (64, 40, 110), 0.55)
    glow(180, 300, 240, (16, 60, 80), 0.45)
    glow(560, 640, 280, (80, 36, 60), 0.35)


def paint_back_stars():
    # Sparse distant stars; a few get a tiny sparkle.
    for _ in range(230):
        x = rng.uniform(20, 780)
        y = rng.uniform(20, 780)
        # Keep the burst corridor a little clearer so the galaxy owns it.
        bx = x - CRACK[0]
        by = y - CRACK[1]
        proj = bx * DIAG[0] + by * DIAG[1]
        perp = abs(-bx * DIAG[1] + by * DIAG[0])
        if 0.0 < proj < 430.0 and perp < 90.0:
            continue
        bright = rng.uniform(0.25, 1.0)
        size = rng.choice([0.7, 0.7, 1.0, 1.3])
        col = rng.choice([WHITE, WHITE, (220, 225, 255), (255, 240, 210)])
        disc(x, y, size, col, bright, soft=1.0)
        if bright > 0.9 and rng.random() < 0.25:
            sparkle(x, y, 5.0, col, 0.5)


# ---------------------------------------------------------------- the frame

def paint_frame():
    """Thin gold frame, broken at the top-right where the galaxy exits."""
    m = 26  # inset
    # Top edge: stops short of the corner (the break).
    line(m, m, 600, m, GOLD, width=3.0, alpha=0.95)
    # Right edge: starts below the corner (the break).
    line(774, 210, 774, 774, GOLD, width=3.0, alpha=0.95)
    # Bottom and left edges: whole.
    line(m, 774, 774, 774, GOLD, width=3.0, alpha=0.95)
    line(m, m, m, 774, GOLD, width=3.0, alpha=0.95)
    # Corner marks where the frame was torn away: small gold shards.
    line(612, 22, 640, 34, GOLD_BRIGHT, width=2.0, alpha=0.9)
    line(640, 34, 628, 48, GOLD, width=2.0, alpha=0.8)
    line(778, 224, 764, 248, GOLD_BRIGHT, width=2.0, alpha=0.9)
    line(764, 248, 780, 258, GOLD, width=2.0, alpha=0.8)


# ---------------------------------------------------------------- the seed

def paint_seed():
    """One small almond-shaped seed, warm amber, split open at the top.

    Drawn as a rotated ellipse (long axis along the burst diagonal),
    shaded darker toward its base, with a jagged glowing crack across
    its crown — the exact point the galaxy pours out of.
    """
    cx, cy = 266.0, 598.0
    a, b = 62.0, 44.0  # semi-axes
    ang = math.radians(-38.0)
    ca, sa = math.cos(ang), math.sin(ang)
    x0 = int(cx - 74)
    x1 = int(cx + 74)
    y0 = int(cy - 74)
    y1 = int(cy + 74)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            dx = x - cx
            dy = y - cy
            # Rotate into the ellipse's own frame.
            u = dx * ca + dy * sa
            v = -dx * sa + dy * ca
            q = (u / a) ** 2 + (v / b) ** 2
            if q > 1.0:
                continue
            # Shade: bright toward the crack (top-right), dark at the base.
            t = max(0.0, min(1.0, 0.5 - (u * 0.55 + v * 0.35) / 60.0))
            col = lerp_rgb(AMBER, SEED_DARK, t)
            edge = 1.0
            if q > 0.82:
                edge = max(0.0, (1.0 - q) / 0.18)
            blend(x, y, col[0], col[1], col[2], edge)
    # Dark rim so the seed reads against the night.
    for k in range(72):
        th = k / 72.0 * 2.0 * math.pi
        ex = cx + math.cos(th) * a
        ey = cy + math.sin(th) * b
        rx = ex * ca - ey * sa + cx * (1 - ca) + cy * sa
        ry = ex * sa + ey * ca + cy * (1 - ca) - cx * sa
        disc(rx, ry, 1.4, SEED_DEEP, 0.55, soft=1.0)
    # The crack: a dark fissure across the crown with light inside it.
    # Drawn dark first so the split reads on the seed's amber body,
    # then a thin bright line along the same zigzag for the glow
    # escaping it. The split starts inside the seed and exits through
    # its crown tip.
    crack_pts = [(296, 580), (304, 568), (300, 558), (310, 548),
                 (306, 538), (316, 528)]
    for (x0, y0), (x1, y1) in zip(crack_pts, crack_pts[1:]):
        line(x0, y0, x1, y1, SEED_DEEP, width=5.0, alpha=1.0)
    for (x0, y0), (x1, y1) in zip(crack_pts, crack_pts[1:]):
        line(x0, y0, x1, y1, (255, 236, 170), width=1.8, alpha=1.0)
    # Wedge of light: a fan of bright streaks fanning out of the split.
    for ang_deg, ln in [(-38, 46), (-24, 58), (-52, 52), (-10, 40),
                        (-66, 38)]:
        ar = math.radians(ang_deg)
        line(312, 552, 312 + math.cos(ar) * ln, 552 + math.sin(ar) * ln,
             (255, 232, 160), width=2.2, alpha=0.85)
    glow(306, 550, 22, GOLD_BRIGHT, 0.7)
    # Two shell lips curling away from the split.
    line(296, 580, 286, 566, SEED_DARK, width=4.0, alpha=0.9)
    line(316, 528, 328, 518, SEED_DARK, width=4.0, alpha=0.9)


# ---------------------------------------------------------------- the galaxy

def paint_core_glow():
    # The white-hot heart of the burst, right at the crack, plus a long
    # bright streak that drags the eye up the diagonal.
    glow(CRACK[0], CRACK[1], 170, (255, 214, 130), 0.9)
    glow(CRACK[0], CRACK[1], 70, (255, 246, 220), 1.0)
    disc(CRACK[0], CRACK[1], 16, (255, 250, 235), 1.0, soft=4.0)
    x0, y0 = along(0.02)
    # One soft, thin streak dragging the eye up the diagonal — a beam
    # of light, not a rod: no thick solid bar across the galaxy.
    line(x0, y0, along(0.34)[0], along(0.34)[1],
         (255, 240, 200), width=3.5, alpha=0.35)
    # Dense star cluster hugging the crack: the galaxy is thickest
    # where it pours out, thinning as it races away.
    for _ in range(130):
        t = rng.random() ** 2.0 * 0.35
        perp = rng.gauss(0.0, 26.0 + 70.0 * t)
        x, y = along(t, perp)
        size = rng.uniform(0.8, 3.0) * (1.0 - t)
        col = rng.choice([WHITE, GOLD_BRIGHT, (255, 230, 170)])
        glow(x, y, size * 3.0, col, 0.5)
        disc(x, y, size, col, 0.95, soft=1.0)


def paint_spiral():
    """Two spiral arms unwinding from the crack along the diagonal.

    The spiral's centre drifts up the diagonal as the arms unwind, so
    the whole galaxy is stretched along the burst axis: it is visibly
    escaping, not sitting still. Stars shrink and cool from white-gold
    at the core to cyan and violet at the rim. Each arm is a band, not
    a line: a soft nebulous wash under a dense scatter of stars, so the
    arms read as a galaxy at a glance instead of dotted rings.
    """
    for arm in (0.0, math.pi):
        for k in range(420):
            t = k / 419.0
            # One graceful sweep (~1.1 turns), not a tight coil: the arms
            # must flow out toward the corner, not loop back on themselves.
            ang = arm + t * 7.0
            rad = 9.0 + t * 220.0
            ccx, ccy = along(t * 0.94)
            px = ccx + math.cos(ang) * rad * 0.62
            py = ccy + math.sin(ang) * rad * 0.62
            # Scatter across the band's width so the arm has body.
            px += rng.gauss(0.0, 4.0 + 14.0 * t)
            py += rng.gauss(0.0, 4.0 + 14.0 * t)
            size = 3.4 * (1.0 - t) + 0.7
            if t < 0.35:
                col = lerp_rgb(WHITE, GOLD_BRIGHT, t / 0.35)
            elif t < 0.7:
                col = lerp_rgb(GOLD_BRIGHT, CYAN, (t - 0.35) / 0.35)
            else:
                col = lerp_rgb(CYAN, VIOLET, (t - 0.7) / 0.3)
            # Nebulous band wash under the stars (only near the arm).
            glow(px, py, size * 5.0 + 6.0, col, 0.16 * (1.0 - t * 0.5))
            glow(px, py, size * 3.2, col, 0.35 * (1.0 - t * 0.6))
            disc(px, py, size, col, 0.95, soft=1.2)
            if rng.random() < 0.05:
                sparkle(px, py, size * 4.0 + 4.0, col, 0.7)


def paint_speed_lines():
    """Thin streaks parallel to the diagonal: the burst in motion.

    Short and numerous, hugging the corridor — long scratches read as
    damage, short ones read as speed.
    """
    for _ in range(44):
        t = rng.uniform(0.05, 1.0)
        perp = rng.uniform(-150.0, 150.0)
        # Lines hug the corridor more tightly near the core.
        perp *= 0.45 + 0.55 * t
        x0, y0 = along(t, perp)
        length = rng.uniform(18.0, 70.0) * (1.1 - t * 0.55)
        x1 = x0 + DIAG[0] * length
        y1 = y0 + DIAG[1] * length
        col = rng.choice([WHITE, GOLD_BRIGHT, CYAN, (255, 220, 160)])
        line(x0, y0, x1, y1, col, width=rng.uniform(1.0, 1.8),
             alpha=rng.uniform(0.2, 0.5))


def paint_hero_stars():
    """A few big four-point stars riding the arm, plus escapees outside
    the broken frame corner — stars that already got out."""
    for (t, perp, size) in [(0.18, -34, 15), (0.38, 42, 18),
                            (0.55, -58, 13), (0.72, 30, 16),
                            (0.86, -20, 12)]:
        x, y = along(t, perp)
        sparkle(x, y, size, GOLD_BRIGHT, 0.95)
    # Escapees beyond the frame's broken corner.
    sparkle(724, 52, 14, WHITE, 0.9)
    sparkle(766, 96, 10, CYAN, 0.85)
    disc(700, 84, 2.2, WHITE, 1.0, soft=1.0)
    disc(748, 140, 1.8, GOLD_BRIGHT, 1.0, soft=1.0)


def paint_particles():
    """Small glowing embers and dust trailing the arms."""
    for _ in range(70):
        t = rng.uniform(0.0, 1.0)
        perp = rng.gauss(0.0, 55.0 + 60.0 * t)
        x, y = along(t, perp)
        size = rng.uniform(0.8, 2.4)
        col = rng.choice([GOLD_BRIGHT, WHITE, CYAN, (255, 190, 120)])
        glow(x, y, size * 3.0, col, 0.5)
        disc(x, y, size, col, 0.9, soft=1.0)


# ---------------------------------------------------------------- PNG encode

def png_bytes():
    """Encode the canvas as a deterministic RGB PNG (filter 0 rows)."""
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: None
        raw += canvas[y * W * 3:(y + 1) * W * 3]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += chunk(b"IEND", b"")
    return png


def main():
    paint_background()
    paint_nebula()
    paint_back_stars()
    paint_spiral()
    paint_core_glow()
    paint_speed_lines()
    paint_particles()
    paint_hero_stars()
    paint_seed()
    paint_frame()

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    data = png_bytes()
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes, %dx%d)" % (path, len(data), W, H))


if __name__ == "__main__":
    main()
