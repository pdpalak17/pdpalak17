import glob
import re
import xml.etree.ElementTree as ET

NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)


def q(tag):
    return f"{{{NS}}}{tag}"


# Original generator grid spacing (per week / per day step)
STEP_X, STEP_Y = 20.0, 11.545

# New flat layout: one tile step along each isometric axis
UX, UY = 10.0, 5.77      # down-right axis
K = 0.85                 # tile size vs. spacing (gap between tiles)
HSCALE = 1.0             # building height multiplier
PAD = 12


def read_tile(g):
    m = re.match(r"translate\(\s*([-\d.]+)[ ,]+([-\d.]+)\s*\)", g.get("transform", ""))
    x, y = float(m.group(1)), float(m.group(2))
    anim = g.find(q("animateTransform"))
    if anim is not None:                       # animated tile: start y = ground level
        y = float(anim.get("values").split(";")[0].split()[1])
    rects = g.findall(q("rect"))
    side_h = float(rects[1].get("height"))     # final (grown) height
    h = (side_h - 2.6) * 1.15 * HSCALE + 2.0
    return x, y, h, [r.get("fill") for r in rects[:3]]


def pts(points):
    return " ".join(f"{px:.2f},{py:.2f}" for px, py in points)


for f in glob.glob("profile-3d-contrib/*.svg"):
    root = ET.parse(f).getroot()
    bg = root.find(q("rect"))
    bgfill = bg.get("fill") if bg is not None else "#00000f"
    groups = root.findall(q("g"))
    if not groups:
        print(f, "no groups, skipped")
        continue

    raw = [read_tile(g) for g in groups[0].findall(q("g"))]
    if not raw:
        print(f, "no tiles, skipped")
        continue

    ox, oy = raw[0][0], raw[0][1]
    cells = []
    for x, y, h, fills in raw:
        a = (x - ox) / STEP_X
        b = (y - oy) / STEP_Y
        cells.append([round((a + b) / 2), round((b - a) / 2), h, fills])
    minw = min(c[0] for c in cells)
    mind = min(c[1] for c in cells)
    for c in cells:
        c[0] -= minw
        c[1] -= mind
    cells.sort(key=lambda c: (c[1], c[0]))     # back rows first

    shapes, xs, ys = [], [], []
    for w, d, h, (top, left, right) in cells:
        tx = w * 2 * UX - d * UX
        ty = d * UY
        T = (tx, ty)
        R = (tx + UX * K, ty + UY * K)
        L = (tx - UX * K, ty + UY * K)
        B = (tx, ty + 2 * UY * K)
        up = lambda p: (p[0], p[1] - h)
        shapes.append(f'<polygon points="{pts([L, B, up(B), up(L)])}" fill="{left}"/>')
        shapes.append(f'<polygon points="{pts([B, R, up(R), up(B)])}" fill="{right}"/>')
        shapes.append(f'<polygon points="{pts([up(T), up(R), up(B), up(L)])}" fill="{top}"/>')
        for p in (T, R, L, B, up(T)):
            xs.append(p[0]); ys.append(p[1])

    minx, miny = min(xs) - PAD, min(ys) - PAD
    W, H = max(xs) - minx + PAD, max(ys) - miny + PAD
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" '
        f'viewBox="{minx:.2f} {miny:.2f} {W:.2f} {H:.2f}">'
        f'<rect x="{minx:.2f}" y="{miny:.2f}" width="{W:.2f}" height="{H:.2f}" fill="{bgfill}"/>'
        + "".join(shapes) + "</svg>"
    )
    open(f, "w", encoding="utf-8").write(svg)
    print(f, "flattened", len(cells), "tiles")
