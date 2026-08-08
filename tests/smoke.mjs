/**
 * smoke.mjs —— 真浏览器冒烟测试
 *
 * 用系统 Chrome 打开 dist/明儒学案.html，逐个视图走一遍，
 * 把 console 上的任何 error/pageerror 都算作失败。
 *
 * 为什么非要真浏览器：这套页面的核心是 SVG 布局与力导向，
 * jsdom 里 getBBox/getComputedStyle 全是零，测了等于没测。
 *
 * 用法：node tests/smoke.mjs [绝对路径的 html]
 */
import { createRequire } from 'node:module';
import { existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));

/** puppeteer-core 可能装在项目外的托管 workspace 里，ESM 不吃 NODE_PATH，手动找一遍 */
function loadPuppeteer() {
  const bases = [import.meta.url,
    ...(process.env.NODE_PATH || '').split(':').filter(Boolean)
      .map((p) => pathToFileURL(`${p}/`).href)];
  for (const base of bases) {
    try { return createRequire(base)('puppeteer-core'); } catch { /* 下一个 */ }
  }
  return null;
}
const puppeteer = loadPuppeteer();
if (!puppeteer) {
  console.error('缺少 puppeteer-core。设置 NODE_PATH 指向含该包的 node_modules 再跑。');
  process.exit(2);
}
const TARGET = process.argv[2] || resolve(HERE, '..', 'dist', '明儒学案.html');
const CHROME = ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/Applications/Chromium.app/Contents/MacOS/Chromium',
  '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'].find(existsSync);

const VIEWS = ['graph', 'roster', 'time', 'geo', 'kg', 'orphan', 'book', 'yangming'];
const results = [];
const errors = [];
const ok = (n, d = '') => results.push(['PASS', n, d]);
const bad = (n, d = '') => { results.push(['FAIL', n, d]); errors.push(`${n} ${d}`); };

if (!CHROME) { console.error('找不到可用的 Chrome/Chromium'); process.exit(2); }
if (!existsSync(TARGET)) { console.error(`目标不存在：${TARGET}`); process.exit(2); }

const browser = await puppeteer.launch({
  executablePath: CHROME, headless: 'new',
  args: ['--no-sandbox', '--allow-file-access-from-files'],
});
const page = await browser.newPage();
await page.setViewport({ width: 1440, height: 900 });

const consoleErrors = [];
page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()); });
page.on('pageerror', (e) => consoleErrors.push(`[pageerror] ${e.message}`));

await page.goto(`file://${TARGET}`, { waitUntil: 'load', timeout: 60000 });
await page.waitForFunction(() => !!window.__MRXA_APP__, { timeout: 30000 })
  .then(() => ok('启动', '__MRXA_APP__ 已挂载'))
  .catch(() => bad('启动', '30s 内未完成 boot'));

/* ---------- 数据规模 ---------- */
const meta = await page.evaluate(() => {
  const m = window.__MRXA_APP__?.model;
  if (!m) return null;
  return {
    schools: m.schools.length, persons: m.personList.length,
    relations: m.relations.length, edges: m.edgeList().length,
    orphans: (m.orphanList() || []).length, tabs: document.querySelectorAll('#tabs button').length,
    coverage: document.querySelector('#coverage')?.textContent || '',
  };
});
if (meta) {
  ok('模型', `${meta.schools} 学案 / ${meta.persons} 人 / ${meta.relations} 关系 / ${meta.edges} 连线`);
  meta.tabs === VIEWS.length ? ok('页签', `${meta.tabs} 个`) : bad('页签', `期望 ${VIEWS.length}，实得 ${meta.tabs}`);
  meta.coverage.length > 8 ? ok('概览行', meta.coverage) : bad('概览行', '为空');
} else bad('模型', '取不到 model');

/* ---------- 默认首页 = 知识图谱（#content/kg）+ 菜单次序/名称 ---------- */
const home = await page.evaluate(() => ({
  hash: location.hash,
  tabs: [...document.querySelectorAll('#tabs button')].map((b) => b.textContent.trim()),
}));
home.hash === '#content/kg' ? ok('默认首页', '知识图谱 #content/kg') : bad('默认首页', `实得 ${home.hash}`);
const wantTabs = ['知识图谱', '谱系总图', '人物线索', '时间线索', '地理线索', '孤点现象', '学案原文', '阳明心学'];
home.tabs.join(',') === wantTabs.join(',')
  ? ok('菜单次序', wantTabs.join(' / '))
  : bad('菜单次序', `实得 ${home.tabs.join(',')}`);

/* ---------- 逐视图 ---------- */
const PROBE = {
  graph: '#graph .node', roster: '#roster details', time: '#tline rect',
  geo: '#geoGrid .gprov', kg: '#kg .kg-node', orphan: '#orphanBody .orphan-chip',
  book: '#tocPane .toc-item', yangming: '#yangmingRoot .ym-chapter',
};
for (const v of VIEWS) {
  await page.evaluate((n) => { location.hash = `#content/${n}`; }, v);
  await new Promise((r) => setTimeout(r, v === 'kg' ? 1200 : 450));
  const r = await page.evaluate((sel, name) => ({
    shown: document.querySelector(`#sec-${name}`)?.classList.contains('on'),
    n: document.querySelectorAll(sel).length,
  }), PROBE[v], v);
  if (!r.shown) bad(`视图 ${v}`, '未激活');
  else if (!r.n) bad(`视图 ${v}`, `无内容（${PROBE[v]} 命中 0）`);
  else ok(`视图 ${v}`, `${PROBE[v]} × ${r.n}`);
}

/* ---------- 阳明心学专页：侧边栏 / 原版结构 / 滚动监听 / 移动折叠 ---------- */
await page.evaluate(() => { location.hash = '#content/yangming'; });
await new Promise((r) => setTimeout(r, 800));
const ym = await page.evaluate(() => ({
  links: document.querySelectorAll('#yangmingRoot .ym-link').length,
  hero: document.querySelectorAll('#yangmingRoot .ym-hero-title span').length,
  chapters: document.querySelectorAll('#yangmingRoot .ym-chapter').length,
  navTop: document.querySelector('#yangmingRoot .ym-nav')?.getBoundingClientRect().top ?? -1,
  mainTop: document.querySelector('#yangmingRoot .ym-main')?.getBoundingClientRect().top ?? -1,
  bands: document.querySelectorAll('#yangmingRoot .ym-band').length,
  matrix: document.querySelectorAll('#yangmingRoot .ym-matrix').length,
  quadBoards: document.querySelectorAll('#yangmingRoot .ym-quad-board').length,
  figures: document.querySelectorAll('#yangmingRoot .ym-figure').length,
}));
ym.hero === 4 && ym.chapters === 14
  ? ok('阳明心学 内容', `四句教 ${ym.hero} 句 · ${ym.chapters} 章`)
  : bad('阳明心学 内容', `hero=${ym.hero} ch=${ym.chapters}`);
ym.links === 15 ? ok('阳明心学 章节目录', `${ym.links} 个章节链接`) : bad('阳明心学 章节目录', `链接 ${ym.links} 个`);
ym.navTop > 0 && ym.navTop < ym.mainTop
  ? ok('阳明心学 目录置顶', '章节目录在正文上方')
  : bad('阳明心学 目录置顶', `nav=${ym.navTop} main=${ym.mainTop}`);
ym.bands === 2 && ym.matrix === 1 && ym.quadBoards === 12 && ym.figures === 3
  ? ok('阳明心学 原版结构', `色带 ${ym.bands} · 矩阵 ${ym.matrix} · 四象板 ${ym.quadBoards} · 小人 ${ym.figures}`)
  : bad('阳明心学 原版结构', `bands=${ym.bands} matrix=${ym.matrix} quad=${ym.quadBoards} fig=${ym.figures}`);

// 渐入：滚到第一章后，镜像布局与子盒应淡入
const revealed = await page.evaluate(() => new Promise((resolve) => {
  document.getElementById('ym-ch1')?.scrollIntoView({ behavior: 'instant', block: 'start' });
  setTimeout(() => resolve(
    document.querySelectorAll('#yangmingRoot .ym-reveal.is-in').length), 500);
}));
revealed >= 3 ? ok('阳明心学 渐入', `${revealed} 个区块已淡入`) : bad('阳明心学 渐入', `仅 ${revealed}`);

const spy = await page.evaluate(() => new Promise((resolve) => {
  const el = document.getElementById('ym-ch13');
  if (!el) return resolve('无 ym-ch13');
  el.scrollIntoView({ behavior: 'instant', block: 'start' });
  setTimeout(() => resolve(
    document.querySelector('#yangmingRoot .ym-link.on')?.dataset.yg || ''), 300);
}));
spy === 'ch13' ? ok('阳明心学 滚动监听', `滚到 拾叁 后高亮 ${spy}`) : bad('阳明心学 滚动监听', `高亮 ${spy}`);

/* ---------- 交互 ---------- */
await page.evaluate(() => { location.hash = '#content/graph'; });
await new Promise((r) => setTimeout(r, 400));
const card = await page.evaluate(() => {
  const n = document.querySelector('#graph .node');
  if (!n) return { err: '图上没有节点' };
  n.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  const pc = document.querySelector('#pc');
  return { show: pc?.classList.contains('show'), text: (pc?.textContent || '').slice(0, 60) };
});
card.show ? ok('人物卡', card.text.replace(/\s+/g, ' ')) : bad('人物卡', card.err || '点击后未弹出');

/* 两页的箭头必须同向：都从师指向徒。反了就会读成「徒教师」 */
await page.evaluate(() => { location.hash = '#content/kg'; });
await new Promise((r) => setTimeout(r, 900));
const dir = await page.evaluate(() => {
  const edges = window.__MRXA_APP__.ctl.kg.view?.edges?.();
  if (!edges || !edges.length) return { err: '取不到图谱连线' };
  const wrong = edges.filter((e) => e.source !== e.teacher || e.target !== e.disciple);
  return { n: edges.length, wrong: wrong.length, eg: edges[0] };
});
if (dir.err) bad('箭头朝向', dir.err);
else if (dir.wrong) bad('箭头朝向', `${dir.wrong}/${dir.n} 条方向相反`);
else ok('箭头朝向', `${dir.n} 条皆自师指向徒（如 ${dir.eg.teacher} → ${dir.eg.disciple}）`);

const prov = await page.evaluate(() => {
  const m = window.__MRXA_APP__.model;
  const hit = m.relations.find((r) => r.cited && r.provenance);
  if (!hit) return { err: '没有带出处的关系' };
  window.__MRXA_APP__.ctl.graph.locate?.(hit.from);
  return { from: hit.from, to: hit.to, src: JSON.stringify(hit.provenance).slice(0, 80) };
});
prov.err ? bad('关系出处', prov.err) : ok('关系出处', `${prov.from} → ${prov.to} ${prov.src}`);

/* ---------- 旧链接兼容 ---------- */
for (const [legacy, want] of [['#v12', 'book'], ['#all', 'graph'], ['#kgf王阳明', 'kg']]) {
  await page.evaluate((h) => { location.hash = h; window.__MRXA_APP__.router.migrateLegacyHash(); }, legacy);
  await new Promise((r) => setTimeout(r, 250));
  const got = await page.evaluate(() => window.__MRXA_APP__.router.currentRoute()?.name);
  got === want ? ok(`旧链接 ${legacy}`, `→ ${got}`) : bad(`旧链接 ${legacy}`, `期望 ${want}，实得 ${got}`);
}

/* ---------- 全文 ---------- */
await page.evaluate(() => { location.hash = '#content/book/12'; });
await new Promise((r) => setTimeout(r, 1500));
const vol = await page.evaluate(() => ({
  chars: (document.querySelector('#reader')?.textContent || '').length,
}));
vol.chars > 500 ? ok('卷次正文', `第 12 卷 ${vol.chars} 字`) : bad('卷次正文', `只读到 ${vol.chars} 字`);

// 卷前三篇：路由参数是字符串 x1/x2/x3，走的分支跟数字卷号不同，必须单独验
for (const [key, label] of [['x1', '原序'], ['x2', '发凡'], ['x3', '师说']]) {
  await page.evaluate((k) => { location.hash = `#content/book/${k}`; }, key);
  await new Promise((r) => setTimeout(r, 900));
  const fm = await page.evaluate(() => ({
    title: document.querySelector('#reader .reader-head h3')?.textContent || '',
    chars: (document.querySelector('#reader .reader-body')?.textContent || '').length,
    chips: document.querySelectorAll('#reader .reader-head .pchip').length,
  }));
  const good = fm.chars > 500 && !fm.title.startsWith('卷');
  good ? ok(`卷前 ${label}`, `${fm.title} ${fm.chars} 字 · 关联 ${fm.chips} 人`)
       : bad(`卷前 ${label}`, `标题「${fm.title}」正文 ${fm.chars} 字`);
}

// 目录里这三篇必须排在卷一之前，且次序为 原序 → 发凡 → 师说，否则等于没放对位置
const order = await page.evaluate(() => [...document.querySelectorAll('#tocPane .toc-item')]
  .slice(0, 4).map((x) => x.dataset.v));
order.join(',') === 'x1,x2,x3,1'
  ? ok('卷前次序', '原序 → 发凡 → 师说 → 卷一')
  : bad('卷前次序', `目录前四项是 ${order.join(',')}`);

// 打开学案原文（不带篇目参数）默认应落在卷前首篇 原序
const def = await page.evaluate(() => {
  location.hash = '#content/book';
  return new Promise((resolve) => setTimeout(() => resolve(
    document.querySelector('#tocPane .toc-item.on')?.dataset.v || ''), 1100));
});
def === 'x1' ? ok('默认页', '打开学案原文默认显示 原序（x1）')
            : bad('默认页', `默认激活的篇目是 ${def}`);

if (consoleErrors.length) bad('控制台', `${consoleErrors.length} 条错误`);
else ok('控制台', '无 error');

await browser.close();

/* ---------- 报告 ---------- */
const w = Math.max(...results.map(([, n]) => n.length));
for (const [s, n, d] of results) {
  console.log(`  ${s === 'PASS' ? '✓' : '✗'} ${n.padEnd(w)}  ${d}`);
}
if (consoleErrors.length) {
  console.log('\n  控制台错误：');
  [...new Set(consoleErrors)].slice(0, 12).forEach((e) => console.log(`    · ${e.slice(0, 220)}`));
}
const failed = results.filter(([s]) => s === 'FAIL').length;
console.log(`\n  ${results.length - failed} 通过 / ${failed} 失败`);
process.exit(failed ? 1 : 0);
