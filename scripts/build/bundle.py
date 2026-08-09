#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bundle.py —— 多页面构建器：src/ + data/ + vendor/ → dist/ 71 个页面

站点是「一分类一页面」的菜单结构，每个页面只带自己的内容：

  index.html      知识图谱（默认首页，唯一 d3 力导向页）
  graph.html      谱系总图（自研 tree-layout）
  roster.html     人物线索
  time.html       时间线索
  geo.html        地理线索
  orphan.html     孤点现象
  book/           学案原文：按卷分页，64 页
    index.html          卷前一篇（原序/发凡/师说，页内三个 tab）
    chapter-one.html …  63 卷各一页（chapter-sixty-three.html），
                        每页只内联本卷正文，加载快、互不影响
  yangming.html   阳明心学

每页只内联：
  · 本页的 CSS（tokens + base + 本视图样式 + 人物卡）
  · 本页的 JS（core + model/repository + 本页控制器与视图，由入口模块可达图决定）
  · 本页需要的数据切片（核心 7 份 + 额外项；yangming 仅阳明页）
  · d3 仅 kg 页
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

CORE_JSON = ['persons', 'schools', 'relations', 'orphans', 'geo', 'timeline', 'toc']

_ONES = ['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
_TEENS = ['ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen',
          'seventeen', 'eighteen', 'nineteen']
_TENS = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty']


def num_to_words(n):
    """1–63 → one … sixty-three（学案原文卷页文件名）"""
    if n < 10:
        return _ONES[n]
    if n < 20:
        return _TEENS[n - 10]
    t, o = n // 10, n % 10
    return '%s%s' % (_TENS[t], '-%s' % _ONES[o] if o else '')


def book_pages():
    """学案原文 64 页：卷前一篇（3 tab）+ 63 卷各一页"""
    css = ['tokens', 'base', 'book', 'card']
    pages = [{
        'id': 'book', 'file': 'book/index.html', 'css': css,
        'entry': 'pages/book.js', 'extra_data': ['volumes'], 'book_vol': 'front',
    }]
    for i in range(1, 64):
        pages.append({
            'id': 'book', 'file': 'book/chapter-%s.html' % num_to_words(i),
            'css': css, 'entry': 'pages/book.js',
            'extra_data': ['volumes'], 'book_vol': str(i),
        })
    return pages


# 页面清单：7 个分类 + 学案原文 64 页（css 按层叠顺序）
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
    {'id': 'yangming', 'file': 'yangming.html',
     'css': ['tokens', 'base', 'yangming', 'yangming-quad'],
     'entry': 'pages/yangming.js', 'extra_data': ['yangming']},
] + book_pages()


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


def collect_data(extra, book_vol=None):
    """核心 7 份 + 本页额外项（volumes / yangming），压成一行塞进 window.__MRXA__

    book 页按卷切片：卷前页只带 x1/x2/x3，卷 N 页只带第 N 卷正文。
    """
    payload = {}
    for name in CORE_JSON:
        payload[name] = json.loads(read(DATA / ('%s.json' % name)))
    if 'volumes' in extra:
        volumes = {}
        if book_vol == 'front':
            for k in ('x1', 'x2', 'x3'):
                volumes[k] = json.loads(read(DATA / 'volumes' / ('%s.json' % k)))
        else:
            key = 'v%02d' % int(book_vol)
            volumes[book_vol] = json.loads(read(DATA / 'volumes' / ('%s.json' % key)))
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
    payload = collect_data(spec.get('extra_data', []), spec.get('book_vol'))

    stamp = time.strftime('%Y-%m-%d %H:%M')
    head = '<style>\n/* 构建于 %s · 本页样式见 src/styles/ */\n%s\n</style>' % (stamp, css)

    scripts = []
    if spec.get('d3'):
        d3 = VENDOR / 'd3.v3.min.js'
        if not d3.exists():
            raise FileNotFoundError('缺少 %s，先执行 scripts/build/fetch_vendor.sh' % d3)
        scripts.append('<script>/* d3 v3.5.17 · 力导向布局 */\n%s\n</script>' % read(d3))
    scripts.append('<script>window.__MRXA__ = JSON.parse(`%s`);</script>' % js_literal(payload))
    if spec.get('book_vol'):
        # 学案原文页：告诉控制器「本页是哪一篇」（front 或卷号字符串）
        scripts.append('<script>window.__BOOK__ = %s;</script>'
                       % ('"front"' if spec['book_vol'] == 'front' else "'%s'" % spec['book_vol']))
    scripts.append('<script>\n/* 由 %d 个 ES 模块打包而成 · 源码见 src/ */\n%s\n</script>'
                   % (len(order), code))

    html = (shell
            .replace('<!--SEO-->', '<!--SEO-->\n<title>名儒学案图谱</title>\n<!--/SEO-->')
            .replace('<!--STYLES-->', head)
            .replace('<!--SECTION-->', section)
            .replace('<!--SCRIPTS-->', '\n'.join(scripts)))
    # 菜单里当前页高亮（构建期注入，避免 JS 闪烁）。
    # 学案原文 64 页共用同一条菜单锚点（book/index.html），用 id 定位。
    menu_file = 'book/index.html' if spec['id'] == 'book' else spec['file']
    html = html.replace('<a href="%s" data-page="%s">'
                        % (menu_file, spec['id']),
                        '<a href="%s" data-page="%s" class="on">'
                        % (menu_file, spec['id']))
    out = DIST / spec['file']
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding='utf-8')
    return out, len(order), len(html)


# 旧版单文件 book.html 的跳板：读到 ?v= 就跳到对应卷页，否则进卷前篇页。
# 不留新结构的副本，只当 404 兜底，让老书签（book.html?v=12）不失效。
BOOK_STUB = """<!DOCTYPE html>
<html lang="zh-Hans">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<meta name="robots" content="noindex"/>
<title>学案原文 · 名儒学案图谱</title>
<script>
(function () {
  var w = ['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine'];
  var teens = ['ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen',
    'seventeen', 'eighteen', 'nineteen'];
  var tens = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty'];
  function words(n) {
    if (n < 10) return w[n];
    if (n < 20) return teens[n - 10];
    var o = n % 10;
    return tens[Math.floor(n / 10)] + (o ? '-' + w[o] : '');
  }
  var m = location.search.match(/[?&]v=([^&]+)/);
  if (!m) { location.replace('book/index.html'); return; }
  var v = decodeURIComponent(m[1]);
  if (/^\\d+$/.test(v)) { location.replace('book/chapter-' + words(+v) + '.html'); return; }
  if (v === 'x1' || v === 'x2' || v === 'x3') { location.replace('book/index.html?p=' + v); return; }
  location.replace('book/index.html');
})();
</script>
</head>
<body></body>
</html>
"""


def main():
    DIST.mkdir(exist_ok=True)
    total = 0
    for spec in PAGES:
        out, nmod, size = build_page(spec)
        total += size
        print('  %-13s %s（%d 模块 · %.2f MB）'
              % (spec['id'], out.relative_to(DIST), nmod, size / 1048576))
    (DIST / 'book.html').write_text(BOOK_STUB, encoding='utf-8')   # 旧书签跳板
    print('  book.html     旧版单文件跳板（→ book/ 分页）')
    print('  共 %d 页 · %.2f MB' % (len(PAGES), total / 1048576))


if __name__ == '__main__':
    main()
