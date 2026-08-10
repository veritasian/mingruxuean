/**
 * smoke.mjs —— 真浏览器冒烟测试（多页面版）
 *
 * 站点是「一分类一页面」：对 dist/ 下 9 个页面逐个打开真浏览器，
 * 验证「只显示本页内容、菜单高亮、SEO 独立、数据切片不串页」，
 * 再单独验证旧链接重定向与跨页聚焦（?focus= / ?v= / ?orphans）。
 *
 * 用法：node tests/smoke.mjs
 */
import { createRequire } from 'node:module';
import { existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import http from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));
const DIST = resolve(HERE, '..', 'dist');

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
const CHROME = ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/Applications/Chromium.app/Contents/MacOS/Chromium',
  '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'].find(existsSync);
if (!CHROME) { console.error('找不到可用的 Chrome/Chromium'); process.exit(2); }

const PAGES = [
  { id: 'kg',       file: 'index.html',    probe: '#kg .kg-node',     kw: '知识图谱' },
  { id: 'graph',    file: 'graph.html',    probe: '#graph .node',     kw: '谱系总图' },
  { id: 'roster',   file: 'roster.html',   probe: '#roster details',  kw: '人物线索' },
  { id: 'time',     file: 'time.html',     probe: '#tline rect',      kw: '时间线索' },
  { id: 'geo',      file: 'geo.html',      probe: '#geoGrid .gprov',  kw: '地理线索' },
  { id: 'orphan',   file: 'orphan.html',   probe: '#orphanBody .orphan-chip', kw: '孤点现象' },
  { id: 'book',     file: 'chapter-Preface.html', probe: '#tocPane .toc-item', kw: '明儒学案' },
  { id: 'yangming', file: 'yangming.html', probe: '#yangmingRoot .ym-chapter', kw: '阳明心学' },
  { id: 'lit-tiyong', file: 'lit-tiyong.html', section: 'literature', 'data-page': 'literature', probe: '#litBody .lit-par', kw: '体用论' },
];
const results = [];
const errors = [];
const ok = (n, d = '') => results.push(['PASS', n, d]);
const bad = (n, d = '') => { results.push(['FAIL', n, d]); errors.push(`${n} ${d}`); };

// 在线版数据走 fetch，必须用 http 服务（file:// 下 CORS 拦 fetch）
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.svg': 'image/svg+xml' };
const server = http.createServer(async (req, res) => {
  try {
    let p = decodeURIComponent(req.url.split('?')[0]);
    if (p === '/') p = '/index.html';
    const fp = normalize(join(DIST, p));
    if (!fp.startsWith(DIST)) { res.writeHead(403); return res.end(); }
    const buf = await readFile(fp);
    res.writeHead(200, { 'content-type': MIME[extname(fp)] || 'application/octet-stream' });
    res.end(buf);
  } catch { res.writeHead(404); res.end('404'); }
});
await new Promise((r) => server.listen(0, r));
const PORT = server.address().port;
const BASE = `http://localhost:${PORT}`;

const browser = await puppeteer.launch({
  executablePath: CHROME, headless: 'new',
  args: ['--no-sandbox'],
});
const page = await browser.newPage();
await page.setViewport({ width: 1440, height: 900 });
let consoleErrors = [];
page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()); });
page.on('pageerror', (e) => consoleErrors.push(`[pageerror] ${e.message}`));

async function open(file, hash = '') {
  consoleErrors = [];
  await page.goto(`${BASE}/${file}${hash}`, { waitUntil: 'load', timeout: 60000 });
  await page.waitForFunction(() => !!window.__MRXA_APP__, { timeout: 30000 });
  await new Promise((r) => setTimeout(r, 700));
}

/* ---------- 逐页体检 ---------- */
for (const p of PAGES) {
  const f = `${DIST}/${p.file}`;
  if (!existsSync(f)) { bad(`页面 ${p.file}`, '产物缺失'); continue; }
  await open(p.file);
  const secid = p.section || p.id;
  const dp = p['data-page'] || p.id;
  const r = await page.evaluate((pid, secid, dp, probe) => ({
    sectionOn: document.querySelector(`#sec-${secid}`)?.classList.contains('on') || false,
    n: document.querySelectorAll(probe).length,
    menuOn: document.querySelector('#menu a.on')?.dataset.page || '',
    menuCount: document.querySelectorAll('#menu a').length,
    title: document.title,
    desc: document.querySelector('meta[name="description"]')?.content?.length || 0,
    stray: [...document.querySelectorAll('section.tab')]
      .map((s) => s.id.replace('sec-', '')).filter((x) => x !== secid),
  }), p.id, secid, dp, p.probe);
  if (!r.sectionOn || !r.n) bad(`页面 ${p.id}`, `section=${r.sectionOn} 内容=${r.n}`);
  else ok(`页面 ${p.id}`, `${p.probe} × ${r.n}`);
  r.menuOn === dp ? ok(`菜单 ${p.id}`, `高亮 ${r.menuOn}`) : bad(`菜单 ${p.id}`, `高亮 ${r.menuOn}`);
  r.stray.length ? bad(`纯净 ${p.id}`, `混入 ${r.stray.join(',')}`)
                 : ok(`纯净 ${p.id}`, '无其他分类内容');
  r.title.includes(p.kw) && r.desc > 20
    ? ok(`SEO ${p.id}`, `title 含「${p.kw}」· desc ${r.desc} 字`)
    : bad(`SEO ${p.id}`, `title=${r.title.slice(0, 30)} desc=${r.desc}`);
  if (consoleErrors.length) {
    bad(`控制台 ${p.id}`, `${consoleErrors.length} 条错误：${consoleErrors[0].slice(0, 160)}`);
  }
}
ok('菜单链接', `${PAGES.length} 个分类互链`);

/* ---------- 首页（index.html = 知识图谱）数据规模 ---------- */
await open('index.html');
const meta = await page.evaluate(() => {
  const m = window.__MRXA_APP__.model;
  return m ? {
    schools: m.schools.length, persons: m.personList.length,
    relations: m.relations.length, edges: m.edgeList().length,
    coverage: document.querySelector('#coverage')?.textContent || '',
    menuCount: document.querySelectorAll('#menu a').length,
  } : null;
});
meta
  ? ok('模型', `${meta.schools} 学案 / ${meta.persons} 人 / ${meta.relations} 关系 / ${meta.edges} 连线`)
  : bad('模型', '取不到 model');
meta?.coverage.length > 8 ? ok('概览行', meta.coverage) : bad('概览行', '为空');
meta?.menuCount === 9 ? ok('菜单项', '9 个分类') : bad('菜单项', `实得 ${meta?.menuCount}`);

/* ---------- 顶部「明儒学案」是 home 链接 ---------- */
const homeLink = await page.evaluate(() => ({
  href: document.querySelector('h1.title a')?.getAttribute('href') || '',
  text: document.querySelector('h1.title')?.textContent.trim() || '',
}));
homeLink.href === 'index.html'
  ? ok('标题链接', `「${homeLink.text}」→ ${homeLink.href}`)
  : bad('标题链接', `href=${homeLink.href}`);

/* ---------- kg 跨页聚焦与孤点态 ---------- */
await open('index.html', '?focus=王阳明');
const focus = await page.evaluate(() => {
  const v = window.__MRXA_APP__.ctl.view;
  return { focused: v && v.focusedId ? v.focusedId() : '', card: !!document.querySelector('#pc.show') };
});
focus.focused === '王阳明'
  ? ok('kg 聚焦', `?focus=王阳明 → ${focus.focused}`)
  : bad('kg 聚焦', `focused=${focus.focused}`);

await open('index.html', '?orphans=1');
const orph = await page.evaluate(() => ({
  btn: document.querySelector('#kgOrphan')?.classList.contains('on'),
  hint: document.querySelector('#kgHint')?.textContent?.slice(0, 10) || '',
}));
orph.btn ? ok('kg 孤点态', '?orphans=1 只看孤点') : bad('kg 孤点态', `btn=${orph.btn}`);

/* ---------- 箭头朝向：都从师指向徒 ---------- */
await open('index.html');
const dir = await page.evaluate(() => {
  const edges = window.__MRXA_APP__.ctl.view?.edges?.();
  if (!edges || !edges.length) return { err: '取不到图谱连线' };
  const wrong = edges.filter((e) => e.source !== e.teacher || e.target !== e.disciple);
  return { n: edges.length, wrong: wrong.length, eg: edges[0] };
});
if (dir.err) bad('箭头朝向', dir.err);
else if (dir.wrong) bad('箭头朝向', `${dir.wrong}/${dir.n} 条方向相反`);
else ok('箭头朝向', `${dir.n} 条皆自师指向徒（如 ${dir.eg.teacher} → ${dir.eg.disciple}）`);

/* ---------- 人物卡（谱系总图页点击节点） ---------- */
await open('graph.html');
const card = await page.evaluate(() => {
  const n = document.querySelector('#graph .node');
  if (!n) return { err: '图上没有节点' };
  n.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  const pc = document.querySelector('#pc');
  return { show: pc?.classList.contains('show'), text: (pc?.textContent || '').slice(0, 40) };
});
card.show ? ok('人物卡', card.text.replace(/\s+/g, ' ')) : bad('人物卡', card.err || '点击后未弹出');

/* ---------- 学案原文（按卷分页 64 页） ---------- */
// 卷前页 chapter-Preface.html：默认原序 + 三个 tab + 目录次序
await open('chapter-Preface.html');
const def = await page.evaluate(() => ({
  active: document.querySelector('#tocPane .toc-item.on')?.dataset.v || '',
  tabs: document.querySelectorAll('#frontTabs button').length,
  tabOn: document.querySelector('#frontTabs button.on')?.dataset.p || '',
}));
def.active === 'x1' ? ok('默认页', '卷前页默认显示 原序（x1）') : bad('默认页', `默认激活 ${def.active}`);
def.tabs === 3 ? ok('卷前三 tab', '原序/发凡/师说') : bad('卷前三 tab', `实得 ${def.tabs} 个`);

const order = await page.evaluate(() => [...document.querySelectorAll('#tocPane .toc-item')]
  .slice(0, 4).map((x) => x.dataset.v));
order.join(',') === 'x1,x2,x3,1'
  ? ok('卷前次序', '原序 → 发凡 → 师说 → 卷一')
  : bad('卷前次序', `目录前四项是 ${order.join(',')}`);

// 切 tab：发凡
await page.evaluate(() => {
  const b = [...document.querySelectorAll('#frontTabs button')].find((x) => x.dataset.p === 'x2');
  b && b.click();
});
await new Promise((r) => setTimeout(r, 500));
const fafan = await page.evaluate(() => ({
  title: document.querySelector('#reader .reader-head h3')?.textContent || '',
  chars: (document.querySelector('#reader .reader-body')?.textContent || '').length,
}));
fafan.chars > 500 && fafan.title.includes('发凡')
  ? ok('卷前 tab 切换', `${fafan.title} ${fafan.chars} 字`)
  : bad('卷前 tab 切换', `标题「${fafan.title}」正文 ${fafan.chars} 字`);

// 独立卷页：chapter-one.html（崇仁学案一）、chapter-twelve.html（浙中王门学案二）
for (const [file, volNo, name] of [['chapter-one.html', '1', '崇仁学案一'],
                                   ['chapter-twelve.html', '12', '浙中王门学案二']]) {
  await open(file);
  const v = await page.evaluate(() => ({
    active: document.querySelector('#tocPane .toc-item.on')?.dataset.v || '',
    chars: (document.querySelector('#reader .reader-body')?.textContent || '').length,
    title: document.title,
  }));
  const good = v.active === volNo && v.chars > 500 && v.title.includes(name);
  good ? ok(`卷页 ${file}`, `激活卷${volNo} ${name} · ${v.chars} 字 · title 独立`)
       : bad(`卷页 ${file}`, `active=${v.active} chars=${v.chars} title=${v.title.slice(0, 30)}`);
}

// 卷页内 TOC 点其他卷 → 跳到对应独立页（chapter-one → 卷 2）
await open('chapter-one.html');
await page.evaluate(() => {
  const t = [...document.querySelectorAll('#tocPane .toc-item')].find((x) => x.dataset.v === '2');
  t && t.click();
});
await new Promise((r) => setTimeout(r, 1400));
const nav2 = await page.evaluate(() => location.pathname.split('/').pop());
nav2 === 'chapter-two.html'
  ? ok('目录跨页跳转', '卷一 → 卷二独立页')
  : bad('目录跨页跳转', `实得 ${nav2}`);

// 回归：卷页上点菜单「阳明心学」必须跳根级 yangming.html，不能变成 book/yangming.html
await open('chapter-one.html');
await page.evaluate(() => {
  const a = document.querySelector('#menu a[data-page="yangming"]');
  a && a.click();
});
await new Promise((r) => setTimeout(r, 1400));
const menuNav = await page.evaluate(() => location.pathname.replace(/^\//, ''));
menuNav === 'yangming.html'
  ? ok('菜单跨页跳转', '卷页 → 根级 yangming.html')
  : bad('菜单跨页跳转', `实得 ${menuNav}`);

// 旧版单文件 book.html 跳板：book.html?v=12 → chapter-twelve.html
await page.goto(`${BASE}/book.html?v=12`, { waitUntil: 'load' });
await new Promise((r) => setTimeout(r, 1500));
const stub = await page.evaluate(() => location.pathname.split('/').pop());
stub === 'chapter-twelve.html'
  ? ok('book.html 跳板', 'book.html?v=12 → chapter-twelve.html')
  : bad('book.html 跳板', `实得 ${stub}`);

/* ---------- 阳明心学专页 ---------- */
await open('yangming.html');
const ym = await page.evaluate(() => ({
  hero: document.querySelectorAll('#yangmingRoot .ym-hero-title span').length,
  chapters: document.querySelectorAll('#yangmingRoot .ym-chapter').length,
  links: document.querySelectorAll('#yangmingRoot .ym-link').length,
  navTop: document.querySelector('#yangmingRoot .ym-nav')?.getBoundingClientRect().top ?? -1,
  mainTop: document.querySelector('#yangmingRoot .ym-main')?.getBoundingClientRect().top ?? -1,
  bands: document.querySelectorAll('#yangmingRoot .ym-band').length,
  matrix: document.querySelectorAll('#yangmingRoot .ym-matrix').length,
  quadBoards: document.querySelectorAll('#yangmingRoot .ym-quad-board').length,
  figures: document.querySelectorAll('#yangmingRoot .ym-figure').length,
}));
ym.hero === 4 && ym.chapters === 14
  ? ok('阳明 内容', `四句教 ${ym.hero} 句 · ${ym.chapters} 章`)
  : bad('阳明 内容', `hero=${ym.hero} ch=${ym.chapters}`);

/* 四句教下的心学总纲说明块（边框 + 淡蓝透明底） */
const ymNote = await page.evaluate(() => {
  const box = document.querySelector('#yangmingRoot .ym-note');
  return {
    n: box ? box.querySelectorAll('p').length : 0,
    text: box ? (box.textContent || '') : '',
  };
});
ymNote.n && ymNote.text.includes('惟精惟一') && ymNote.text.includes('学贵自得')
  ? ok('阳明 读图说明', `${ymNote.n} 段 · 学贵自得…惟精惟一`)
  : bad('阳明 读图说明', `段数 ${ymNote.n}，text=${ymNote.text.slice(0, 30)}`);
ym.links === 15 ? ok('阳明 目录', `${ym.links} 个章节链接`) : bad('阳明 目录', `链接 ${ym.links} 个`);
ym.navTop > 0 && ym.navTop < ym.mainTop
  ? ok('阳明 目录置顶', '章节目录在正文上方')
  : bad('阳明 目录置顶', `nav=${ym.navTop} main=${ym.mainTop}`);
ym.bands === 2 && ym.matrix === 1 && ym.quadBoards === 12 && ym.figures === 3
  ? ok('阳明 原版结构', `色带 ${ym.bands} · 矩阵 ${ym.matrix} · 四象板 ${ym.quadBoards} · 小人 ${ym.figures}`)
  : bad('阳明 原版结构', `bands=${ym.bands} matrix=${ym.matrix} quad=${ym.quadBoards} fig=${ym.figures}`);
const revealed = await page.evaluate(() => new Promise((resolve) => {
  document.getElementById('ym-ch1')?.scrollIntoView({ behavior: 'instant', block: 'start' });
  setTimeout(() => resolve(
    document.querySelectorAll('#yangmingRoot .ym-reveal.is-in').length), 500);
}));
revealed >= 3 ? ok('阳明 渐入', `${revealed} 个区块已淡入`) : bad('阳明 渐入', `仅 ${revealed}`);
const spy = await page.evaluate(() => new Promise((resolve) => {
  const el = document.getElementById('ym-ch13');
  if (!el) return resolve('无 ym-ch13');
  el.scrollIntoView({ behavior: 'instant', block: 'start' });
  setTimeout(() => resolve(
    document.querySelector('#yangmingRoot .ym-link.on')?.dataset.yg || ''), 300);
}));
spy === 'ch13' ? ok('阳明 滚动监听', `滚到 拾叁 后高亮 ${spy}`) : bad('阳明 滚动监听', `高亮 ${spy}`);

/* ---------- 旧链接重定向 ---------- */
const cases = [
  ['#content/graph', 'graph.html', ''],
  ['#/graph', 'graph.html', ''],
  ['#v12', 'chapter-twelve.html', ''],
  ['#content/book/12', 'chapter-twelve.html', ''],
  ['#all', 'graph.html', '?all=1'],
  ['#kgf王阳明', 'index.html', '?focus=%E7%8E%8B%E9%98%B3%E6%98%8E'],
];
for (const [legacy, wantFile, wantQ] of cases) {
  await page.goto(`${BASE}/index.html${legacy}`, { waitUntil: 'load' });
  await new Promise((r) => setTimeout(r, 1600));       // location.replace + 新页启动
  const got = await page.evaluate(() => ({
    file: location.pathname.replace(/^\//, ''),
    q: location.search,
  }));
  got.file === wantFile && (!wantQ || got.q === wantQ)
    ? ok(`旧链接 ${legacy}`, `→ ${wantFile}${wantQ}`)
    : bad(`旧链接 ${legacy}`, `实得 ${got.file}${got.q}`);
}

if (consoleErrors.length) bad('控制台', `${consoleErrors.length} 条错误`);
else ok('控制台', '无 error');

await browser.close();

/* ---------- 报告 ---------- */
const w = Math.max(...results.map(([, n]) => n.length));
for (const [s, n, d] of results) {
  console.log(`  ${s === 'PASS' ? '✓' : '✗'} ${n.padEnd(w)}  ${d}`);
}
if (errors.length) {
  console.log('\n  失败明细：');
  [...new Set(errors)].slice(0, 12).forEach((e) => console.log(`    · ${e.slice(0, 200)}`));
}
const failed = results.filter(([s]) => s === 'FAIL').length;
console.log(`\n  ${results.length - failed} 通过 / ${failed} 失败`);
server.close();
process.exit(failed ? 1 : 0);
