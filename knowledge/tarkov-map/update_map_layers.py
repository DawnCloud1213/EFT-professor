import json, re

# Read transform config
with open(r"A:\JUST_DO_IT\EFT-professor\knowledge\tarkov-map\transform_config.json", encoding="utf-8") as f:
    transforms = json.load(f)

# Read current HTML
with open(r"A:\JUST_DO_IT\EFT-professor\tarkov-map.html", encoding="utf-8") as f:
    html = f.read()

# Extract tile ranges from current MAP_LAYERS
tile_ranges = {}
for m in re.finditer(r'"([\w-]+)":\s*\{[^}]*tx0:\s*(-?\d+)[^}]*tx1:\s*(\d+)[^}]*ty0:\s*(\d+)[^}]*ty1:\s*(\d+)', html):
    tile_ranges[m.group(1)] = (int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)))

print(f"Found tile ranges for: {list(tile_ranges.keys())}")

# Build new MAP_LAYERS entries with transform
new_lines = []
for name, cfg in sorted(transforms.items()):
    a, b, c, d = cfg['transform']
    rot = cfg['rotation']
    tile = cfg['tilePath']
    tx0, tx1, ty0, ty1 = tile_ranges.get(name, (0, 1, 0, 1))
    
    # Get existing abstract config
    existing_m = re.search(
        rf'"{name}":\s*\{{[^}}]*abstract:\s*\{{\s*file:\s*"([^"]*)",\s*crsW:\s*([\d.]+),\s*crsH:\s*([\d.]+)\s*\}}',
        html, re.DOTALL
    )
    if existing_m:
        file_path = existing_m.group(1)
        crsW = existing_m.group(2)
        crsH = existing_m.group(3)
    else:
        file_path = f"maps/svg/{name.title()}.svg"
        crsW = "1000"
        crsH = "1000"
    
    entry = (
        f'    "{name}": {{ tileUrl: "{tile}", '
        f'tx0: {tx0}, tx1: {tx1}, ty0: {ty0}, ty1: {ty1}, rot: {rot}, '
        f'transform: [{a:.4f}, {b:.2f}, {c:.4f}, {d:.2f}], '
        f'abstract: {{ file: "{file_path}", crsW: {crsW}, crsH: {crsH} }} }},'
    )
    new_lines.append(entry)
    print(f"  {name}: tx0={tx0} rot={rot} a={a:.4f} b={b:.2f} d={d:.2f}")

# Add variant maps (night-factory, ground-zero-21, etc.)
variants = [
    '"night-factory":   { tileUrl: "https://assets.tarkov.dev/maps/factory/main/{z}/{x}/{y}.png",           tx0: 0,  tx1: 1,  ty0: 0,  ty1: 1,  rot: 90,  transform: [1.6290, 119.90, 1.6290, 139.30], abstract: { file: "maps/svg/Factory.svg",       crsW: 130.82,  crsH: 141.23 }},',
    '"ground-zero-21":  { tileUrl: "https://assets.tarkov.dev/maps/groundzero/main_summer/{z}/{x}/{y}.png",  tx0: 0,  tx1: 1,  ty0: 0,  ty1: 1,  rot: 180, transform: [0.5240, 167.30, 0.5240, 65.10], abstract: { file: "maps/2d/Ground_Zero.jpg",    crsW: 600,     crsH: 600 }},',
    '"ground-zero-tutorial":{tileUrl:"https://assets.tarkov.dev/maps/groundzero/main_summer/{z}/{x}/{y}.png",tx0:0, tx1:1, ty0:0, ty1:1, rot:180, transform: [0.5240, 167.30, 0.5240, 65.10], abstract: { file: "maps/2d/Ground_Zero.jpg",    crsW: 600,     crsH: 600 }},',
]
# Add abstract-only maps (lighthouse, streets, terminal, icebreaker)
abstract_only = [
    '"lighthouse":      { abstract: { file: "maps/2d/Lighthouse.png",       crsW: 1059.38, crsH: 1722.95, rot: 180 }},',
    '"streets-of-tarkov":{abstract: { file: "maps/2d/Streets_of_Tarkov.png", crsW: 605.32,  crsH: 831.58,  rot: 180 }},',
    '"terminal":        { abstract: { file: "maps/2d/Terminal.jpg",         crsW: 887.70,  crsH: 1043.95, rot: 180 }},',
    '"icebreaker":      { abstract: { file: "maps/2d/Icebreaker.jpg",        crsW: 7680,    crsH: 4320,    rot: 180 }},',
]

# Build the complete MAP_LAYERS
map_layers = "const MAP_LAYERS = {\n"
for entry in new_lines:
    map_layers += f"    {entry}\n"
map_layers += "    // Variants\n"
for v in variants:
    map_layers += f"    {v}\n"
map_layers += "    // Abstract-only maps\n"
for a in abstract_only:
    map_layers += f"    {a}\n"
map_layers += "};"

# Replace in HTML
old_start = html.find("const MAP_LAYERS = {")
old_end = html.find("};", old_start) + 2
html = html[:old_start] + map_layers + html[old_end:]

with open(r"A:\JUST_DO_IT\EFT-professor\tarkov-map.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"\n✅ Updated MAP_LAYERS with transform params")
print(f"   Total maps: {len(new_lines) + len(variants) + len(abstract_only)}")
