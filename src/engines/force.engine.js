/**
 * force.engine.js —— 知识图谱力导布局（包一层 D3 v3）
 *
 * 把 d3.layout.force 关在这个文件里。控制器只调用 start/stop/focus/resize，
 * 完全不接触 d3 全局对象 —— 将来要换 d3 v7 或 cytoscape，只改这一个文件。
 *
 * charge 与 linkDistance 随节点数自适应：节点少时松散好看，
 * 节点多时必须收紧，否则会摊成一张糊掉的网。
 */
export function createForce({ nodes, links, width, height, d3 = window.d3 }) {
  if (!d3 || !d3.layout || !d3.layout.force) {
    throw new Error('force.engine 需要 D3 v3（d3.layout.force）');
  }

  const n = nodes.length || 1;
  const charge = -Math.max(120, Math.min(900, 24000 / Math.sqrt(n)));
  const distance = Math.max(28, Math.min(90, 900 / Math.sqrt(n)));

  const sim = d3.layout.force()
    .nodes(nodes)
    .links(links)
    .size([width, height])
    .charge(charge)
    .linkDistance((l) => distance * (l.weak ? 1.35 : 1))
    .linkStrength((l) => (l.weak ? 0.25 : 0.7))
    .gravity(0.09)
    .friction(0.9);

  const api = {
    sim,
    start() { sim.start(); return api; },
    stop() { sim.stop(); return api; },
    /** 拖动结束后钉住，免得辛苦看清的结构又被弹走 */
    drag(onDragStart) {
      const behavior = sim.drag()
        .on('dragstart', (d) => {
          d.fixed = true;
          if (onDragStart) onDragStart(d);
        });
      return behavior;
    },
    resize(w, h) {
      sim.size([w, h]);
      sim.start();
      return api;
    },
    /** 把某个节点拽到中心并钉住，用于「聚焦此人」 */
    focus(node, cx, cy) {
      nodes.forEach((d) => { d.fixed = false; });
      if (!node) { sim.resume(); return api; }
      node.x = cx; node.y = cy;
      node.px = cx; node.py = cy;
      node.fixed = true;
      sim.alpha(0.35);
      return api;
    },
    onTick(fn) { sim.on('tick', fn); return api; },
    onEnd(fn) { sim.on('end', fn); return api; },
    destroy() { sim.on('tick', null); sim.on('end', null); sim.stop(); },
  };
  return api;
}

/** 邻接表：高亮时判断两点是否直连 */
export function adjacencyOf(links) {
  const adj = new Map();
  for (const l of links) {
    const a = l.source.id || l.source;
    const b = l.target.id || l.target;
    if (!adj.has(a)) adj.set(a, new Set());
    if (!adj.has(b)) adj.set(b, new Set());
    adj.get(a).add(b);
    adj.get(b).add(a);
  }
  return adj;
}
