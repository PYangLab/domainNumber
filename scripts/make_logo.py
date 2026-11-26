"""Draw the kDomainBench logo: a tissue section covered by a Visium-like hexagonal
spot array and coloured by spatial domain. The domains are curved, slanted layers,
as in the DLPFC sections the benchmark uses, with a few mixed spots at the borders.

Writes docs/assets/logo.svg (for the header) and docs/assets/favicon.svg.

    python scripts/make_logo.py
"""
import math
import random
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "docs" / "assets"

# One colour per domain, ordered so that neighbouring layers contrast.
PALETTE = ["#4e79a7", "#f28e2b", "#59a14f", "#e15759", "#76b7b2", "#edc948", "#b07aa1"]


def tissue_spots(cx, cy, ax, ay, pitch, tilt_deg, bend, seed=3):
    """Hexagonal lattice inside an organic, wide tissue outline.

    Returns (x, y, domain) for each spot. Domains are bands along a tilted,
    bent axis; spots near a border sometimes take the neighbouring domain.
    """
    rnd = random.Random(seed)
    n = len(PALETTE)
    dy = pitch * math.sqrt(3) / 2
    tilt = math.radians(tilt_deg)
    cos_t, sin_t = math.cos(tilt), math.sin(tilt)

    def inside(x, y):
        u, v = (x - cx) / ax, (y - cy) / ay
        th = math.atan2(v, u)
        edge = 1 + 0.07 * math.sin(2 * th + 0.6) + 0.05 * math.sin(3 * th + 2.1) + 0.03 * math.sin(5 * th)
        return math.hypot(u, v) <= edge

    pts = []
    for j in range(-int(ay / dy) - 3, int(ay / dy) + 4):
        y = cy + j * dy
        off = pitch / 2 if j % 2 else 0.0
        for i in range(-int(ax / pitch) - 3, int(ax / pitch) + 4):
            x = cx + i * pitch + off
            if not inside(x, y):
                continue
            # depth across the layers: tilted axis, bent so the layers curve
            u, v = (x - cx) / ax, (y - cy) / ay
            along = u * cos_t + v * sin_t
            across = -u * sin_t + v * cos_t
            pts.append((x, y, along + bend * across * across + 0.04 * math.sin(across * 7)))
    ds = sorted(p[2] for p in pts)
    lo, hi = ds[0], ds[-1]
    out = []
    for x, y, d in pts:
        t = (d - lo) / (hi - lo) * n
        k = min(n - 1, int(t))
        frac = t - int(t)
        # border spots: occasionally take the neighbouring domain
        if frac < 0.18 and k > 0 and rnd.random() < 0.35:
            k -= 1
        elif frac > 0.82 and k < n - 1 and rnd.random() < 0.35:
            k += 1
        out.append((x, y, k))
    return out


def svg(spots, radius, title=None, pad=1.0):
    """The viewBox is fitted to the spots, so no spot is ever cut off."""
    x0 = min(x for x, _, _ in spots) - radius - pad
    y0 = min(y for _, y, _ in spots) - radius - pad
    w = max(x for x, _, _ in spots) + radius + pad - x0
    h = max(y for _, y, _ in spots) + radius + pad - y0
    body = [f'<circle cx="{x - x0:.1f}" cy="{y - y0:.1f}" r="{radius}" fill="{PALETTE[k]}"/>' for x, y, k in spots]
    head = f"<title>{title}</title>\n  " if title else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.1f} {h:.1f}" '
            f'width="{w:.1f}" height="{h:.1f}">\n  {head}' + "\n  ".join(body) + "\n</svg>\n")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # Header logo: a near-round section, slightly wider than tall.
    spots = tissue_spots(cx=58, cy=50, ax=54, ay=46, pitch=7.0, tilt_deg=-28, bend=0.9)
    (OUT / "logo.svg").write_text(svg(spots, 2.9, "kDomainBench"))
    # Favicon: round section, bigger spots, so it reads at 16 px.
    spots = tissue_spots(cx=50, cy=50, ax=44, ay=44, pitch=12.0, tilt_deg=-35, bend=0.8, seed=5)
    (OUT / "favicon.svg").write_text(svg(spots, 5.0))
    print("wrote", OUT / "logo.svg", OUT / "favicon.svg")


if __name__ == "__main__":
    main()
