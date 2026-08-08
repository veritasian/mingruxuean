/**
 * book.view.js —— 学案原文阅读器
 *
 * 左目录右正文。正文源是维基文库的 wikitext，需要先剥掉模板、脚注、
 * 表格再转段落 —— 这段清洗逻辑单独放在 wikitext.js，本文件只管排版。
 */
import { el, clear, esc } from '../core/dom.js';
import { toHTML } from '../data/wikitext.js';

const NUM = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十'];

function cn(n) {
  if (n <= 10) return NUM[n];
  if (n < 20) return `十${NUM[n - 10]}`;
  const t = Math.floor(n / 10); const o = n % 10;
  return `${NUM[t]}十${o ? NUM[o] : ''}`;
}

/** 目录左栏的短标：正编是「卷十二」，卷前篇是「原序」「师说」 */
function tag(info) {
  return info.front ? (info.label || info.name) : `卷${cn(info.volume)}`;
}

/** 正文标题：卷前篇不冠卷号，它本来就不是卷 */
function title(info) {
  return info.front || !info.volume || Number.isNaN(Number(info.volume))
    ? esc(info.name)
    : `卷${info.volume}　${esc(info.name)}`;
}

export function renderToc(container, model, { onOpen } = {}) {
  clear(container);
  container.appendChild(el('div.toc-cap', { text: '目录 · 卷前三篇 + 六十三卷（含附案）' }));
  for (const v of model.tocEntries()) {
    const d = el('div.toc-item', {
      dataset: { v: String(v.key) },
      html: `<span class="tv${v.front ? ' tv-front' : ''}">${esc(tag(v))}</span>`
        + `<div><div class="tn2">${esc(v.name)}</div>`
        + `<div class="tp">${esc(v.front ? (v.note || '') : (v.persons || []).join(' '))}</div></div>`,
    });
    d.addEventListener('click', () => onOpen && onOpen(v.key));
    container.appendChild(d);
  }
}

export function markActive(container, v) {
  container.querySelectorAll('.toc-item')
    .forEach((x) => x.classList.toggle('on', x.dataset.v === String(v)));
}

function peopleChips(info, model, onPick) {
  const box = el('div.people');
  for (const name of info.persons || []) {
    const known = !!model.persons[name];
    const chip = el('span.pchip', {
      text: name,
      style: known ? { color: 'var(--accent)' } : {},
      dataset: known ? { go: name } : {},
    });
    if (known) chip.addEventListener('click', (e) => { e.stopPropagation(); onPick && onPick(name, chip); });
    box.appendChild(chip);
  }
  return box;
}

export function renderLoading(reader, info) {
  clear(reader);
  const head = el('div.reader-head', { html: `<h3>${title(info)}</h3>` });
  reader.append(head, el('div.reader-status', { text: '正在载入原文…' }));
}

export function renderVolume(reader, info, text, model, { onPick } = {}) {
  clear(reader);
  const note = info.front && info.note ? `<div class="reader-note">${esc(info.note)}</div>` : '';
  const head = el('div.reader-head', { html: `<h3>${title(info)}</h3>${note}` });
  head.appendChild(peopleChips(info, model, onPick));
  const body = el('div.reader-body', { html: toHTML(text) });
  reader.append(head, body);
  return body;
}

export function renderError(reader, info, err) {
  const page = `明儒學案/${info.name_original || info.name}`;
  const url = `https://zh.wikisource.org/wiki/${encodeURIComponent(page)}`;
  reader.innerHTML = `<div class="reader-head"><h3>${title(info)}</h3></div>
    <div class="reader-status">本篇正文载入失败。可直接前往维基文库阅读：
    <a href="${url}" target="_blank" rel="noopener" style="color:var(--accent)">${esc(page)}</a>
    <br/><span style="font-size:12px">${esc(String((err && err.message) || err))}</span></div>`;
}

/** 检索结果列表 */
export function renderResults(box, hits, model, { onOpen } = {}) {
  box.style.display = 'block';
  clear(box);
  if (!hits.length) {
    box.appendChild(el('div.sres-item', { text: '无结果。可换用更短的词，或直接检索人名、书名。' }));
    return;
  }
  for (const h of hits) {
    const info = model.volumeInfo(h.vol) || { name: '', volume: h.vol };
    const item = el('div.sres-item', {
      dataset: { v: String(h.vol), at: String(h.at || 0) },
      html: `<div class="shead"><span class="sv">${esc(tag({ ...info, front: !!info.id }))}</span>`
        + `<span class="st">${esc(info.name)}</span>`
        + `<span class="sc">相似度 ${h.score}</span></div>`
        + `<div class="sp">${h.snippet || ''}</div>`,
    });
    item.addEventListener('click', () => { box.style.display = 'none'; onOpen && onOpen(h.vol, h.needle); });
    box.appendChild(item);
  }
}

/** 打开卷后滚到命中段并闪一下 */
export function highlight(body, needle) {
  if (!needle) return;
  const pars = [...body.querySelectorAll('.par')];
  const hit = pars.find((p) => p.textContent.includes(needle));
  if (!hit) return;
  hit.scrollIntoView({ behavior: 'smooth', block: 'center' });
  hit.classList.add('hit');
  setTimeout(() => hit.classList.remove('hit'), 2500);
}
