import glob
import math
import re
import xml.etree.ElementTree as ET

NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)


def q(tag):
    return f"{{{NS}}}{tag}"


ANGLE = -30                      # rotate counter-clockwise so the strip is level
PAD = 12
COS = math.cos(math.radians(ANGLE))
SIN = math.sin(math.radians(ANGLE))


def rot(x, y):
    return x * COS - y * SIN, x * SIN + y * COS


for f in glob.glob("profile-3d-contrib/*.svg"):
    tree = ET.parse(f)
    root = tree.getroot()
    groups = root.findall(q("g"))
    bg = root.find(q("rect"))
    if not groups:
        print(f, "no groups, skipped")
        continue

    bgfill = bg.get("fill") if bg is not None else "#00000f"
    buildings = groups[0]

    xs, ys = [], []
    for g in buildings.findall(q("g")):
        m = re.match(r"translate\(\s*([-\d.]+)[ ,]+([-\d.]+)\s*\)", g.get("transform", ""))
        if not m:
            continue
        tx, ty = float(m.group(1)), float(m.group(2))
        rects = g.findall(q("rect"))
        h = float(rects[1].get("height")) * 1.15 if len(rects) > 1 else 3
        # tile bounding box in the generator's own coordinates
        for cx, cy in ((tx, ty - 10.4), (tx + 36, ty - 10.4),
                       (tx, ty + 10.4 + h), (tx + 36, ty + 10.4 + h)):
            rx, ry = rot(cx, cy)
            xs.append(rx)
            ys.append(ry)

    minx, miny = min(xs) - PAD, min(ys) - PAD
    W, H = max(xs) - minx + PAD, max(ys) - miny + PAD

    # keep only the buildings group, rotated
    for child in list(root):
        if child is not buildings:
            root.remove(child)
    buildings.set("transform", f"rotate({ANGLE})")

    new_bg = ET.Element(q("rect"), {
        "x": f"{minx:.2f}", "y": f"{miny:.2f}",
        "width": f"{W:.2f}", "height": f"{H:.2f}", "fill": bgfill,
    })
    root.insert(0, new_bg)

    root.set("viewBox", f"{minx:.2f} {miny:.2f} {W:.2f} {H:.2f}")
    root.set("width", f"{W:.0f}")
    root.set("height", f"{H:.0f}")

    tree.write(f, encoding="utf-8", xml_declaration=False)
    print(f, "rotated and cropped:", f"{W:.0f}x{H:.0f}")
