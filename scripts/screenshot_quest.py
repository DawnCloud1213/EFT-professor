#!/usr/bin/env python3
"""One-click quest screenshot: hide others, resize container, take screenshots.

Usage:
  python scripts/screenshot_quest.py "情报就是力量"
  python scripts/screenshot_quest.py "Introduction"
"""
import sys, os, json, re, time, threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

PROJECT_DIR = r"A:\JUST_DO_IT\EFT-professor"
HTML_PATH = os.path.join(PROJECT_DIR, "tarkov-map.html")
OUT_DIR = os.path.join(PROJECT_DIR, "quest_screenshots")
PORT = 8765

# ── helpers ──────────────────────────────────────────────────────

def start_server():
    os.chdir(PROJECT_DIR)
    server = HTTPServer(("127.0.0.1", PORT), SimpleHTTPRequestHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    print(f"  HTTP server on :{PORT}")
    return server

def find_quest(name):
    """Parse HTML to find quest ID, English name, and maps."""
    with open(HTML_PATH, encoding="utf-8") as f:
        h = f.read()

    # CN_QUEST_NAMES
    idx = h.find("const CN_QUEST_NAMES = {")
    end = h.find("};", idx)
    cn_data = {}
    for m in re.finditer(r'"([a-f0-9]+)":\s*"([^"]+)"', h[idx:end]):
        cn_data[m.group(1)] = m.group(2)

    # QUEST_MARKERS
    idx2 = h.find("const QUEST_MARKERS = [")
    end2 = h.find("];", idx2)
    qm = []
    for m in re.finditer(r'{([^}]+)}', h[idx2:end2]):
        try:
            qm.append(json.loads("{" + m.group(1) + "}"))
        except:
            pass

    # Match by Chinese or English name
    tid = None
    for qid, cn_name in cn_data.items():
        if name.lower() in cn_name.lower():
            tid = qid; break
    if not tid:
        for entry in qm:
            if name.lower() in entry.get("name", "").lower():
                tid = entry["id"]; break
    if not tid:
        print(f"❌ Quest '{name}' not found!")
        sys.exit(1)

    en_name = next((e["name"] for e in qm if e["id"] == tid), "?")
    cn_name = cn_data.get(tid, en_name)
    maps = list(dict.fromkeys(e["mapNormalizedName"] for e in qm if e["id"] == tid))

    idx3 = h.find("const MAPS_DATA = [")
    end3 = h.find("];", idx3)
    map_display = {}
    for m in maps:
        dm = re.search(r'"name":"([^"]+)".*?"normalizedName":"' + m + '"', h[idx3:end3])
        map_display[m] = dm.group(1) if dm else m

    print(f"  Quest: {cn_name} ({en_name})  |  ID: {tid}")
    print(f"  Maps:  {', '.join(f'{m} ({map_display[m]})' for m in maps)}")
    return tid, en_name, cn_name, maps, map_display

# ── main ─────────────────────────────────────────────────────────

def screenshot_quest(name):
    tid, en_name, cn_name, maps, map_display = find_quest(name)
    os.makedirs(OUT_DIR, exist_ok=True)
    server = start_server()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 2560, "height": 1440})
        page = context.new_page()

        for i, m in enumerate(maps):
            print(f"\n  [{i+1}/{len(maps)}] {map_display[m]} ({m})...", end=" ", flush=True)

            # Fresh page load each map
            page.goto(f"http://127.0.0.1:{PORT}/tarkov-map.html",
                      wait_until="networkidle", timeout=15000)
            time.sleep(1)

            # Skip maps without MAP_LAYERS data
            has_map = page.evaluate("(name) => name in MAP_LAYERS", m)
            if not has_map:
                print(f"  ⚠️ No MAP_LAYERS data, skipping.")
                continue

            # All-in-one JS: switchMap → hide all + show target → satellite → resize container
            js = f"""
() => {{
    switchMap('{m}');
    hiddenQuestIds.clear();
    QUEST_MARKERS.forEach(q => hiddenQuestIds.add(q.id));
    const t = QUEST_MARKERS.find(q => q.name === '{en_name}' && q.mapNormalizedName === '{m}');
    if (t) hiddenQuestIds.delete(t.id);
    updateQuestMarkers(currentMap);
    buildQuestList('');
    setLayerStyle('satellite');
    return new Promise(r => setTimeout(() => {{
        const b = MAP_LAYERS[currentMap].bounds;
        const sw = map.latLngToContainerPoint(L.latLng(b[0][0], b[0][1]));
        const ne = map.latLngToContainerPoint(L.latLng(b[1][0], b[1][1]));
        const ow = Math.abs(ne.x - sw.x);
        const oh = Math.abs(ne.y - sw.y);
        const mc = document.getElementById('map-container');
        mc.style.width = ow + 'px';
        mc.style.height = oh + 'px';
        mc.style.flex = '0 0 auto';
        map.invalidateSize(true);
        r(JSON.stringify({{w: Math.round(ow), h: Math.round(oh), markers: document.querySelectorAll('.trader-marker').length}}));
    }}, 2000));
}}
"""
            try:
                result = json.loads(page.evaluate(js))
            except Exception as e:
                print(f"  ❌ JS evaluate failed: {e}")
                continue

            print(f"  {result['markers']} markers, size {result['w']}x{result['h']}")
            time.sleep(0.5)

            # Screenshot — only the #map element
            out_path = os.path.join(OUT_DIR, f"{m}.png")
            try:
                page.locator("#map").screenshot(path=out_path)
                fsize = os.path.getsize(out_path) / 1024
                print(f"  Saved: {m}.png ({result['w']}x{result['h']}, {fsize:.0f}KB)")
            except Exception as e:
                print(f"  ❌ Screenshot failed: {e}")
                continue

        browser.close()
        server.shutdown()

    print(f"\n✅ Done! {len(maps)} screenshots → {OUT_DIR}/")
    for m in maps:
        print(f"   {map_display[m]}: quest_screenshots/{m}.png")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/screenshot_quest.py '任务名'")
        print("Examples:")
        print("  python scripts/screenshot_quest.py '介绍'")
        print("  python scripts/screenshot_quest.py 'Introduction'")
        sys.exit(1)
    screenshot_quest(sys.argv[1])
