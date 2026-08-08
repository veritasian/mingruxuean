/**
 * tree-layout.engine.js —— 谱系图布局（纯计算，不碰 DOM）
 *
 * 一个学案一列，列内自上而下排人。之所以自己算而不用 d3.tree：
 * 这张图不是树，一个人可以有多位老师（王道同时学于甘泉与阳明），
 * d3.tree 只接受严格树形，喂进去会丢边。
 *
 * 排序有两档：
 *   book  —— 依《明儒学案》原书出场次序（黄宗羲已按辈分编次，最稳）
 *   depth —— 依算出来的师承代次，同代内再按原书次序
 * 两者都不会把列撑宽 —— 列宽固定，视觉上「一列即一学案」这条读图
 * 约定才立得住。
 *
 * 输出 Map<id,{x,y}>，视图拿坐标去画；换布局算法不必动视图。
 */
export const DEFAULTS = {
  colWidth: 168,
  rowHeight: 40,
  top: 46,
  left: 74,
  gutter: 28,
};

/**
 * @param {object} opt
 *   schools  [{id, members:[id]}]  按原书顺序
 *   depth    Map<id, number>       代次
 *   order    'book' | 'depth'
 *   filter   (id) => boolean
 */
export function layout({ schools, depth, order = 'book', filter = () => true, metrics = {} }) {
  const m = { ...DEFAULTS, ...metrics };
  const pos = new Map();
  const columns = [];
  let col = 0;
  let maxRows = 0;

  for (const school of schools) {
    const members = school.members.filter(filter);
    if (!members.length) continue;

    const ordered = order === 'depth' ? sortByDepth(members, depth) : members.slice();
    const x = m.left + col * m.colWidth + m.colWidth / 2;
    ordered.forEach((id, row) => {
      pos.set(id, { x, y: m.top + row * m.rowHeight, col, row, depth: depth.get(id) || 0, school: school.id });
    });
    columns.push({ id: school.id, x, col, count: ordered.length });
    maxRows = Math.max(maxRows, ordered.length);
    col += 1;
  }

  return {
    pos,
    columns,
    width: m.left + col * m.colWidth + m.gutter,
    height: m.top + maxRows * m.rowHeight + m.rowHeight,
    metrics: m,
  };
}

/** 同代次的保持原书先后，不要因为排序把黄宗羲的编次打乱 */
function sortByDepth(members, depth) {
  return members
    .map((id, i) => ({ id, i, d: depth.get(id) || 0 }))
    .sort((a, b) => (a.d - b.d) || (a.i - b.i))
    .map((x) => x.id);
}

export function bounds(pos, pad = 30) {
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const p of pos.values()) {
    minX = Math.min(minX, p.x); maxX = Math.max(maxX, p.x);
    minY = Math.min(minY, p.y); maxY = Math.max(maxY, p.y);
  }
  if (!Number.isFinite(minX)) return { minX: 0, minY: 0, maxX: 1, maxY: 1 };
  // 右侧留得多一些，人名是画在圆点右边的
  return { minX: minX - pad, minY: minY - pad, maxX: maxX + pad * 3, maxY: maxY + pad };
}

export function boundsOf(pos, ids, pad = 30) {
  const sub = new Map();
  ids.forEach((id) => { if (pos.has(id)) sub.set(id, pos.get(id)); });
  return bounds(sub, pad);
}

/** 贝塞尔连线：竖直方向的师承线，弯一点比直线好认 */
export function edgePath(a, b) {
  if (!a || !b) return '';
  const midY = (a.y + b.y) / 2;
  return `M${a.x},${a.y} C${a.x},${midY} ${b.x},${midY} ${b.x},${b.y}`;
}
