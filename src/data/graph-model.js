/**
 * graph-model.js —— 从关系表派生图结构
 *
 * relations.json 是一张扁平的边表，图上要用的邻接、师徒、代次、连通分量
 * 都是从它算出来的。这些计算放在数据层算一次，各视图共用，
 * 不要让谱系图和知识图谱各自算一遍还算得不一样。
 */

/** 只取够可信的边；阈值可调，孤点数量会随之变化 */
export function buildGraph(persons, relations, { minConfidence = 0, types = null } = {}) {
  const teachers = new Map();   // 弟子 → [老师]
  const students = new Map();   // 老师 → [弟子]
  const adjacency = new Map();  // 无向邻接
  const edges = [];

  const keep = (r) => r.confidence >= minConfidence
    && (!types || types.includes(r.type))
    && persons[r.from] && persons[r.to];

  for (const r of relations) {
    if (!keep(r)) continue;
    push(teachers, r.from, r.to);
    push(students, r.to, r.from);
    push(adjacency, r.from, r.to);
    push(adjacency, r.to, r.from);
    edges.push(r);
  }

  const degree = new Map();
  for (const [id, ns] of adjacency) degree.set(id, ns.length);
  const orphans = Object.keys(persons).filter((id) => !degree.get(id));

  return { teachers, students, adjacency, edges, degree, orphans };
}

function push(map, k, v) {
  if (!map.has(k)) map.set(k, []);
  const arr = map.get(k);
  if (!arr.includes(v)) arr.push(v);
}

/** 代次：没有老师的算第 0 代。带环保护，古籍里互为师友的情况是有的。 */
export function computeDepth(ids, teachers) {
  const memo = new Map();
  const walk = (id, seen) => {
    if (memo.has(id)) return memo.get(id);
    if (seen.has(id)) return 0;
    seen.add(id);
    const ts = teachers.get(id) || [];
    const d = ts.length ? Math.max(...ts.map((t) => walk(t, seen))) + 1 : 0;
    seen.delete(id);
    memo.set(id, d);
    return d;
  };
  const out = new Map();
  for (const id of ids) out.set(id, walk(id, new Set()));
  return out;
}

/** 上溯全部师承 */
export function ancestorsOf(id, teachers, acc = new Set()) {
  for (const t of teachers.get(id) || []) {
    if (acc.has(t)) continue;
    acc.add(t);
    ancestorsOf(t, teachers, acc);
  }
  return acc;
}

/** 下延全部门人 */
export function descendantsOf(id, students, acc = new Set()) {
  for (const s of students.get(id) || []) {
    if (acc.has(s)) continue;
    acc.add(s);
    descendantsOf(s, students, acc);
  }
  return acc;
}

/** 连通分量：用来看图到底裂成了几块 */
export function components(ids, adjacency) {
  const seen = new Set();
  const out = [];
  for (const id of ids) {
    if (seen.has(id)) continue;
    const group = [];
    const stack = [id];
    seen.add(id);
    while (stack.length) {
      const cur = stack.pop();
      group.push(cur);
      for (const n of adjacency.get(cur) || []) {
        if (seen.has(n)) continue;
        seen.add(n);
        stack.push(n);
      }
    }
    out.push(group);
  }
  return out.sort((a, b) => b.length - a.length);
}

/** 某条边的全部出处，人物卡片要用 */
export function provenanceOf(relations, from, to) {
  const hit = relations.find((r) => r.from === from && r.to === to);
  return hit ? hit.provenance : [];
}
