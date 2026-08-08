/**
 * store.js —— 全局状态
 *
 * 只放「跨视图共享」的东西：当前路由、选中人物、聚焦学案、主题。
 * 单个视图自己的状态（滚动位置、折叠与否）留在各自控制器里，不往这儿塞，
 * 否则这里很快就会变成第二个大杂烩。
 */
import { emit, EV } from './bus.js';

const state = {
  route: 'graph',
  selectedPerson: null,
  focusedSchool: null,
  theme: 'zen',
  data: null,
};

const PERSIST_KEYS = ['theme'];
const LS_PREFIX = 'mrxa.';

export function get(key) {
  return key ? state[key] : { ...state };
}

export function set(key, value, { silent = false } = {}) {
  if (state[key] === value) return value;
  state[key] = value;
  if (PERSIST_KEYS.includes(key)) {
    try { localStorage.setItem(LS_PREFIX + key, JSON.stringify(value)); } catch (e) { /* 隐私模式下会抛 */ }
  }
  if (!silent) emit(`state:${key}`, value);
  return value;
}

export function restore() {
  for (const k of PERSIST_KEYS) {
    try {
      const raw = localStorage.getItem(LS_PREFIX + k);
      if (raw != null) state[k] = JSON.parse(raw);
    } catch (e) { /* 忽略坏值 */ }
  }
}

export function selectPerson(id) {
  set('selectedPerson', id);
  emit(id ? EV.PERSON_SELECTED : EV.PERSON_CLEARED, id);
}

export function focusSchool(school) {
  set('focusedSchool', school);
  emit(EV.SCHOOL_FOCUSED, school);
}
