/**
 * book.controller.js —— 学案原文控制器
 *
 * 六十三卷按需取，取到就顺手进检索索引 —— 所以「读过的卷才搜得到」。
 * 为了让检索一上来就可用，进入本页时后台把全部卷预热一遍，
 * 分批 requestIdleCallback，不抢渲染线程。
 */
import { $, esc } from '../core/dom.js';
import { loadVolume } from '../data/repository.js';
import { toPlain } from '../data/wikitext.js';
import { createIndex } from '../engines/search.engine.js';
import * as view from '../views/book.view.js';

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
    view.renderToc(tocPane, model, { onOpen: (v) => open(v) });
    $('#qBtn').addEventListener('click', () => runSearch($('#q').value));
    $('#q').addEventListener('keydown', (e) => { if (e.key === 'Enter') runSearch(e.target.value); });
    $('#qClear').addEventListener('click', () => { $('#q').value = ''; sres.style.display = 'none'; });
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

  /** 后台把全部卷灌进索引，一次三卷，空闲时才做 */
  function warm() {
    if (warming) return;
    warming = true;
    const queue = model.tocEntries().map((x) => x.key).filter((v) => !plain.has(v));
    const total = queue.length;
    const idle = window.requestIdleCallback || ((fn) => setTimeout(() => fn({ timeRemaining: () => 8 }), 30));
    const step = () => {
      if (!queue.length) { setStatus(`全文检索就绪：${index.size} 篇已入索引`); return; }
      Promise.all(queue.splice(0, 3).map((v) => ingest(v).catch(() => null)))
        .then(() => { setStatus(`正在建立全文索引… ${index.size}/${total} 篇`); idle(step); });
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
      // 正编卷号是数字，卷前篇是 x1/x2/x3 字符串，路由参数统一在这里还原成对应类型。
      // 不指定篇目时默认打开卷前首篇（原序），与原书开篇次序一致。
      const raw = params[0];
      let v = /^\d+$/.test(String(raw || '')) ? Number(raw) : raw;
      if (!v) v = model.tocEntries()[0] && model.tocEntries()[0].key;
      if (v && v !== current) open(v);
      else if (!current) setStatus('点击左侧篇目开始阅读；全文检索在后台建索引，稍候即可使用。');
    },
    open,
    currentVolume: () => current,
  };
}
