import glob
import re
import xml.etree.ElementTree as ET

NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)


def q(tag):
    return f"{{{NS}}}{tag}"


# Generator grid spacing (used only to read week/day out of the original SVG)
STEP_X, STEP_Y = 20.0, 11.545

# Flat front-view layout
CW = 9          # bar width
PX = 14         # horizontal pitch between weeks
PY = 10         # vertical pitch between days
DX, DY = 4, 4   # depth of each bar (top/right faces)
HSCALE = 0.5    # bar height multiplier
PAD = 10


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
    return " ".join(f"{a:.1f},{b:.1f}" for a, b in points)


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
    for w, d, h, (top, front, right) in cells:
        x = w * PX
        yb = d * PY + DY                       # bottom edge of the front face
        yt = yb - h                            # top edge of the front face
        shapes.append(f'<rect x="{x}" y="{yt:.1f}" width="{CW}" height="{h:.1f}" fill="{front}"/>')
        shapes.append(f'<polygon points="{pts([(x + CW, yt), (x + CW + DX, yt - DY), (x + CW + DX, yb - DY), (x + CW, yb)])}" fill="{right}"/>')
        shapes.append(f'<polygon points="{pts([(x, yt), (x + CW, yt), (x + CW + DX, yt - DY), (x + DX, yt - DY)])}" fill="{top}"/>')
        xs += [x, x + CW + DX]
        ys += [yt - DY, yb]

    minx, miny = min(xs) - PAD, min(ys) - PAD
    W, H = max(xs) - minx + PAD, max(ys) - miny + PAD
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" '
        f'viewBox="{minx:.1f} {miny:.1f} {W:.1f} {H:.1f}">'
        f'<rect x="{minx:.1f}" y="{miny:.1f}" width="{W:.1f}" height="{H:.1f}" fill="{bgfill}"/>'
        + "".join(shapes) + "</svg>"
    )
    open(f, "w", encoding="utf-8").write(svg)
    print(f, "front-view chart:", len(cells), "bars,", f"{W:.0f}x{H:.0f}")
