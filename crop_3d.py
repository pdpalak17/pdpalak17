import glob
import xml.etree.ElementTree as ET

SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)

# x, y, width, height of the area that contains only the buildings
X, Y, W, H = 10, 130, 1200, 705

for f in glob.glob("profile-3d-contrib/*.svg"):
    tree = ET.parse(f)
    root = tree.getroot()

    seen_first_g = False
    for child in list(root):
        if child.tag == f"{{{SVG}}}g":
            if not seen_first_g:
                seen_first_g = True      # keep the buildings
            else:
                root.remove(child)       # drop radar, pie, bottom text
        elif child.tag == f"{{{SVG}}}rect":
            child.set("x", str(X))       # background fills the new area
            child.set("y", str(Y))
            child.set("width", str(W))
            child.set("height", str(H))

    root.set("viewBox", f"{X} {Y} {W} {H}")
    root.set("width", str(W))
    root.set("height", str(H))

    tree.write(f, encoding="utf-8", xml_declaration=False)
    print(f, "cropped")
