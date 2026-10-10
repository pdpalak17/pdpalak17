import glob, re

pattern = re.compile(
    r'<g[^>]*>\s*<path[^>]*d="M5 3\.25a\.75[^"]*"[^>]*?(?:/>|>\s*</path>)\s*</g>'
    r'\s*<text[^>]*>[^<]*(?:<title>[^<]*</title>)?\s*</text>',
    re.S,
)

for f in glob.glob("profile-3d-contrib/*.svg"):
    s = open(f, encoding="utf-8").read()
    new, n = pattern.subn("", s)
    if n:
        open(f, "w", encoding="utf-8").write(new)
    print(f, "removed" if n else "no match")
