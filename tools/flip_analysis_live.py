#!/usr/bin/env python3
"""Live Flea Market Flip Analysis — SPT Local DB + Trader Assort Data"""

import json
import os
from collections import defaultdict

SPT = "D:/free games/EFT/SPT"
DB = f"{SPT}/SPT_Data/database"

# --- Load data ---
items_db = json.load(open(f"{DB}/templates/items.json", encoding="utf8"))
prices = json.load(open(f"{DB}/templates/prices.json", encoding="utf8"))

RUBLE_TPL = "5449016a4bdc2d6f028b456f"

# Trader configs
TRADERS = {
    "54cb50c76803fa8b248b4571": "Prapor",
    "54cb57776803fa99248b456e": "Therapist",
    "579dc571d53a0658a154fbec": "Fence",
    "58330581ace78e27b8b10cee": "Skier",
    "5935c25fb3acc3127c3d8cd9": "Peacekeeper",
    "5a7c2eca46aef81a7ca2145d": "Mechanic",
    "5ac3b934156ae10c4430e83c": "Ragman",
    "5c0647fdd443bc2504c2d371": "Jaeger",
}

def get_name(tid):
    """Get best available name for an item."""
    item = items_db.get(tid, {})
    sn = item.get("_shortName")
    if sn and sn != "None" and sn != "??":
        return sn
    name_field = item.get("_name", "")
    if name_field:
        # Clean up internal names
        cleaned = name_field.replace("_", " ").replace("weapon ", "").replace("spec ", "").replace("item ", "")
        parts = cleaned.split()
        return " ".join(p.capitalize() for p in parts[:3])
    return tid[:8]

def get_category(tid):
    """Get the category name for an item."""
    item = items_db.get(tid, {})
    parent = item.get("_parent", "")
    parent_item = items_db.get(parent, {})
    return parent_item.get("_name", parent[:20]).replace("_", " ").title()

print("=" * 80)
print("🏪  跳蚤倒卖 · 高性价比利润分析 (SPT 本地数据库实时)")
print("=" * 80)
print()

# ============================================================
# TYPE A: 商人现金购买 → 跳蚤倒卖
# (Direct Cash Purchase from Trader → Flea Flip)
# ============================================================
print("【A】商人直接现金购买 → 跳蚤倒卖")
print("-" * 70)

direct_flips = []

for tid, trader_name in TRADERS.items():
    try:
        assort = json.load(open(f"{DB}/traders/{tid}/assort.json", encoding="utf8"))
    except:
        continue

    for item in assort["items"]:
        sell_id = item["_id"]
        tpl = item["_tpl"]
        limit = item.get("upd", {}).get("BuyRestrictionMax", 0)
        if limit <= 0:
            continue

        scheme = assort["barter_scheme"].get(sell_id)
        if not scheme:
            continue

        trader_price = None
        # Look for pure RUB cost
        for req in scheme[0]:
            if req.get("_tpl") == RUBLE_TPL:
                trader_price = req["count"]
                break

        if not trader_price:
            continue

        flea_price = prices.get(tpl, 0)
        if flea_price <= 0:
            continue

        profit_per_item = flea_price - trader_price
        margin = profit_per_item / trader_price * 100 if trader_price > 0 else 0
        total_per_restock = profit_per_item * limit

        if profit_per_item > 0 and margin >= 15:
            direct_flips.append({
                "name": get_name(tpl),
                "trader": trader_name,
                "buy": trader_price,
                "sell": flea_price,
                "profit": profit_per_item,
                "margin": margin,
                "limit": limit,
                "total": total_per_restock,
            })

direct_flips.sort(key=lambda x: x["total"], reverse=True)

print(f"📊 发现 {len(direct_flips)} 个可盈利直接倒卖方案（按单次补货总利润排序）")
print()
print(f"{'#':>3} | {'物品':<30} | {'商人':<12} | {'进价':>10} | {'卖价':>10} | {'单件利润':>10} | {'利润率':>7} | {'限购':>4} | {'单次利润':>10}")
print("-" * 110)

for i, f in enumerate(direct_flips[:20], 1):
    print(f"{i:>3} | {f['name']:<30} | {f['trader']:<12} | {f['buy']:>10,}₽ | {f['sell']:>10,}₽ | {f['profit']:>+10,}₽ | {f['margin']:>6.1f}% | {f['limit']:>4} | {f['total']:>+10,}₽")

print()

# ============================================================
# TYPE B: 交换倒卖 (Barter Arbitrage)
# (Buy components on flea → trade to trader → sell on flea)
# ============================================================
print()
print("【B】物品交换倒卖 (Barter Arbitrage)")
print("-" * 70)

barter_flips = []

for tid, trader_name in TRADERS.items():
    try:
        assort = json.load(open(f"{DB}/traders/{tid}/assort.json", encoding="utf8"))
    except:
        continue

    for item in assort["items"]:
        sell_id = item["_id"]
        tpl = item["_tpl"]
        limit = item.get("upd", {}).get("BuyRestrictionMax", 0)
        if limit <= 0:
            continue

        scheme = assort["barter_scheme"].get(sell_id)
        if not scheme:
            continue

        # Skip pure cash purchases (no barter)
        is_cash_only = any(req.get("_tpl") == RUBLE_TPL for req in scheme[0])
        if is_cash_only and len(scheme[0]) == 1:
            continue

        flea_price_out = prices.get(tpl, 0)
        if flea_price_out <= 0:
            continue

        # Calculate cost of barter components
        component_cost = 0
        components = []
        for req in scheme[0]:
            comp_tpl = req["_tpl"]
            qty = req.get("count", 1)
            comp_price = prices.get(comp_tpl, 0)
            if comp_tpl == RUBLE_TPL:
                comp_price = qty  # RUB is exact
            elif comp_price == 0:
                component_cost = None
                break
            component_cost += comp_price * qty
            components.append({
                "name": get_name(comp_tpl),
                "count": qty,
                "price": comp_price,
            })

        if component_cost is None or component_cost <= 0:
            continue

        profit = flea_price_out - component_cost
        margin = profit / component_cost * 100 if component_cost > 0 else 0

        if profit > 0 and margin >= 20:
            barter_flips.append({
                "name": get_name(tpl),
                "trader": trader_name,
                "cost": component_cost,
                "sell": flea_price_out,
                "profit": profit,
                "margin": margin,
                "limit": limit,
                "total": profit * limit,
                "components": components,
            })

barter_flips.sort(key=lambda x: x["total"], reverse=True)

print(f"📊 发现 {len(barter_flips)} 个可盈利交换倒卖方案")
print()
print(f"{'#':>3} | {'物品':<30} | {'商人':<12} | {'材料成本':>10} | {'卖价':>10} | {'利润':>10} | {'利润率':>7} | {'限购':>4} | {'单次利润':>10}")
print("-" * 110)

for i, f in enumerate(barter_flips[:20], 1):
    print(f"{i:>3} | {f['name']:<30} | {f['trader']:<12} | {f['cost']:>10,}₽ | {f['sell']:>10,}₽ | {f['profit']:>+10,}₽ | {f['margin']:>6.1f}% | {f['limit']:>4} | {f['total']:>+10,}₽")

# ============================================================
# BEST PROFIT PER RESTOCK (限购利润排行)
# ============================================================
print()
print("=" * 80)
print("💰  单次补货总利润 TOP 15（最值得跑一趟的倒卖）")
print("=" * 80)
print(f"{'#':>3} | {'物品':<30} | {'类型':<10} | {'成本':>10} | {'利润':>10} | {'利润率':>7} | {'限购':>4} | {'单次总利润':>12}")
print("-" * 85)

# Combine direct flips and barter flips, sort by total profit
all_flips = []
for f in direct_flips:
    all_flips.append((f["total"], f["name"], "直接购买", f["buy"], f["profit"], f["margin"], f["limit"]))
for f in barter_flips:
    all_flips.append((f["total"], f["name"], "交换", f["cost"], f["profit"], f["margin"], f["limit"]))

all_flips.sort(key=lambda x: x[0], reverse=True)

for i, (total, name, ftype, cost, profit, margin, limit) in enumerate(all_flips[:15], 1):
    print(f"{i:>3} | {name:<30} | {ftype:<10} | {cost:>10,}₽ | {profit:>+10,}₽ | {margin:>6.1f}% | {limit:>4} | {total:>+12,}₽")

print()

# ============================================================
# HIGHEST MARGIN_CHAMPS (利润率之王)
# ============================================================
print("=" * 80)
print("🔥  利润率之王 TOP 15（最高 %，本小利大）")
print("=" * 80)
print(f"{'#':>3} | {'物品':<30} | {'类型':<10} | {'成本':>10} | {'利润':>10} | {'利润率':>7} | {'限购':>4} | {'单次总利润':>12}")
print("-" * 85)

by_margin = [(f["margin"], f["name"], "直接购买", f["buy"], f["profit"], f["total"], f["limit"])
             for f in direct_flips]
by_margin += [(f["margin"], f["name"], "交换", f["cost"], f["profit"], f["total"], f["limit"])
              for f in barter_flips]
by_margin.sort(key=lambda x: x[0], reverse=True)

for i, (margin, name, ftype, cost, profit, total, limit) in enumerate(by_margin[:15], 1):
    print(f"{i:>3} | {name:<30} | {ftype:<10} | {cost:>10,}₽ | {profit:>+10,}₽ | {margin:>6.1f}% | {limit:>4} | {total:>+12,}₽")

print()
print("=" * 80)
print("📋 倒卖核心策略总结：")
print("=" * 80)
print("""
🅰️  直接倒卖（Direct Flip）：商人处卢布买 → 跳蚤卖
    • 简单快速，不需要收集材料
    • 注意商人的 BuyRestrictionMax（限购数）
    • 每次补货~3小时刷新

🅱️  交换倒卖（Barter Flip）：跳蚤买零件 → 跟商人换 → 跳蚤卖成品
    • 利润通常更高，但需要提前收零件
    • 要确保零件有足够供应量
    • 适合夜盘（低价时收零件）

⚠️  关键提醒：
    1. 所有价格基于 SPT 本地数据库，不同版本价格波动大
    2. 单次总利润 = 单件利润 × 限购数（决定实际收益上限）
    3. 利润率高但限购 1 的，只能当零花钱
    4. 实际跳蚤卖价受市场供需影响，不一定能按底价卖出
""")
