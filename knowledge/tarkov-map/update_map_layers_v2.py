import json, urllib.request, re

# Load transform config
with open(r"A:\JUST_DO_IT\EFT-professor\knowledge\tarkov-map\transform_config.json", encoding="utf-8") as f:
    transforms = json.load(f)

# Extract actual bounds from tarkov.dev source
url = "https://tarkov.dev/static/js/index.e2e4604e.js"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=15) as resp:
    js = resp.read().decode('utf-8')

bounds = {}
for nm in re.finditer(r'"normalizedName":"([^"]+)"', js):
    name = nm.group(1)
    rest = js[nm.end():nm.end()+5000]
    m = re.search(r'"projection":"interactive".*?"bounds":\[\[([-\d.]+),([-\d.]+)\],\[([-\d.]+),([-\d.]+)\]\]', rest, re.DOTALL)
    if m:
        bounds[name] = [[float(m.group(1)), float(m.group(2))], [float(m.group(3)), float(m.group(4))]]

# SVG URLs
SVG_URLS = {
    "factory": "https://assets.tarkov.dev/maps/svg/Factory.svg",
    "customs": "https://assets.tarkov.dev/maps/svg/Customs.svg",
    "woods": "https://assets.tarkov.dev/maps/svg/Woods.svg",
    "shoreline": "https://assets.tarkov.dev/maps/svg/Shoreline.svg",
    "reserve": "https://assets.tarkov.dev/maps/svg/Reserve.svg",
    "interchange": "https://assets.tarkov.dev/maps/svg/Interchange.svg",
}

# Build MAP_LAYERS
lines = ['const MAP_LAYERS = {']
lines.append('    // tarkov.dev official transform config — rotation + transform + bounds + tileUrl')

for name in sorted(transforms.keys()):
    cfg = transforms[name]
    a, b, c, d = cfg['transform']
    rot = cfg['rotation']
    tile = cfg['tilePath']
    svg = SVG_URLS.get(name)
    bnd = bounds.get(name, [[0, 0], [1000, 1000]])
    min_z, max_z = (2, 6) if name in ('woods','customs','factory','shoreline','reserve','interchange','the-lab') else (1, 5)

    entry = (
        f'    "{name}": {{ rotation: {rot}, '
        f'transform: [{a:.4f}, {b:.2f}, {c:.4f}, {d:.2f}], '
        f'bounds: [[{bnd[0][0]:.0f}, {bnd[0][1]:.0f}], [{bnd[1][0]:.0f}, {bnd[1][1]:.0f}]], '
        f'tileUrl: "{tile}", minZoom: {min_z}, maxZoom: {max_z}'
    )
    if svg:
        entry += f', svgUrl: "{svg}"'
    entry += ' },'
    lines.append(entry)
    print(f"  {name:25s} rot={rot:3d} a={a:.4f} b={b:.2f} bounds=[{bnd[0][0]:.0f},{bnd[0][1]:.0f}],[{bnd[1][0]:.0f},{bnd[1][1]:.0f}]")

lines.append('};')

# Write to HTML
with open(r"A:\JUST_DO_IT\EFT-professor\tarkov-map.html", encoding="utf-8") as f:
    html = f.read()

old_start = html.find("const MAP_LAYERS = {")
old_end = html.find("};", old_start) + 2
html = html[:old_start] + "\n".join(lines) + html[old_end:]

with open(r"A:\JUST_DO_IT\EFT-professor\tarkov-map.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"\n✅ Updated MAP_LAYERS ({len(transforms)} maps)")
