"""仔仔细细查藏身处升级需求"""
import json

profile = json.load(open("E:/JUST_DO_IT/EFT-professor/user_profile_backup.json"))
items_db = json.load(open("D:/free games/EFT/SPT/SPT_Data/database/templates/items.json"))
hideout_db = json.load(open("D:/free games/EFT/SPT/SPT_Data/database/hideout/areas.json"))
locale = json.load(open("D:/free games/EFT/SPT/SPT_Data/database/locales/global/ch.json", encoding="utf8"))
prices = json.load(open("D:/free games/EFT/SPT/SPT_Data/database/templates/prices.json"))

areas = profile.get("characters", {}).get("pmc", {}).get("Hideout", {}).get("Areas", [])
items = profile.get("characters", {}).get("pmc", {}).get("Inventory", {}).get("items", [])

AREA_NAMES = {
    0: "水收集器",1: "休息室",2: "厨房",3: "工作台",4: "暖气",
    5: "太阳能",6: "医疗站",7: "卫生间",8: "NVIDIA",9: "比特币矿机",
    10: "照明",11: "通风",12: "空气过滤",13: "情报中心",14: "武器箱",
    15: "发电机",16: "供水",17: "卫生间2",18: "Area18",19: "Area19",
    20: "太阳能2",21: "工作台2",22: "情报中心2",23: "空气过滤2",
    24: "圈地",25: "圈地2",26: "圈地3",27: "圈地4"
}

CURRENCY_NAMES = {
    "5449016a4bdc2d6f028b456f": "₽RUB",
    "5696686a4bdc2da3298b456a": "$USD",
    "569668774bdc2da2298b4568": "€EUR"
}

# Count cash properly - check StackObjectsCount
def count_items(item_list):
    result = {}
    for it in item_list:
        tpl = it["_tpl"]
        upd = it.get("upd", {})
        if "StackObjectsCount" in upd:
            count = upd["StackObjectsCount"]
        elif "count" in upd:
            count = upd["count"]
        else:
            count = 1
        result[tpl] = result.get(tpl, 0) + count
    return result

stash_counts = count_items(items)

# 1. First check what the hideout database actually says for each facility
# Let's look at the RAW stage data for a few facilities the user questioned
print("=" * 100)
print("🔍 原始藏身处数据库需求检查")
print("=" * 100)

# Get max levels
max_levels = {}
for area in hideout_db:
    at = area.get("type", -1)
    stages = area.get("stages", {})
    mx = max(int(k) for k in stages.keys() if k.isdigit())
    max_levels[at] = mx
    name = AREA_NAMES.get(at, f"Area{at}")
    
    # Print all stages requirements in detail
    print(f"\n{'─' * 100}")
    print(f"📋 {name} (type={at}) | 最高Lv{mx}")
    for lv_str in sorted(stages.keys(), key=lambda x: int(x)):
        stage = stages[lv_str]
        lv = int(lv_str)
        reqs = stage.get("requirements", [])
        
        # Check if current profile level matches
        profile_area = next((a for a in areas if a.get("type") == at), None)
        current_lv = profile_area.get("level", 0) if profile_area else -1
        
        if lv <= current_lv:
            continue  # Skip already unlocked levels
        
        if lv > current_lv + 1:
            continue  # Only show next level
            
        print(f"\n  ▶ Lv{current_lv} → Lv{lv}")
        for req in reqs:
            rt = req.get("type", "?")
            if rt == "Item":
                tpl = req["templateId"]
                cnt = req.get("count", 1)
                iname = locale.get("templates", {}).get(tpl, {}).get("Name", "")
                iname2 = items_db.get(tpl, {}).get("_shortName", "")
                cname = CURRENCY_NAMES.get(tpl, "")
                owned = stash_counts.get(tpl, 0)
                
                if cname:
                    display_name = cname
                elif iname:
                    display_name = iname
                elif iname2:
                    display_name = iname2
                else:
                    display_name = tpl[:30]
                
                status = "✅" if owned >= cnt else "❌"
                print(f"    {status} {display_name:<35s} 需要 {cnt:>8,}  持有 {owned:>10,}")
            
            elif rt == "Area":
                an = AREA_NAMES.get(req.get("areaType", -1), f"Area{req.get('areaType',-1)}")
                rlv = req.get("requiredLevel", 0)
                # Check if this pre-req is met
                prereq_area = next((a for a in areas if a.get("type") == req.get("areaType", -1)), None)
                prereq_lv = prereq_area.get("level", 0) if prereq_area else 0
                prereq_status = "✅" if prereq_lv >= rlv else "❌"
                print(f"    {prereq_status} 前置: {an} Lv{rlv} (当前Lv{prereq_lv})")
            
            elif rt == "Skill":
                sn = req.get("skillName", "?")
                sl = req.get("skillLevel", 0)
                print(f"    ℹ️  技能: {sn} Lv{sl}")
            
            else:
                print(f"    ? {rt}: {json.dumps(req)[:100]}")

print(f"\n{'=' * 100}")
print("💰 当前现金")
for tpl, name in CURRENCY_NAMES.items():
    print(f"  {name}: {stash_counts.get(tpl, 0):>12,}")
