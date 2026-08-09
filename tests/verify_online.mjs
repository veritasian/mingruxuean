/**
 * verify_online.mjs —— 在线版真浏览器验证（http 服务，fetch 数据）
 * 重点：图谱 #kg .kg-node 是否真实渲染（v10 翻车点），文本页静态内容是否到位。
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
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

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

const require = createRequire(import.meta.url);
const puppeteer = require('puppeteer-core');

const results = [];
const ok = (n, d) => { results.push(['PASS', n, d]); console.log('  ✓', n, d || ''); };
const bad = (n, d) => { results.push(['FAIL', n, d]); console.log('  ✗', n, d || ''); };

await new Promise((r) => server.listen(0, r));
const PORT = server.address().port;
const BASE = `http://localhost:${PORT}`;
console.log('静态服务已起：', BASE);

const browser = await puppeteer.launch({
  executablePath: CHROME, headless: 'new',
  args: ['--no-sandbox'],
});
const page = await browser.newPage();
await page.setViewport({ width: 1440, height: 900 });
let errs = [];
page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
page.on('pageerror', (e) => errs.push(`[pageerror] ${e.message}`));

async function open(file, hash = '') {
  errs = [];
  await page.goto(`${BASE}/${file}${hash}`, { waitUntil: 'load', timeout: 60000 });
  await page.waitForFunction(() => !!window.__MRXA_APP__, { timeout: 30000 });
  await new Promise((r) => setTimeout(r, 900));
}

// 1) 知识图谱 —— 真渲染节点
try {
  await open('index.html');
  const r = await page.evaluate(() => ({
    nodes: document.querySelectorAll('#kg .kg-node').length,
    cov: document.querySelector('#coverage')?.textContent || '',
    edges: window.__MRXA_APP__.ctl.view?.edges?.().length || 0,
  }));
  r.nodes > 0 ? ok('kg 图谱渲染', `#kg .kg-node × ${r.nodes}，连线 ${r.edges}`) : bad('kg 图谱渲染', '无节点');
  r.cov ? ok('kg 概览行', r.cov) : bad('kg 概览行', '空');
} catch (e) { bad('kg 图谱渲染', e.message); }

// 2) 谱系总图
try {
  await open('graph.html');
  const n = await page.evaluate(() => document.querySelectorAll('#graph .node').length);
  n > 0 ? ok('graph 渲染', `#graph .node × ${n}`) : bad('graph 渲染', '无节点');
} catch (e) { bad('graph 渲染', e.message); }

// 3) 时间轴
try {
  await open('time.html');
  const n = await page.evaluate(() => document.querySelectorAll('#tline rect').length);
  n > 0 ? ok('time 渲染', `#tline rect × ${n}`) : bad('time 渲染', '无柱');
} catch (e) { bad('time 渲染', e.message); }

// 4) 地理图 + noscript（noscript 在 JS 开启时不进 DOM，查原始 HTML）
try {
  await open('geo.html');
  const grid = await page.evaluate(() => document.querySelectorAll('#geoGrid .gprov').length);
  const raw = await readFile(join(DIST, 'geo.html'), 'utf8');
  const noscript = raw.includes('<noscript') && raw.includes('geo-noscript');
  grid > 0 ? ok('geo 渲染', `#geoGrid .gprov × ${grid}`) : bad('geo 渲染', '无省块');
  noscript ? ok('geo noscript', '有静态对照表（源 HTML）') : bad('geo noscript', '缺兜底');
} catch (e) { bad('geo 渲染', e.message); }

// 5) 文本页：静态正文预渲染（无 JS 也能读）
try {
  await open('roster.html');
  const txt = await page.evaluate(() => (document.querySelector('#roster')?.textContent || '').length);
  txt > 200 ? ok('roster 静态正文', `#roster 文本 ${txt} 字`) : bad('roster 静态正文', `仅 ${txt} 字`);
} catch (e) { bad('roster 静态正文', e.message); }

// 6) 学案原文：卷文预渲染
try {
  await open('chapter-Preface.html');
  const txt = await page.evaluate(() => (document.querySelector('#reader .reader-body')?.textContent || '').length);
  txt > 200 ? ok('book 静态正文', `#reader 正文 ${txt} 字`) : bad('book 静态正文', `仅 ${txt} 字`);
} catch (e) { bad('book 静态正文', e.message); }

// 7) 阳明
try {
  await open('yangming.html');
  const txt = await page.evaluate(() => {
    const el = document.querySelector('#yangmingRoot');
    return { len: el?.textContent.length || 0, ch: el?.querySelectorAll('.ym-chapter').length || 0 };
  });
  txt.len > 100 ? ok('yangming 静态正文', `文本 ${txt.len} 字 · ${txt.ch} 章`) : bad('yangming 静态正文', '空');
} catch (e) { bad('yangming 静态正文', e.message); }

// 8) 控制台错误（全局）
const allErr = errs.length;
allErr === 0 ? ok('控制台', '无 error') : bad('控制台', `${allErr} 条：${errs.slice(0, 3).join(' | ')}`);

await browser.close();
server.close();

const fails = results.filter((r) => r[0] === 'FAIL').length;
console.log(`\n${results.length - fails}/${results.length} 通过`);
process.exit(fails ? 1 : 0);
