# 混合方案实施计划: 卫星瓦片拼合底图 + SVG viewBox 坐标校准

**Goal:** 把 `tarkov-map.html` 改造成双模式：卫星图（下载瓦片拼合）为主、抽象 SVG 图为备选，利用 SVG viewBox 作为 CRS 坐标参考系，实现游戏坐标 → 底图像素的精确映射。

---

## 一、背景调研结论

### 1.1 tarkov.dev 地图架构（已实机验证）

```
卫星模式 (卫星图)
  └─ PNG 瓦片层: assets.tarkov.dev/maps/{map}/{layer}/{z}/{x}/{y}.png
  └─ SVG 覆盖层: 交互区域（红框、撤离点、出生点区）
  └─ Marker 层: 任务目标图标、撤离点图标、POI

抽象模式 (抽象图)
  └─ SVG 底图层: assets.tarkov.dev/maps/svg/{Map}.svg (手绘矢量地图)
  └─ SVG 覆盖层: 同上
  └─ Marker 层: 同上
```

### 1.2 每张地图的卫星瓦片参数（已从网站实时提取）

| 地图 | URL 模式 | Zoom | X 范围 | Y 范围 | 瓦片数 | 拼合尺寸 |
|:----:|:--------:|:----:|:------:|:------:|:-----:|:--------:|
| Factory | `factory/main/{z}/{x}/{y}.png` | 1 | 0~1 | 0~1 | 4 (2×2) | 512×512 |
| Customs | `customs_0.16/main/{z}/{x}/{y}.png` | 2 | 1~3 | 0~3 | 12 (3×4) | 768×1024 |
| Woods | `woods/main_0.16/{z}/{x}/{y}.png` | 2 | -1~3 | 0~3 | 20 (5×4) | 1280×1024 |
| Shoreline | `shoreline/main_summer/{z}/{x}/{y}.png` | 2 | 0~3 | 0~3 | 16 (4×4) | 1024×1024 |
| Reserve | `reserve/main/{z}/{x}/{y}.png` | 2 | 0~3 | 0~3 | 16 (4×4) | 1024×1024 |
| Interchange | `interchange/main/{z}/{x}/{y}.png` | 1 | -1~2 | 0~1 | 8 (4×2) | 1024×512 |
| Lighthouse | ?（待扫描） | ? | ? | ? | ? | ? |
| Streets of Tarkov | ?（待扫描） | ? | ? | ? | ? | ? |
| The Lab | ?（待扫描） | ? | ? | ? | ? | ? |
| Ground Zero | ?（待扫描） | ? | ? | ? | ? | ? |
| Labyrinth | ?（待扫描） | ? | ? | ? | ? | ? |
| Terminal | ?（待扫描） | ? | ? | ? | ? | ? |
| Icebreaker | ?（待扫描） | ? | ? | ? | ? | ? |

### 1.3 坐标映射关键

SVG viewBox = CRS 坐标空间。游戏 {x,z}→(rotation)→CRS 坐标→viewBox 内位置。
卫星瓦片也共享同一 CRS 空间（Leaflet 在卫星模式下叠加 SVG overlay 来验证）。

当前映射精度受限于：我们使用游戏坐标线性映射到 JPG 像素，但缺少 CRS→像素的精确投影参数。
使用卫星瓦片 + SVG viewBox 作为 CRS 参考 => 理论上可达接近 tarkov.dev 的像素精度。

---

## 二、Phase 1: 扫描全部地图的卫星瓦片参数

### Task 1.1: 批量提取瓦片参数

用 Playwright MCP 遍历全部 16 张地图，每张：
1. 导航到 `https://tarkov.dev/map/{name}`
2. 切换到卫星模式
3. 等待 tiles 加载
4. 提取所有瓦片 URL → 解析 z, x, y 范围

**输出文件:** `knowledge/tarkov-api/tile_params.json`

```json
{
  "factory": {
    "pattern": "https://assets.tarkov.dev/maps/factory/main/{z}/{x}/{y}.png",
    "zoom": 1, "xMin": 0, "xMax": 1, "yMin": 0, "yMax": 1,
    "svgViewBox": "0 0 130.82 141.23"
  },
  ...
}
```

### Task 1.2: 对无 tiles 的地图做 fallback

某些地图（如 Icebreaker、Terminal）可能没有卫星模式或 tiles 为空。记录为 `"noSatellite": true`，回退到 JPG。

**验证方式:** 检查 `tileCount > 0`

---

## 三、Phase 2: 下载 & 拼合卫星瓦片

### Task 2.1: 编写瓦片下载脚本

**文件:** `scripts/download_tiles.py`

功能：
- 读取 `tile_params.json`
- 对每张地图，按 (x,y) 范围并行下载所有瓦片
- 跳过已下载的（断点续传）
- 用 Pillow 拼合成一张大图
- 保存到 `maps/satellite/{name}.png`

```python
def download_and_stitch(name, params):
    pattern = params['pattern']
    z = params['zoom']
    tiles = []
    for x in range(params['xMin'], params['xMax']+1):
        row = []
        for y in range(params['yMin'], params['yMax']+1):
            url = pattern.replace('{z}', str(z)).replace('{x}', str(x)).replace('{y}', str(y))
            img = download(url)  # 256×256 PNG
            row.append(img)
        tiles.append(row)
    # Stitch: tileSize=256
    stitched = Image.new('RGB', (len(tiles[0])*256, len(tiles)*256))
    for yi, row in enumerate(tiles):
        for xi, tile in enumerate(row):
            stitched.paste(tile, (xi*256, yi*256))
    stitched.save(f'maps/satellite/{name}.png')
```

**注意:** 部分地图的 x 范围可能包含负数（如 Woods x:-1~3），需偏移到 0 基点。

### Task 2.2: 验证拼合质量

对每张拼合图：
- 打开查看是否完整
- 检查相邻瓦片是否对齐
- 确认长宽比合理

---

## 四、Phase 3: 坐标校准 — 提取 SVG viewBox

### Task 3.1: 已下载的 SVG 提取 viewBox

从 `maps/svg/*.svg` 提取 viewBox 属性
从 `generate_positions.py` 已有的 ROTATION 数据

输出:

```javascript
const MAP_CRS = {
    factory:   { vbW: 130.82,   vbH: 141.23,   rot: 90   },
    customs:   { vbW: 1062.48,  vbH: 535.17,   rot: 180  },
    woods:     { vbW: 1472.79,  vbH: 1420.60,  rot: 180  },
    // ...
};
```

### Task 3.2: 缺失 SVG 的地图

对于 Laboratory、Labyrinth、Ground_Zero、Streets_of_Tarkov：
- 从卫星瓦片模式的反向推算 viewBox
- 或者留空用游戏坐标范围直接映射

---

## 五、Phase 4: 修改 HTML 使用卫星底图

### Task 4.1: 更新 MAP_IMAGES

```javascript
const MAP_IMAGES = {
    factory: { 
        file: "maps/satellite/factory.png",
        crsW: 130.82, crsH: 141.23,  // viewBox = CRS bounds
        imgW: 512,    imgH: 512,     // 拼合图像素
        rot: 90
    },
    // ...
};
```

### Task 4.2: 底图切换按钮

添加一个 "切换底图" 按钮：
- 卫星图（默认，优先）
- 抽象图（SVG fallback）
- 2D 手绘图（最终 fallback）

### Task 4.3: 更新 switchMap()

```javascript
function switchMap(normalizedName) {
    const img = MAP_IMAGES[normalizedName];
    const bounds = [[0, 0], [img.crsH, img.crsW]];  // CRS.Simple [y, x]
    // 用拼合图作为 imageOverlay
    map.fitBounds(bounds);
    L.imageOverlay(img.file, bounds).addTo(map);
}
```

---

## 六、Phase 5: 坐标映射修正

### Task 5.1: 更新 generate_positions.py

**核心改动:** 现在底图是 CRS 坐标系中的卫星图（CRS 单位 = 像素在 viewBox 级别）。

```python
# 坐标转换逻辑:
# Step 1: 游戏 {x,z} → (rotation) → CRS 归一化 0-1
# Step 2: CRS 归一化 → viewBox 内坐标
# Step 3: 直接作为 Leaflet CRS.Simple position [y, x]
#
# position = [CRS_y, CRS_x]
# 其中 CRS_y 和 CRS_x 是全局 viewBox 坐标（不是像素）
```

对于无 viewBox 的地图:
```python
# 回退: 用游戏坐标范围直接映射到拼合图像素
# jpgY = (1 - nz_m) * imgH
# jpgX = ny * imgW
```

### Task 5.2: 重新生成全部位置

```bash
python3 scripts/generate_positions.py
```

---

## 七、Phase 6: 验证

### Task 6.1: 视觉验证

对每个地图：
1. 打开 HTML
2. 切换到该地图
3. 检查卫星图完整显示 ✅
4. 搜索几个任务 → 标记位置合理 ✅
5. 切换回抽象图 → 正常 ✅

### Task 6.2: 坐标精度对比

选 3 个已知任务，用 Playwright 从 tarkov.dev 提取像素位置：
- 我们的标记位置
- tarkov.dev 的标记位置
- 计算偏移量（应 <5%）

### Task 6.3: Edge cases

- 无卫星图的地图（JPG fallback）
- 16 张地图全部可切换
- 搜索+过滤正常

---

## 八、文件改动清单

| 文件 | 改动 |
|------|------|
| `tarkov-map.html` | MAP_IMAGES → 卫星图 + CRS bounds、底图切换按钮、switchMap 更新 |
| `scripts/download_tiles.py` | **新建** — 下载并拼合瓦片 |
| `generate_positions.py` | 坐标映射 → viewBox CRS 坐标 |
| `knowledge/tarkov-api/tile_params.json` | **新建** — 每张图的瓦片参数 |
| `maps/satellite/*.png` | **新建** — 拼合后的卫星底图 |
| `maps/svg/*.svg` | 已存在（作为抽象模式回退） |

## 九、风险 & 应对

| 风险 | 应对 |
|------|------|
| 某些地图卫星瓦片不存在（404） | JPG fallback |
| 瓦片拼合后边缘不对齐 | 检查 256×256 标准尺寸，换更小的 zoom 重试 |
| SVG viewBox 与卫星图 CRS 不对齐 | 用两组撤离点坐标做最小二乘拟合校准 |
| 瓦片下载量大（~200 tiles × 100KB = 20MB） | 不费流量，下载一次永久使用 |
| file:// 下跨域问题 | SVG viewBox 是内嵌数据，不涉及跨域 |

## 十、执行顺序

```
Phase 1 (扫描瓦片参数) 
  ↓
Phase 2 (下载 + 拼合)
  ↓
Phase 3 (提取 viewBox)
  ↓
Phase 4 (修改 HTML) ← Phase 5 (坐标修正)
  ↓ 可并行            ↓
Phase 6 (验证)
```

---

**预计总工作量:** 2-3 小时（批量瓦片下载最耗时）

**准备好了！大佬确认后我就开干喵~ (ฅ´ω`ฅ) 感谢猫条！** 🐟
