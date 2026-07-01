#!/usr/bin/env python3
"""Generate quest marker positions from game 3D coordinates."""
import json, math, re
from collections import defaultdict

# Map ID → normalized name mapping
MAP_IDS = {
    "55f2d3fd4bdc2d5f408b4567": "factory",
    "56f40101d2720b2a4d8b45d6": "customs",
    "5704e3c2d2720bac5b8b4567": "woods",
    "5704e4dad2720bb55b8b4567": "lighthouse",
    "5704e554d2720bac5b8b456e": "shoreline",
    "5704e5fad2720bc05b8b4567": "reserve",
    "5714dbc024597771384a510d": "interchange",
    "5714dc692459777137212e12": "streets-of-tarkov",
    "5b0fc42d86f7744a585f9105": "the-lab",
    "653e6760052c01c1c805532f": "ground-zero",
    "6733700029c367a3d40b02af": "the-labyrinth",
}

# Read current HTML (needed for MAP_LAYERS + QUEST_MARKERS)
HTML_PATH = r"A:\JUST_DO_IT\EFT-professor\tarkov-map.html"
with open(HTML_PATH, "r", encoding="utf-8") as f:
    html = f.read()

# Parse MAP_LAYERS from HTML to get CRS dimensions and rotation
# This keeps Python in sync with the HTML definitions — single source of truth
ml_start = html.find("const MAP_LAYERS = {")
ml_end = html.find("};", ml_start) + 2
map_layers_js = html[ml_start:ml_end]

CRS_SIZES = {}
ROTATION = {}
pattern = r'"([^"]+)":\s*\{[^}]*crsW:\s*([\d.]+)[^}]*crsH:\s*([\d.]+)[^}]*rot:\s*([\d.]+)'
for m in re.finditer(pattern, map_layers_js):
    name = m.group(1)
    CRS_SIZES[name] = (float(m.group(2)), float(m.group(3)))
    ROTATION[name] = float(m.group(4))

print(f"Parsed {len(CRS_SIZES)} maps from MAP_LAYERS")

# Parse QUEST_MARKERS — find the LAST definition (JS uses last if duplicates exist)
idx = html.rfind("const QUEST_MARKERS = [")
end_idx = html.find("];\n\nconst CN_QUEST_NAMES", idx)
if end_idx == -1:
    end_idx = html.find("];\n\nconst TRADER_COLORS", idx)
if end_idx == -1:
    end_idx = html.find("];\n\n\n", idx)

section = html[idx:end_idx + 2]

# Parse JSON entries
entries = []
brace_depth = 0
current = ""
in_string = False
for ch in section:
    if ch == '"' and not in_string:
        in_string = True
    elif ch == '"' and in_string:
        in_string = False
    if not in_string:
        if ch == '{':
            brace_depth += 1
        elif ch == '}':
            brace_depth -= 1
    current += ch
    if brace_depth == 0 and current.strip().endswith("},"):
        try:
            entries.append(json.loads(current.rstrip(',')))
        except:
            pass
        current = ""
    elif brace_depth == 0 and current.strip() == "}":
        try:
            entries.append(json.loads(current))
        except:
            pass
        current = ""

print(f"Parsed {len(entries)} quests")

# Read game coordinates from tarkov.dev API dump
with open(r"A:\JUST_DO_IT\EFT-professor\knowledge\tarkov-map\all_tasks_full.json", "r", encoding="utf-8") as f:
    tasks_raw = json.load(f)

tasks = tasks_raw['data']['tasks']

# Build lookup: zone position per task objective
task_coords = {}
for tid, task in tasks.items():
    zones_found = []
    for obj in task.get('objectives', []):
        for zone in obj.get('zones', []):
            if 'position' in zone:
                mid = zone.get('map', '')
                if mid in MAP_IDS:
                    norm_name = MAP_IDS[mid]
                    x = zone['position']['x']
                    z = zone['position']['z']
                    zones_found.append((norm_name, x, z))
    if zones_found:
        task_coords[tid] = zones_found

# Group game coords by map to find ranges
by_map = defaultdict(list)
for tid, coords_list in task_coords.items():
    for norm_name, x, z in coords_list:
        by_map[norm_name].append((x, z))

# Calculate bounds per map
map_bounds = {}
for name, coords in by_map.items():
    xs = [c[0] for c in coords]
    zs = [c[1] for c in coords]
    map_bounds[name] = (min(xs), max(xs), min(zs), max(zs))
    w, h = CRS_SIZES.get(name, (1000, 1000))
    rot = ROTATION.get(name, 0)
    print(f"{name}: X [{min(xs):.0f}, {max(xs):.0f}] Z [{min(zs):.0f}, {max(zs):.0f}] -> CRS {w}x{h} rot={rot}")

# Assign positions to quest markers
for e in entries:
    map_name = e["mapNormalizedName"]
    if map_name not in CRS_SIZES:
        continue
    w, h = CRS_SIZES[map_name]
    bounds = map_bounds.get(map_name)
    rot = ROTATION.get(map_name, 0)

    tid = e["id"]
    if tid in task_coords:
        coords = task_coords[tid]
        match = [c for c in coords if c[0] == map_name]
        if match:
            gx, gz = match[0][1], match[0][2]
            if bounds:
                min_x, max_x, min_z, max_z = bounds
                span_x = max(max_x - min_x, 1)
                span_z = max(max_z - min_z, 1)

                # Normalize game coords to [0, 1]
                nx = (gx - min_x) / span_x
                nz = (gz - min_z) / span_z

                # Center around 0.5 before rotation
                cx = nx - 0.5
                cz = nz - 0.5

                # Apply coordinateToCardinalRotation
                # After rotation: ry > 0 = north, ry < 0 = south
                rad = math.radians(rot)
                rx = cx * math.cos(rad) - cz * math.sin(rad)
                ry = cx * math.sin(rad) + cz * math.cos(rad)

                # Map to CRS image pixels with margin
                # (ry + 0.5) correctly maps north (positive ry) to top (small img_y)
                margin = 0.10
                img_x = round(w * (margin + (1 - 2 * margin) * (rx + 0.5)))
                img_y = round(h * (margin + (1 - 2 * margin) * (ry + 0.5)))

                e["position"] = [img_y, img_x]
                continue

# Grid fallback for quests without game coordinates
by_map_quests = defaultdict(list)
for e in entries:
    by_map_quests[e["mapNormalizedName"]].append(e)

for map_name, quests in by_map_quests.items():
    if map_name not in CRS_SIZES:
        continue
    w, h = CRS_SIZES[map_name]
    total = len(quests)
    cols = max(1, math.ceil(math.sqrt(total * w / h)))
    rows = math.ceil(total / cols)
    margin = 0.12
    for i, q in enumerate(quests):
        if "position" not in q:
            col = i % cols
            row = i // cols
            y = round(h * (margin + (1 - 2 * margin) * (row + 0.5) / rows))
            x = round(w * (margin + (1 - 2 * margin) * (col + 0.5) / cols))
            q["position"] = [y, x]

# Write back to HTML
new_entries_lines = []
for e in entries:
    obj_str = json.dumps(e["objectives"], ensure_ascii=False)
    pos = e["position"]
    new_entries_lines.append(
        f'{{"id": "{e["id"]}", "name": "{e["name"]}", '
        f'"mapNormalizedName": "{e["mapNormalizedName"]}", '
        f'"trader": "{e["trader"]}", "objectives": {obj_str}, '
        f'"position": [{pos[0]}, {pos[1]}]}}'
    )

new_markers = "const QUEST_MARKERS = [\n" + ",\n".join(new_entries_lines) + "\n];"

html = html[:idx] + new_markers + html[end_idx + 2:]

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\nDone ({len(html)/1024:.0f} KB)")
print(f"  {len(entries)} total quest markers")
