#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bundle.py —— 总装：src/ + data/ + vendor/ → dist/明儒学案.html

产物是一个可以直接双击打开的离线单文件：不连网、不起服务器、
拷给别人也能看。代价是体积，所以正文按卷内联成一张表，
运行时仍然按需取用（repository.js 里的懒加载对内联版一样生效）。

同时产出 index.html（开发版）：走原生 ES module + fetch，
改一个文件刷新即可，不必重新打包。两版共用同一份 src/。

注入顺序有讲究：
  1. d3 v3（力导向图谱依赖，先于业务代码）
  2. window.__MRXA__ 数据（业务代码启动时立刻要读）
  3. 业务代码 bundle
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from esm_bundle import bundle  # noqa: E402

SRC = ROOT / 'src'
DATA = ROOT / 'data'
DIST = ROOT / 'dist'
VENDOR = ROOT / 'vendor'

# 层叠顺序即依赖顺序：变量 → 骨架 → 各视图
CSS_ORDER = ['tokens', 'base', 'graph', 'card', 'roster',
             'timeline', 'geo', 'book', 'kg', 'orphan', 'yangming', 'yangming-quad']
CORE_JSON = ['persons', 'schools', 'relations', 'orphans', 'geo', 'timeline', 'toc']


def read(p):
    return Path(p).read_text(encoding='utf-8')


def collect_css():
    parts = []
    for name in CSS_ORDER:
        f = SRC / 'styles' / ('%s.css' % name)
        if not f.exists():
            raise FileNotFoundError('缺少样式 %s' % f)
        parts.append('/* ===== %s.css ===== */\n%s' % (name, read(f).strip()))
    return '\n\n'.join(parts)


def collect_data():
    """核心 JSON + 卷前三篇 + 63 卷正文 + 阳明心学，压成一行塞进 window.__MRXA__"""
    payload = {}
    for name in CORE_JSON:
        payload[name] = json.loads(read(DATA / ('%s.json' % name)))
    volumes = {}
    for f in sorted((DATA / 'volumes').glob('v*.json')):
        volumes[str(int(f.stem[1:]))] = json.loads(read(f))
    # 卷前篇（原序、发凡、师说）不占卷号，键就是文件名 x1/x2/x3
    for f in sorted((DATA / 'volumes').glob('x*.json')):
        volumes[f.stem] = json.loads(read(f))
    payload['volumes'] = volumes
    payload['yangming'] = json.loads(read(DATA / 'yangming.json'))
    return payload, len(volumes)


def js_literal(payload):
    """
    嵌进 <script> 的 JSON 必须防住 </script> 与行分隔符，
    否则整份文件会在正文里某个字符上突然断掉 —— 排查起来很折磨。
    """
    raw = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    return (raw.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
               .replace('</script', '<\\/script').replace('\u2028', '\\u2028')
               .replace('\u2029', '\\u2029'))


def build_single_file():
    shell = read(SRC / 'shell.html')
    css = collect_css()
    code, order = bundle(SRC / 'app.js', SRC)
    payload, nvol = collect_data()

    d3 = VENDOR / 'd3.v3.min.js'
    if not d3.exists():
        raise FileNotFoundError('缺少 %s，先执行 scripts/build/fetch_vendor.sh' % d3)

    stamp = time.strftime('%Y-%m-%d %H:%M')
    head = ('<style>\n/* 构建于 %s · 源码见 src/styles/ */\n%s\n</style>' % (stamp, css))

    scripts = '\n'.join([
        '<script>/* d3 v3.5.17 · 力导向布局 */\n%s\n</script>' % read(d3),
        '<script>window.__MRXA__ = JSON.parse(`%s`);</script>' % js_literal(payload),
        '<script>\n/* 由 %d 个 ES 模块打包而成 · 源码见 src/ */\n%s\n</script>' % (len(order), code),
    ])

    html = shell.replace('<!--STYLES-->', head).replace('<!--SCRIPTS-->', scripts)
    DIST.mkdir(exist_ok=True)
    out = DIST / '明儒学案.html'
    out.write_text(html, encoding='utf-8')
    return out, len(order), nvol, len(html)


DEV_TPL = """<!-- 开发版：原生 ES module + fetch，改完刷新即可，不必打包。
     必须用本地服务器打开：python3 -m http.server 8080 -->
"""


def build_dev_page():
    shell = read(SRC / 'shell.html')
    links = '\n'.join('<link rel="stylesheet" href="src/styles/%s.css"/>' % n for n in CSS_ORDER)
    scripts = ('<script src="vendor/d3.v3.min.js"></script>\n'
               '<script type="module" src="src/app.js"></script>')
    html = shell.replace('<!--STYLES-->', links).replace('<!--SCRIPTS-->', scripts)
    out = ROOT / 'index.html'
    out.write_text(DEV_TPL + html, encoding='utf-8')
    return out


def main():
    out, nmod, nvol, size = build_single_file()
    dev = build_dev_page()
    print('  单文件  %s' % out.relative_to(ROOT))
    print('          %d 个模块 · %d 卷正文 · %.2f MB' % (nmod, nvol, size / 1048576))
    print('  开发版  %s（需 python3 -m http.server）' % dev.relative_to(ROOT))


if __name__ == '__main__':
    main()
