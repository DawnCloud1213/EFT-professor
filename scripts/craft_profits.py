#!/usr/bin/env python3
"""
🏠 藏身处正利润制造查询器
===========================
实时从 tarkov.dev API 拉取配方 + 价格数据，计算正利润制造方案。

用法：
  python craft_profits.py              # 按利润率排序（默认）
  python craft_profits.py --sort profit # 按利润金额排序
  python craft_profits.py --positive-only  # 只看正利润
  python craft_profits.py --min-profit 10000  # 只看利润 > 10000₽ 的
  python craft_profits.py --no-cache    # 强制从 API 拉取（不读本地缓存）
  python craft_profits.py --station Medstation  # 只看某个设施
"""

import json, sys, os, time
from urllib.request import Request, urlopen
from urllib.error import URLError

# ── 路径 ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_DIR = os.path.join(SCRIPT_DIR, '..', 'knowledge')
HIDEOUT_RAW = os.path.join(KNOWLEDGE_DIR, '藏身处升级', 'hideout_raw.json')
FLEA_RAW = os.path.join(KNOWLEDGE_DIR, '市场行情', 'flea_raw.json')

# ── GraphQL 查询 ──
CRAFT_QUERY = """
{
  hideoutStations {
    name
    levels {
      level
      crafts {
        craftTime
        requiredItems {
          quantity
          item {
            id
            name
            shortName
            avg24hPrice
            lastLowPrice
            sellFor { priceRUB vendor { name } }
          }
        }
        rewardItems {
          quantity
          item {
            id
            name
            shortName
            avg24hPrice
            lastLowPrice
            sellFor { priceRUB vendor { name } }
          }
        }
      }
    }
  }
}
"""

GRAPHQL_URL = 'https://api.tarkov.dev/graphql'

# ── 获取物品最佳价格 ──
def get_best_price(item_dict):
    """从 API 返回的 item 字段中获取最佳出售价"""
    price = 0
    # flea price
    if item_dict.get('avg24hPrice'):
        price = max(price, item_dict['avg24hPrice'])
    if item_dict.get('lastLowPrice'):
        price = max(price, item_dict['lastLowPrice'])
    # vendor sell prices
    for s in item_dict.get('sellFor', []):
        if s.get('priceRUB') and s['priceRUB'] > price:
            price = s['priceRUB']
    return price

# ── API 拉取 ──
def fetch_from_api():
    """从 tarkov.dev API 拉取配方+价格"""
    req = Request(GRAPHQL_URL, data=json.dumps({'query': CRAFT_QUERY}).encode(),
                  headers={'Content-Type': 'application/json'},
                  method='POST')
    try:
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        if 'errors' in data:
            raise Exception(f"API Error: {data['errors']}")
        return data['data']['hideoutStations'], True
    except URLError as e:
        raise Exception(f"API不可达: {e}")
    except Exception as e:
        raise e

# ── 本地缓存构建价格表 ──
def build_local_price_map(load_callback=None):
    """从本地 flea_raw.json 构建价格索引"""
    with open(FLEA_RAW, 'r', encoding='utf-8') as f:
        data = json.load(f)
    price_map = {}
    name_map = {}
    for item in data['items']:
        flea = item.get('lastLowPrice') or item.get('avg24hPrice') or 0
        vendor_prices = [s['priceRUB'] for s in item.get('sellFor', []) if s.get('priceRUB') and isinstance(s['priceRUB'], (int, float))]
        best = max([flea] + vendor_prices) if vendor_prices else flea
        if best and best > 0:
            price_map[item['id']] = best
        name_map[item['id']] = item.get('shortName', item['name'])
    return price_map, name_map

# ── 计算利润 ──
def calc_profits(stations, prices, names, source_is_api=False):
    results = []
    source_tag = "API" if source_is_api else "本地缓存"
    data_age = "实时" if source_is_api else "知识库静态数据"
    
    for station in stations:
        for level in station.get('levels', []):
            if not level.get('crafts'):
                continue
            for craft in level['crafts']:
                duration = craft.get('craftTime') or craft.get('duration', 0)
                hours = round(duration / 60, 1) if duration else 0
                
                # 输入
                input_cost = 0
                input_parts = []
                skip = False
                for ri in craft['requiredItems']:
                    qty = ri['quantity']
                    item = ri['item']
                    item_id = item.get('id')
                    
                    if source_is_api:
                        price = get_best_price(item)
                    else:
                        price = prices.get(item_id, 0)
                    
                    if price == 0:
                        skip = True
                        break
                    
                    name = item.get('shortName', item.get('name', '?'))
                    input_cost += price * qty
                    input_parts.append(f"{name}x{qty}")
                
                if skip:
                    continue
                
                # 输出
                output_value = 0
                output_parts = []
                for ri in craft['rewardItems']:
                    qty = ri['quantity']
                    item = ri['item']
                    item_id = item.get('id')
                    
                    if source_is_api:
                        price = get_best_price(item)
                    else:
                        price = prices.get(item_id, 0)
                    
                    if price == 0:
                        skip = True
                        break
                    
                    name = item.get('shortName', item.get('name', '?'))
                    output_value += price * qty
                    output_parts.append(f"{name}x{qty}")
                
                if skip:
                    continue
                
                profit = output_value - input_cost
                margin = round(profit / input_cost * 100, 1) if input_cost > 0 else 0
                
                results.append({
                    'station': station['name'],
                    'level': level['level'],
                    'duration': duration,
                    'hours': hours,
                    'input': ' + '.join(input_parts),
                    'cost': input_cost,
                    'output': ' + '.join(output_parts),
                    'value': output_value,
                    'profit': profit,
                    'margin': margin,
                    'source': source_tag,
                    'data_age': data_age,
                })
    
    return results

# ── 输出 ──
def print_table(results, positive_only=True, min_profit=0, station_filter=None):
    # 筛选
    filtered = results
    if positive_only:
        filtered = [r for r in filtered if r['profit'] > 0]
    if min_profit > 0:
        filtered = [r for r in filtered if r['profit'] >= min_profit]
    if station_filter:
        filtered = [r for r in filtered if r['station'].lower() == station_filter.lower()]
    
    filtered.sort(key=lambda x: x['margin'], reverse=True)
    
    # 打印头部信息
    if filtered:
        print(f"📊 数据来源：{filtered[0]['source']} | {filtered[0]['data_age']}")
    print()
    
    # 表格头
    print(f"{'#':<3} {'设施':<18} {'配方':<42} {'成本(₽)':>9} {'产出(₽)':>9} {'利润(₽)':>9} {'利润率':>6} {'时长(h)':>7}")
    print("─" * 105)
    
    for i, r in enumerate(filtered, 1):
        inp_short = r['input'][:40]
        cost_str = f"{r['cost']:,}"
        val_str = f"{r['value']:,}"
        profit_str = f"+{r['profit']:,}" if r['profit'] > 0 else f"{r['profit']:,}"
        print(f"{i:<3} {r['station']:<18} {inp_short:<40} {cost_str:>9} {val_str:>9} {profit_str:>9} {r['margin']:>5}% {str(r['hours']):>5}h")
    
    print(f"─" * 105)
    print(f"共 {len(filtered)} 个配方 (总 {len(results)} 配方)")
    
    if positive_only:
        profit_count = len([r for r in results if r['profit'] > 0])
        loss_count = len([r for r in results if r['profit'] <= 0])
        print(f"正利润: {profit_count} | 负利润/零利润: {loss_count}")

# ── 主入口 ──
def main():
    args = sys.argv[1:]
    sort_by = 'margin'  # default
    positive_only = True
    min_profit = 0
    station_filter = None
    force_api = False
    
    for a in args:
        if a == '--sort-profit' or a == '--sort':
            sort_by = 'profit'
        elif a == '--all':
            positive_only = False
        elif a == '--no-cache' or a == '--force-api':
            force_api = True
        elif a.startswith('--min-profit='):
            min_profit = int(a.split('=')[1])
        elif a.startswith('--station='):
            station_filter = a.split('=')[1]
        elif a == '--help' or a == '-h':
            print(__doc__)
            return
    
    # 先尝试 API
    api_success = False
    stations = None
    
    try:
        stations, api_success = fetch_from_api()
    except Exception as e:
        print(f"⚠️ API 不可用: {e}")
        print("使用本地缓存数据...")
    
    if not api_success or not stations:
        # 使用本地 hideout_raw.json + flea_raw.json
        if not os.path.exists(HIDEOUT_RAW) or not os.path.exists(FLEA_RAW):
            print("❌ 找不到本地缓存文件，且 API 不可用")
            print(f"   需要: {HIDEOUT_RAW}")
            print(f"   需要: {FLEA_RAW}")
            sys.exit(1)
        
        with open(HIDEOUT_RAW, 'r', encoding='utf-8') as f:
            data = json.load(f)
        stations = data['hideoutStations']
        prices, names = build_local_price_map()
        results = calc_profits(stations, prices, names, source_is_api=False)
    else:
        # API 成功，直接传 None 占位
        results = calc_profits(stations, None, None, source_is_api=True)
    
    print_table(results, positive_only=positive_only, min_profit=min_profit, station_filter=station_filter)

if __name__ == '__main__':
    main()
