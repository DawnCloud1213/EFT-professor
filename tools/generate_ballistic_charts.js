#!/usr/bin/env node
/**
 * EFT 弹道表批量生成脚本
 * 
 * 用法: 通过 Playwright MCP (mcp__playwright__browser_run_code_unsafe) 执行
 * 
 * 原理:
 * 1. 打开 tarkovgunsmith.com/ballistic_calculator
 * 2. 通过 page.evaluate dispatch MouseEvent 操作 Mantine Select 下拉框
 * 3. 选择口径 → 武器 → 枪管 → 弹药 → Generate → 截图
 * 
 * 坑点记录:
 * - Hermes browser tools 无法触发 Mantine Select 的 React 状态更新
 * - 必须用 Playwright MCP + page.evaluate dispatch 'click' 事件
 * - Step Four 弹药选项文本格式为 "M80Speed: 820 m/s, Pen: 43, Dam: 80"
 *   需要用 .startsWith('M80') 匹配而非精确匹配
 * - readonly 的 input 用 page.keyboard.type() 输入不会触发搜索过滤
 *   但点击后 dropdown 会打开所有选项，直接 evaluate 点击目标选项即可
 */

// ============== 核心函数 ==============

/** 通过 dispatch MouseEvent 点击匹配的 option */
async function clickOpt(text) {
  return await page.evaluate((t) => {
    for (const o of document.querySelectorAll('[role="option"]'))
      if (o.textContent.trim().startsWith(t)) {
        o.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
        o.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true }));
        o.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
        return true;
      }
    return false;
  }, text);
}

/** 选择下拉框的完整流程: 点击 → 等待 → clickOpt */
async function sel(ph, opt) {
  await page.locator(`input[placeholder="${ph}"]`).click();
  await page.waitForTimeout(500);
  const r = await clickOpt(opt);
  console.log(`  ${ph} -> ${opt}: ${r ? '✅' : '❌'}`);
  await page.waitForTimeout(400);
}

/** 将 Max Distance 设为指定值（默认 350m） */
async function setMaxDistance(dist = 350) {
  await page.evaluate((d) => {
    for (const inp of document.querySelectorAll('input'))
      if (inp.value === '200' && inp.type === 'text') {
        const ns = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
        ns.call(inp, String(d));
        inp.dispatchEvent(new Event('input', { bubbles: true }));
        break;
      }
  }, dist);
}

/** 截图前处理: 表格行高压缩 + 高度=内容实际高度(不多不少) + 隐藏固定 footer 防遮挡 */
async function prepareScreenshot() {
  // 第一步: 注入行高压缩 style (等 reflow)
  await page.evaluate(() => {
    if (!document.getElementById('tight-table')) {
      const style = document.createElement('style');
      style.id = 'tight-table';
      style.textContent = `
        .tgMainTableInAppShell table td, .tgMainTableInAppShell table th {
          padding: 3px 6px !important;
        }
      `;
      document.head.appendChild(style);
    }
    const f = document.querySelector('footer, .mantine-AppShell-footer, [class*="footer"]');
    if (f) f.style.display = 'none';
  });
  await page.waitForTimeout(400);
  // 第二步: 重置高度后读取压缩后的内容高度
  await page.evaluate(() => {
    const el = document.querySelector('.tgMainTableInAppShell');
    if (el) {
      el.style.height = 'auto';
      el.style.maxHeight = 'none';
      el.style.height = el.scrollHeight + 'px';
    }
  });
  await page.waitForTimeout(400);
}

/** 图表 Distance Max 设为指定值 (Mantine NumberInput: 必须真实键盘输入 + Tab blur) */
async function setChartMaxDistance(dist) {
  // focus 图表控制区的 Distance Max 输入框 (含 Distance Min/Max/Drop Max 文本的区域内最后一个 text input)
  const focused = await page.evaluate(() => {
    const inputs = Array.from(document.querySelectorAll('input'));
    for (const inp of inputs) {
      if (inp.type === 'text' && !inp.disabled) {
        let p = inp.parentElement;
        for (let j = 0; j < 8 && p; j++) {
          const t = p.textContent || '';
          if (t.includes('Distance Max') && t.includes('Distance Min') && t.includes('Drop Max')) {
            const ins = Array.from(p.querySelectorAll('input')).filter(x => x.type === 'text' && !x.disabled);
            if (ins.length) { ins[ins.length - 1].focus(); ins[ins.length - 1].select(); }
            return true;
          }
          p = p.parentElement;
        }
      }
    }
    return false;
  });
  if (!focused) return false;
  await page.keyboard.press('Control+a');
  await page.keyboard.type(String(dist));
  await page.keyboard.press('Tab');
  await page.waitForTimeout(1200);
  return true;
}

/** 布局调整(v8最终版): 外层配置栏16%/右区84% + 隐藏空col + 表格40%(min-width:0)/图表60% + 图表容器maxWidth解锁 */
async function adjustLayout() {
  return await page.evaluate(() => {
    // 1. 外层 grid: 配置栏 16% / 右区 84%
    const outerGrid = Array.from(document.querySelectorAll('.mantine-Grid-root')).find(g => {
      return Array.from(g.children).some(ch => ch.classList && ch.classList.contains('mantine-Grid-col') && ch.querySelector(':scope > .mantine-Grid-root'));
    });
    if (outerGrid) {
      Array.from(outerGrid.querySelectorAll(':scope > .mantine-Grid-col')).forEach(c => {
        const hasGridChild = Array.from(c.children).some(ch => ch.classList && ch.classList.contains('mantine-Grid-root'));
        if (hasGridChild) { c.style.flex = '0 0 84%'; c.style.maxWidth = '84%'; }
        else { c.style.flex = '0 0 16%'; c.style.maxWidth = '16%'; }
      });
    }
    // 2. 内层 grid: 隐藏空 col + 表格 40% / 图表 60%
    const table = document.querySelector('.tgMainTableInAppShell');
    const chart = document.querySelector('.recharts-responsive-container');
    if (table && chart) {
      const findDirectCol = (target) => {
        let cur = target;
        while (cur && cur !== document.body) {
          if (cur.classList && cur.classList.contains('mantine-Grid-col')) {
            const colsInside = cur.querySelectorAll('.mantine-Grid-col');
            let hasDirect = true;
            for (const c of colsInside) { if (c.contains(target)) { hasDirect = false; break; } }
            if (hasDirect) return cur;
          }
          cur = cur.parentElement;
        }
        return null;
      };
      const tableCol = findDirectCol(table);
      const chartCol = findDirectCol(chart);
      if (tableCol && chartCol && tableCol.parentElement === chartCol.parentElement) {
        Array.from(tableCol.parentElement.querySelectorAll(':scope > .mantine-Grid-col')).forEach(c => {
          if (c !== tableCol && c !== chartCol) c.style.display = 'none';
        });
        tableCol.style.minWidth = '0';
        tableCol.style.flex = '0 0 40%';
        tableCol.style.maxWidth = '40%';
        chartCol.style.flex = '0 0 60%';
        chartCol.style.maxWidth = '60%';
      }
    }
    // 3. 图表容器 maxWidth 解锁
    document.querySelectorAll('div').forEach(d => {
      const cs = getComputedStyle(d);
      if (cs.maxWidth === '650px' && d.querySelector('.recharts-responsive-container')) {
        d.style.maxWidth = 'none';
        d.style.width = '100%';
      }
    });
    return true;
  });
}

/** X 轴刻度细分: 从现有刻度反推线性映射, 克隆 tick 插入每 stepM 米的刻度 + grid 竖线 */
async function injectTicks(stepM = 50) {
  return await page.evaluate((step) => {
    const svgs = document.querySelectorAll('svg');
    for (const s of svgs) {
      const texts = Array.from(s.querySelectorAll('text')).map(t => t.textContent.trim());
      if (!texts.some(t => /^\d+m$/.test(t)) || s.getBoundingClientRect().width < 300) continue;
      const ticksGroup = s.querySelector('.recharts-cartesian-axis-ticks');
      const gridVertical = s.querySelector('.recharts-cartesian-grid-vertical');
      if (!ticksGroup) return 'no ticks group';
      const tick150 = Array.from(ticksGroup.querySelectorAll('.recharts-cartesian-axis-tick')).find(t => t.textContent.trim() === '150m');
      const tick450 = Array.from(ticksGroup.querySelectorAll('.recharts-cartesian-axis-tick')).find(t => t.textContent.trim() === '450m');
      if (!tick150 || !tick450) return 'template missing';
      const x150 = parseFloat(tick150.querySelector('text').getAttribute('x'));
      const x450 = parseFloat(tick450.querySelector('text').getAttribute('x'));
      const pxPerM = (x450 - x150) / 300;
      const plotLeft = x150 - 150 * pxPerM;
      const maxDist = 450;
      const existing = new Set(Array.from(ticksGroup.querySelectorAll('.recharts-cartesian-axis-tick-value')).map(t => t.textContent.trim()));
      const newDists = [];
      for (let d = step; d <= maxDist; d += step) {
        if (!existing.has(d + 'm')) newDists.push(d);
      }
      for (const d of newDists) {
        const x = plotLeft + (d / maxDist) * (x450 - plotLeft);
        const clone = tick150.cloneNode(true);
        const line = clone.querySelector('line');
        const textEl = clone.querySelector('text');
        const tspan = clone.querySelector('tspan');
        line.setAttribute('x1', x); line.setAttribute('x2', x);
        textEl.setAttribute('x', x);
        tspan.setAttribute('x', x);
        tspan.textContent = d + 'm';
        ticksGroup.appendChild(clone);
        if (gridVertical) {
          const gv = Array.from(gridVertical.querySelectorAll('line'));
          if (gv.length) {
            const gclone = gv[0].cloneNode(true);
            gclone.setAttribute('x1', x); gclone.setAttribute('x2', x);
            gridVertical.appendChild(gclone);
          }
        }
      }
      return { added: newDists.length, dists: newDists };
    }
    return 'chart not found';
  }, stepM);
}

/** 生成所有弹药的弹道表截图 (完整流程: 表格 + 图表范围 + 宽布局 + 50m 刻度) */
async function generateAllAmmos(ammoList, outputPrefix, maxDist = 350) {
  await setMaxDistance(maxDist);
  for (const ammo of ammoList) {
    console.log(`--- ${ammo} ---`);
    await sel('Step Four', ammo);
    await page.locator('button:has-text("Generate Drop Table")').click();
    await page.waitForTimeout(3000);
    await setChartMaxDistance(maxDist);
    await adjustLayout();
    await injectTicks(50);
    await prepareScreenshot();
    const fn = `${outputPrefix}_${ammo.toLowerCase().replace(/[-\s]/g,'_')}_drop.png`;
    await page.screenshot({ path: `${OUT_DIR}/${fn}`, fullPage: true });
    console.log(`  Saved: ${fn}`);
  }
}


// ============== 使用示例 ==============

// 常量配置
const OUT_DIR = 'E:/JUST_DO_IT/EFT-professor/knowledge/弹道资源';

// ---- 示例 1: 单枪管武器 (SR-25) ----
async function generateSR25() {
  await page.goto('https://tarkovgunsmith.com/ballistic_calculator');
  await page.waitForTimeout(1500);
  
  await sel('Step One', '7.62x51mm');
  await sel('Step Two', 'SR-25');
  await sel('Step Three', 'SR-25 20"');
  await generateAllAmmos(['M80', 'M61', 'M62', 'M993'], 'sr25');
}

// ---- 示例 2: 双枪管武器 (M10, 两种枪管) ----
async function generateM10() {
  // 枪管 1: 27" 685mm
  await page.goto('https://tarkovgunsmith.com/ballistic_calculator');
  await page.waitForTimeout(1500);
  await sel('Step One', '.338 LM');
  await sel('Step Two', 'TRG M10');
  await sel('Step Three', 'M10 27" .338LM');
  await generateAllAmmos(['AP', 'FMJ', 'UCW', 'TAC-X'], 'm10_27');
  
  // 枪管 2: 23.5" 597mm
  await page.goto('https://tarkovgunsmith.com/ballistic_calculator');
  await page.waitForTimeout(1500);
  await sel('Step One', '.338 LM');
  await sel('Step Two', 'TRG M10');
  await sel('Step Three', 'M10 23.5" .338LM');
  await generateAllAmmos(['AP', 'FMJ', 'UCW', 'TAC-X'], 'm10_235');
}

// ---- 其他武器速查参数 ----
const WEAPON_CONFIGS = {
  'spear': {
    caliber: '6.8x51mm',
    weapon: 'SPEAR 6.8',
    barrel: 'SPEAR 13"',
    ammos: ['FMJ', 'Hybrid'],
    prefix: 'spear',
    maxDist: 450
  },
  'sr25': {
    caliber: '7.62x51mm',
    weapon: 'SR-25',
    barrel: 'SR-25 20"',
    ammos: ['M80', 'M61', 'M62', 'M993'],
    prefix: 'sr25'
  },
  'g28': {
    caliber: '7.62x51mm',
    weapon: 'G28',
    barrel: '417 16.5"',
    ammos: ['M80', 'M61', 'M62', 'M993'],
    prefix: 'g28'
  },
  't5000': {
    caliber: '7.62x51mm',
    weapon: 'T-5000M',
    barrel: 'T-5000M 660mm',
    ammos: ['M80', 'M61', 'M62', 'M993'],
    prefix: 't5000'
  },
  'm10_27': {
    caliber: '.338 LM',
    weapon: 'TRG M10',
    barrel: 'M10 27" .338LM',
    ammos: ['AP', 'FMJ', 'UCW', 'TAC-X'],
    prefix: 'm10_27'
  },
  'm10_235': {
    caliber: '.338 LM',
    weapon: 'TRG M10',
    barrel: 'M10 23.5" .338LM',
    ammos: ['AP', 'FMJ', 'UCW', 'TAC-X'],
    prefix: 'm10_235'
  },
  'ak50': {
    caliber: '.50 BMG',
    weapon: 'AK-50',
    barrel: 'AK-50 24"',
    ammos: ['M903', 'M33', 'M21', 'HP'],
    prefix: 'ak50'
  },
  'ak12': {
    caliber: '5.45x39mm',
    weapon: 'AK-12',
    barrel: null, // AK-12 无枪管选项 (n/a)
    ammos: ['BP'],
    prefix: 'ak12',
    maxDist: 200
  },
  'r11_18': {
    caliber: '7.62x51mm',
    weapon: 'RSASS',
    barrel: 'AR-10 18"',
    ammos: ['M80'],
    prefix: 'r11_18',
    maxDist: 450
  },
  'axmc': {
    caliber: '.338 LM',
    weapon: 'AXMC',
    barrel: 'AXMC .338LM 28"',
    ammos: ['FMJ'],
    prefix: 'axmc'
  }
};

// ---- 通用生成函数 ----
async function generateWeapon(config) {
  await page.goto('https://tarkovgunsmith.com/ballistic_calculator');
  await page.waitForTimeout(1500);
  await sel('Step One', config.caliber);
  await sel('Step Two', config.weapon);
  if (config.barrel) await sel('Step Three', config.barrel);
  await generateAllAmmos(config.ammos, config.prefix, config.maxDist || 350);
}
