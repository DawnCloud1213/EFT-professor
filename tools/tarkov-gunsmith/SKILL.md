---
name: tarkov-gunsmith
description: Tarkov Gunsmith 弹道图自动化生成工具。通过 Playwright 操作 tarkovgunsmith.com/ballistic_calculator，批量生成武器×多种弹药×350m 的弹道下坠表截图。支持半自动（SKILL步骤）和全自动（delegate_task）两种模式。
category: gaming
triggers:
  - 用户要求弹道计算/弹道对比/弹道下坠图
  - 用户说"给XX枪生成弹道图"
  - 用户要求"做AXMC测试"或"做弹道测试"
related_skills:
  - eft-professor
---

# Tarkov Gunsmith — 弹道图自动化生成工具

## 定位

本 skill 是 `eft-professor` 的补充技能，专注 **tarkovgunsmith.com** 弹道计算器的自动化操作。
有两套用法：

- **半自动模式**：load skill 后按步骤手动操作 Playwright MCP 工具
- **全自动模式**：用 `delegate_task` 派生子 agent 批量完成

## 核心流程

### 1. 准备工作

浏览器导航到弹道计算器页面：
```
https://tarkovgunsmith.com/ballistic_calculator
```

### 2. 一次截图的标准步骤

```
1. 选口径 → 武器 → 枪管 → 弹药
2. 左栏 Misc → 填 Max Distance = 350
3. 点 Generate Drop Table
4. ✅ 验证结果 header："{weapon} (defAmmo: ...) with {弹药名} @ ..." 确认弹药正确
5. 右栏 Charts → 填 Distance Max = 350（⚠️ 独立控制！与左栏不同步！）
6. 确认 FAQ 已折叠（AX tree 无 dialog 元素）
7. fullPage 截图 → 保存
```

### 3. 弹药切换流程

```python
# ✅ 正确步骤：
await page.getByRole('searchbox', { name: 'Calculation Ammo' }).click()
# 重新snapshot获取option列表
await page.getByRole('option', { name: 'M62 Speed: 820 m/s, Pen: 42, Dam:' }).click()
# 点 Generate → 先看 header 确认 "with M62" → 再截图
```

### 4. 切换武器流程

换武器后 **必须重新选枪管和弹药**！页面不会自动重置。

### 5. 保存位置

全部保存到工作区目录：
```
A:/JUST_DO_IT/EFT-professor/弹道测试报告/{武器}_{弹药}/*_350m.png
```

## 🚨 已知陷阱（必须遵守）

### 陷阱1：弹药dropdown「假成功」

**JS evaluate 点击 option 可能返回 'clicked' 但实际未切换！**
必须每轮 Generate 后看 header 确认弹药名。

### 陷阱2：两个距离参数独立

| 参数 | 位置 | 作用 |
|------|:----:|:----|
| Max Distance (m) | 左栏 Misc 区 | 控制数据表范围 |
| Distance Max | 右栏 Charts 区 | **独立控制图表 X 轴** |

**两个都要填 350！**

### 陷阱3：FAQ 遮挡

FAQ 展开后是模态对话框，**必须关闭后才截图**。

### 陷阱4：导航栏点击拦截

navbar 会拦截 option 点击（"subtree intercepts pointer events"）。
兜底：用 JS evaluate 点击：
```javascript
document.querySelectorAll('[role="option"]')[N].click()
```

### 陷阱5：Mantine combobox

搜索框是 readonly，不能用 fill/type。
只能用点击 option 的方式选。

**推荐的弹药选择方式（2026-06-25 实战验证）**：
```javascript
// ✅ 最佳方案：用 run_code_unsafe + force:true 绕过导航栏/视口遮挡
async (page) => {
  const sv = page.getByRole('searchbox', { name: 'Calculation Ammo' });
  await sv.click();
  await page.waitForTimeout(300);
  await page.getByRole('option', { name: 'M62 Speed: 820' }).click({ force: true });
  await page.waitForTimeout(300);
  // 验证
  const val = await sv.inputValue();
  // 如果没选上，重试（最多3次）
}
```

**关键经验**：
- `getByRole('option', { name }).click({ force: true })` 比 `{ force: false }`（默认）更可靠，绕过  viewport/导航栏遮挡检查
- 但 **选完后要立即读取 searchbox 的值验证**，因为 React Mantine 内部状态更新不一定同步
- 发现值不对 → 重试（循环最多3次） → 确认后才 Generate
- Generate 后还要看结果 header 二次验证

### 陷阱6：MSYS + 代理 + Python

设 http_proxy 后 python3 pipe 崩（exit 49）。
用 `curl -x` 写文件 → Python 读文件，或在 execute_code 内操作。

## 配置表

具体武器/口径/枪管/弹药组合见：
```
A:/JUST_DO_IT/EFT-professor/tools/tarkov-gunsmith/config.yaml
```

## 全自动模式（delegate_task）

在 SKILL.md 或 context 中附上 config.yaml 相关配置，然后：
```
给 AXMC 生成 AP/FMJ/TAC-X/UCW 的 350m 弹道图
→ spawn 子 agent 用 Playwright 操作
→ 子 agent 返回文件路径
```

## 测试记录

见：
```
A:/JUST_DO_IT/EFT-professor/弹道测试报告/README.md
```
