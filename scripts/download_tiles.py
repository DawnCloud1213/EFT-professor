#!/usr/bin/env python3
"""Download and stitch satellite tiles for all EFT maps."""
import os, json, sys, time
from PIL import Image
import urllib.request
import concurrent.futures

BASE_DIR = r"A:\JUST_DO_IT\EFT-professor"
OUT_DIR = os.path.join(BASE_DIR, "maps", "satellite")
os.makedirs(OUT_DIR, exist_ok=True)

TILE_PARAMS = {
    "factory":       {"url": "https://assets.tarkov.dev/maps/factory/main/{z}/{x}/{y}.png",          "z": 1, "x0": 0,  "x1": 1,  "y0": 0,  "y1": 1},
    "customs":       {"url": "https://assets.tarkov.dev/maps/customs_0.16/main/{z}/{x}/{y}.png",      "z": 2, "x0": 1,  "x1": 3,  "y0": 0,  "y1": 3},
    "woods":         {"url": "https://assets.tarkov.dev/maps/woods/main_0.16/{z}/{x}/{y}.png",        "z": 2, "x0": -1, "x1": 3,  "y0": 0,  "y1": 3},
    "shoreline":     {"url": "https://assets.tarkov.dev/maps/shoreline/main_summer/{z}/{x}/{y}.png",   "z": 2, "x0": 0,  "x1": 3,  "y0": 0,  "y1": 3},
    "reserve":       {"url": "https://assets.tarkov.dev/maps/reserve/main/{z}/{x}/{y}.png",            "z": 2, "x0": 0,  "x1": 3,  "y0": 0,  "y1": 3},
    "interchange":   {"url": "https://assets.tarkov.dev/maps/interchange/main/{z}/{x}/{y}.png",        "z": 1, "x0": -1, "x1": 2,  "y0": 0,  "y1": 1},
    "the-lab":       {"url": "https://assets.tarkov.dev/maps/labs_v4/1st/{z}/{x}/{y}.png",             "z": 2, "x0": 0,  "x1": 3,  "y0": 0,  "y1": 3},
    "ground-zero":   {"url": "https://assets.tarkov.dev/maps/groundzero/main_summer/{z}/{x}/{y}.png",  "z": 1, "x0": 0,  "x1": 1,  "y0": 0,  "y1": 1},
    "the-labyrinth": {"url": "https://assets.tarkov.dev/maps/labyrinth/main/{z}/{x}/{y}.png",           "z": 1, "x0": 0,  "x1": 1,  "y0": 0,  "y1": 1},
}

def download_tile(url, path):
    """Download a single tile, skip if exists."""
    if os.path.exists(path):
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            with open(path, "wb") as f:
                f.write(resp.read())
        return True
    except Exception as e:
        print(f"  FAILED: {url} -> {e}")
        return False

def process_map(name, params):
    """Download all tiles for a map and stitch them."""
    print(f"\n{name}:")
    z = params["z"]
    tile_size = 256
    
    # Build tile URL list
    tile_urls = {}
    for x in range(params["x0"], params["x1"] + 1):
        for y in range(params["y0"], params["y1"] + 1):
            url = params["url"].replace("{z}", str(z)).replace("{x}", str(x)).replace("{y}", str(y))
            cache_name = f"{name}_{z}_{x}_{y}.png"
            cache_path = os.path.join(OUT_DIR, cache_name)
            tile_urls[(x, y)] = (url, cache_path)
    
    # Download all tiles
    total = len(tile_urls)
    print(f"  Downloading {total} tiles...")
    success = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as exec:
        futures = {exec.submit(download_tile, url, path): (x,y) for (x,y), (url, path) in tile_urls.items()}
        for fut in concurrent.futures.as_completed(futures):
            if fut.result():
                success += 1
    
    if success < total:
        print(f"  Only {success}/{total} tiles downloaded, stitching what we have")
    
    # Determine grid dimensions
    x_min, x_max = params["x0"], params["x1"]
    y_min, y_max = params["y0"], params["y1"]
    cols = x_max - x_min + 1
    rows = y_max - y_min + 1
    
    # Stitch
    stitched = Image.new("RGB", (cols * tile_size, rows * tile_size), (128, 128, 128))
    for x in range(x_min, x_max + 1):
        for y in range(y_min, y_max + 1):
            cache_name = f"{name}_{z}_{x}_{y}.png"
            cache_path = os.path.join(OUT_DIR, cache_name)
            if os.path.exists(cache_path):
                tile_img = Image.open(cache_path)
                px = (x - x_min) * tile_size
                py = (y - y_min) * tile_size
                stitched.paste(tile_img, (px, py))
    
    out_path = os.path.join(OUT_DIR, f"{name}.png")
    stitched.save(out_path)
    print(f"  Saved: {out_path} ({stitched.width}x{stitched.height})")
    return {"name": name, "width": stitched.width, "height": stitched.height}

if __name__ == "__main__":
    print("=== Tarkov.dev Satellite Tile Downloader ===")
    print(f"Output: {OUT_DIR}")
    
    results = {}
    for name, params in TILE_PARAMS.items():
        results[name] = process_map(name, params)
    
    summary_path = os.path.join(BASE_DIR, "knowledge", "tarkov-api", "tile_results.json")
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Done! {len(results)} maps processed")
    print(f"Summary: {summary_path}")
