"""
Screenshot "Is This a Reference?" task - robust version with debugging
"""
import os, time, json
from playwright.sync_api import sync_playwright

TASK_ID = "66d9cbb67b491f9d5304f6e6"
URL = "http://localhost:8765/tarkov-map.html"
OUTPUT_DIR = r"A:\JUST_DO_IT\EFT-professor\screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

MAPS = [
    ("streets-of-tarkov", "Streets of Tarkov"),
    ("ground-zero", "Ground Zero"),
    ("ground-zero-21", "Ground Zero 21+"),
    ("lighthouse", "Lighthouse"),
    ("reserve", "Reserve"),
    ("customs", "Customs"),
    ("factory", "Factory"),
    ("woods", "Woods"),
    ("shoreline", "Shoreline"),
]

def screenshot_task(browser, map_name, map_label):
    page = browser.new_page()
    page.set_viewport_size({"width": 1920, "height": 1080})
    
    try:
        page.goto(URL, wait_until="load")
        page.wait_for_selector('#map', timeout=15000)
        time.sleep(2)
        
        # Switch to satellite view
        page.evaluate("() => { setLayerStyle('satellite'); }")
        time.sleep(1)
        
        # Switch map
        page.evaluate(f"(name) => {{ switchMap(name); }}", map_name)
        time.sleep(2)
        
        # Debug: check current map
        debug = page.evaluate("""() => JSON.stringify({
            currentMap: typeof currentMap !== 'undefined' ? currentMap : 'undefined',
            markersOnMap: document.querySelectorAll('.trader-marker').length
        })""")
        print(f"  After switch to {map_name}: {debug}")
        
        # Now filter quests
        result = page.evaluate("""
        (taskId) => {
            if (typeof hiddenQuestIds === 'undefined') return 'no-hiddenQuestIds';
            if (typeof QUEST_MARKERS === 'undefined') return 'no-QUEST_MARKERS';
            
            // Check how many entries for this task+map combo
            const matches = QUEST_MARKERS.filter(q => q.id === taskId && q.mapNormalizedName === currentMap);
            
            // Hide all then show only this task
            hiddenQuestIds.clear();
            QUEST_MARKERS.forEach(q => hiddenQuestIds.add(q.id));
            
            matches.forEach(m => hiddenQuestIds.delete(m.id));
            
            if (typeof updateQuestMarkers === 'function') updateQuestMarkers(currentMap);
            if (typeof buildQuestList === 'function') buildQuestList('');
            
            const markers = document.querySelectorAll('.trader-marker').length;
            return JSON.stringify({
                matches_on_this_map: matches.length,
                markers_after_filter: markers,
                currentMap: currentMap
            });
        }
        """, TASK_ID)
        print(f"  Filter result: {result}")
        
        time.sleep(1)
        
        # Hide sidebars
        page.evaluate("""
        () => {
            const s = document.getElementById('sidebar');
            const p = document.getElementById('search-panel');
            const b = document.querySelector('.search-collapse-btn');
            if(s) s.style.display='none';
            if(p) p.style.display='none';
            if(b) b.style.display='none';
            if(typeof map!=='undefined' && map.invalidateSize)
                setTimeout(() => map.invalidateSize(), 100);
        }
        """)
        time.sleep(1)
        
        # Screenshot
        path = os.path.join(OUTPUT_DIR, f"is-this-a-reference_{map_name}.png")
        el = page.query_selector('#map')
        if el:
            el.screenshot(path=path)
        else:
            page.screenshot(path=path)
        
        print(f"  ✓ Screenshot saved: {os.path.basename(path)}")
        return path
    except Exception as e:
        import traceback
        print(f"  ✗ {map_label} FAILED: {e}")
        traceback.print_exc()
        return None
    finally:
        page.close()


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        print(f"Starting screenshots for {len(MAPS)} maps...")
        for map_name, map_label in MAPS:
            print(f"\n--- {map_label} ---")
            screenshot_task(browser, map_name, map_label)
        browser.close()
    print("\n=== All done! ===")

if __name__ == "__main__":
    main()
