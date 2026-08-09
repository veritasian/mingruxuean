/**
 * book.controller.js —— 学案原文控制器（按卷分页版）
 *
 * 学案原文已拆成 64 个独立页面（卷前一篇 3 tab + 63 卷各一页），
 * 每个页面只内联自己那份正文，加载快、互不影响。本控制器是它们共用的：
 *
 *   · 本页是哪一篇？由打包时注入的 window.__BOOK__ 决定（'front' 或卷号）
 *   · 左目录点击 → 跳到对应卷的页面（跨页），卷前篇在本页内切 tab
 *   · 检索只建「本页内联的卷」的索引（卷前页 3 篇、卷页 1 篇）
 */
import { $, esc } from '../core/dom.js';
import { loadVolume } from '../data/repository.js';
import { toPlain } from '../data/wikitext.js';
import { createIndex } from '../engines/search.engine.js';
import { chapterFile } from '../router/index.js';
import * as view from '../views/book.view.js';

const MINE = (typeof window !== 'undefined' && window.__BOOK__) || 'front';

export function create(model, { onPick }) {
  const tocPane = $('#tocPane');
  const reader = $('#reader');
  const sres = $('#sres');
  const index = createIndex();
  const plain = new Map();
  let built = false;
  let warming = false;
  let current = null;

  function build() {
    if (built) return;
    built = true;
    view.renderToc(tocPane, model, { onOpen: (v) => navTo(v) });
    $('#qBtn').addEventListener('click', () => runSearch($('#q').value));
    $('#q').addEventListener('keydown', (e) => { if (e.key === 'Enter') runSearch(e.target.value); });
    $('#qClear').addEventListener('click', () => { $('#q').value = ''; sres.style.display = 'none'; });
    if (MINE === 'front') buildFrontTabs();
  }

  /** 卷前篇页：原序 / 发凡 / 师说 三个 tab，本页内切换 */
  function buildFrontTabs() {
    const box = $('#frontTabs');
    if (!box) return;
    box.hidden = false;
    for (const it of model.tocEntries().filter((x) => x.front)) {
      const b = document.createElement('button');
      b.type = 'button';
      b.textContent = it.label || it.name;
      b.dataset.p = String(it.key);
      b.addEventListener('click', () => open(it.key));
      box.appendChild(b);
    }
  }

  function markFrontTab(v) {
    const box = $('#frontTabs');
    if (!box) return;
    box.querySelectorAll('button').forEach((b) =>
      b.classList.toggle('on', b.dataset.p === String(v)));
  }

  /** 左目录点击：卷前篇（本页）切 tab，正编卷号跳独立页（都平铺在站点根） */
  function navTo(v) {
    if (MINE === 'front' && (v === 'x1' || v === 'x2' || v === 'x3')) {
      open(v);
      return;
    }
    location.href = chapterFile(v);
  }

  async function ingest(v) {
    if (plain.has(v)) return plain.get(v);
    const vol = await loadVolume(v);
    const text = toPlain(vol.text || '');
    plain.set(v, text);
    index.add(v, text);
    return text;
  }

  async function open(v, needle) {
    build();
    const info = model.volumeInfo(v);
    if (!info) return;
    current = v;
    view.markActive(tocPane, v);
    markFrontTab(v);
    view.renderLoading(reader, info);
    try {
      const vol = await loadVolume(v);
      await ingest(v);
      const body = view.renderVolume(reader, info, vol.text || '', model, { onPick });
      if (needle) view.highlight(body, needle);
    } catch (err) {
      view.renderError(reader, info, err);
    }
  }

  /** 只建本页内联的卷的索引（卷前页 3 篇、卷页 1 篇），空闲时做 */
  function warm() {
    if (warming) return;
    warming = true;
    const avail = new Set(Object.keys((window.__MRXA__ && window.__MRXA__.volumes) || {}));
    const queue = model.tocEntries().map((x) => x.key)
      .filter((v) => avail.has(String(v)) && !plain.has(v));
    const total = queue.length;
    const idle = window.requestIdleCallback || ((fn) => setTimeout(() => fn({ timeRemaining: () => 8 }), 30));
    const step = () => {
      if (!queue.length) { setStatus(`本卷已入索引（${index.size} 篇），可检索。`); return; }
      Promise.all(queue.splice(0, 3).map((v) => ingest(v).catch(() => null)))
        .then(() => { setStatus(`正在建立本卷索引… ${index.size}/${total} 篇`); idle(step); });
    };
    idle(step);
  }

  function setStatus(msg) {
    const s = $('#pullStatus');
    if (s) s.textContent = msg;
  }

  function runSearch(q) {
    const query = String(q || '').trim();
    if (!query) return;
    if (!index.size) { setStatus('索引尚未建立，请稍候…'); warm(); return; }
    const hits = index.search(query, 12).map((h) => {
      const text = plain.get(h.vol) || '';
      const ex = index.excerpt(text, query, 34, 1)[0];
      return {
        ...h,
        needle: ex ? ex.hit : query,
        snippet: ex
          ? `${esc(ex.before)}<mark>${esc(ex.hit)}</mark>${esc(ex.after)}`
          : esc(text.slice(0, 80)),
      };
    });
    view.renderResults(sres, hits, model, { onOpen: (v, needle) => open(v, needle) });
  }

  return {
    enter({ params }) {
      build();
      warm();
      // 本页固定是哪一篇由 window.__BOOK__ 决定（'front' 或卷号字符串）；
      // ?v= 参数可覆盖（深链用）。卷号还原成数字以匹配目录表。
      let v = params[0];
      if (!v) v = MINE === 'front' ? 'x1' : Number(MINE);
      if (v && v !== current) open(v);
      else if (!current) setStatus('点击左侧篇目开始阅读；本卷索引稍候即可用。');
    },
    open,
    currentVolume: () => current,
  };
}
