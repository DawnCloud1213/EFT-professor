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

/** 截图前处理: 拉高表格容器显示全部行 + 隐藏固定 footer 防遮挡 */
async function prepareScreenshot() {
  await page.evaluate(() => {
    const el = document.querySelector('.tgMainTableInAppShell');
    if (el) { el.style.height = '3000px'; el.style.maxHeight = 'none'; }
    const f = document.querySelector('footer, .mantine-AppShell-footer, [class*="footer"]');
    if (f) f.style.display = 'none';
  });
  await page.waitForTimeout(500);
}

/** 生成所有弹药的弹道表截图 */
async function generateAllAmmos(ammoList, outputPrefix, maxDist = 350) {
  await setMaxDistance(maxDist);
  for (const ammo of ammoList) {
    console.log(`--- ${ammo} ---`);
    await sel('Step Four', ammo);
    await page.locator('button:has-text("Generate Drop Table")').click();
    await page.waitForTimeout(3000);
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
  await setMaxDistance350();
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
  await setMaxDistance350();
  await generateAllAmmos(['AP', 'FMJ', 'UCW', 'TAC-X'], 'm10_27');
  
  // 枪管 2: 23.5" 597mm
  await page.goto('https://tarkovgunsmith.com/ballistic_calculator');
  await page.waitForTimeout(1500);
  await sel('Step One', '.338 LM');
  await sel('Step Two', 'TRG M10');
  await sel('Step Three', 'M10 23.5" .338LM');
  await setMaxDistance350();
  await generateAllAmmos(['AP', 'FMJ', 'UCW', 'TAC-X'], 'm10_235');
}

// ---- 其他武器速查参数 ----
const WEAPON_CONFIGS = {
  'spear': {
    caliber: '6.8x51mm',
    weapon: 'SPEAR 6.8',
    barrel: 'SPEAR 13"',
    ammos: ['FMJ', 'Hybrid'],
    prefix: 'spear'
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
