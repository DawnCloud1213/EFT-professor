# Tarkov Gunsmith 弹道图生成工具

自动化批量生成 Tarkov Gunsmith 弹道计算器的弹道图（截图），
支持多种武器 × 多种弹药 × 自定义距离。

## 目录结构

```
tools/tarkov-gunsmith/
├── config.yaml      # 武器/枪管/弹药配置表
├── README.md        # 本说明文档
└── templates/       # (预留) 弹药组合模板

弹道测试报告/         # 输出目录（工作区根目录）
├── M700_M80/
├── M700_M62/
├── M700_M993/
├── G28_M80/
├── G28_M62/
├── G28_M993/
└── AXMC_AP/ ...
```

## 工作流说明

本工具定位为 **Hermes Agent 的半自动化工作流**：
用现有的 Playwright MCP 工具链，按 SKILL.md 中的步骤操作。
不需要安装独立的 Python 依赖。

## 支持的武器组合

| 口径 | 武器 | 枪管 | 弹药列表 |
|------|------|------|---------|
| 7.62x51mm | M700 | 20" stainless steel | M80, M62, M993 |
| 7.62x51mm | G28 | 417 16.5" | M80, M62, M993 |
| .338 LM | AXMC | AXMC .338LM 28" | AP, FMJ, TAC-X, UCW |

## 已知陷阱

详见 SKILL.md 的陷阱章节。

## 扩展指南

1. 打开 `https://tarkovgunsmith.com/ballistic_calculator`
2. 选择口径 → 武器 → 枪管
3. 打开弹药下拉查看有哪些弹药
4. 在 `config.yaml` 中新增条目
5. 按 SKILL.md 的步骤生成
