# EFT Professor — AI Agent Guide

> 本文件帮助 AI 助手（Hermes / Claude Code / Cline 等）理解项目结构、约定与工作流。

## 项目概述

EFT Professor 是一个**单文件离线 EFT 综合工具站**，核心是 `tarkov-map.html` — 基于 Leaflet.js 的交互地图 SPA，支持 15 张地图的双模式（抽象图 + 卫星图）渲染，内嵌 255+ 个任务标记。

项目还包含 SPT（逃离塔科夫离线版）知识宝库、交换数据分析、弹道图生成工具等附属模块。

## 目录结构

```
A:\JUST_DO_IT\EFT-professor/
├── tarkov-map.html              # ▶ 核心单页应用 (~94KB, 1049行)
├── generate_positions.py        # 任务坐标生成脚本（数据 → HTML 内嵌）
├── spt-wiki-full.md             # SPT 知识宝典（461行，Agent RAG用）
├── AGENTS.md                    # ↫ 就是这个文件
│
├── knowledge/
│   ├── INDEX.md                 # 知识库索引
│   ├── barters/                 # EFT 杂物交换数据
│   └── tarkov-map/              # 地图数据层
│       ├── all_tasks_full.json  # 510个任务全量数据 (2MB)
│       ├── maps.json            # 地图元数据
│       ├── transform_config.json # 坐标变换参数
│       └── update_map_layers.py # 地图图层更新脚本
│
├── maps/                        # 地图图片
│   ├── 2d/                      # 抽象图 (15张)
│   ├── 3d/                      # 卫星/3D渲染 (15张)
│   └── satellite/               # 瓦片缓存 (可重建)
│
├── tools/
│   └── tarkov-gunsmith/         # 弹道图截图生成工具
│
└── scripts/                     # 辅助脚本
```

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | 纯 HTML/CSS/JS + [Leaflet.js](https://leafletjs.com/) |
| 地图坐标系 | `L.CRS.Simple` + `L.Transformation`（游戏坐标 → 像素坐标） |
| 数据源 | [tarkov.dev](https://tarkov.dev) REST API |
| 工具脚本 | Python 3.11 |
| 自动化 | Playwright (Hermes browser tools) |

## 坐标系统（重要！）

这是项目最复杂的部分，agent 修改坐标相关代码前务必阅读：

- **游戏坐标**: `[gz, gx]` — gz=南北(Z轴), gx=东西(X轴)
- **Rotation 角度** 从 tarkov.dev API `/regular/maps` 的 `coordinateToCardinalRotation` 字段读取
- **180° 旋转**: `nx → img_x`, `nz → img_y` 直接映射，无翻转
- **非 180°** : 顺时针 (CW) 旋转，不额外翻转
- **CRS 尺寸** 从 HTML 中 `MAP_LAYERS` 的 `crsWidth/crsHeight` 解析
- **transform 参数** 在 `knowledge/tarkov-map/transform_config.json` 中

### 验证流程
1. 从 tarkov.dev API 获取地图 rotation 值
2. 计算 CRS 坐标 → 像素坐标
3. 在浏览器中截图比对标记位置
4. 以用户地图知识和经验为最终标准

## AI Agent 工作约定

### 通用
- **语言**: 与用户中文交流，但项目内专业名词（物品/Skills/地图名）保留英文
- **修改前出计划**：改代码前必须先出详细计划（markdown），等用户批准
- **改完必验证**：前端改动须截图 + `browser_vision` 确认效果
- **数据溯源**：坐标/物品数据从 tarkov.dev API 或官方源取，不靠猜测

### 隐私安全
- 用户路径/IP/个人信息输出时做脱敏处理
- 本地路径示例输出格式：`user/mods/`（省略盘符和用户名）

### Agent 自身
- Hermes 不继承 AGENTS.md 为系统指令，但请在每次开始任务前读取此文件
- Claude Code 自动读取 `CLAUDE.md`（可软链接到此文件）
- Cline 自动读取 `.clinerules`（可软链接到此文件）

## 常用命令

```bash
# 生成任务坐标（读取 all_tasks_full.json → 写入 tarkov-map.html）
python generate_positions.py

# 更新地图图层配置（从 API 拉取最新地图元数据）
python knowledge/tarkov-map/update_map_layers.py

# 下载卫星瓦片
python scripts/download_tiles.py

# 本地预览 HTML
# 直接在浏览器打开 tarkov-map.html
```

## 数据流

```
tarkov.dev API
    ↓ curl / Python
knowledge/tarkov-map/  (JSON 缓存)
    ↓ generate_positions.py
tarkov-map.html        (坐标内嵌到 JS)
    ↓ 浏览器打开
用户看到带标记的交互地图
```

## 已知陷阱

1. **MSYS 代理陷阱**：MSYS bash 下 `python3` 会因代理环境崩溃 (exit 49)。用 `python`（venv 版本）替代，或 curl → 文件 → python 读取的方式规避。
2. **物品中文名**：「洁厕灵」= Ox Bleach（灰瓶），不是 Bleach（蓝瓶）。遇到中文名必须通过 API 确认映射。
3. **坐标编号陷阱**：SPT 存档 JSON 中 `hideout Areas` 的 type 编号不能直接映射设施名称，不同版本编号不同。
4. **tarkov.dev API** 无速率限制，端点 `json.tarkov.dev/xxx`。
