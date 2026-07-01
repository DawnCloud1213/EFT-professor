#!/usr/bin/env python3
"""Regenerate tarkov-map.html with clean SVGs as base maps, fixing all issues."""
import os, json, re, math

BASE = r"A:\JUST_DO_IT\EFT-professor"
HTML_PATH = os.path.join(BASE, "tarkov-map.html")

# Read existing HTML, keep HTML structure and JS functions, rebuild data section
with open(HTML_PATH, "r", encoding="utf-8") as f:
    html = f.read()

# MAP_LAYERS: SVG only (no satellite tiles)
# For maps without SVGs, use 2D JPG with same viewBox CRS
MAP_LAYERS_JS = '''const MAP_LAYERS = {
    "factory":         { file: "maps/svg/Factory.svg",          crsW: 130.82, crsH: 141.23,  rot: 90 },
    "customs":         { file: "maps/svg/Customs.svg",          crsW: 1062.48, crsH: 535.17,  rot: 180 },
    "woods":           { file: "maps/svg/Woods.svg",            crsW: 1472.79, crsH: 1420.60, rot: 180 },
    "lighthouse":      { file: "maps/svg/Lighthouse.svg",       crsW: 1059.38, crsH: 1722.95, rot: 180 },
    "shoreline":       { file: "maps/svg/Shoreline.svg",        crsW: 1559.57, crsH: 1032.49, rot: 180 },
    "reserve":         { file: "maps/svg/Reserve.svg",          crsW: 827.29,  crsH: 761.16,  rot: 195.209 },
    "interchange":     { file: "maps/svg/Interchange.svg",      crsW: 1127.69, crsH: 947.03,  rot: 180 },
    "streets-of-tarkov":{file: "maps/2d/Streets_of_Tarkov.jpg", crsW: 605.32,  crsH: 831.58,  rot: 180, isFallback: true },
    "night-factory":   { file: "maps/svg/Factory.svg",          crsW: 130.82,  crsH: 141.23,  rot: 90 },
    "the-lab":         { file: "maps/2d/Laboratory.jpg",        crsW: 1238,    crsH: 1078,    rot: 270, isFallback: true },
    "ground-zero":     { file: "maps/2d/Ground_Zero.jpg",       crsW: 600,     crsH: 600,     rot: 180, isFallback: true },
    "ground-zero-21":  { file: "maps/2d/Ground_Zero.jpg",       crsW: 600,     crsH: 600,     rot: 180, isFallback: true },
    "ground-zero-tutorial":{file: "maps/2d/Ground_Zero.jpg",    crsW: 600,     crsH: 600,     rot: 180, isFallback: true },
    "the-labyrinth":   { file: "maps/2d/Labyrinth.jpg",         crsW: 4800,    crsH: 4320,    rot: 90,  isFallback: true },
    "terminal":        { file: "maps/svg/Terminal.svg",         crsW: 887.70,  crsH: 1043.95, rot: 180 },
    "icebreaker":      { file: "maps/2d/Icebreaker.jpg",        crsW: 7680,    crsH: 4320,    rot: 180, isFallback: true }
};'''

# Replace MAP_LAYERS in HTML
ml_start = html.find("const MAP_LAYERS = {")
ml_end = html.find("};", ml_start) + 2
html = html[:ml_start] + MAP_LAYERS_JS + html[ml_end:]

# Remove style toggle buttons, simplify to single mode
# Change the two buttons to just one label
html = html.replace(
    '<button id="style-satellite" class="style-btn" onclick="setLayerStyle(\\\'satellite\\\')">🛰️ 卫星图</button>\\n        <button id="style-abstract" class="style-btn" onclick="setLayerStyle(\\\'abstract\\\')">🎨 抽象图</button>',
    '<span style="color:#d4c896;font-size:13px;margin:0 0 8px 12px;display:block">🖼️ 矢量手绘底图</span>'
)

# Also update switchMap to remove dual-layer logic (just use MAP_LAYERS directly)
switchmap_idx = html.find("const style = currentLayerStyle;")
if switchmap_idx > 0:
    end = html.find("\n    const crsW", switchmap_idx)
    html = html[:switchmap_idx] + "    const layer = mapData;\n    const crsW" + html[end:]

# Remove setLayerStyle function and style-btn CSS
html = html.replace(
    '\nfunction setLayerStyle(style) {\n        currentLayerStyle = style;\n        localStorage.setItem(\'tarkovMapStyle\', style);\n        document.querySelectorAll(\'.style-btn\').forEach(b => b.classList.remove(\'active\'));\n        document.getElementById(\'style-\' + style).classList.add(\'active\');\n        if (currentMap) switchMap(currentMap);\n    }',
    ''
)
html = html.replace(
    'applyStyleStyle(currentLayerStyle);',
    ''
)

# Clean up style-btn CSS class
html = html.replace(
    '\n.style-btn { background:#333; border:1px solid #555; color:#ccc; padding:4px 10px; cursor:pointer; font-size:13px; display:inline-block; margin:0 0 0 12px; border-radius:3px; }'
    '\n.style-btn.active { background:#d4c896; color:#1a1a1c; border-color:#d4c896; }',
    ''
)

# Remove duplicate MAP_LAYERS if any (the subagent's old code)
# Ensure there's only exactly ONE definition
count = html.count("const MAP_LAYERS = {")
if count > 1:
    # Keep only first, remove rest
    first = html.find("const MAP_LAYERS = {")
    second = html.find("const MAP_LAYERS = {", first + 20)
    if second > 0:
        second_end = html.find("};", second) + 2
        html = html[:second] + html[second_end:]

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print("✅ MAP_LAYERS simplified to single SVG-based layer")
print(f"   File size: {len(html)} bytes")

# Verify
checks = ["const MAP_LAYERS = {", "switchMap", "updateQuestMarkers", "CN_QUEST_NAMES", "TRADER_COLORS"]
for c in checks:
    print(f"   {'✅' if c in html else '❌'} Contains: {c}")
