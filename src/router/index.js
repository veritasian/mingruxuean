/**
 * router/index.js —— 多页面站点：只剩旧链接重定向
 *
 * 站点已从「单文件 + 哈希路由」重构为「每分类一个独立页面」，
 * 页面之间用普通 <a href> 互相链接，不再有 #content/ 路由。
 * 这个模块只保留一件事：把旧地址（#content/kg、#v12、#kgf王阳明、
 * #all、#/graph 等）重定向到对应的新页面，保证老书签不 404。
 *
 * 全站只有这里碰 location.hash。
 */
const FILE = {
  kg: 'index.html', graph: 'graph.html', roster: 'roster.html',
  time: 'time.html', geo: 'geo.html', orphan: 'orphan.html',
  book: 'book.html', yangming: 'yangming.html',
};

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
      target = param ? `book.html?v=${encodeURIComponent(param)}` : 'book.html';
    } else if (FILE[view]) {
      target = param ? `${FILE[view]}?focus=${encodeURIComponent(param)}` : FILE[view];
    }
  } else if (/^v\d+$/.test(first)) {
    target = `book.html?v=${first.slice(1)}`;               // #v12 → 第 12 卷
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
