/**
 * dom.js —— DOM 小工具
 *
 * 没有引入框架，所以把最常用的几个动作收在这里，省得各视图各写一遍
 * createElement + setAttribute + appendChild 的三段式。
 */
const SVGNS = 'http://www.w3.org/2000/svg';

export function $(sel, root = document) {
  return root.querySelector(sel);
}

export function $$(sel, root = document) {
  return [...root.querySelectorAll(sel)];
}

/** el('div.card', {title:'x'}, [child, '文本']) */
export function el(spec, attrs = {}, children = []) {
  const [tag, ...classes] = String(spec).split('.');
  const node = document.createElement(tag || 'div');
  if (classes.length) node.className = classes.join(' ');
  applyAttrs(node, attrs);
  append(node, children);
  return node;
}

export function svg(tag, attrs = {}, children = []) {
  const node = document.createElementNS(SVGNS, tag);
  applyAttrs(node, attrs);
  append(node, children);
  return node;
}

function applyAttrs(node, attrs) {
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k === 'text') node.textContent = v;
    else if (k === 'html') node.innerHTML = v;
    else if (k === 'style' && typeof v === 'object') Object.assign(node.style, v);
    else if (k.startsWith('on') && typeof v === 'function') {
      node.addEventListener(k.slice(2).toLowerCase(), v);
    } else if (k === 'dataset') Object.assign(node.dataset, v);
    else node.setAttribute(k, v === true ? '' : v);
  }
}

function append(node, children) {
  for (const c of [].concat(children)) {
    if (c == null || c === false) continue;
    node.appendChild(typeof c === 'object' ? c : document.createTextNode(String(c)));
  }
}

export function clear(node) {
  while (node && node.firstChild) node.removeChild(node.firstChild);
  return node;
}

export function esc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/** 尺寸变化回调，自动降级到 window.resize */
export function onResize(node, fn) {
  if (typeof ResizeObserver === 'function') {
    const ro = new ResizeObserver(() => fn(node.clientWidth, node.clientHeight));
    ro.observe(node);
    return () => ro.disconnect();
  }
  const h = () => fn(node.clientWidth, node.clientHeight);
  window.addEventListener('resize', h);
  return () => window.removeEventListener('resize', h);
}

export function debounce(fn, ms = 120) {
  let t = null;
  return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
}
