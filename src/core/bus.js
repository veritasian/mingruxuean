/**
 * bus.js —— 事件总线
 *
 * 各层之间只通过事件说话，不互相持有引用。这是「改一处不炸另一处」的前提：
 * 控制器不知道有哪些视图在听，视图也不用知道是谁触发了它。
 */
const channels = new Map();

export function on(event, fn) {
  if (!channels.has(event)) channels.set(event, new Set());
  channels.get(event).add(fn);
  return () => off(event, fn);
}

export function once(event, fn) {
  const un = on(event, (...a) => { un(); fn(...a); });
  return un;
}

export function off(event, fn) {
  const s = channels.get(event);
  if (s) s.delete(fn);
}

export function emit(event, payload) {
  const s = channels.get(event);
  if (!s) return;
  // 复制一份再遍历：回调里可能会 off 掉自己
  for (const fn of [...s]) {
    try {
      fn(payload);
    } catch (err) {
      console.error(`[bus] ${event} 处理出错`, err);
    }
  }
}

export function clear(event) {
  if (event) channels.delete(event);
  else channels.clear();
}

/** 约定的事件名集中在这里，避免各处手写字符串拼错 */
export const EV = {
  ROUTE_CHANGED: 'route:changed',
  DATA_READY: 'data:ready',
  PERSON_SELECTED: 'person:selected',
  PERSON_CLEARED: 'person:cleared',
  SCHOOL_FOCUSED: 'school:focused',
  THEME_CHANGED: 'theme:changed',
  VIEWPORT_RESIZED: 'viewport:resized',
  VOLUME_OPENED: 'volume:opened',
  SEARCH_SUBMITTED: 'search:submitted',
};
