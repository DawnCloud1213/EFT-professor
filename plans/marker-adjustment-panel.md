# 地图任务标记手动调节方案

## 背景

tarkov.dev 的 transform 参数无法直接精确匹配所有地图的任务标记位置。需要提供一个交互式调节面板，让用户手动微调标记的位置、缩放和旋转，并将调整结果持久化。

---

## 1. 界面设计

在侧边栏底部添加「标记微调」面板：

```
┌─────────────────────┐
│ 🔧 标记微调          │
│                     │
│ X 偏移: [===|====-] │  ← 滑块, 范围 -500 ~ +500
│ Y 偏移: [====|-===] │  ← 滑块, 范围 -500 ~ +500
│ 缩放:   [-==|====]  │  ← 滑块, 范围 0.5 ~ 2.0
│ 旋转°:  [===|====]  │  ← 滑块, 范围 -45 ~ +45
│ X镜像: [  ]  Y镜像: [  ] │  ← 开关
│                     │
│ 实时显示: X: +12, Y: -8, S: 1.05, R: 2°, MX:×, MY:×
│                     │
│ [🔄 重置]  [💾 保存] │
└─────────────────────┘
```

### 控件详细规格

| 参数 | 最小值 | 最大值 | 步长 | 默认值 | 说明 |
|------|--------|--------|------|--------|------|
| X 偏移 | -500 | 500 | 1 | 0 | 水平平移 |
| Y 偏移 | -500 | 500 | 1 | 0 | 垂直平移 |
| 缩放 | 0.5 | 2.0 | 0.01 | 1.0 | 标记整体缩放 |
| 旋转 | -45° | 45° | 0.5° | 0 | 标记绕中心旋转 |
| X镜像 | 0/1 | — | 开关 | 0 | 水平方向翻转 |
| Y镜像 | 0/1 | — | 开关 | 0 | 垂直方向翻转 |

---

## 2. 数据存储

### 数据结构

```javascript
const MARKER_ADJUSTMENTS = {
    "woods":              { tx: 0, ty: 0, scale: 1.0, rot: 0, mx: false, my: false },
    "customs":            { tx: 0, ty: 0, scale: 1.0, rot: 0, mx: false, my: false },
    "factory":            { tx: 0, ty: 0, scale: 1.0, rot: 0, mx: false, my: false },
    "shoreline":          { tx: 0, ty: 0, scale: 1.0, rot: 0, mx: false, my: false },
    "reserve":            { tx: 0, ty: 0, scale: 1.0, rot: 0, mx: false, my: false },
    "interchange":        { tx: 0, ty: 0, scale: 1.0, rot: 0, mx: false, my: false },
    "the-lab":            { tx: 0, ty: 0, scale: 1.0, rot: 0, mx: false, my: false },
    "ground-zero":        { tx: 0, ty: 0, scale: 1.0, rot: 0, mx: false, my: false },
    "the-labyrinth":      { tx: 0, ty: 0, scale: 1.0, rot: 0, mx: false, my: false },
    "lighthouse":         { tx: 0, ty: 0, scale: 1.0, rot: 0, mx: false, my: false },
    "streets-of-tarkov":  { tx: 0, ty: 0, scale: 1.0, rot: 0, mx: false, my: false },
    "terminal":           { tx: 0, ty: 0, scale: 1.0, rot: 0, mx: false, my: false },
    "icebreaker":         { tx: 0, ty: 0, scale: 1.0, rot: 0, mx: false, my: false },
    // 变体地图复用主地图的数据
    "night-factory":      null,        // → 复用 factory
    "ground-zero-21":     null,        // → 复用 ground-zero
    "ground-zero-tutorial": null,      // → 复用 ground-zero
};
```

### 持久化

- **存储介质**: `localStorage`
- **Key**: `tarkov_marker_adjustments`
- **保存时机**: 点击「确认保存」按钮
- **加载时机**: 页面加载时从 localStorage 恢复
- **继承规则**: 变体地图（night-factory 等）如果自己的数据为 null，查找主地图配置

```javascript
// 保存
function saveAdjustments() {
    localStorage.setItem('tarkov_marker_adjustments', JSON.stringify(MARKER_ADJUSTMENTS));
}

// 加载
function loadAdjustments() {
    const saved = localStorage.getItem('tarkov_marker_adjustments');
    if (saved) {
        const data = JSON.parse(saved);
        Object.keys(data).forEach(key => {
            if (MARKER_ADJUSTMENTS[key] !== undefined) {
                MARKER_ADJUSTMENTS[key] = data[key];
            }
        });
    }
}
```

### 分辨率无关性

调整参数在 CRS 坐标系（游戏坐标空间）中存储，不受显示分辨率影响：

- 偏移的单位是 CRS 坐标单位（对应游戏坐标 x/z 的单位）
- 缩放的依据是 CRS 坐标的比例
- 不同屏幕分辨率和缩放级别下效果一致

---

## 3. 标记坐标应用

### 当前坐标计算（在 updateQuestMarkers 中）

```javascript
// 旋转后的游戏坐标 → CRS 坐标
const gx = q.position[1];
const gz = q.position[0];
// 180°: rx=gx, rz=gz
// 其他: CW 旋转
let rx, rz;
if (Math.abs(rot - 180) < 0.01) {
    rx = gx; rz = gz;
} else {
    rx = gx * cosR + gz * sinR;
    rz = -gx * sinR + gz * cosR;
}
```

### 添加手动调整

```javascript
// 获取该地图的调整参数
const adj = MARKER_ADJUSTMENTS[normalizedName] || { tx:0, ty:0, scale:1, rot:0, mx:false, my:false };

// 如果有变体继承
if (!adj && normalizedName === 'night-factory') {
    adj = MARKER_ADJUSTMENTS['factory'];
}

// 应用镜像
let mr = rx, mz = rz;
if (adj.mx) mr = -rx;    // X轴镜像
if (adj.my) mz = -rz;    // Y轴镜像

// 应用缩放 & 旋转
const rad_adj = adj.rot * Math.PI / 180;
const cos_a = Math.cos(rad_adj);
const sin_a = Math.sin(rad_adj);
const scaled_rx = mr * adj.scale;
const scaled_rz = mz * adj.scale;
const adj_x = scaled_rx * cos_a - scaled_rz * sin_a + adj.tx;
const adj_y = scaled_rx * sin_a + scaled_rz * cos_a + adj.ty;

// 放置标记
const marker = L.marker([adj_y, adj_x], {icon: icon}).addTo(markersLayer);
```

---

## 4. 调节面板实现

### HTML 结构

```html
<div id="adjust-panel" style="display:block;margin-top:10px;padding:8px;background:#2d2d2f;border:1px solid #3a3a3d;border-radius:6px;">
    <div style="color:#c7c5b3;font-size:12px;margin-bottom:6px;">🔧 标记微调</div>
    <div class="adj-row">
        <span style="color:#888;font-size:11px;width:50px;display:inline-block;">X偏移</span>
        <input type="range" id="adj-tx" min="-500" max="500" value="0" style="width:100px;">
        <span id="adj-tx-val" style="color:#c7c5b3;font-size:11px;width:40px;text-align:right;">0</span>
    </div>
    <div style="display:flex;gap:12px;padding:0 8px;margin-bottom:8px">
        <label style="font-size:11px;color:#888;display:flex;align-items:center;gap:4px;cursor:pointer;">
            <input type="checkbox" id="adj-mx"> X镜像
        </label>
        <label style="font-size:11px;color:#888;display:flex;align-items:center;gap:4px;cursor:pointer;">
            <input type="checkbox" id="adj-my"> Y镜像
        </label>
    </div>
    <div style="display:flex;gap:6px;padding:0 8px">
        <button id="adj-reset" style="flex:1;padding:3px 6px;background:#333;border:1px solid #555;color:#ccc;border-radius:3px;cursor:pointer;">🔄 重置</button>
        <button id="adj-save" style="flex:1;padding:3px 6px;background:#d4c896;border:1px solid #d4c896;color:#1a1a1c;border-radius:3px;cursor:pointer;">💾 保存</button>
    </div>
</div>
</div>
```

### 交互逻辑

```javascript
// 滑块事件绑定
['tx','ty','scale','rot'].forEach(param => {
    const slider = document.getElementById(`adj-${param}`);
    slider.addEventListener('input', function() {
        // 更新显示值
        document.getElementById(`adj-${param}-val`).textContent = this.value;
        // 实时更新地图标记（调用 switchMap 刷新）
        if (currentMap) {
            const prev = currentMap;
            currentMap = null;
            switchMap(prev);
        }
    });
});

// 重置
document.getElementById('adj-reset').addEventListener('click', function() {
    if (!currentMap) return;
    MARKER_ADJUSTMENTS[currentMap] = { tx:0, ty:0, scale:1, rot:0 };
    updateSliderValues(currentMap);
    refreshMap(currentMap);
});

// 保存
document.getElementById('adj-save').addEventListener('click', function() {
    saveAdjustments();
    showToast('✅ 已保存');
});
```

### 切换地图时更新滑块

```javascript
function updateSliderValues(mapName) {
    const adj = getAdjustmentForMap(mapName);
    document.getElementById('adj-tx').value = adj.tx;
    document.getElementById('adj-tx-val').textContent = adj.tx;
    // ...类似处理其余参数
}
```

---

## 5. 涉及的文件

| 文件 | 改动 |
|------|------|
| `tarkov-map.html` | 调节面板 HTML（sidebar 底部） |
| `tarkov-map.html` | `MARKER_ADJUSTMENTS` 数据结构 + `loadAdjustments` |
| `tarkov-map.html` | `updateQuestMarkers` 应用调整参数 |
| `tarkov-map.html` | 滑块事件绑定 + 保存/重置逻辑 |

*注：纯前端修改，不需要改 Python 脚本。*

---

## 6. 测试项

| 测试 | 步骤 | 预期 |
|------|------|------|
| X 偏移 | 调 X+100 → 保存 → 刷新 | 标记右移，刷新后保留 |
| Y 偏移 | 调 Y-50 → 保存 → 刷新 | 标记上移 |
| 缩放 | 调 S=1.5 → 保存 | 标记扩散 |
| 旋转 | 调 R=10° → 保存 | 标记阵列旋转 |
| 地图独立 | Woods 调 X+50 → 切 Customs → 切回 Woods | Woods 偏移仍在，Customs 不变 |
| 变体继承 | 调 ground-zero → 切 ground-zero-21 | ground-zero-21 复用同样的参数 |
| 重置 | 点击重置 → 保存 | 所有参数归零 |
