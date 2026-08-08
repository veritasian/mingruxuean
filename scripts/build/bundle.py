#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bundle.py —— 多页面构建器：src/ + data/ + vendor/ → dist/ 8 个页面

站点是「一分类一页面」的菜单结构，每个页面只带自己的内容：

  index.html      知识图谱（默认首页，唯一 d3 力导向页）
  graph.html      谱系总图（d3 纵向树）
  roster.html     人物线索
  time.html       时间线索
  geo.html        地理线索
  orphan.html     孤点现象
  book.html       学案原文（唯一内联 volumes 的页，体量最大）
  yangming.html   阳明心学

每页只内联：
  · 本页的 CSS（tokens + base + 本视图样式 + 人物卡）
  · 本页的 JS（core + model/repository + 本页控制器与视图，由入口模块可达图决定）
  · 本页需要的数据切片（核心 7 份 + 额外项；volumes 仅 book、yangming 仅阳明页）
  · d3 仅 kg / graph 两页
页面之间用普通 <a> 链接，旧的 #content/ 哈希由 src/router 重定向。
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

# 页面清单：css 按层叠顺序（变量 → 骨架 → 视图），data 为基础 7 份 + extra_data
PAGES = [
    {'id': 'kg',       'file': 'index.html', 'd3': True,
     'css': ['tokens', 'base', 'kg', 'card'], 'entry': 'pages/kg.js', 'extra_data': []},
    {'id': 'graph',    'file': 'graph.html',
     'css': ['tokens', 'base', 'graph', 'card'], 'entry': 'pages/graph.js', 'extra_data': []},
    {'id': 'roster',   'file': 'roster.html',
     'css': ['tokens', 'base', 'roster', 'card'], 'entry': 'pages/roster.js', 'extra_data': []},
    {'id': 'time',     'file': 'time.html',
     'css': ['tokens', 'base', 'timeline', 'card'], 'entry': 'pages/time.js', 'extra_data': []},
    {'id': 'geo',      'file': 'geo.html',
     'css': ['tokens', 'base', 'geo', 'card'], 'entry': 'pages/geo.js', 'extra_data': []},
    {'id': 'orphan',   'file': 'orphan.html',
     'css': ['tokens', 'base', 'orphan', 'card'], 'entry': 'pages/orphan.js', 'extra_data': []},
    {'id': 'book',     'file': 'book.html',
     'css': ['tokens', 'base', 'book', 'card'], 'entry': 'pages/book.js', 'extra_data': ['volumes']},
    {'id': 'yangming', 'file': 'yangming.html',
     'css': ['tokens', 'base', 'yangming', 'yangming-quad'],
     'entry': 'pages/yangming.js', 'extra_data': ['yangming']},
]
CORE_JSON = ['persons', 'schools', 'relations', 'orphans', 'geo', 'timeline', 'toc']


def read(p):
    return Path(p).read_text(encoding='utf-8')


def collect_css(names):
    parts = []
    for name in names:
        f = SRC / 'styles' / ('%s.css' % name)
        if not f.exists():
            raise FileNotFoundError('缺少样式 %s' % f)
        parts.append('/* ===== %s.css ===== */\n%s' % (name, read(f).strip()))
    return '\n\n'.join(parts)


def collect_data(extra):
    """核心 7 份 + 本页额外项（volumes / yangming），压成一行塞进 window.__MRXA__"""
    payload = {}
    for name in CORE_JSON:
        payload[name] = json.loads(read(DATA / ('%s.json' % name)))
    if 'volumes' in extra:
        volumes = {}
        for f in sorted((DATA / 'volumes').glob('v*.json')):
            volumes[str(int(f.stem[1:]))] = json.loads(read(f))
        # 卷前篇（原序、发凡、师说）不占卷号，键就是文件名 x1/x2/x3
        for f in sorted((DATA / 'volumes').glob('x*.json')):
            volumes[f.stem] = json.loads(read(f))
        payload['volumes'] = volumes
    if 'yangming' in extra:
        payload['yangming'] = json.loads(read(DATA / 'yangming.json'))
    return payload


def js_literal(payload):
    """嵌进 <script> 的 JSON 必须防住 </script> 与行分隔符"""
    raw = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    return (raw.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
               .replace('</script', '<\\/script').replace('\u2028', '\\u2028')
               .replace('\u2029', '\\u2029'))


def build_page(spec):
    shell = read(SRC / 'shell.html')
    section = read(SRC / 'sections' / ('%s.html' % spec['id']))
    css = collect_css(spec['css'])
    code, order = bundle(SRC / spec['entry'], SRC)
    payload = collect_data(spec.get('extra_data', []))

    stamp = time.strftime('%Y-%m-%d %H:%M')
    head = '<style>\n/* 构建于 %s · 本页样式见 src/styles/ */\n%s\n</style>' % (stamp, css)

    scripts = []
    if spec.get('d3'):
        d3 = VENDOR / 'd3.v3.min.js'
        if not d3.exists():
            raise FileNotFoundError('缺少 %s，先执行 scripts/build/fetch_vendor.sh' % d3)
        scripts.append('<script>/* d3 v3.5.17 · 力导向布局 */\n%s\n</script>' % read(d3))
    scripts.append('<script>window.__MRXA__ = JSON.parse(`%s`);</script>' % js_literal(payload))
    scripts.append('<script>\n/* 由 %d 个 ES 模块打包而成 · 源码见 src/ */\n%s\n</script>'
                   % (len(order), code))

    html = (shell
            .replace('<!--SEO-->', '<!--SEO-->\n<title>名儒学案图谱</title>\n<!--/SEO-->')
            .replace('<!--STYLES-->', head)
            .replace('<!--SECTION-->', section)
            .replace('<!--SCRIPTS-->', '\n'.join(scripts)))
    # 菜单里当前页高亮（构建期注入，避免 JS 闪烁）
    html = html.replace('<a href="%s" data-page="%s">'
                        % (spec['file'], spec['id']),
                        '<a href="%s" data-page="%s" class="on">'
                        % (spec['file'], spec['id']))
    out = DIST / spec['file']
    out.write_text(html, encoding='utf-8')
    return out, len(order), len(html)


def main():
    DIST.mkdir(exist_ok=True)
    total = 0
    for spec in PAGES:
        out, nmod, size = build_page(spec)
        total += size
        print('  %-13s %s（%d 模块 · %.2f MB）'
              % (spec['id'], out.name, nmod, size / 1048576))
    print('  共 %d 页 · %.2f MB' % (len(PAGES), total / 1048576))


if __name__ == '__main__':
    main()
