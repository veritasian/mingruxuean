/**
 * router/index.js —— 哈希路由
 *
 * 地址栏就是应用状态的唯一书面记录。谁想跳转就调 go()，
 * 谁想知道现在在哪就听 ROUTE_CHANGED —— 视图之间不用互相调用
 * 「你先关掉我再打开」这种命令式代码。
 *
 * 形如：#content/graph          总图
 *       #content/book/12       学案原文第 12 卷
 *       #content/kg/王阳明     知识图谱聚焦某人
 *       #content/graph?all     带修饰符
 * 旧式 #/graph 仍可解析（兼容旧书签），但新生成的链接一律走 #content/ 前缀。
 */
import { emit, EV } from '../core/bus.js';
import * as store from '../core/store.js';

const DEFAULT = 'kg';
const PREFIX = 'content';
let routes = [];
let current = null;
let started = false;

/** 注册一条路由。pattern 只认第一段，参数由 parse 交给控制器自己解释 */
export function register(name, { title = '', onEnter, onLeave } = {}) {
  routes.push({ name, title, onEnter, onLeave });
  return () => { routes = routes.filter((r) => r.name !== name); };
}

export function parse(hash) {
  const raw = String(hash || '').replace(/^#\/?/, '');
  if (!raw) return { name: DEFAULT, params: [], query: '' };
  const [path, query = ''] = raw.split('?');
  let segs = path.split('/').filter(Boolean).map(decodeURIComponent);
  // 新格式 #content/<view>；兼容旧格式 #/<view>
  if (segs[0] === PREFIX) segs = segs.slice(1);
  return { name: segs[0] || DEFAULT, params: segs.slice(1), query };
}

export function stringify({ name, params = [], query = '' }) {
  const tail = params.length ? `/${params.map(encodeURIComponent).join('/')}` : '';
  return `#${PREFIX}/${name}${tail}${query ? `?${query}` : ''}`;
}

/** 跳转。replace=true 时不留历史记录，适合视图内部的状态同步 */
export function go(name, params = [], { query = '', replace = false } = {}) {
  const target = stringify({ name, params, query });
  if (location.hash === target) { dispatch(); return; }
  if (replace) history.replaceState(null, '', target);
  else location.hash = target;
  if (replace) dispatch();
}

export function currentRoute() {
  return current;
}

function known(name) {
  return routes.some((r) => r.name === name);
}

function dispatch() {
  const next = parse(location.hash);
  if (!known(next.name)) next.name = DEFAULT;

  const changedView = !current || current.name !== next.name;
  if (changedView && current) {
    const prev = routes.find((r) => r.name === current.name);
    if (prev && prev.onLeave) prev.onLeave(current);
  }

  current = next;
  store.set('route', next.name);

  const hit = routes.find((r) => r.name === next.name);
  if (hit) {
    if (hit.title) document.title = `${hit.title} · 明儒学案`;
    if (hit.onEnter) hit.onEnter(next, { changedView });
  }
  emit(EV.ROUTE_CHANGED, { ...next, changedView });
}

export function start() {
  if (started) return;
  started = true;
  window.addEventListener('hashchange', dispatch);
  if (!location.hash) history.replaceState(null, '', stringify({ name: DEFAULT }));
  dispatch();
}

/** 兼容旧版链接：#kg / #v12 / #kg王阳明 / #all / #graph */
export function migrateLegacyHash() {
  const h = String(location.hash || '').replace(/^#/, '');
  // 新格式 #content/<view> 与旧格式 #/<view> 都由 parse 处理，不在这里改写
  if (!h || h.startsWith('/') || h.startsWith(`${PREFIX}/`)) return;
  let target = null;
  if (/^v\d+$/.test(h)) target = stringify({ name: 'book', params: [h.slice(1)] });
  else if (h.startsWith('kgf')) target = stringify({ name: 'kg', params: [decodeURIComponent(h.slice(3))] });
  else if (h === 'all') target = stringify({ name: 'graph', query: 'all' });
  else target = stringify({ name: h });
  history.replaceState(null, '', target);
}
