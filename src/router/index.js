/**
 * router/index.js —— 多页面站点：只剩旧链接重定向
 *
 * 站点已从「单文件 + 哈希路由」重构为「每分类一个独立页面」，
 * 页面之间用普通 <a href> 互相链接，不再有 #content/ 路由。
 * 这个模块只保留两件事：
 *   1. 把旧地址（#content/kg、#v12、#kgf王阳明、#all、#/graph 等）重定向到对应新页面
 *   2. 学案原文的跨页跳转帮助（卷号 → chapter-one.html 式文件名）
 *
 * 全部页面平铺在站点根目录（不设 book/ 二级目录）。
 * 全站只有这里碰 location.hash。
 */
const FILE = {
  kg: 'index.html', graph: 'graph.html', roster: 'roster.html',
  time: 'time.html', geo: 'geo.html', orphan: 'orphan.html',
  book: 'chapter-Preface.html', yangming: 'yangming.html',
};

const ONES = ['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine'];
const TEENS = ['ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen',
  'seventeen', 'eighteen', 'nineteen'];
const TENS = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty'];

/** 1–63 → one … sixty-three（学案原文卷页的文件名用） */
export function numToWords(n) {
  const k = Number(n);
  if (!k || k < 1 || k > 63) return String(n);
  if (k < 10) return ONES[k];
  if (k < 20) return TEENS[k - 10];
  const t = Math.floor(k / 10); const o = k % 10;
  return `${TENS[t]}${o ? `-${ONES[o]}` : ''}`;
}

/**
 * 学案原文某个篇目 → 它所在的页面（都平铺在站点根）：
 *   卷前篇 x1/x2/x3 → chapter-Preface.html?p=xN（同一页内切 tab）
 *   卷 N（1–63）    → chapter-<英文数字>.html（独立页）
 */
export function chapterFile(v) {
  if (v === 'x1' || v === 'x2' || v === 'x3') return `chapter-Preface.html?p=${v}`;
  return `chapter-${numToWords(v)}.html`;
}

/**
 * 读 location.hash，若是旧格式就 location.replace 到新页面。
 * 返回 true 表示已发起跳转（调用方应停止后续启动）。
 */
export function redirectLegacy() {
  const raw = String(location.hash || '').replace(/^#\/?/, '');
  if (!raw) return false;

  const [path, query = ''] = raw.split('?');
  const segs = path.split('/').filter(Boolean).map(decodeURIComponent);
  const first = segs[0] || '';
  let target = null;

  if (first === 'content') {
    // 新格式旧用法：#content/kg、#content/graph?all、#content/book/12、#content/kg/王阳明
    const view = segs[1];
    const param = segs[2];
    if (view === 'book') {
      target = param ? chapterFile(param) : 'chapter-Preface.html';
    } else if (FILE[view]) {
      target = param ? `${FILE[view]}?focus=${encodeURIComponent(param)}` : FILE[view];
    }
  } else if (/^v\d+$/.test(first)) {
    target = chapterFile(first.slice(1));                   // #v12 → 第 12 卷
  } else if (first === 'all') {
    target = 'graph.html?all=1';                            // #all → 总图全览
  } else if (first.startsWith('kgf')) {
    target = `index.html?focus=${encodeURIComponent(first.slice(3))}`;  // #kgf王阳明
  } else if (FILE[first]) {
    target = segs[1] ? `${FILE[first]}?focus=${encodeURIComponent(segs[1])}` : FILE[first];
  }

  if (!target) return false;
  if (query) target += (target.includes('?') ? '&' : '?') + query;
  location.replace(target);
  return true;
}
