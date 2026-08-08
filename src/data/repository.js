/**
 * repository.js —— 唯一的数据入口
 *
 * 全站只有这里碰 fetch。视图和控制器要数据就问它，不自己去拿。
 * 好处很实际：单文件打包版把 JSON 内联进了 window.__MRXA__，
 * 开发版走 fetch，两种形态的差异被挡在这一层里，上面完全无感。
 *
 * 63 卷正文按卷懒加载 —— 一次性塞 2.8MB 进内存没有必要，
 * 读者一次只看一卷。
 */
const BASE = (typeof window !== 'undefined' && window.__MRXA_BASE__) || './data/';
const INLINE = (typeof window !== 'undefined' && window.__MRXA__) || null;

const cache = new Map();
const CORE = ['persons', 'schools', 'relations', 'orphans', 'geo', 'timeline', 'toc'];

async function loadJSON(name) {
  if (cache.has(name)) return cache.get(name);
  if (INLINE && INLINE[name]) {
    cache.set(name, INLINE[name]);
    return INLINE[name];
  }
  const res = await fetch(`${BASE}${name}.json`);
  if (!res.ok) throw new Error(`加载 ${name}.json 失败：${res.status}`);
  const json = await res.json();
  cache.set(name, json);
  return json;
}

/** 一次把核心数据取齐，避免各视图各自触发一轮请求 */
export async function loadCore() {
  const parts = await Promise.all(CORE.map(loadJSON));
  const bundle = {};
  CORE.forEach((k, i) => { bundle[k] = parts[i]; });
  return normalize(bundle);
}

function normalize(b) {
  const persons = b.persons;
  const relations = b.relations.relations || b.relations;
  // 学案 → 成员，成员表已按原书出场顺序排好，这里不再重排
  const schools = b.schools;
  const bySchool = new Map(schools.map((s) => [s.id, s]));
  const personList = Object.values(persons);

  // 生卒/籍贯挂回人物上，视图就不用到处 join
  const period = b.timeline.period || {};
  const places = b.geo.places || {};
  for (const p of personList) {
    p.period = period[p.id] || null;
    p.place = places[p.id] || null;
  }

  return {
    persons,
    personList,
    schools,
    bySchool,
    relations,
    relationMeta: b.relations.meta || {},
    orphans: b.orphans,
    geo: b.geo,
    timeline: b.timeline,
    toc: b.toc,
  };
}

/**
 * 单卷正文，按需取，取过就留着。
 * v 是数字（1–63 正编，文件 v01…v63）或字符串（卷前篇 x1/x2，文件同名）。
 */
export async function loadVolume(v) {
  const numeric = /^\d+$/.test(String(v));
  const key = numeric ? `volumes/v${String(v).padStart(2, '0')}` : `volumes/${v}`;
  if (cache.has(key)) return cache.get(key);
  if (INLINE && INLINE.volumes && INLINE.volumes[v]) {
    cache.set(key, INLINE.volumes[v]);
    return INLINE.volumes[v];
  }
  const res = await fetch(`${BASE}${key}.json`);
  if (!res.ok) throw new Error(`加载 ${numeric ? `第 ${v} 卷` : v} 失败：${res.status}`);
  const json = await res.json();
  cache.set(key, json);
  return json;
}

export function peek(name) {
  return cache.get(name) || null;
}

/** 阳明心学专页内容（整体内联，不分卷） */
export async function loadYangming() {
  return loadJSON('yangming');
}
