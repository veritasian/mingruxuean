/**
 * model.js —— 应用级派生模型
 *
 * repository 负责「取回来」，graph-model 负责「算图」，
 * 这里负责把两者拼成视图真正想问的那些问题：
 * 「他老师是谁」「这个学案什么颜色」「他是不是孤点，哪一类孤点」。
 *
 * 视图一律通过它取数，不直接摸 relations 数组 —— 这样以后换数据格式
 * 只要改这一个文件。
 */
import { buildGraph, computeDepth, ancestorsOf, descendantsOf, components } from './graph-model.js';

const PALETTE = [
  '#A23B2E', '#2E6F73', '#7B5EA7', '#B5762A', '#3F7A4E', '#8C3F63',
  '#2F5D8C', '#9A6B2F', '#5B7A2E', '#7A3E3E', '#3E6B8C', '#8C6B3E',
  '#5E4B8C', '#2E7A6B', '#8C4B2E', '#4B5E8C', '#6B8C3E',
];

// 王门六派的头一位是「代表」不是「祖师」——阳明弟子分流出去的支派，
// 顶上那个人并没有开宗立派的身份。
const REPRESENTATIVE = new Set([
  '浙中王门学案', '江右王门学案', '南中王门学案',
  '楚中王门学案', '北方王门学案', '粤闽王门学案',
]);

export function createModel(core) {
  const { persons, personList, schools, relations, orphans, timeline, geo, toc } = core;

  const colors = {};
  schools.forEach((s, i) => { colors[s.id] = PALETTE[i % PALETTE.length]; });

  const members = {};
  schools.forEach((s) => { members[s.id] = s.members.slice(); });

  const founders = new Set();
  schools.forEach((s) => (s.founders || []).forEach((n) => { if (persons[n]) founders.add(n); }));

  const graph = buildGraph(persons, relations);
  const byPerson = new Map();
  for (const r of relations) {
    if (!persons[r.from] || !persons[r.to]) continue;
    push(byPerson, r.from, r);
    push(byPerson, r.to, r);
  }
  for (const list of byPerson.values()) list.sort((a, b) => b.confidence - a.confidence);

  const orphanMap = new Map();
  (orphans.orphans || []).forEach((o) => {
    orphanMap.set(o.id, { ...o, label: (orphans.kinds[o.kind] || {}).label || o.kind });
  });

  const depth = computeDepth(Object.keys(persons), graph.teachers);

  return {
    // 原始层
    persons, personList, schools, relations, toc, timeline, geo,
    orphanData: orphans,
    meta: core.relationMeta,
    // 索引
    colors, members, graph, depth,
    schoolIds: schools.map((s) => s.id),
    // 查询
    colorOf: (s) => colors[s] || '#8a7bbf',
    isFounder: (id) => founders.has(id),
    roleTag: (id) => (REPRESENTATIVE.has(persons[id] && persons[id].school) ? '代表' : '祖'),
    roleBadge: (id) => (REPRESENTATIVE.has(persons[id] && persons[id].school) ? '代表' : '创始人'),
    teachersOf: (id) => graph.teachers.get(id) || [],
    studentsOf: (id) => graph.students.get(id) || [],
    neighborsOf: (id) => graph.adjacency.get(id) || [],
    relationsOf: (id) => byPerson.get(id) || [],
    degreeOf: (id) => graph.degree.get(id) || 0,
    orphanOf: (id) => orphanMap.get(id) || null,
    orphanList: () => [...orphanMap.values()],
    ancestors: (id) => ancestorsOf(id, graph.teachers),
    descendants: (id) => descendantsOf(id, graph.students),
    components: () => components(Object.keys(persons), graph.adjacency),
    periodOf: (id) => (persons[id] && persons[id].period) || null,
    placeOf: (id) => (persons[id] && persons[id].place) || null,
    /**
     * 目录条目：卷前三篇（原序、发凡、师说）排在六十三卷之前，与原书次序一致。
     * 卷前篇的键是 'x1'/'x2'/'x3' 字符串，正编是数字 1–63，两套号不混。
     */
    tocEntries: () => [
      ...(toc.front || []).map((x) => ({ ...x, key: x.id, front: true })),
      ...(toc.volumes || []).map((x) => ({ ...x, key: x.volume, front: false })),
    ],
    volumeInfo: (v) => (toc.volumes || []).find((x) => x.volume === v)
      || (toc.front || []).find((x) => x.id === v)
      || null,
    /** 谱系图/知识图谱共用的边表：只取师承与私淑，附见不画 */
    edgeList: () => relations.filter((r) => r.type !== '附见'
      && persons[r.from] && persons[r.to]),
  };
}

function push(map, k, v) {
  if (!map.has(k)) map.set(k, []);
  map.get(k).push(v);
}
