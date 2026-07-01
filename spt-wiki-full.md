# SPT (Single Player Tarkov / 逃离塔科夫离线版) 知识宝典

> 📅 数据来源：SPT 官方 Wiki ([sp-tarkov/wiki](https://github.com/sp-tarkov/wiki)) — 2026年6月
> 📌 当前 SPT 版本：`4.0.x`（基于 EFT `0.16.9.0.40087`，2025年10月2日）

---

## 目录

1. [什么是 SPT](#1-what-is-spt)
2. [系统要求](#2-系统要求)
3. [安装指南](#3-安装指南)
4. [SPT 工作原理](#4-spt-工作原理)
5. [存档与配置文件 (Profiles)](#5-存档与配置文件-profiles)
6. [模组 (Mods)](#6-模组-mods)
7. [Bot 难度系统](#7-bot-难度系统)
8. [性能优化](#8-性能优化)
9. [更新 SPT](#9-更新-spt)
10. [常见问题 (FAQ)](#10-常见问题-faq)
11. [已知问题](#11-已知问题)
12. [官方链接与资源](#12-官方链接与资源)

---

## 1. What is SPT

**SPT (Single Player Tarkov)** 是《逃离塔科夫》的离线单机模组框架，由粉丝为粉丝制作。

### 核心特性
| 特性 | 说明 |
|------|------|
| 🔌 完全离线 | 无需网络连接，完全不触及 BSG 服务器 |
| 📈 进度保存 | 任务、物品、技能、藏身处均可正常推进 |
| 🎯 高还原度 | 游戏系统与线上模式行为一致 |
| 🛡️ 稳定可靠 | 无掉线、无外挂 |
| 🔧 高度可模组化 | 通过强大的模组系统自定义一切 |
| 🆓 完全免费 | 软件和源码均免费（非商业用途） |
| 📖 开源 | 可在 GitHub 上查阅、Fork、构建 |

> ⚠️ SPT **需要已购买的正版 EFT** 才能运行。不要同时运行 SPT 和 Live EFT（包括启动器）。

---

## 2. 系统要求

| 项目 | 最低要求 |
|------|----------|
| 操作系统 | Windows 10/11 64-bit |
| CPU | Intel Core i5-10400F / AMD Ryzen 5 5600 或更新 |
| 内存 | **32GB** 或以上（强烈建议） |
| GPU | DX11 兼容，**8GB+ VRAM** |
| 存储 | SSD，**70GB+ 空闲空间** |
| 依赖 | [.NET Framework 4.7.2](https://dotnet.microsoft.com/download/dotnet-framework/thank-you/net472-developer-pack-offline-installer) |
| | [.NET Runtime 9.0](https://dotnet.microsoft.com/en-us/download/dotnet/9.0) — 下载 **ASP.NET Core Runtime** 和 **.NET Desktop Runtime** |

### ⚠️ 内存特别说明
- 虽然 16GB 内存有玩家仍能游玩，但这依赖于页面文件（pagefile），会导致卡顿和性能下降
- EFT 多年来对系统资源需求持续增长，16GB 已不足够
- 如果页面文件无法正常工作，需要手动设置（见 [性能优化](#8-性能优化) 章节）

### 安装所需磁盘空间（累计）
| 阶段 | 空间 |
|------|------|
| Patcher (降级工具) | ~8GB (始终在 C:\\) |
| 客户端拷贝 | ~70GB |
| 解压/拷贝 Patcher | ~14GB |
| 后处理 | ~35GB |
| **安装过程中峰值** | **~100GB** |
| **安装完毕后** | **~60GB** |

---

## 3. 安装指南

### 安装前准备
1. ✅ 确保 EFT 通过 BSG Launcher 或 Steam 更新到最新版本
2. ✅ 启动 Live EFT 至少到主菜单或仓库界面，确保所有必要文件已生成
3. ✅ 关闭 Live EFT

### 安装步骤
1. 下载 [SPT Installer](https://forge.sp-tarkov.com/installer)
2. 运行 SPT Installer
3. 阅读 Installer 信息页，点击下一步
4. **选择安装路径**：
   - ❌ **不要**安装到受保护位置（如文档、桌面）
   - ❌ **不要**安装到 Live EFT 文件夹
   - ✅ 推荐：`C:\Games\SPT`
5. 点击"开始安装"并等待完成
6. 运行 `SPT.Server` → 等待绿色文字 `Server has started, happy playing`
7. 运行 `SPT.Launcher` → 按屏幕提示操作：
   - 可复制 Live EFT 的游戏设置
   - 用户名随意，**不要用 Live EFT 用户名**（尤其是直播/录像时）
   - 选择任意游戏版本（不限于你购买的 EFT 版本）
8. 点击 "Start Game" 进入游戏

### ⚠️ 常见安装问题速查
| 问题 | 解决方案 |
|------|----------|
| "Could not find a downgrade patcher" | EFT 刚更新，等待 SPT 团队更新降级工具；或你未更新 EFT |
| Server 闪退/无法打开 | 安装 [.NET Runtime 9.0](https://dotnet.microsoft.com/en-us/download/dotnet/9.0) 的 ASP.NET Core Runtime 和 Desktop Runtime，重启电脑 |
| "Watermark" 错误 | `SPT.Server` / `SPT.Launcher` 被移出 `[游戏目录]\SPT` 文件夹，移回去后用右键"发送到桌面"创建快捷方式 |
| 带有特殊字符的文件夹路径 | 路径中不能包含某些 Unicode 字符（尤其是日语和韩语字符）|

---

## 4. SPT 工作原理

### 安装机制
- SPT Installer 会**复制**你的 EFT 文件，并在必要时自动降级到特定版本
- Installer 始终安装最新 SPT 版本
- 每个 SPT 版本对应特定 EFT 版本（详见 [Release 页面](https://github.com/sp-tarkov/build/releases)）
- SPT 与 Live EFT 完全独立，更新 EFT 不影响 SPT
- 安装后可自由复制/移动/删除 SPT

### 封号风险
- ✅ **不会被封禁**，前提是不与 Live EFT 同时运行
- ❌ 不要安装到 Live EFT 文件夹
- ❌ 不要在 BSG Discord 里炫耀 SPT 并暴露你的 Live EFT 用户名
- 官方声明：无任何经验证的因仅玩 SPT 而被封的案例

### 游戏机制
- 创建档案时可选择**任意版本**（不限于你拥有的 EFT 版本）
- 包含 EFT PvE 模式的所有功能：所有任务、物品、商人
- 跳蚤市场通过随机生成的报价模拟
- 所有进度在撤离后保存
- AI PMC 会随你等级提升获得更好装备
- SPT 使用 EFT 的练习模式系统（所以永远都是"练习模式"，但战利品和任务进度会保存）
- ⚠️ Alt+F4 或崩溃退出 = 不保存任何进度（等同于该 raid 从未发生）
- 服务器关闭时保险、跳蚤、藏身处制作会在下次启动时"追赶上"进度

### 版本号语义
`SPT X.Y.Z`
| 位置 | 含义 | 影响 |
|------|------|------|
| X (Major) | SPT 或 EFT 大重构 | ⚠️ 需全新安装，旧模组不兼容 |
| Y (Minor) | 使用新版 EFT | ⚠️ 需全新安装，旧模组不兼容 |
| Z (Patch/Hotfix) | Bug 修复 | ✅ 覆盖更新即可，模组通常兼容，存档兼容 |

---

## 5. 存档与配置文件 (Profiles)

### 什么是 Profile？
- Profile 就是你的存档文件，存储角色所有信息：物品、任务、技能、藏身处等
- 不包含游戏设置或模组配置
- 数量不限，版本不限（全部本地存储）

### 存档位置
```
[游戏目录]\SPT\user\profiles\[profile_ID].json
```
- 格式为 JSON，可用记事本打开（但不建议手动编辑！）
- 可自由备份/复制

### 自动备份
SPT 自动在以下位置创建备份：
```
[游戏目录]\SPT\user\profiles\backups\
```
- 按日期时间创建文件夹
- 包含 `activeMods.json` 显示当时安装的模组

### 恢复备份
1. 关闭游戏、启动器、服务器
2. 从备份文件夹复制 profile
3. 粘贴到 `profiles` 文件夹，覆盖原文件

### ⚠️ 模组与存档
- 大多数模组可安全添加到现有存档
- **移除某些模组可能导致存档无法使用**（特别是添加新商人/任务/物品的模组）
- 阅读模组页面确认是否安全移除

### 紧急修复被模组损坏的存档
1. 打开 `[游戏目录]\SPT\SPT_Data\Server\configs\core.json`
2. 将 `removeModItemsFromProfile` 设为 `true`
3. 将 `removeInvalidTradersFromProfile` 设为 `true`
4. 保存并启动 SPT
> ⚠️ 这是"最后手段"，修复后仍可能出现随机崩溃、bot 不生成等问题

---

## 6. 模组 (Mods)

### 模组类型

| 类型 | 安装位置 | 说明 |
|------|----------|------|
| **Server 模组** | `[游戏目录]\SPT\user\mods` | 与服务器交互，可创建自定义商人/任务/武器/物品，调整保险/技能/bot生成等 |
| **Client 模组** | `[游戏目录]\BepInEx\plugins` | 直接与游戏交互，功能最强大，可改变 bot AI、HUD、动画等 |
| **组合模组** | 两者皆有 | 同时包含 Server 和 Client 部分 |

- Server 模组：关闭游戏和服务器后配置，通过 config 文件或自带配置工具
- Client 模组：通过游戏内 `F12` 菜单配置（部分无设置界面）
- 大部分 Client 模组可安全添加到现有存档
- 只有 Server 模组会显示在服务器控制台和启动器中

### 安装模组前必读
1. **先启动原版 SPT 到主菜单**，确认能正常游玩后再装模组
2. 安装 [7-Zip](https://www.7-zip.org/) 解压（**WinRAR/Windows 自带解压可能损坏文件**）
3. 安装 [Notepad++](https://notepad-plus-plus.org/) 方便编辑配置文件
4. **只安装与你 SPT 版本兼容的模组**
5. **关闭所有 SPT 相关程序**后再安装/移除模组
6. **小批量安装**，每次验证能正常运行

### 安装方法
1. 用 7-Zip 打开模组压缩包
2. 如果包内有 `SPT` / `BepInEx` 文件夹，直接**拖放全部内容**到游戏根目录
3. 如果结构不对，在 Discord `#mod-questions-4-0` 频道反馈

### 更新模组
- 大多数模组直接覆盖安装即可
- 如果更新后出问题，删除旧模组文件后全新安装
- 使用 [Check Mods](https://forge.sp-tarkov.com/mod/2471/check-mods) 工具检查哪些模组需要更新

### 推荐模组列表 (SPT 4.0)

#### 🤖 AI 改进
- [SAIN](https://forge.sp-tarkov.com/mod/791/sain) — 完整的 AI 战斗系统替换
- [Nerf Bot Grenades](https://forge.sp-tarkov.com/mod/1925/nerfbotgrenades) — 削弱 bot 手雷

#### ⚡ 性能优化
- [AI Limit](https://forge.sp-tarkov.com/mod/1945/ai-limit) — 限制远处 AI 活动
- [Corpse Cleaner](https://forge.sp-tarkov.com/mod/2058/sptcorpsecleaner) — 清理尸体
- [DERP](https://forge.sp-tarkov.com/mod/2200/dynamic-external-resolution-patch-derp) — 动态分辨率
- [Remove The Dead](https://forge.sp-tarkov.com/mod/1551/remove-the-dead) — 移除死亡 bot

#### 🎯 Bot 生成与进度
- [ABPS](https://forge.sp-tarkov.com/mod/2097/abps) — Bot 放置系统（**只装一个 bot 生成模组**）
- [APBS](https://forge.sp-tarkov.com/mod/1594/apbs) — Bot 渐进装备系统（**只装一个 bot 进度模组**）

#### 🖥️ 视觉与 HUD
- [Amands' Sense](https://forge.sp-tarkov.com/mod/2521/amands-sense-updated) — 增强感知
- [Game Panel HUD](https://forge.sp-tarkov.com/mod/456/game-panel-hud) — 自定义 HUD
- [Borkel's Realistic NVGs](https://forge.sp-tarkov.com/mod/954/borkels-realistic-night-vision-goggles-nvgs-and-t-7) — 真实夜视仪
- [HollywoodFX](https://forge.sp-tarkov.com/mod/2003/hollywoodfx) — 画面特效

#### 🔧 便利功能 (QoL)
- **Fixes**: EOTech Fix, FOV Fix, Flicker Fix, Hands Are Not Busy, Item Attribute Fix 等
- **UI**: Dynamic Maps, Quest Tracker, Trader Scrolling, UI Fixes, Expanded Task Text 等
- **物品**: All Quest Checkmarks, Better Keys, Gilded Key Storage, Item Info, MoreCheckmarks 等
- **背包/仓库**: AutoDeposit, Quick Sell, Foldables, Show Me The Money 等

#### 📊 综合调整
- [SVM (Server Value Modifier)](https://forge.sp-tarkov.com/mod/236/server-value-modifier-svm) — SPT 的瑞士军刀，一体化调整工具
- [CWX's MegaMod](https://forge.sp-tarkov.com/mod/1454/cwx-megamod) — 多功能综合调整
- [Lacy's PvE Tweaks](https://forge.sp-tarkov.com/mod/2395/lacys-pve-tweaks) — PvE 微调

### 50/50 排查法 (Binary Search)
当模组导致问题时，**二分法**比逐个排查快得多：

| 模组数量 | 逐个排查次数 | 二分排查次数 |
|----------|-------------|-------------|
| 50 个 | 最多 50 次 | 约 7 次 |
| 100 个 | 最多 100 次 | 约 8 次 |

**步骤**：
1. 先验证问题是模组导致的（移除所有模组测试）
2. 备份 `[游戏目录]\SPT` 和 `[游戏目录]\BepInEx` 到新文件夹
3. 创建测试用的新 Profile
4. 移出一半模组到临时文件夹
5. 启动 SPT 测试问题是否复现
6. 根据结果（复现/消失）知道问题模组在哪一半中
7. 重复步骤 4-6 直到定位到单个模组
8. 恢复备份中除问题模组外的所有模组

---

## 7. Bot 难度系统

### EFT 战前难度设置
Bot 有 4 种**难度等级 (Difficulty Class)**：
- **Easy** (简单)
- **Medium** (中等)
- **Hard** (困难)
- **Impossible** (不可能)

战前设置决定了哪些等级可以生成：
| 设置 | 生成的 Bot 等级 |
|------|----------------|
| As in online (如线上) | 从 Easy → Medium → Hard 渐进 |
| Easy | 仅 Easy |
| Medium | 仅 Medium |
| Hard | 仅 Hard |
| Impossible | 仅 Impossible |

> 以上仅影响 PMC 和 Scav，Boss 在所有等级下难度相同

### SAIN 预设
SAIN 模组的 `F6` 菜单可以**单独调整每个难度等级的行为**，但这**不会改变哪些等级可以生成**（只改变表现）。

### 如何调整难度？
| 你觉得 | 解决方案 |
|--------|----------|
| Bot 太难 | 选择更简单的 SAIN 预设 (如 Baby Bots)；战前设置选择 Easy/Medium |
| Bot 太简单 | 选择更难的 SAIN 预设 (如 Death Wish)；战前设置选择 Hard/Impossible |

---

## 8. 性能优化

### 为什么 SPT 比线上 PVP 性能差？
SPT 在你本地 PC 上运行所有 Bot AI 逻辑。线上模式这些逻辑在 BSG 服务器运行，SPT 会导致严重的 **CPU 瓶颈**。

表现：GPU 和 CPU 使用率都很低（GPU 在等 CPU，CPU 在慢速处理 Bot）
CPUs with powerful single-threaded performance will improve FPS the most. AMD's X3D CPUs are optimal.

### 优化方案
| 优化项 | 说明 |
|--------|------|
| [Waypoints](https://forge.sp-tarkov.com/mod/827/waypoints-expanded-navmesh) | 优化 AI 寻路 |
| [AI Limit](https://forge.sp-tarkov.com/mod/1945/ai-limit) | 停用远处 AI（影响玩法但提升性能） |
| [VRAM Cleaner](https://forge.sp-tarkov.com/mod/2173/vram-cleaner) | 释放 GPU 显存 |
| [Remove The Dead](https://forge.sp-tarkov.com/mod/1551/remove-the-dead) | 清理尸体 |
| 减少 Bot 生成数量 | 在 Bot 生成模组中降低数量 |
| 移除 AI 功能模组 | 给 Bot 添加新功能的模组最影响性能 |
| 关闭 Dynamic Maps 小地图 | 减少渲染负担 |
| Vaulting 设为 Press | 而非 Auto |
| 关闭 Nvidia Reflex | 图形设置中 |
| 关闭 V-Sync | 图形设置中 |
| 纹理质量设为 Low/Medium | 减少内存使用 |
| Streets 使用 Low texture mode | |
| Nvidia Smooth Motion / AMD Fluid Motion Frames | 利用 GPU 插帧 |

### boot.config
默认内容（不需要修改以获得性能提升）：
```
gfx-enable-gfx-jobs=1
gfx-enable-native-gfx-jobs=1
wait-for-native-debugger=0
hdr-display-enabled=0
gc-max-time-slice=3
single-instance=
build-guid=[some ID]
```

### 页面文件 (Pagefile)
- Windows 应设置为"自动管理所有驱动器的分页文件大小"
- 确保驱动器有 30GB+ 空闲空间
- **不建议使用 RAM Cleaner Fix**（反而可能导致问题）
- 如果自动管理仍因内存不足崩溃，可手动设置：

| 内存 | Initial Size | Maximum Size |
|------|-------------|-------------|
| 16 GB | 16000 | 40000 |
| 32 GB | 32000 | 80000 |

### Headless Client (高级)
使用 [Fika](https://forge.sp-tarkov.com/mod/2326/project-fika) 可以在另一台电脑（或同台电脑的不同 CPU 核心）托管 raid，分离游戏渲染和 Bot 处理负载。
> ⚠️ 同台电脑运行 Headless Client 不是官方支持的配置，可能导致性能下降、崩溃、系统不稳定

---

## 9. 更新 SPT

### Hotfix 更新 (如 4.0.1 → 4.0.4)
1. 从 [Release 页面](https://github.com/sp-tarkov/build/releases/latest) 底部下载 Direct Download 文件
2. 关闭游戏/启动器/服务器
3. 用 7-Zip 打开下载文件
4. 将内容复制到**现有 SPT 文件夹**，覆盖所有文件
5. 更新所有模组到最新版本
> ✅ 这种方法只覆盖 SPT 基础文件，不会覆盖你的存档/模组/模组配置

### 大版本更新 (如 3.11 → 4.0)
- ❌ 无法通过覆盖更新
- ✅ 必须全新安装 SPT（不需要删除旧版本）
- 旧模组不兼容，需要下载适配新版本的模组
- 未模组化的旧 Profile 可能可用

---

## 10. 常见问题 (FAQ)

### 基础问题
| 问题 | 答案 |
|------|------|
| SPT 运行的 EFT 版本？ | `0.16.9.0.40087` (2025年10月2日) |
| Labyrinth 地图？ | ✅ 已在 4.0 中 |
| Hardcore/Softcore wipe？ | ❌ 不在 4.0 中（可用模组模拟） |
| 4.0 会包含后续 EFT 补丁吗？ | ❌ 不会，新内容将在 SPT 4.1 中 |
| 3.11 → 4.0 性能提升？ | 稍有提升（BSG 优化了多个地图的剔除） |

### 模组问题
| 问题 | 答案 |
|------|------|
| 3.11 模组能在 4.0 用吗？ | ❌ 完全不兼容 |
| 4.0.0 的模组能用于 4.0.x 吗？ | ✅ 通常兼容，看 Release 页面兼容性说明 |
| 某模组何时更新到 4.0？ | 无人知晓，不要骚扰模组作者 |

### Bot 问题
- Bot 默认不会主动移动（只在战斗中移动），这是 BSG 的设计决定，非 SPT 问题
- SPT 使用 EFT 的 PvE Bot 生成系统，Bot 会持续生成到地图上限
- 目前（4.0）没有让 Bot 主动移动的模组（SAIN 仅影响战斗行为）

### 存档与模组兼容
- 未模组化的 3.11 Profile 可以用于 4.0 ✅
- 有模组的 3.11 Profile 需要开新档 ❌

### 其他
- 安装 SPT 后可以删除 Live EFT 的 `EscapeFromTarkov_Data` 文件夹（但不完全卸载 EFT）
- Steam 版 EFT 需禁用自动更新防止重新下载该文件夹
- SPT 4.0 的 `\SPT` 文件夹有很多文件是正常的（允许模组方法补丁）
- `SPT.Launcher` 和 `SPT.Server` 是快捷方式，实际 exe 在 `[游戏目录]\SPT` 中

---

## 11. 已知问题

### SPT 已知问题 (4.0)
- 部分需要 PMC 在特定地点生成的任务无法完成（该位置无 bot 生成点）
- Scav 模式下选择 Overview 标签可能导致客户端卡死（Alt+F4 回退）
- 服务器离线期间活跃的跳蚤报价会标记为过期（物品通过邮件返回）
- 跳蚤按物品过滤时分类数量显示不正确
- 含某些 Unicode 字符的文件夹路径导致服务器无法加载（特别是日语/韩语）
- 撤离时使用低耐久医疗包可能留下 0 耐久物品
- Lightkeeper 不在游戏中给奖励，通过邮件发送
- 藏身处的比特币计数器有小幅不同步（约 5 分钟延迟）
- 替换日常/周常任务可能导致软锁（重启解决）
- 节日空投无战利品（无已知修复）
- 关闭 Boss 生成会阻止 PMC Bot 生成（**更新 SPT**）
- 选择 Scav 却以 PMC 身份进入（**更新 SPT**）

### 快速修复
| 症状 | 修复 |
|------|------|
| "Not a valid Win32 FileTime" | 更新 SPT 或不用 Hijri 日历 |
| Server 模组不在启动器中显示 | 更新 SPT；Client 模组不会显示在启动器 |
| Scav 跑刀时几乎没有 PMC | 更新 SPT，不要延长 raid 时间 |
| 空跳蚤 + 404 错误 | 更新 SPT |
| Kollontay 仍在高级 Ground Zero 生成 | 更新 SPT |
| Crisis 不解锁新制作 | 更新 SPT |
| 点击 Play 无反应 | 更新 SPT |

---

## 12. 官方链接与资源

| 资源 | 链接 |
|------|------|
| 🌐 官方网站 | [sp-tarkov.com](https://www.sp-tarkov.com/) |
| 🏭 SPT Forge (模组中心) | [forge.sp-tarkov.com](https://forge.sp-tarkov.com/) |
| 💬 Discord | [discord.sp-tarkov.com](http://discord.sp-tarkov.com/) |
| 📖 文档 | [docs.sp-tarkov.com](https://docs.sp-tarkov.com/) |
| 🛠️ 开发 | [dev.sp-tarkov.com](https://dev.sp-tarkov.com/) |
| 📦 GitHub | [github.com/sp-tarkov](https://github.com/sp-tarkov/) |
| 💝 Patreon | [patreon.com/sptarkov](https://www.patreon.com/sptarkov) |
| 📋 EFT Wiki | [escapefromtarkov.fandom.com](https://escapefromtarkov.fandom.com/wiki/Changelog) |

### 重要页面直达
- [SPT Installer 下载](https://forge.sp-tarkov.com/installer)
- [SPT Release 页面](https://github.com/sp-tarkov/build/releases)
- [SPT Wiki (GitHub)](https://github.com/sp-tarkov/wiki)
- [3.11 手动安装指南](https://github.com/sp-tarkov/build/wiki/3.11-Manual-Installation-Instructions)
- [推荐模组列表](https://wiki.sp-tarkov.com/Recommended_Mods_40)
- [性能调优](https://wiki.sp-tarkov.com/Performance_Tuning)
- [安装模组指南](https://wiki.sp-tarkov.com/Installing_Mods)

---

> 💡 **提示**：遇到问题先查阅 [FAQ](#10-常见问题-faq) 和 [已知问题](#11-已知问题)，大部分问题更新 SPT 即可解决。最佳获取支持的途径是 [Discord](http://discord.sp-tarkov.com/) 的 `#spt-support` 频道。
>
> 📝 本文档汇总自 [SPT Wiki](https://github.com/sp-tarkov/wiki)，适用于 **SPT 4.0.x** 版本。
