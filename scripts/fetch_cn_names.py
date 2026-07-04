#!/usr/bin/env python3
"""Fetch Chinese task names from tarkov.dev API and update CN_QUEST_NAMES in HTML."""
import json, re, urllib.request, os

HTML_PATH = r"A:\JUST_DO_IT\EFT-professor\tarkov-map.html"
API_URL = "https://json.tarkov.dev/regular/tasks_zh"

# 1) Fetch translations
print("Fetching tasks_zh...")
try:
    with urllib.request.urlopen(API_URL, timeout=30) as resp:
        translations = json.load(resp)
except Exception as e:
    print(f"urllib failed: {e}, trying curl fallback...")
    os.system(f'curl -sL --max-time 30 "{API_URL}" -o "A:/JUST_DO_IT/EFT-professor/tasks_zh_cache.json"')
    with open("A:/JUST_DO_IT/EFT-professor/tasks_zh_cache.json", encoding="utf-8") as f:
        translations = json.load(f)

print(f"Translations dict size: {len(translations)} entries")

# Handle possible {"data": {...}} wrapper
if "data" in translations and not any(k.endswith(" name") for k in translations.keys()):
    translations = translations["data"]
    print(f"Unwrapped data, now: {len(translations)} entries")

# 2) Read HTML
with open(HTML_PATH, encoding="utf-8") as f:
    html = f.read()

# 3) Extract all task IDs from QUEST_MARKERS
idx = html.find("const QUEST_MARKERS = [")
end = html.find("];", idx)
qm_block = html[idx:end+2]
task_ids = set(re.findall(r'"id": "([a-f0-9]+)"', qm_block))
print(f"QUEST_MARKERS: {len(task_ids)} unique task IDs")

# 4) Build CN_QUEST_NAMES mapping
cn_names = {}
for tid in sorted(task_ids):
    name = None
    for suffix in [" name", " Name", "name", "Name", ""]:
        key = tid + suffix
        if key in translations and translations[key]:
            val = translations[key]
            if isinstance(val, str) and len(val) > 1 and not val.startswith(tid):
                name = val
                break
    if name:
        cn_names[tid] = name

print(f"Found Chinese names: {len(cn_names)} / {len(task_ids)}")
missing = task_ids - set(cn_names.keys())
if missing:
    print(f"Missing ({len(missing)}): {', '.join(sorted(missing)[:10])}...")

# 5) Replace CN_QUEST_NAMES in HTML
old_start = html.find("const CN_QUEST_NAMES = {")
old_end = html.find("};", old_start) + 2

new_cn_block = "const CN_QUEST_NAMES = " + json.dumps(
    cn_names, ensure_ascii=False, indent=2
) + ";"

# Preserve indentation style
before = html[:old_start]
after = html[old_end:]
html_new = before + new_cn_block + after

# 6) Write back
with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html_new)

print(f"Updated HTML: {len(html_new)} bytes")
print("Done!")
