#!/usr/bin/env python3
"""Generate quest marker positions from game 3D coordinates."""
import json, math, re
from collections import OrderedDict

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

IMAGE_SIZES = {
    "factory": (6720, 3328), "customs": (7680, 4025), "woods": (6994, 6843),
    "lighthouse": (2242, 3892), "shoreline": (6668, 4567), "reserve": (4701, 2785),
    "interchange": (4300, 2378), "streets-of-tarkov": (7620, 5877),
    "the-lab": (3820, 1980), "ground-zero": (6920, 6920),
    "the-labyrinth": (4800, 4320), "terminal": (5760, 3240),
    "icebreaker": (7680, 4320), "night-factory": (6720, 3328),
    "ground-zero-21": (6920, 6920), "ground-zero-tutorial": (6920, 6920),
}

# coordinateToCardinalRotation: 90 for factory = swap X/Z
# For maps with rotation 90: imageY = gameX, imageX = gameZ
# For maps with rotation 180: imageY = -gameX, imageX = -gameZ
# For maps with rotation 0: imageY = gameZ, imageX = gameX
ROTATION = {
    "factory": 90, "night-factory": 90, "the-labyrinth": 90,
    "customs": 180, "woods": 180, "lighthouse": 180, "shoreline": 180,
    "reserve": 195.209, "interchange": 180, "streets-of-tarkov": 180,
    "the-lab": 270, "ground-zero": 180, "ground-zero-21": 180,
    "ground-zero-tutorial": 180, "terminal": 180, "icebreaker": 180,
}

# Read current HTML
with open(r"A:\JUST_DO_IT\EFT-professor\tarkov-map.html", "r", encoding="utf-8") as f:
    html = f.read()

# Parse current QUEST_MARKERS to get quest data (without position)
# Find the LAST definition — JS uses the last one, and there may be duplicates
idx = html.rfind("const QUEST_MARKERS = [")
end_idx = html.find("];\n\nconst CN_QUEST_NAMES", idx)
if end_idx == -1:
    end_idx = html.find("];\n\nconst TRADER_COLORS", idx)
if end_idx == -1:
    # Fallback: find ]; followed by blank lines
    end_idx = html.find("];\n\n\n", idx)
    
section = html[idx:end_idx+2]

# Parse entries by finding JSON objects
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

# Read game coordinates
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

# For each task, find the matching quest entry and assign position
# Group game coords by map to find ranges
from collections import defaultdict
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
    w, h = IMAGE_SIZES.get(name, (1000, 1000))
    rot = ROTATION.get(name, 0)
    print(f"{name}: X [{min(xs):.0f}, {max(xs):.0f}] Z [{min(zs):.0f}, {max(zs):.0f}] → img {w}x{h} rot={rot}°")

# Assign positions to quest markers
for e in entries:
    map_name = e["mapNormalizedName"]
    if map_name not in IMAGE_SIZES:
        continue
    w, h = IMAGE_SIZES[map_name]
    bounds = map_bounds.get(map_name)
    rot = ROTATION.get(map_name, 0)
    
    # Try to find matching game coordinate
    tid = e["id"]
    if tid in task_coords:
        coords = task_coords[tid]
        # Pick first coordinate that matches this map
        match = [c for c in coords if c[0] == map_name]
        if match:
            gx, gz = match[0][1], match[0][2]
            if bounds:
                min_x, max_x, min_z, max_z = bounds
                span_x = max(max_x - min_x, 1)
                span_z = max(max_z - min_z, 1)
                # Normalize to 0-1
                nx = (gx - min_x) / span_x
                nz = (gz - min_z) / span_z
                
                # Center around 0.5
                cx = nx - 0.5
                cz = nz - 0.5
                
                # Apply coordinateToCardinalRotation (counterclockwise)
                # This rotates game axes to align with cardinal directions.
                # After rotation, ry > 0 means north, ry < 0 means south.
                import math
                rad = math.radians(rot)
                rx = cx * math.cos(rad) - cz * math.sin(rad)
                ry = cx * math.sin(rad) + cz * math.cos(rad)
                
                # Map to image pixels with margin
                # The rotation already handles the game→cardinal orientation,
                # so no extra Y-flip needed — (ry + 0.5) maps north (positive ry)
                # to the top of the image (small img_y in Leaflet CRS.Simple).
                margin = 0.10
                img_x = round(w * (margin + (1 - 2*margin) * (rx + 0.5)))
                img_y = round(h * (margin + (1 - 2*margin) * (ry + 0.5)))
                
                e["position"] = [img_y, img_x]
                continue
    
    # Fallback: grid position
    pass

# Generate positions for quests without game coords using grid
by_map_quests = defaultdict(list)
for e in entries:
    by_map_quests[e["mapNormalizedName"]].append(e)

for map_name, quests in by_map_quests.items():
    if map_name not in IMAGE_SIZES:
        continue
    w, h = IMAGE_SIZES[map_name]
    total = len(quests)
    cols = max(1, math.ceil(math.sqrt(total * w / h)))
    rows = math.ceil(total / cols)
    margin = 0.12
    for i, q in enumerate(quests):
        if "position" not in q:
            col = i % cols
            row = i // cols
            y = round(h * (margin + (1 - 2*margin) * (row + 0.5) / rows))
            x = round(w * (margin + (1 - 2*margin) * (col + 0.5) / cols))
            q["position"] = [y, x]

# Write back to HTML
new_entries_lines = []
for e in entries:
    obj_str = json.dumps(e["objectives"], ensure_ascii=False)
    pos = e["position"]
    new_entries_lines.append(f'{{"id": "{e["id"]}", "name": "{e["name"]}", "mapNormalizedName": "{e["mapNormalizedName"]}", "trader": "{e["trader"]}", "objectives": {obj_str}, "position": [{pos[0]}, {pos[1]}]}}')

new_markers = "const QUEST_MARKERS = [\n" + ",\n".join(new_entries_lines) + "\n];"

html = html[:idx] + new_markers + html[end_idx+2:]

with open(r"A:\JUST_DO_IT\EFT-professor\tarkov-map.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"\n✅ Written ({len(html)/1024:.0f} KB)")
print(f"   {len(entries)} total quest markers")
