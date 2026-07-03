#!/usr/bin/env python3
"""Generate quest marker positions using raw game coordinates.

Output: raw game coordinates [gz, gx] — no rotation, no transform.
CRS on frontend handles CCW rotation + L.Transformation automatically.
"""
import json, re, math

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

HTML_PATH = r"A:\JUST_DO_IT\EFT-professor\tarkov-map.html"
TRANSFORM_PATH = r"A:\JUST_DO_IT\EFT-professor\knowledge\tarkov-map\transform_config.json"

# Read HTML
with open(HTML_PATH, "r", encoding="utf-8") as f:
    html = f.read()

# Read transform config
with open(TRANSFORM_PATH, "r", encoding="utf-8") as f:
    transforms = json.load(f)

print(f"Loaded {len(transforms)} transform configs")

# Parse QUEST_MARKERS
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
escape_next = False
for ch in section:
    if escape_next:
        escape_next = False
        current += ch
        continue
    if ch == '\\' and in_string:
        escape_next = True
        current += ch
        continue
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
        json_start = current.find("{")
        if json_start >= 0:
            try:
                entries.append(json.loads(current[json_start:].rstrip(',')))
            except:
                pass
        current = ""
    elif brace_depth == 0 and current.strip().endswith("}"):
        json_start = current.find("{")
        if json_start >= 0:
            try:
                entries.append(json.loads(current[json_start:]))
            except:
                pass
        current = ""

print(f"Parsed {len(entries)} quests")

# Read game coordinates
with open(r"A:\JUST_DO_IT\EFT-professor\knowledge\tarkov-map\all_tasks_full.json", "r", encoding="utf-8") as f:
    tasks_raw = json.load(f)

tasks = tasks_raw['data']['tasks']

# Build lookup
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

# Assign rotated game coordinates — collect all unique zone positions
for e in entries:
    map_name = e["mapNormalizedName"]
    if map_name not in transforms:
        continue

    tid = e["id"]
    if tid in task_coords:
        coords = task_coords[tid]
        match = [co for co in coords if co[0] == map_name]
        if match:
            # Collect all unique positions, dedup by rounded [gz, gx]
            unique = set()
            for _, x, z in match:
                unique.add((round(z), round(x)))
            # Output raw game coordinates [gz, gx]
            # CRS handles rotation + transformation on frontend
            e["positions"] = sorted(list(unique))
            continue

# Grid fallback
from collections import defaultdict
by_map_quests = defaultdict(list)
for e in entries:
    by_map_quests[e["mapNormalizedName"]].append(e)

for map_name, quests in by_map_quests.items():
    if map_name not in transforms:
        continue
    total = len(quests)
    cols = max(1, math.ceil(math.sqrt(total)))
    rows = math.ceil(total / cols)
    for i, q in enumerate(quests):
        if "positions" not in q:
            col = i % cols
            row = i // cols
            q["positions"] = [[row * 100, col * 100]]

# Write back to HTML
new_entries_lines = []
for e in entries:
    obj_str = json.dumps(e["objectives"], ensure_ascii=False)
    poss = e.get("positions", [[0, 0]])
    new_entries_lines.append(
        f'{{"id": "{e["id"]}", "name": "{e["name"]}", '
        f'"mapNormalizedName": "{e["mapNormalizedName"]}", '
        f'"trader": "{e["trader"]}", "objectives": {obj_str}, '
        f'"positions": {json.dumps(poss)}}}'
    )

new_markers = "const QUEST_MARKERS = [\n" + ",\n".join(new_entries_lines) + "\n];"

html = html[:idx] + new_markers + html[end_idx + 2:]

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\nDone ({len(html)/1024:.0f} KB)")
print(f"  {len(entries)} total quest markers")
