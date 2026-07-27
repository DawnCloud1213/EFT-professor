#!/usr/bin/env python3
"""获取塔科夫八大知识域原始数据 + 生成 Obsidian 笔记"""
import json, os, textwrap, math
from urllib.request import Request, urlopen
from urllib.error import HTTPError

API_URL = "https://api.tarkov.dev/graphql"
HEADERS = {"Content-Type": "application/json", "User-Agent": "EFT-Professor/1.0"}
BASE = "E:/JUST_DO_IT/EFT-professor/knowledge"

def query(graphql: str, label: str) -> dict:
    """执行 GraphQL 查询并返回 JSON"""
    data = json.dumps({"query": graphql}).encode()
    req = Request(API_URL, data=data, headers=HEADERS)
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        body = e.read().decode()[:500]
        print(f"  ❌ {label}: HTTP {e.code} – {body}")
        return {}
    except Exception as e:
        print(f"  ❌ {label}: {e}")
        return {}

def save_json(data: dict, path: str):
    """保存 JSON，含 data 字段检查"""
    if "data" in data and data["data"]:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data["data"], f, ensure_ascii=False, indent=2)
        kb = os.path.getsize(path) / 1024
        print(f"  ✅ {os.path.basename(path)} ({kb:.0f} KB)")
    else:
        print(f"  ⚠️  {os.path.basename(path)} 无有效数据")

# ─── 1. 弹药数据 ───
print("\n=== 1/8 弹药弹道数据 ===")
ammo_q = """{ammo{
  item{id name shortName}
  caliber weight stackMaxSize tracer tracerColor
  damage armorDamage fragmentationChance penetrationPower
  projectileCount ballisticCooldown velocity
}}"""
save_json(query(ammo_q, "弹药"), f"{BASE}/弹药弹道/ammo_raw.json")

# ─── 2. 藏身处升级 ───
print("\n=== 2/8 藏身处升级 ===")
hideout_q = """{hideoutStations{
  id name
  levels{
    id level
    itemRequirements{item{id name shortName} quantity}
    station{name}
    crafts{
      craftTime
      requiredSkills{name level}
      rewardItems{item{id name shortName} quantity}
      requiredItems{item{id name shortName} quantity}
}}}}"""
save_json(query(hideout_q, "藏身处"), f"{BASE}/藏身处升级/hideout_raw.json")

# ─── 3. Boss数据 ───
print("\n=== 3/8 Boss数据 ===")
boss_q = """{bosses{
  name imagePortraitLink
  spawnLocations{map{name} spawnChance spawnTime}
  escorts{name}
  health{bodyPart max}
  items{
    item{name shortName}
    slotId
}}}
"""
save_json(query(boss_q, "Boss"), f"{BASE}/Boss数据/bosses_raw.json")

# ─── 4. 钥匙数据 ───
print("\n=== 4/8 钥匙与任务物品 ===")
keys_q = """{items(type: keys){
  id name shortName
  properties{...on KeyProperties{uses}}
  categories{name}
  types
}}"""
save_json(query(keys_q, "钥匙"), f"{BASE}/钥匙与任务物品/keys_raw.json")

# ─── 5. 市场行情 ───
print("\n=== 5/8 市场行情 ===")
flea_q = """{items(limit: 2000){
  id name shortName
  properties{...on ItemProperties{examinedOnFirstAction}}
  fleaMarketFee low24hPrice avg24hPrice high24hPrice
  lastLowPrice traderPrices{trader{name} price}
  types categories{name}
}}"""
save_json(query(flea_q, "市场"), f"{BASE}/市场行情/flea_raw.json")

# ─── 6. 武器改装 ───
print("\n=== 6/8 武器改装 ===")
mods_q = """{items(type: mods){
  id name shortName
  categories{name}
  weight
  properties{
    ...on WeaponProperties{ergonomics recoil accuracy}
    ...on ArmorProperties{armorClass}
  }
  types
}}"""
save_json(query(mods_q, "配件"), f"{BASE}/武器改装/mods_raw.json")

# ─── 7. 弹药对武器的兼容性（弹种口径映射） ───
print("\n=== 弹药口径映射 ===")
# 从 ammo_raw 中提取 caliber 去重
ammo_path = f"{BASE}/弹药弹道/ammo_raw.json"
if os.path.exists(ammo_path):
    with open(ammo_path) as f:
        ammo_data = json.load(f)
    calibers = set()
    for a in ammo_data.get("ammo", []):
        cal = a.get("caliber", "")
        if cal:
            calibers.add(cal)
    out = {"total_calibers": len(calibers), "calibers": sorted(calibers)}
    with open(f"{BASE}/弹药弹道/calibers_map.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 口径映射: {len(calibers)} 种")
else:
    print("  ⚠️  ammo_raw.json 尚不存在")

print("\n✅ 所有数据拉取完成!")
