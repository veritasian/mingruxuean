#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
esm_bundle.py —— 把一组 ES module 打成单个 <script> 能跑的代码

为什么不上 rollup/esbuild：
  这套源码只用了最规矩的四种语法（具名 import / namespace import /
  export function|const|class / 无默认导出、无动态 import），
  为它引一整条 node 工具链不划算，也会让「打开就能构建」这件事变难。
  这里做的事很窄：给每个模块套一个函数作用域，把 import 换成 __req()，
  把 export 收集成一次 Object.assign。窄，所以可靠。

刻意保留的行为：
  - 每个模块独立作用域 —— core/bus.js 和 core/dom.js 都导出 clear，不会打架
  - 保留原始行内容与顺序 —— 出错时浏览器行号仍能对上源文件（模块内相对）
  - 发现循环依赖直接报错 —— 与其运行期拿到 undefined，不如构建期就停
"""
import re
import sys
from pathlib import Path

RUNTIME = """\
(function () {
'use strict';
var __M = Object.create(null);
function __def(id, fn) { __M[id] = { fn: fn, exports: null, running: false }; }
function __req(id) {
  var m = __M[id];
  if (!m) throw new Error('[bundle] 缺少模块：' + id);
  if (m.exports) return m.exports;
  m.exports = {};
  m.fn(m.exports, __req);
  return m.exports;
}
"""

RE_NS = re.compile(r"^import\s+\*\s+as\s+([A-Za-z_$][\w$]*)\s+from\s+['\"]([^'\"]+)['\"];?\s*$")
RE_NAMED = re.compile(r"^import\s*\{([^}]*)\}\s*from\s*['\"]([^'\"]+)['\"];?\s*$", re.S)
RE_DEFAULT = re.compile(r"^import\s+([A-Za-z_$][\w$]*)\s*,?\s*(?:\{([^}]*)\})?\s*from\s*['\"]([^'\"]+)['\"];?\s*$", re.S)
RE_BARE = re.compile(r"^import\s+['\"]([^'\"]+)['\"];?\s*$")

RE_EXP_DECL = re.compile(r"^export\s+(async\s+function|function|const|let|var|class)\s+([A-Za-z_$][\w$]*)")
RE_EXP_LIST = re.compile(r"^export\s*\{([^}]*)\}\s*;?\s*$")
RE_EXP_DEFAULT = re.compile(r"^export\s+default\s+")


def _named_pairs(body):
    """`a, b as c` -> [('a','a'), ('b','c')]"""
    out = []
    for piece in body.split(','):
        piece = piece.strip()
        if not piece:
            continue
        if ' as ' in piece:
            src, dst = [x.strip() for x in piece.split(' as ', 1)]
        else:
            src = dst = piece
        out.append((src, dst))
    return out


def _norm(base, spec):
    """'../core/bus.js' 相对 'views/' -> 'core/bus.js'"""
    parts = [p for p in base.parts if p != '.']
    for seg in spec.split('/'):
        if seg in ('', '.'):
            continue
        if seg == '..':
            if parts:
                parts.pop()
        else:
            parts.append(seg)
    return '/'.join(parts)


def transform(mod_id, source):
    """单个模块：改写 import/export，返回 (代码体, 依赖列表)"""
    deps, exports, out = [], [], []
    for raw in source.split('\n'):
        line = raw.rstrip('\r')
        stripped = line.strip()

        m = RE_NS.match(stripped)
        if m:
            dep = _norm(Path(mod_id).parent, m.group(2))
            deps.append(dep)
            out.append("const %s = __req(%r);" % (m.group(1), dep))
            continue

        m = RE_NAMED.match(stripped)
        if m:
            dep = _norm(Path(mod_id).parent, m.group(2))
            deps.append(dep)
            binds = ', '.join('%s: %s' % (s, d) if s != d else s
                              for s, d in _named_pairs(m.group(1)))
            out.append("const { %s } = __req(%r);" % (binds, dep))
            continue

        m = RE_BARE.match(stripped)
        if m:
            dep = _norm(Path(mod_id).parent, m.group(1))
            deps.append(dep)
            out.append("__req(%r);" % dep)
            continue

        if stripped.startswith('import ') and ' from ' in stripped:
            m = RE_DEFAULT.match(stripped)
            if m:
                dep = _norm(Path(mod_id).parent, m.group(3))
                deps.append(dep)
                out.append("const __ns_%d = __req(%r);" % (len(deps), dep))
                out.append("const %s = __ns_%d.default;" % (m.group(1), len(deps)))
                if m.group(2):
                    binds = ', '.join('%s: %s' % (s, d) if s != d else s
                                      for s, d in _named_pairs(m.group(2)))
                    out.append("const { %s } = __ns_%d;" % (binds, len(deps)))
                continue
            raise SyntaxError('%s: 无法识别的 import —— %s' % (mod_id, stripped))

        m = RE_EXP_DECL.match(stripped)
        if m:
            exports.append(m.group(2))
            out.append(line.replace('export ', '', 1))
            continue

        m = RE_EXP_LIST.match(stripped)
        if m:
            for src, dst in _named_pairs(m.group(1)):
                exports.append('%s: %s' % (dst, src) if src != dst else src)
            continue

        if RE_EXP_DEFAULT.match(stripped):
            exports.append('default: __default')
            out.append(RE_EXP_DEFAULT.sub('const __default = ', line, count=1))
            continue

        if stripped.startswith('export '):
            raise SyntaxError('%s: 无法识别的 export —— %s' % (mod_id, stripped))

        out.append(line)

    if exports:
        out.append('Object.assign(__exp, { %s });' % ', '.join(exports))
    return '\n'.join(out), deps


def collect(entry_path, root):
    """从入口出发抓全图，顺带查环"""
    root = Path(root)
    entry_id = str(Path(entry_path).relative_to(root))
    mods, order, state = {}, [], {}

    def visit(mod_id, trail):
        if state.get(mod_id) == 'done':
            return
        if state.get(mod_id) == 'visiting':
            raise RuntimeError('循环依赖：%s' % ' -> '.join(trail + [mod_id]))
        state[mod_id] = 'visiting'
        f = root / mod_id
        if not f.exists():
            raise FileNotFoundError('%s 找不到（被 %s 引用）' % (mod_id, trail[-1] if trail else '入口'))
        code, deps = transform(mod_id, f.read_text(encoding='utf-8'))
        mods[mod_id] = code
        for d in deps:
            visit(d, trail + [mod_id])
        state[mod_id] = 'done'
        order.append(mod_id)

    visit(entry_id, [])
    return entry_id, order, mods


def bundle(entry_path, root):
    entry_id, order, mods = collect(entry_path, root)
    chunks = [RUNTIME]
    for mod_id in order:
        chunks.append("__def(%r, function (__exp, __req) {\n/* ---- %s ---- */\n%s\n});\n"
                      % (mod_id, mod_id, mods[mod_id]))
    chunks.append("__req(%r);\n})();\n" % entry_id)
    return '\n'.join(chunks), order


if __name__ == '__main__':
    root = Path(sys.argv[1] if len(sys.argv) > 1 else 'src')
    code, order = bundle(root / 'app.js', root)
    sys.stderr.write('模块 %d 个，%d 字符\n' % (len(order), len(code)))
    sys.stdout.write(code)
