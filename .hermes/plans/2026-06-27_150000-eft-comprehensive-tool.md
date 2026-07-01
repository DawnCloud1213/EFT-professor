# EFT 综合工具站 Implementation Plan

> **For Hermes:** Use delegate_task to implement this plan task-by-task.

**Goal:** 基于 tarkov.dev API 构建一个单文件本地 EFT 综合工具站，包含地图/任务/物品/交换/藏身处/商人信息，可在浏览器直接打开离线使用。

**Architecture:** 从现有的 `tarkov-map.html`（Leaflet + CRS.Simple）扩展为多标签 SPA。API 数据预先缓存到 HTML 内嵌的 JS 对象中。

**Tech Stack:** 
- Leaflet.js (地图)
- 纯 HTML/CSS/JS (单文件)
- tarkov.dev REST API (数据源)
- 数据预缓存策略：首次从 API 下载 JSON → 内嵌到 HTML

---

## Current Context

已有：
- `A:\JUST_DO_IT\EFT-professor\tarkov-map.html` (100KB, 255 quests, 16 maps)
- `A:\JUST_DO_IT\EFT-professor\knowledge\tarkov-map\all_tasks_full.json` (2MB, 510 tasks)
- `A:\JUST_DO_IT\EFT-professor\generate_positions.py` (坐标生成脚本)
- `maps/2d/` (16 张地图图片)

API 端点：
- `json.tarkov.dev/regular/items` — 物品数据库
- `json.tarkov.dev/regular/tasks` — 任务数据 ✅ (已缓存)
- `json.tarkov.dev/regular/maps` — 地图数据 ✅ (部分缓存)
- `json.tarkov.dev/regular/barters` — 交换配方
- `json.tarkov.dev/regular/crafts` — 藏身处制造
- `json.tarkov.dev/regular/hideout` — 藏身处设施
- `json.tarkov.dev/regular/traders` — 商人信息

---

## Phase 1: 数据层 — 预缓存全部 API 数据到本地 JSON

### Task 1.1: 下载 items 数据

**Objective:** 从 API 获取全量物品数据并缓存

**Files:**
- Create: `A:\JUST_DO_IT\EFT-professor\knowledge\tarkov-api\items.json`

**操作:**
```bash
curl -sL --max-time 30 "https://json.tarkov.dev/regular/items" -o "knowledge/tarkov-api/items.json"
```

验证：检查 JSON 结构和大小（预期 >5MB）

### Task 1.2: 下载 barters 数据

**Objective:** 获取交换配方

**Files:**
- Create: `knowledge/tarkov-api/barters.json`

```bash
curl -sL --max-time 30 "https://json.tarkov.dev/regular/barters" -o "knowledge/tarkov-api/barters.json"
```

### Task 1.3: 下载 crafts + hideout 数据

**Objective:** 获取藏身处相关数据

**Files:**
- Create: `knowledge/tarkov-api/crafts.json`
- Create: `knowledge/tarkov-api/hideout.json`

```bash
curl -sL --max-time 30 "https://json.tarkov.dev/regular/crafts" -o "knowledge/tarkov-api/crafts.json"
curl -sL --max-time 30 "https://json.tarkov.dev/regular/hideout" -o "knowledge/tarkov-api/hideout.json"
```

### Task 1.4: 下载 traders 数据

**Objective:** 获取商人等级/解锁信息

**Files:**
- Create: `knowledge/tarkov-api/traders.json`

```bash
curl -sL --max-time 15 "https://json.tarkov.dev/regular/traders" -o "knowledge/tarkov-api/traders.json"
```

### Task 1.5: 创建数据索引

**Objective:** 为所有缓存数据建立索引说明

**Files:**
- Create: `knowledge/tarkov-api/INDEX.md`

内容：描述每个 JSON 文件的内容、大小、更新时间。

---

## Phase 2: 任务模块增强

### Task 2.1: 修复坐标映射

**Objective:** 根据 API 返回的真实 rotation 参数修正所有任务点坐标

**Files:**
- Modify: `generate_positions.py` (rotation 已修复 ✅)
- Run → 生成 `tarkov-map.html`

### Task 2.2: 任务列表增强 — 中英文名 + 筛选

**Objective:** 在右侧面板添加更多筛选维度（商人、状态、地图）

**Files:**
- Modify: `tarkov-map.html`

改动：
- 任务列表添加 trader 颜色标签
- 添加下拉筛选：按商人、按地图
- 任务完成状态标记（本地 localStorage 存储）

---

## Phase 3: 物品浏览器

### Task 3.1: 创建物品数据压缩版

**Objective:** 把 items.json 压缩为可嵌入 HTML 的轻量版

思路：从全量 items 中提取：
- id, name, shortName, description
- 类型 (categories)
- 图片 URL
- 重量、格子数
- 护甲等级/耐久（如适用）
- 跳蚤市场价格

**Files:**
- Create: `scripts/prepare_items_data.py`

输出轻量 JSON 对象（~1MB 压缩后）

### Task 3.2: 物品搜索页签

**Objective:** 在 tarkov-map.html 中添加「物品」tab

**UI:**
- 顶部导航标签：🗺️ 地图 | 📦 物品 | 🔄 交换 | 🏠 藏身处 | 👤 商人
- 物品页面：搜索框 + 分类筛选 + 网格展示
- 点击物品展开详情弹窗

**Files:**
- Modify: `tarkov-map.html`

### Task 3.3: 物品详情弹窗

**Objective:** 点击物品显示完整信息

内容：
- 物品名称（中/英）
- 分类
- 重量、格子数
- 护甲属性（如适用）
- 跳蚤市场参考价
- 哪些任务需要
- 哪些交换配方使用

---

## Phase 4: 交换 & 制造模块

### Task 4.1: 交换浏览器

**Objective:** 添加「交换」tab 展示所有 barters

UI：
- 按商人分组展示
- 搜索/筛选
- 显示：「给→得」的交换关系
- 标记性价比（API 提供价格数据的话）

**Files:**
- Modify: `tarkov-map.html`

### Task 4.2: 藏身处制造列表

**Objective:** 展示所有 hideout crafts

UI：
- 按设施分组（工作台、医疗站、营养单元等）
- 显示材料 → 产物的制造链
- 标记需要解锁的设施等级

---

## Phase 5: 藏身处升级助手

### Task 5.1: 藏身处需求计算器

**Objective:** 输入当前藏身处等级，显示后续升级所需材料

UI：
- 设施列表（带当前等级选择）
- 自动计算升级所需物品汇总
- 标记已满足/缺失的材料

---

## Phase 6: 整合与部署

### Task 6.1: 数据构建脚本

**Objective:** 创建一键构建脚本

```bash
# build_tool.sh 功能：
# 1. 从 API 拉取最新数据
# 2. 压缩嵌入 HTML
# 3. 生成最终的 tarkov-tool.html
```

### Task 6.2: 最终验证

**Objective:** 打开 HTML 验证所有功能可用

验证清单：
- [ ] 16 张地图切换正常
- [ ] 任务标记显示在正确位置
- [ ] 物品搜索可用
- [ ] 交换列表展示
- [ ] 藏身处数据加载
- [ ] 离线打开无报错

---

## 风险与权衡

| 风险 | 缓解 |
|------|------|
| items.json 过大（~20MB） | 提取轻量子集嵌入，全量放 local JSON |
| 图片不内嵌 | 用 CDN 链接（需要在线），或跳过 |
| 单 HTML 文件过大 | 保持模块化 JS，必要时拆为 HTML+JS 两个文件 |
| 数据过期 | 提供「更新数据」按钮触发 API 重新下载 |
| 离线可用性 | 所有数据已内嵌/缓存，地图图片本地 |

---

## 执行计划优先级

```
Phase 1 (数据缓存) → Phase 2 (任务增强) 
→ Phase 3 (物品) → Phase 4 (交换+制造) 
→ Phase 5 (藏身处) → Phase 6 (整合)
```

每个 Phase 按顺序执行，但 Phase 1 可以全部并行下载。

现在开始执行吗？喵~ 😺
