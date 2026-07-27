#!/usr/bin/env python3
"""Parse SPT save file and resolve item IDs to names via tarkov.dev API."""
import json
import sys
import subprocess
from collections import Counter, defaultdict

SAVE_PATH = "E:/JUST_DO_IT/EFT-professor/69568f09db017222c89b1183.json"

def load_save():
    with open(SAVE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def resolve_items_via_api(item_ids):
    """Batch resolve item IDs to names using tarkov.dev GraphQL API."""
    unique_ids = list(set(item_ids))
    result_map = {}
    
    for batch in chunk_list(unique_ids, 50):
        ids_json = json.dumps(batch)
        query = """
        query {
          items(ids: %s) {
            id name shortName categories { name }
          }
        }
        """ % ids_json
        
        curl_cmd = [
            "curl", "-s",
            "-X", "POST",
            "https://api.tarkov.dev/graphql",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"query": query})
        ]
        
        try:
            resp = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=30)
            data = json.loads(resp.stdout)
            if "data" in data and data["data"] and data["data"]["items"]:
                for item in data["data"]["items"]:
                    cat = item["categories"][0]["name"] if item.get("categories") else "Unknown"
                    result_map[item["id"]] = {
                        "name": item["name"],
                        "shortName": item["shortName"],
                        "category": cat
                    }
        except Exception as e:
            print(f"  ⚠️  API batch error: {e}", file=sys.stderr)
    
    return result_map

def categorize_items(items, name_map):
    """Organize items by category for display."""
    # Count items by category
    category_counts = Counter()
    category_items = defaultdict(list)
    
    # Track stash location items (items with grid positions in stash)
    stash_items = []
    equipment_items = []  # Items on the character (equipped)
    hideout_items = []    # Hideout area items
    
    for item in items:
        tid = item["_tpl"]
        info = name_map.get(tid, {"name": tid[:12]+"...", "shortName": tid[:8]+"...", "category": "Unknown"})
        cat = info["category"]
        
        slot = item.get("slotId", "")
        has_location = "location" in item
        parent = item.get("parentId", "")
        
        entry = {
            "id": item["_id"][:8],
            "tpl": tid,
            "name": info["name"],
            "shortName": info["shortName"],
            "category": cat,
            "slot": slot,
            "has_location": has_location,
            "count": item.get("upd", {}).get("StackObjectsCount", 1)
        }
        
        category_counts[cat] += 1
        
        if slot == "hideout":
            hideout_items.append(entry)
        elif has_location and not parent.startswith("664113fa"):
            stash_items.append(entry)
        else:
            equipment_items.append(entry)
    
    return category_counts, dict(category_items), stash_items, equipment_items, hideout_items

def main():
    print("🐱 喵科夫教授 · 存档物资分析报告")
    print("=" * 60)
    
    # Load save
    save = load_save()
    pmc = save["characters"]["pmc"]
    
    print(f"👤 玩家: {pmc['Info']['Nickname']}")
    print(f"🎖️ 阵营: {pmc['Info']['Side']}  |  Lv.{pmc['Info']['Level']}")
    print(f"💰 经验: {pmc['Info']['Experience']:,}")
    
    # Get inventory
    inventory = pmc["Inventory"]
    items = inventory["items"]
    print(f"\n📦 物品总数: {len(items)} 件")
    
    # Extract all unique _tpl IDs
    all_tpls = [item["_tpl"] for item in items]
    unique_tpls = set(all_tpls)
    print(f"🔖 物品种类: {len(unique_tpls)} 种")
    
    # Resolve via API
    print(f"\n🔄 正在查询 tarkov.dev API 解析物品名...", end=" ", flush=True)
    name_map = resolve_items_via_api(all_tpls)
    resolved = sum(1 for tid in unique_tpls if tid in name_map)
    print(f"完成！({resolved}/{len(unique_tpls)} 已解析)")
    
    # Categorize
    cat_counts, cat_items, stash_items, equip_items, hideout_items = categorize_items(items, name_map)
    
    # Summary by category
    print(f"\n📊 === 物资分类概览 ===")
    for cat, count in cat_counts.most_common(15):
        print(f"  {cat}: {count} 件")
    
    # Equipment summary
    print(f"\n🎒 === 正在穿戴/携带的装备 ===")
    equipped = [e for e in equip_items if e["has_location"]]
    for item in equipped[:30]:
        cnt = f" x{item['count']}" if item["count"] > 1 else ""
        print(f"  • {item['name']}{cnt}")
    if len(equipped) > 30:
        print(f"  ... 还有 {len(equipped) - 30} 件")
    
    # Stash top items
    print(f"\n🏠 === 仓库中的主要物资 ===")
    # Group by shortName for dedup
    stash_summary = Counter()
    for item in stash_items:
        stash_summary[item["shortName"]] += item["count"]
    for (name, qty), _ in stash_summary.most_common(20):
        print(f"  • {name} x{qty}")
    if len(stash_summary) > 20:
        print(f"  ... 还有 {len(stash_summary) - 20} 种其他物品")
    
    # Notable items - check for high value items
    valuable_keywords = ["keycard", "key", "Red", "Violet", "Black", "Blue", "Yellow",
                         "Labs", "GPU", "LEDX", "bitcoin", "BTC", "military", "armor",
                         "weapon", "ammo case", "items case", "lucky scav"]
    
    print(f"\n💎 === 可能有价值的物品 ===")
    valuable = []
    for item in stash_items + equip_items:
        for kw in valuable_keywords:
            if kw.lower() in item["name"].lower() or kw.lower() in item["shortName"].lower():
                valuable.append(item)
                break
    
    # Deduplicate
    seen_names = set()
    for item in valuable[:25]:
        key = f"{item['name']} x{item['count']}"
        if key not in seen_names:
            seen_names.add(key)
            cnt = f" x{item['count']}" if item["count"] > 1 else ""
            print(f"  💠 {item['name']}{cnt}  [{item['category']}]")
    
    # Hideout items
    if hideout_items:
        print(f"\n🏗️ === 藏身处设施 ===")
        hideout_summary = Counter()
        for item in hideout_items:
            hideout_summary[item["name"]] += item["count"]
        for name, qty in hideout_summary.most_common(10):
            print(f"  • {name} x{qty}")
    
    print(f"\n{'=' * 60}")
    print(f"✅ 分析完毕喵~ 主人仓库里共有 {len(stash_items)} 件仓库物品 + {len(equip_items)} 件随身物品 + {len(hideout_items)} 件藏身处设施！")
    
    # Save full resolved list for reference
    output = {
        "player": pmc["Info"]["Nickname"],
        "level": pmc["Info"]["Level"],
        "side": pmc["Info"]["Side"],
        "total_items": len(items),
        "unique_types": len(unique_tpls),
        "resolved": resolved,
        "unresolved": unique_tpls - set(name_map.keys()),
        "categories": dict(cat_counts),
        "total_stash": len(stash_items),
        "total_equipped": len(equip_items),
        "total_hideout": len(hideout_items),
    }
    outpath = "E:/JUST_DO_IT/EFT-professor/save_analysis_result.json"
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"📝 详细数据已保存到 save_analysis_result.json")

if __name__ == "__main__":
    main()
