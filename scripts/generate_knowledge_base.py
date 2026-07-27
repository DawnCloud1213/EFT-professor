#!/usr/bin/env python3
"""
塔科夫八大知识域 → Obsidian 笔记生成器
从 tarkov.dev GraphQL API 拉取数据，生成结构化 Markdown 笔记
"""
import json, subprocess, os, textwrap
from datetime import datetime

API = "https://api.tarkov.dev/graphql"
BASE = "E:/JUST_DO_IT/EFT-professor/knowledge"
VAULT = "E:/JUST_DO_IT/EFT-professor"  # Obsidian vault root

def gql(query):
    r = subprocess.run(["curl", "-s", "--max-time", "30", API,
        "-H", "Content-Type: application/json",
        "-H", "User-Agent: EFT-Professor/1.0",
        "-d", json.dumps({"query": query})],
        capture_output=True, text=True)
    return json.loads(r.stdout)

def save(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    kb = len(content.encode()) / 1024
    print(f"  ✅ {os.path.basename(path)} ({kb:.0f} KB)")

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    kb = os.path.getsize(path) / 1024
    print(f"  ✅ {os.path.basename(path)} ({kb:.0f} KB)")

CALIBER_NAMES = {
    "Caliber556x45NATO": "5.56x45 NATO", "Caliber762x39": "7.62x39",
    "Caliber545x39": "5.45x39", "Caliber9x19PARA": "9x19 Parabellum",
    "Caliber12g": "12ga", "Caliber762x54R": "7.62x54R",
    "Caliber762x51": "7.62x51", "Caliber9x39": "9x39",
    "Caliber366TKM": ".366 TKM", "Caliber9x18PM": "9x18 PM",
    "Caliber1143x23ACP": ".45 ACP", "Caliber57x28": "5.7x28",
    "Caliber46x30": "4.6x30", "Caliber9x21": "9x21",
    "Caliber127x55": "12.7x55", "Caliber23x75": "23x75",
    "Caliber40x46": "40x46", "Caliber40mmRU": "40mm RU",
    "Caliber762x25TT": "7.62x25 TT", "Caliber20g": "20ga",
    "Caliber26x75": "26x75", "Caliber30x29": "30x29",
}

# ═══════════════════════════════════════
# 1. 弹药弹道数据
# ═══════════════════════════════════════
print("=" * 50)
print("1/8 弹药弹道数据")
print("=" * 50)

data = gql("{ammo{item{id name shortName} caliber weight tracer tracerColor damage armorDamage fragmentationChance penetrationPower initialSpeed projectileCount}}")
ammo_list = data.get("data", {}).get("ammo", [])
print(f"  拉取到 {len(ammo_list)} 种弹药")
save_json(f"{BASE}/弹药弹道/ammo_raw.json", data["data"])

# 按口径分组
from collections import defaultdict
by_caliber = defaultdict(list)
for a in ammo_list:
    cal = a.get("caliber", "未知")
    by_caliber[cal].append(a)

md = f"""---
tags: [ammo, 弹药, 弹道, tarkov]
updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
---

# 🔫 弹药与弹道数据总表

> 数据来源: tarkov.dev API | 共 {len(ammo_list)} 种弹药 | {len(by_caliber)} 种口径

## 目录

"""
for cal in sorted(by_caliber.keys()):
    cname = CALIBER_NAMES.get(cal, cal)
    md += f"- [[#{cname}|{cname}]] — {len(by_caliber[cal])} 种\n"

for cal in sorted(by_caliber.keys()):
    cname = CALIBER_NAMES.get(cal, cal)
    items = by_caliber[cal]
    md += f"\n---\n## {cname}\n\n"
    md += f"| 弹药 | 伤害 | 穿透 | 肉伤 | 初速 | 曳光 | 破片率 | 弹头数 |\n"
    md += f"|------|:---:|:---:|:---:|:---:|:---:|:----:|:----:|\n"
    for a in sorted(items, key=lambda x: x.get("penetrationPower", 0), reverse=True):
        item = a.get("item", {})
        name = item.get("shortName", item.get("name", "?"))
        dmg = a.get("damage", "?")
        pen = a.get("penetrationPower", "?")
        armor = a.get("armorDamage", "?")
        vel = a.get("initialSpeed", "?")
        tracer = "🔴" if a.get("tracer") else "—"
        frag = a.get("fragmentationChance", 0)
        frag_str = f"{frag*100:.0f}%" if isinstance(frag, (int,float)) else "?"
        proj = a.get("projectileCount", 1)
        md += f"| {name} | {dmg} | {pen} | {armor} | {vel} | {tracer} | {frag_str} | {proj} |\n"

md += "\n## 穿透力排名（Top 10）\n\n"
top_pen = sorted(ammo_list, key=lambda a: a.get("penetrationPower", 0) or 0, reverse=True)[:10]
for i, a in enumerate(top_pen, 1):
    item = a.get("item", {})
    name = item.get("shortName", item.get("name", "?"))
    pen = a.get("penetrationPower", 0)
    dmg = a.get("damage", 0)
    cal = CALIBER_NAMES.get(a.get("caliber",""), a.get("caliber",""))
    md += f"{i}. **{name}** — 穿透 {pen} | 伤害 {dmg} | {cal}\n"

save(f"{BASE}/弹药弹道/弹药弹道数据.md", md)

# ═══════════════════════════════════════
# 2. 藏身处升级
# ═══════════════════════════════════════
print("\n" + "=" * 50)
print("2/8 藏身处升级")
print("=" * 50)

data = gql("{hideoutStations{id name levels{id level constructionTime itemRequirements{item{id name shortName} quantity} crafts{id duration requiredItems{item{id name shortName} quantity} rewardItems{item{id name shortName} quantity}} bonuses{type name value}}}}")
stations = data.get("data", {}).get("hideoutStations", [])
print(f"  拉取到 {len(stations)} 个设施")
save_json(f"{BASE}/藏身处升级/hideout_raw.json", data["data"])

md = f"""---
tags: [hideout, 藏身处, 升级, crafting, tarkov]
updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
---

# 🏠 藏身处升级指南

> 数据来源: tarkov.dev API | 共 {len(stations)} 个设施

"""
for s in stations:
    md += f"\n---\n## {s['name']}\n\n"
    for lv in s.get("levels", []):
        lv_num = lv.get("level", "?")
        time = lv.get("constructionTime", 0)
        time_str = f"{time//3600}h {(time%3600)//60}m" if time else "自动解锁"
        md += f"### 等级 {lv_num}  ⏱ {time_str}\n\n"
        # 材料需求
        reqs = lv.get("itemRequirements", [])
        if reqs:
            md += "**所需材料:**\n"
            for r in reqs:
                ri = r.get("item", {})
                rname = ri.get("shortName", ri.get("name", "?"))
                qty = r.get("quantity", "?")
                md += f"- {rname} × {qty}\n"
        # 制作配方
        crafts = lv.get("crafts", [])
        if crafts:
            md += "\n**制作配方:**\n"
            for c in crafts:
                dur = c.get("duration", 0)
                md += f"  - ⏱ {dur//60}m {dur%60}s\n"
                for ri in c.get("requiredItems", []):
                    rii = ri.get("item", {})
                    rn = rii.get("shortName", rii.get("name", "?"))
                    md += f"    - 消耗: {rn} × {ri.get('quantity','?')}\n"
                for ri in c.get("rewardItems", []):
                    rii = ri.get("item", {})
                    rn = rii.get("shortName", rii.get("name", "?"))
                    md += f"    - 产出: {rn} × {ri.get('quantity','?')}\n"

save(f"{BASE}/藏身处升级/藏身处升级指南.md", md)

# ═══════════════════════════════════════
# 3. Boss数据
# ═══════════════════════════════════════
print("\n" + "=" * 50)
print("3/8 Boss数据")
print("=" * 50)

# Boss 基本信息
data = gql("{bosses{id name normalizedName health{bodyPart max} imagePortraitLink items{id name shortName}}}")
bosses = data.get("data", {}).get("bosses", [])
print(f"  拉取到 {len(bosses)} 个Boss")

# 刷新位置从 maps 查询
data_maps = gql("{maps{name bosses{boss{name} spawnLocations{name chance} spawnChance escorts{name}}}}")
maps_data = data_maps.get("data", {}).get("maps", [])

# 按Boss名聚合 spawn 数据
boss_spawns = defaultdict(list)
for m in maps_data:
    mname = m.get("name", "")
    for b in m.get("bosses", []):
        bname = b.get("boss", {}).get("name", "")
        locs = b.get("spawnLocations", [])
        chance = b.get("spawnChance", 0)
        escorts = [e.get("name","") for e in b.get("escorts",[])]
        boss_spawns[bname].append({"map": mname, "chance": chance, "locations": locs, "escorts": escorts})

save_json(f"{BASE}/Boss数据/bosses_raw.json", data["data"])
save_json(f"{BASE}/Boss数据/boss_spawns.json", dict(boss_spawns))

md = f"""---
tags: [boss, scav, 首领, tarkov]
updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
---

# 👹 Boss 与 Scav 首领数据

> 数据来源: tarkov.dev API | 共 {len(bosses)} 个 Boss/首领

"""
for b in bosses:
    name = b.get("name", "?")
    md += f"\n---\n## {name}\n\n"
    # 血量
    health = b.get("health", [])
    if health:
        md += "| 部位 | 血量 |\n|------|:---:|\n"
        for h in health:
            md += f"| {h.get('bodyPart','?')} | {h.get('max','?')} |\n"
    # 装备
    items = b.get("items", [])
    if items:
        md += "\n**常见掉落:**\n"
        for it in items[:15]:
            iname = it.get("shortName", it.get("name", "?"))
            md += f"- {iname}\n"
    # 刷新
    spawns = boss_spawns.get(name, [])
    if spawns:
        md += "\n**刷新位置:**\n\n"
        for s in spawns:
            md += f"- **{s['map']}** (刷新率 {s.get('chance',0)*100:.0f}%)\n"
            for loc in s.get("locations", []):
                lname = loc.get("name", "?")
                lchance = loc.get("chance", 0)
                if isinstance(lchance, (int,float)) and lchance > 0:
                    md += f"  - {lname}: {lchance*100:.0f}%\n"
                else:
                    md += f"  - {lname}\n"
            if s.get("escorts"):
                md += f"  - 随从: {', '.join(s['escorts'])}\n"

save(f"{BASE}/Boss数据/Boss数据与刷新位置.md", md)

# ═══════════════════════════════════════
# 4. 钥匙与任务物品
# ═══════════════════════════════════════
print("\n" + "=" * 50)
print("4/8 钥匙与任务物品")
print("=" * 50)

data = gql("{items(type:keys){id name shortName properties{...on ItemPropertiesKey{uses}} categories{name} sellFor{vendor{name} priceRUB} lastLowPrice avg24hPrice}}")
keys = data.get("data", {}).get("items", [])
print(f"  拉取到 {len(keys)} 把钥匙")
save_json(f"{BASE}/钥匙与任务物品/keys_raw.json", data["data"])

md = f"""---
tags: [keys, 钥匙, 任务物品, tarkov]
updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
---

# 🔑 钥匙与任务物品清单

> 数据来源: tarkov.dev API | 共 {len(keys)} 把钥匙

"""

# 按价格排序分组
expensive = sorted([k for k in keys if k.get("sellFor")], key=lambda k: max((s.get("priceRUB",0) for s in k.get("sellFor",[])), default=0), reverse=True)

md += "## 💎 最值钱的钥匙（Top 20）\n\n| 钥匙名 | 最高售价 | 跳蚤均价 | 使用次数 |\n|--------|:-------:|:--------:|:-------:|\n"
for k in expensive[:20]:
    name = k.get("shortName", k.get("name", "?"))
    max_price = max((s.get("priceRUB",0) for s in k.get("sellFor",[])), default=0)
    flea = k.get("avg24hPrice") or k.get("lastLowPrice") or 0
    uses = k.get("properties", {}).get("uses", "?") if isinstance(k.get("properties"), dict) else "?"
    md += f"| {name} | {max_price:,}₽ | {flea or '—'} | {uses} |\n"

md += "\n## 📋 全部钥匙清单\n\n| 钥匙 | 英文名 | 售价(最高) | 使用次数 |\n|------|--------|:---------:|:-------:|\n"
for k in sorted(keys, key=lambda x: x.get("shortName", x.get("name",""))):
    name = k.get("shortName", k.get("name", "?"))
    fullname = k.get("name", "?")
    max_price = max((s.get("priceRUB",0) for s in k.get("sellFor",[])), default=0)
    uses = k.get("properties", {}).get("uses", "?") if isinstance(k.get("properties"), dict) else "?"
    price_str = f"{max_price:,}₽" if max_price > 0 else "—"
    uses_str = str(uses) if uses != "?" else "∞" if uses is None else str(uses)
    md += f"| {name} | {fullname} | {price_str} | {uses_str} |\n"

save(f"{BASE}/钥匙与任务物品/钥匙与任务物品清单.md", md)

# ═══════════════════════════════════════
# 5. 市场行情
# ═══════════════════════════════════════
print("\n" + "=" * 50)
print("5/8 市场行情")
print("=" * 50)

data = gql("{items(limit:2000){id name shortName categories{name} sellFor{vendor{name} priceRUB} buyFor{vendor{name} priceRUB} lastLowPrice avg24hPrice low24hPrice high24hPrice}}")
items = data.get("data", {}).get("items", [])
print(f"  拉取到 {len(items)} 个物品")
save_json(f"{BASE}/市场行情/flea_raw.json", data["data"])

# 分析：找出跳蚤 vs 商人差价最大的物品
profitable = []
for it in items:
    flea_price = it.get("avg24hPrice") or it.get("lastLowPrice") or 0
    trader_buy = 0
    for bf in it.get("buyFor", []):
        vname = bf.get("vendor", {}).get("name", "")
        if vname not in ("Flea Market",):
            trader_buy = max(trader_buy, bf.get("priceRUB", 0))
    if flea_price > 0 and trader_buy > 0 and flea_price > trader_buy * 1.1:
        profitable.append({"name": it.get("shortName", it.get("name","?")), "flea": flea_price, "trader": trader_buy, "ratio": flea_price/trader_buy, "profit": flea_price - trader_buy})

profitable.sort(key=lambda x: x["ratio"], reverse=True)

md = f"""---
tags: [market, flea, 跳蚤, 价格, tarkov]
updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
---

# 💰 Flea Market 行情概览

> 数据来源: tarkov.dev API | 共 {len(items)} 个物品

"""
if profitable:
    md += "## 📈 跳蚤 vs 商人套利空间（Top 30）\n\n"
    md += "| 物品 | 跳蚤价 | 商人买入 | 利润 | 倍率 |\n|------|:-----:|:-------:|:---:|:---:|\n"
    for p in profitable[:30]:
        md += f"| {p['name']} | {p['flea']:,}₽ | {p['trader']:,}₽ | +{p['profit']:,}₽ | x{p['ratio']:.1f} |\n"

md += "\n## 🔥 高价值物品（Top 50）\n\n| 物品 | 日均价 | 最低24h | 最高24h |\n|------|:-----:|:-------:|:-------:|\n"
top_items = sorted([it for it in items if it.get("avg24hPrice")], key=lambda x: x.get("avg24hPrice", 0) or 0, reverse=True)[:50]
for it in top_items:
    if it.get("avg24hPrice"):
        md += f"| {it.get('shortName', it.get('name','?'))} | {it['avg24hPrice']:,}₽ | {it.get('low24hPrice') or 0:,}₽ | {it.get('high24hPrice') or 0:,}₽ |\n"

save(f"{BASE}/市场行情/FleaMarket行情概览.md", md)

# ═══════════════════════════════════════
# 6. 武器改装
# ═══════════════════════════════════════
print("\n" + "=" * 50)
print("6/8 武器改装")
print("=" * 50)

data = gql("{items(type:mods limit:500){id name shortName categories{name} weight ergonomicsModifier recoilModifier accuracyModifier types}}")
mods = data.get("data", {}).get("items", [])
print(f"  拉取到 {len(mods)} 个配件（前500）")
save_json(f"{BASE}/武器改装/mods_raw.json", data["data"])

# 按类别分组
mod_cats = defaultdict(list)
for m in mods:
    cats = m.get("categories", [])
    primary_cat = cats[1]["name"] if len(cats) > 1 else (cats[0]["name"] if cats else "其他")
    mod_cats[primary_cat].append(m)

md = f"""---
tags: [mods, 改装, weapon, 配件, tarkov]
updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
---

# 🔧 武器改装配件指南

> 数据来源: tarkov.dev API | 共 {len(mods)} 个配件（显示前500个）

## 配件类别

"""
for cat in sorted(mod_cats.keys()):
    md += f"- [[#{cat}|{cat}]] — {len(mod_cats[cat])} 种\n"

for cat in sorted(mod_cats.keys()):
    items = sorted(mod_cats[cat], key=lambda x: x.get("ergonomicsModifier", 0) or 9999)
    md += f"\n---\n## {cat}\n\n"
    md += f"| 配件 | 重量 | 人机 | 后座 | 精度 |\n|------|:---:|:---:|:---:|:---:|\n"
    for m in items:
        name = m.get("shortName", m.get("name", "?"))
        wt = m.get("weight", "—")
        ergo = m.get("ergonomicsModifier", "—")
        recoil = m.get("recoilModifier", "—")
        acc = m.get("accuracyModifier", "—")
        wt_s = f"{wt:.2f}kg" if isinstance(wt, (int,float)) else "—"
        ergo_s = f"{ergo:+.0f}" if isinstance(ergo, (int,float)) else "—"
        recoil_s = f"{recoil:+.0%}" if isinstance(recoil, (int,float)) else "—"
        acc_s = f"{acc:+.0%}" if isinstance(acc, (int,float)) else "—"
        md += f"| {name} | {wt_s} | {ergo_s} | {recoil_s} | {acc_s} |\n"

# 人机最高
md += "\n## ⚡ 人机增益最高配件（Top 20）\n\n| 配件 | 人机 | 后座 |\n|------|:---:|:---:|\n"
top_ergo = sorted(mods, key=lambda x: x.get("ergonomicsModifier", 0) or -9999, reverse=True)[:20]
for m in top_ergo:
    name = m.get("shortName", m.get("name", "?"))
    ergo = m.get("ergonomicsModifier", "—")
    recoil = m.get("recoilModifier", "—")
    md += f"| {name} | {ergo:+.0f} | {recoil:+.0%} |\n"

save(f"{BASE}/武器改装/武器改装配件指南.md", md)

# ═══════════════════════════════════════
# 7. SPT模组推荐（本地知识）
# ═══════════════════════════════════════
print("\n" + "=" * 50)
print("7/8 SPT模组推荐")
print("=" * 50)

md = f"""---
tags: [spt, mods, 模组, 离线版, tarkov]
updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
---

# 🖥️ SPT 离线版模组推荐

> SPT 安装路径: `D:/free games/EFT/`
> SPT 版本: 4.0.x

## 📦 必备模组

| 模组 | 分类 | 说明 | 推荐度 |
|------|------|------|:----:|
| SAIN | AI | 更聪明的 Scav AI，行为更真实 | ⭐⭐⭐⭐⭐ |
| SWAG + Donuts | AI | 动态刷怪，可配置 PMC/Scav 比例 | ⭐⭐⭐⭐⭐ |
| AmandsGraphics | 画面 | 画质增强 + 性能优化 | ⭐⭐⭐⭐⭐ |
| Fika | 联机 | 合作/对战联机框架 | ⭐⭐⭐⭐ |
| Realism Mod | 游戏性 | 全面真实化：弹道、护甲、治疗 | ⭐⭐⭐⭐ |
| Fontain's FIFO | AI | AI 视野/听觉/反应更真实 | ⭐⭐⭐⭐ |
| Looting Bots | AI | 让 Scav/PMC 会搜刮战利品 | ⭐⭐⭐⭐ |
| Questing Bots | AI | 让 AI 会做任务、跑图 | ⭐⭐⭐⭐ |
| Backdoor Bandit | QoL | 可以撬锁开没钥匙的门 | ⭐⭐⭐ |
| SVM | 配置 | Server Value Modifier — 深度调参 | ⭐⭐⭐⭐⭐ |

## 🔧 已安装

- Fika — 联机框架
- AmandsGraphics — 画质增强

## 📥 安装注意事项

1. **禁止修改或删除游戏原有文件** — 所有模组只做新增
2. BepInEx 插件放 `BepInEx/plugins/`
3. SPT 服务器模组放 `SPT/user/mods/`
4. SAIN + SWAG + Donuts 建议一起装，AI 行为最完整
5. Realism Mod 会大改弹道/护甲，建议先备份存档

## 🔗 相关推荐

- [SPT 官网](https://sp-tarkov.com/)
- [模组下载 — hub.sp-tarkov.com](https://hub.sp-tarkov.com/)
"""

save(f"{BASE}/SPT模组/SPT模组推荐.md", md)

# ═══════════════════════════════════════
# 8. 跳蚤市场套利
# ═══════════════════════════════════════
print("\n" + "=" * 50)
print("8/8 跳蚤套利分析")
print("=" * 50)

# 从已有 barters 数据分析
barters_path = f"{BASE}/barters/barters_analyzed.json"
if os.path.exists(barters_path):
    with open(barters_path) as f:
        barters = json.load(f)
else:
    barters = []

md = f"""---
tags: [barter, 跳蚤, 套利, profit, tarkov]
updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
---

# 💸 跳蚤市场套利与 Barter 分析

> 基于已有 Barter 数据 + Flea Market 行情综合分析

"""
if barters:
    # 按利润排序
    barter_sorted = sorted(barters, key=lambda x: x.get("profit", 0), reverse=True)
    
    md += "## 🥇 最高利润 Barter 交换（Top 30）\n\n"
    md += "| 购入 | 数量 | 成本 | 产出 | 售价 | 利润 | 倍率 |\n|------|:---:|:---:|:----:|:---:|:---:|:---:|\n"
    for b in barter_sorted[:30]:
        required = b.get("requiredItems", [])
        reward = b.get("rewardItems", [])
        # 简单展示第一个材料和产出
        if required and reward:
            ri = required[0]
            rw = reward[0]
            cost = b.get("totalCost", 0)
            profit = b.get("profit", 0)
            ratio = b.get("ratio", 0)
            price = b.get("rewardValue", 0)
            md += f"| {ri.get('shortName','?')} | ×{ri.get('quantity','?')} | {cost:,}₽ | {rw.get('shortName','?')} | {price:,}₽ | **+{profit:,}₽** | x{ratio:.1f} |\n"
    
    md += "\n## 📊 数据概览\n\n"
    total = len(barters)
    profitable = sum(1 for b in barters if b.get("profit", 0) > 0)
    avg_profit = sum(b.get("profit", 0) for b in barters) / total if total > 0 else 0
    md += f"- 总交换数: {total}\n"
    md += f"- 有正利润: {profitable} ({profitable/total*100:.0f}%)\n"
    md += f"- 平均利润: {avg_profit:,.0f}₽\n"
    md += f"- 最高倍率: {barter_sorted[0].get('ratio',0):.1f}x — {barter_sorted[0].get('rewardItems',[{}])[0].get('shortName','?')}\n"
else:
    md += "\n> ⚠️ 暂无分析数据，请先运行 barter 分析脚本\n"

md += "\n## 🎯 快速赚钱策略\n\n"
md += "1. **检查商人物品** — 从商人低价买入，跳蚤高价卖出\n"
md += "2. **藏身处制造** — 搓子弹/配件往往比直接买便宜\n"
md += "3. **Barter 交换** — 用不值钱的杂物换高价值装备\n"
md += "4. **注意 RMT 警告** — 别碰真钱交易喵！\n"

save(f"{BASE}/跳蚤套利/跳蚤市场套利分析.md", md)

# ═══════════════════════════════════════
# 更新 INDEX.md
# ═══════════════════════════════════════
print("\n" + "=" * 50)
print("更新 INDEX.md 总索引")
print("=" * 50)

stats = {
    "弹药弹道": len(ammo_list),
    "藏身处升级": len(stations),
    "Boss数据": len(bosses),
    "钥匙与任务物品": len(keys),
    "市场行情": len(items),
    "武器改装": len(mods),
    "SPT模组": "推荐清单",
    "跳蚤套利": f"{len(barters)}条分析",
}

index = f"""# 🐱 喵科夫知识库 · EFT Professor

> 最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}
> 库路径: `{VAULT}`（Obsidian 库）

---

## 📚 知识域索引

| # | 领域 | 条目 | 笔记路径 | 原始数据 |
|:-:|------|:---:|----------|---------|
| 1 | [[弹药弹道数据|🔫 弹药与弹道]] | {stats['弹药弹道']} 种弹药 | `knowledge/弹药弹道/` | `ammo_raw.json` |
| 2 | [[藏身处升级指南|🏠 藏身处升级]] | {stats['藏身处升级']} 个设施 | `knowledge/藏身处升级/` | `hideout_raw.json` |
| 3 | [[Boss数据与刷新位置|👹 Boss与首领]] | {stats['Boss数据']} 个 Boss | `knowledge/Boss数据/` | `bosses_raw.json` |
| 4 | [[钥匙与任务物品清单|🔑 钥匙清单]] | {stats['钥匙与任务物品']} 把钥匙 | `knowledge/钥匙与任务物品/` | `keys_raw.json` |
| 5 | [[FleaMarket行情概览|💰 市场行情]] | {stats['市场行情']} 个物品 | `knowledge/市场行情/` | `flea_raw.json` |
| 6 | [[武器改装配件指南|🔧 武器改装]] | {stats['武器改装']} 个配件 | `knowledge/武器改装/` | `mods_raw.json` |
| 7 | [[SPT模组推荐|🖥️ SPT模组]] | {stats['SPT模组']} | `knowledge/SPT模组/` | — |
| 8 | [[跳蚤市场套利分析|💸 跳蚤套利]] | {stats['跳蚤套利']} | `knowledge/跳蚤套利/` | — |

---

## 🔗 交叉链接

- [[弹药弹道数据|弹药]] ↔ [[武器改装配件指南|改装]] — 选对子弹才能发挥枪的优势
- [[钥匙与任务物品清单|钥匙]] ↔ [[Boss数据与刷新位置|Boss]] — 有些钥匙是Boss掉落
- [[FleaMarket行情概览|市场]] ↔ [[跳蚤市场套利分析|套利]] — 看行情找赚钱机会
- [[藏身处升级指南|藏身处]] ↔ [[SPT模组推荐|SPT]] — 单机版可调整升级参数

---

## 🗺️ 相关资源

- [[tarkov-map.html|🗺️ 交互地图]] — 在浏览器中查看
- [[SPT知识宝典|📖 SPT Wiki全文]] — 离线版知识完整版
"""

save(f"{BASE}/INDEX.md", index)

print("\n" + "=" * 50)
print(f"✅ 全部完成！8 个知识域已写入 {BASE}")
print("=" * 50)
