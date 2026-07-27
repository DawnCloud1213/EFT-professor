#!/bin/bash
# 批量拉取塔科夫知识库数据
BASE="E:/JUST_DO_IT/EFT-professor/knowledge"
API="https://api.tarkov.dev/graphql"
UA="EFT-Professor/1.0"

fetch() {
    local query="$1" outpath="$2" label="$3"
    mkdir -p "$(dirname "$outpath")"
    curl -s --max-time 30 "$API" \
        -H "Content-Type: application/json" \
        -H "User-Agent: $UA" \
        -d "{\"query\":$query}" > "$outpath"
    local size=$(wc -c < "$outpath")
    echo "  ✅ $label ($size bytes)"
}

echo "=== 1/8 弹药弹道数据 ==="
fetch '"'"'{ammo{item{id name shortName} caliber weight stackMaxSize tracer tracerColor damage armorDamage fragmentationChance penetrationPower projectileCount ballisticCooldown velocity}}'"'" \
    "$BASE/弹药弹道/ammo_raw.json" "弹药"

echo "=== 2/8 藏身处升级 ==="
fetch '"'"'{hideoutStations{id name levels{id level itemRequirements{item{id name shortName} quantity} station{name} crafts{craftTime requiredSkills{name level} rewardItems{item{id name shortName} quantity} requiredItems{item{id name shortName} quantity}}}}}'"'" \
    "$BASE/藏身处升级/hideout_raw.json" "藏身处"

echo "=== 3/8 Boss数据 ==="
fetch '"'"'{bosses{name imagePortraitLink spawnLocations{map{name} spawnChance spawnTime} escorts{name} health{bodyPart max} items{item{name shortName} slotId}}}'"'" \
    "$BASE/Boss数据/bosses_raw.json" "Boss"

echo "=== 4/8 钥匙与任务物品 ==="
fetch '"'"'{items(type:keys){id name shortName properties{...on KeyProperties{uses}} categories{name} types}}'"'" \
    "$BASE/钥匙与任务物品/keys_raw.json" "钥匙"

echo "=== 5/8 市场行情 ==="
fetch '"'"'{items(limit:2000){id name shortName properties{...on ItemProperties{examinedOnFirstAction}} fleaMarketFee low24hPrice avg24hPrice high24hPrice lastLowPrice traderPrices{trader{name} price} types categories{name}}}'"'" \
    "$BASE/市场行情/flea_raw.json" "市场"

echo "=== 6/8 武器改装 ==="
fetch '"'"'{items(type:mods){id name shortName categories{name} weight properties{...on WeaponProperties{ergonomics recoil accuracy} ...on ArmorProperties{armorClass}} types}}'"'" \
    "$BASE/武器改装/mods_raw.json" "配件"

echo "=== 口径映射 ==="
python -c "
import json
with open('$BASE/弹药弹道/ammo_raw.json') as f:
    d = json.load(f)
cals = set()
for a in d.get('data',{}).get('ammo',[]):
    cal = a.get('caliber','')
    if cal: cals.add(cal)
with open('$BASE/弹药弹道/calibers_map.json','w') as f:
    json.dump({'count':len(cals),'calibers':sorted(cals)}, f, ensure_ascii=False, indent=2)
print(f'  ✅ 口径映射: {len(cals)} 种')
"

echo ""
echo "✅ 全部数据拉取完成!"
ls -lh "$BASE/弹药弹道/"*.json "$BASE/藏身处升级/"*.json "$BASE/Boss数据/"*.json "$BASE/钥匙与任务物品/"*.json "$BASE/市场行情/"*.json "$BASE/武器改装/"*.json 2>/dev/null
