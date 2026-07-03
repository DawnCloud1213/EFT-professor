# 方案 B：多 Zone 坐标修复 Implementation Plan

> **目标**：修复 140 个多 zone 任务的数据遗漏，将 `position: [gz, gx]` 改为 `positions: [[gz1,gx1], [gz2,gx2], ...]`

## 数据背景

| 指标 | 当前 | 修复后 |
|------|------|--------|
| HTML QUEST_MARKERS 条目数 | 230 | 230（不变） |
| 标记数 | 230 | ~503（同位置除重后） |
| 多 zone 任务遗漏 | 140 个 | 0 |
| 数据模型 | `position: [gz, gx]` | `positions: [[gz,gx], ...]` |

---

## 影响范围

```
改动文件：
  1. generate_positions.py        — 数据生成层（~15 行改动）
  2. tarkov-map.html              — 前端渲染层（~30 行改动）

不改动：
  - knowledge/tarkov-map/         — 数据缓存不变
  - 侧边栏列表/搜索/计数          — 一条 quest 一个 entry，无影响
```

---

## Phase 1: generate_positions.py

### 改动位置

**1.1 多 zone 收集 + 除重（第 112-128 行区域）**

```python
# 旧代码（只取第一个 zone）：
match = [co for co in coords if co[0] == map_name]
if match:
    gx, gz = match[0][1], match[0][2]
    e["position"] = [round(gz), round(gx)]
    continue

# 新代码（收集所有 zone + 坐标除重）：
match = [co for co in coords if co[0] == map_name]
if match:
    # 收集去重后的坐标，四舍五入 [gz, gx]
    unique_positions = set()
    for _, x, z in match:
        unique_positions.add((round(z), round(x)))
    e["positions"] = sorted(list(unique_positions))  # 排序保证稳定输出
    continue
```

**1.2 输出格式（第 149-158 行区域）**

```python
# 旧代码：
f'"position": [{pos[0]}, {pos[1]}]'

# 新代码：
f'"positions": {json.dumps(e.get("positions", [[0, 0]]))}'
```

**1.3 Grid fallback（第 130-146 行区域）**

```python
# 旧：检查 "position" not in q
# 新：检查 "positions" not in q，并输出 positions 格式
if "positions" not in q:
    q["positions"] = [[row * 100, col * 100]]
```

---

## Phase 2: tarkov-map.html — 标记渲染

### 改动位置：`updateQuestMarkers` 函数（第 862-895 行）

**2.1 标记生成循环（约第 866-894 行）**

```javascript
// 旧代码：
qm.forEach(q => {
    const color = TRADER_COLORS[q.trader] || '#888';
    const initial = q.trader.charAt(0);
    const icon = L.divIcon({...});
    const marker = L.marker([q.position[0], q.position[1]], {icon: icon}).addTo(markersLayer);
    marker.questId = q.id;
    // ... popup + click handler
});

// 新代码：
qm.forEach(q => {
    const color = TRADER_COLORS[q.trader] || '#888';
    const initial = q.trader.charAt(0);
    const icon = L.divIcon({...});
    
    // 兼容新旧格式：positions 数组 / 回退到 position 单点
    const positions = q.positions || (q.position ? [q.position] : [[0, 0]]);
    
    positions.forEach(pos => {
        const marker = L.marker(pos, {icon: icon}).addTo(markersLayer);
        marker.questId = q.id;

        const displayName = getDisplayName(q);
        const objHtml = q.objectives.map(o => `<div class="popup-objective">${o}</div>`).join('');
        marker.bindPopup(`...`);  // 同现有 popup 内容

        marker.on('click', function() {
            highlightQuestInList(q.id);
        });
    });
});
```

**2.2 侧边栏点击处理（第 944-958 行）**

```javascript
// 旧代码 — 遍历所有匹配 marker，打开所有 popup（多 marker 时体验差）：
markersLayer.eachLayer(layer => {
    if (layer instanceof L.Marker && layer.questId === q.id) {
        layer.openPopup();
        highlightQuestInList(q.id);
        map.setView(layer.getLatLng(), Math.max(0, map.getZoom() + 4), {animate: true});
    }
});

// 新代码 — 收集所有匹配 marker，按数量决定行为：
const matching = [];
markersLayer.eachLayer(layer => {
    if (layer instanceof L.Marker && layer.questId === q.id) {
        matching.push(layer);
    }
});
if (matching.length === 1) {
    matching[0].openPopup();
    map.setView(matching[0].getLatLng(), Math.max(0, map.getZoom() + 4), {animate: true});
} else if (matching.length > 1) {
    matching[0].openPopup();
    // 多 marker 时缩放到包围盒
    const group = L.featureGroup(matching);
    map.fitBounds(group.getBounds().pad(0.15), {animate: true, maxZoom: Math.max(0, map.getZoom() + 2)});
}
highlightQuestInList(q.id);
```

---

## Phase 3: 验证

### 3.1 数据完整性验证脚本

```python
# 检查修复后的 HTML 中：
# - 单 zone 任务：positions 数组长度 = 1
# - 多 zone 任务：positions 数组长度 >= 2
# - 同位置除重：positions 中没有重复 [gz, gx]
# - Grid fallback 任务：positions 不为空
```

### 3.2 可视化验证

- 打开 `tarkov-map.html`
- 切到 Streets of Tarkov（18 个多 zone 任务最多）
- 截图确认所有 zone 都有标记
- 点击侧边栏多 zone 任务 → 观察是否缩放到包围框

---

## 风险 & 边界情况

| 边界 | 处理方式 |
|------|---------|
| 旧格式 `position` 仍在数据中 | `positions \|\| [position]` 兜底 |
| 全部 key 都缺失 | fallback `[[0, 0]]` |
| 同一位置多个 zone | `set((round(z), round(x)))` 去重 |
| 排序稳定性 | 除重后用 `sorted()` 排序 |
| 除重损失精度的风险 | 地图标记精度 ~1 米级别，`round()` 完全够用 |

---

## 执行顺序

```
1. 改 generate_positions.py  → 运行生成新 HTML
2. 改 tarkov-map.html 前端   → 浏览器验证
3. 数据完整性交叉检查
4. Git commit + push
```
