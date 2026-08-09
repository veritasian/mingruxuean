#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
web_build.py —— 在线版构建器

与 dist/ 离线自包含版并行产出 web/ 在线版：

  · 内容在构建期预渲染到静态 HTML（book 卷文 / yangming 章节 / 人物名录等）
    → 搜索引擎直接可爬，无需 JS 展示内容
  · CSS 外链（web/styles/）→ 浏览器缓存
  · JS 外链（web/js/，esm_bundle 打包）→ 渐进增强：图谱 d3、人物卡、TOC、检索
  · 数据外链（web/data/）→ JS 交互时 fetch，首屏不加载

数据管线（scripts/{ingest,build}）完全不动。
"""
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bundle import PAGES, read, collect_css, js_literal, num_to_words  # noqa: E402
from wikitext_html import to_html as wikitext_to_html  # noqa: E402
from esm_bundle import bundle  # noqa: E402

SRC = ROOT / 'src'
DATA = ROOT / 'data'
WEB = ROOT / 'web'
VENDOR = ROOT / 'vendor'

# 先清理整个 web/，再重新创建目录结构
shutil.rmtree(str(WEB), ignore_errors=True)
(WEB / 'styles').mkdir(parents=True, exist_ok=True)
(WEB / 'js').mkdir(parents=True, exist_ok=True)
(WEB / 'data').mkdir(parents=True, exist_ok=True)


# ===================================================================
# 1. 复制静态资源：CSS + data JSON + vol HTML
# ===================================================================
def copy_assets():
    start = time.time()
    # CSS
    for f in sorted((SRC / 'styles').glob('*.css')):
        shutil.copy2(str(f), str(WEB / 'styles' / f.name))
    # data JSON（含 volumes 子目录）
    for f in sorted(DATA.rglob('*.json')):
        rel = f.relative_to(DATA)
        dst = WEB / 'data' / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(f), str(dst))
    n = len(list(WEB.rglob('*')))
    print('  复制 %d 个静态资源 (%.1fs)'
          % (n, time.time() - start))


# ===================================================================
# 2. 学案原文正文预渲染（wikitext → HTML，只做一次）
# ===================================================================
VOL_HTML = {}  # {vol_key: html_string}

def prerender_volumes():
    start = time.time()
    for f in sorted((DATA / 'volumes').glob('*.json')):
        d = json.loads(f.read_text(encoding='utf-8'))
        html = wikitext_to_html(d.get('text', ''))
        vol_file = (WEB / 'data' / 'volumes_html' / ('%s.html' % f.stem))
        vol_file.parent.mkdir(parents=True, exist_ok=True)
        vol_file.write_text(html, encoding='utf-8')
        # 以构建期字符串形式记下来，后面注入页面用
        VOL_HTML[str(int(f.stem[1:]))] = html
    print('  预渲染 %d 卷正文 · %.1fs'
          % (len(VOL_HTML), time.time() - start))


# ===================================================================
# 3. 阳明心学章节预渲染
# ===================================================================
def yangming_static():
    d = json.loads((DATA / 'yangming.json').read_text(encoding='utf-8'))
    parts = ['<!-- 阳明心学预渲染（JS 增强前也可见） -->',
             '<div class="ym-hero" style="text-align:center;padding:30px 0;">',
             '<h2 style="font-size:1.5em;letter-spacing:.4em;">%s</h2>' % (d.get('subtitle','')),
             '<p style="color:var(--ink-soft)">%s</p>' % (d.get('heroSub','')),
             '</div>']
    if d.get('note'):
        for p in d['note']:
            parts.append('<p>%s</p>' % p.replace('&','&amp;').replace('<','&lt;'))
    parts.append('<div class="ym-chapters">')
    for ch in d.get('chapters', []):
        parts.append('<section id="ym-%s" class="ym-section">'
                     '<h3>%s %s</h3>' % (ch.get('id',''),
                     ch.get('num',''), ch.get('title','')))
        parts.append('<div class="ym-body">%s</div>' % (ch.get('body','')
                     .replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')))
        parts.append('</section>')
    parts.append('</div>')
    return '\n'.join(parts)


# ===================================================================
# 4. 人物名录预渲染
# ===================================================================
def roster_static():
    persons = json.loads((DATA / 'persons.json').read_text(encoding='utf-8'))
    schools = json.loads((DATA / 'schools.json').read_text(encoding='utf-8'))
    parts = ['<div class="roster-list">']
    for s in schools:
        members = s.get('members', [])
        if not members:
            continue
        parts.append('<details class="roster-school">'
                     '<summary>%s（%d 人）</summary>' % (s['id'], len(members)))
        for pid in members:
            p = persons.get(pid)
            if not p:
                continue
            meta = []
            if p.get('zi'):
                meta.append('字' + p['zi'])
            if p.get('hao'):
                meta.append('号' + p['hao'])
            org = p.get('origin', {})
            if org.get('raw'):
                meta.append(org['raw'])
            life = p.get('life', {})
            if life.get('raw'):
                meta.append('生卒 ' + life['raw'])
            parts.append(
                '<div class="person-item" data-id="%s">'
                '<strong>%s</strong>' % (pid, p['name']) +
                ('<span class="person-meta">%s</span>' % ' · '.join(meta) if meta else '') +
                '</div>')
        parts.append('</details>')
    parts.append('</div>')
    return '\n'.join(parts)


# ===================================================================
# 5. 孤点 / 地理预渲染（列表 + 表格）
# ===================================================================
def orphan_static():
    d = json.loads((DATA / 'orphans.json').read_text(encoding='utf-8'))
    parts = ['<div class="orphan-list">']
    kinds = d.get('kinds', {})
    for kid, info in sorted(kinds.items()):
        items = [o for o in d.get('orphans', []) if o.get('kind') == kid]
        if not items:
            continue
        parts.append('<section><h4>%s · %s（%d 人）</h4>' % (
            info.get('label', kid), info.get('note', ''), len(items)))
        for o in items:
            parts.append('<span class="orphan-chip" data-id="%s">%s</span>' % (
                o.get('id', ''), o.get('name', '')))
        parts.append('</section>')
    parts.append('</div>')
    return '\n'.join(parts)


def geo_static():
    geo = json.loads((DATA / 'geo.json').read_text(encoding='utf-8'))
    persons = json.loads((DATA / 'persons.json').read_text(encoding='utf-8'))
    # 按省份分组
    by_prov = {}
    for pid, g in geo.get('places', {}).items():
        p = persons.get(pid)
        if not p:
            continue
        prov = g.get('prov', '不详')
        by_prov.setdefault(prov, []).append((p['name'], g.get('city', ''), g.get('county', '')))
    parts = ['<table class="geo-tbl"><thead><tr><th>省（今）</th><th>人数</th><th>人物·地市</th></tr></thead>']
    for prov, people in sorted(by_prov.items(), key=lambda x: -len(x[1])):
        names = ', '.join('%s（%s）' % (nm, ct) if ct else nm for nm, ct, _ in people[:8])
        more = '… 等 %d 人' % len(people) if len(people) > 8 else ''
        parts.append('<tr><td>%s</td><td>%d</td><td>%s%s</td></tr>' % (
            prov, len(people), names, more))
    parts.append('</table>')
    return '\n'.join(parts)


# ===================================================================
# 6. 生成每个 Web 页面
# ===================================================================
SHELL = """<!DOCTYPE html>
<html lang="zh-Hans" data-theme="zen">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<!--SEO-->
<!--STYLES-->
</head>
<body>
<div class="theme-sw" id="themeSw"></div>
<div class="wrap">
  <header class="banner">
    <div class="seal">学案</div>
    <h1 class="title"><a href="index.html">明儒学案</a></h1>
    <div class="subtitle">师承谱系 · 明代儒林 · 六十三卷学案全文</div>
    <div class="coverage" id="coverage"></div>
    <nav class="tabs" id="menu">
      <a href="index.html" data-page="kg">知识图谱</a>
      <a href="graph.html" data-page="graph">谱系总图</a>
      <a href="roster.html" data-page="roster">人物线索</a>
      <a href="time.html" data-page="time">时间线索</a>
      <a href="geo.html" data-page="geo">地理线索</a>
      <a href="orphan.html" data-page="orphan">孤点现象</a>
      <a href="chapter-Preface.html" data-page="book">学案原文</a>
      <a href="yangming.html" data-page="yangming">阳明心学</a>
    </nav>
  </header>
  <!--SECTION-->
  <footer>明儒学案 · 师承谱系与全文 ｜ 据维基文库（zh.wikisource.org）整理
    ｜ 关系抽取与出处标注见各人物卡「关系出处」</footer>
</div>
<!--SCRIPTS-->
</body>
</html>
"""


def styles_links(spec):
    """外链 <link>（顺序与 CSS_ORDER 一致）"""
    lines = []
    for name in spec['css']:
        lines.append('<link rel="stylesheet" href="/styles/%s.css"/>' % name)
    return '\n'.join(lines)


def section_static(spec):
    """每页的静态预渲染内容（替代原来的 src/sections/*.html）"""
    sid = spec['id']
    bv = spec.get('book_vol')
    if bv:
        # 学案原文页：卷正文直接嵌在 reader-body 里
        vol = bv == 'front' and 'x1' or str(int(bv))
        vol_name = bv == 'front' and 'x1' or bv
        content = VOL_HTML.get(vol_name, '')
        front_tabs = ''
        if bv == 'front':
            # 卷前三个 tab（原序默认激活，正文已嵌）
            x1c = VOL_HTML.get('x1', '')
            x2c = VOL_HTML.get('x2', '')
            x3c = VOL_HTML.get('x3', '')
            front_tabs = (
                '<div class="front-tabs" id="frontTabs">'
                '<button data-p="x1" class="on">原序</button>'
                '<button data-p="x2">发凡</button>'
                '<button data-p="x3">师说</button>'
                '</div>')
            content = x1c  # 默认原序
            # 另外两篇也嵌在 hidden div 里，JS 切换到 tab 时显示
            content += ('<div hidden id="vol-x2">%s</div>' % x2c +
                        '<div hidden id="vol-x3">%s</div>')
        return (
            '<section class="tab on" id="sec-book">\n'
            + '<div class="tab-head">明儒学案 · 六十三卷全文'
            + '<small>左目录 · 右阅读 · 按卷分页 · 卷内检索</small></div>\n'
            + '<div class="book-bar">'
            + '<input class="qi" id="q" placeholder="本卷检索：如「致良知」…"/>'
            + '<button class="btn" id="qBtn">检索</button>'
            + '<button class="btn" id="qClear">清空</button>'
            + '<span class="hint" id="pullStatus">按卷分页 · 离线可读</span></div>\n'
            + '<div id="sres"></div>\n' + front_tabs + '\n'
            + '<div class="book-shell">'
            + '<div class="toc-pane" id="tocPane"></div>'
            + '<div class="reader" id="reader">'
            + '<div class="reader-body">%s</div>' % content
            + '</div></div></section>\n')
    if sid == 'yangming':
        ym = yangming_static()
        return ('<section class="tab on" id="sec-yangming">'
                + '<div id="yangmingRoot">%s</div></section>\n' % ym)
    if sid == 'roster':
        return ('<section class="tab on" id="sec-roster">'
                + '<div class="tab-head">人物总录'
                + '<small>按学案编次，点击人物弹卡</small></div>'
                + '<div id="roster">%s</div></section>\n' % roster_static())
    if sid == 'orphan':
        return ('<section class="tab on" id="sec-orphan">'
                + '<div class="tab-head">孤点现象'
                + '<small>图上不连线的那些点，各有各的来由</small></div>'
                + '<div id="orphanBody">%s</div></section>\n' % orphan_static())
    if sid == 'geo':
        return ('<section class="tab on" id="sec-geo">'
                + '<div class="tab-head">籍贯地理线索'
                + '<small>明代籍贯 → 今省·市对照</small></div>'
                + '<div id="geoBody">%s</div></section>\n' % geo_static())
    if sid == 'time':
        return ('<section class="tab on" id="sec-time">'
                + '<div class="tab-head">时间线索'
                + '<small>洪武 1368 — 崇祯 1644 · 人物按其活动年代落位</small></div>'
                + '<div id="time-chart">'
                + '<p style="text-align:center;color:var(--ink-soft);padding:40px 0">'
                + '时间轴图表由 JavaScript 渲染（d3 力导向）。加载后可交互筛选年号与人物。</p>'
                + '</div></section>\n')
    if sid in ('kg', 'graph'):
        return ('<section class="tab on" id="sec-%s">' % sid
                + '<div class="tab-head">%s'
                % ('知识图谱' if sid == 'kg' else '谱系总图')
                + '<small>%s</small></div>'
                % ('散落态 · 点击人物即聚合其师承 · 可拖拽 · 滚轮缩放'
                   if sid == 'kg' else '拖拽平移 · 滚轮缩放 · 点击人物弹卡')
                + '<svg id="%s" xmlns="http://www.w3.org/2000/svg"></svg></section>\n' % sid)
    # fallback: 读原始 section 文件
    sf = SRC / 'sections' / ('%s.html' % sid)
    if sf.exists():
        return sf.read_text(encoding='utf-8')
    return ''


def seo_block(spec):
    """基础 SEO（seo.py 构建后覆盖为逐页文案）"""
    return ('<!--SEO-->\n<title>%s</title>\n<!--/SEO-->\n' % spec.get('file', ''))


def build_web():
    start = time.time()
    # --- JS bundles（每个页面一个外部 .js，只含交互逻辑） ---
    print('  打包 JS bundles …')
    d3_code = (VENDOR / 'd3.v3.min.js').read_text(encoding='utf-8')
    WEB_ENTRY = {
        'kg': 'pages/web_kg.js',       'graph': 'pages/web_graph.js',
        'roster': 'pages/web_roster.js', 'time': 'pages/web_time.js',
        'geo': 'pages/web_geo.js',     'orphan': 'pages/web_orphan.js',
        'book': 'pages/web_book.js',   'yangming': 'pages/web_yangming.js',
    }
    for spec in PAGES:
        entry = SRC / WEB_ENTRY[spec['id']]
        code, order = bundle(entry, SRC)
        bundle_out = []
        if spec.get('d3'):
            # 知识图谱页需要 d3（全局变量），加到 bundle 前
            bundle_out.append('/* d3 v3.5.17 */\n%s' % d3_code)
        bundle_out.append('/* %d 模块 */\n%s' % (len(order), code))
        js_file = WEB / 'js' / ('%s.js' % spec['file'].replace('.html', ''))
        js_file.parent.mkdir(parents=True, exist_ok=True)
        js_file.write_text('\n'.join(bundle_out), encoding='utf-8')
    # --- HTML pages ---
    print('  生成 HTML 页面 …')
    for spec in PAGES:
        sec = section_static(spec)
        html = (SHELL
                .replace('<!--SEO-->', seo_block(spec))
                .replace('<!--STYLES-->', styles_links(spec))
                .replace('<!--SECTION-->', sec)
                .replace('<!--SCRIPTS-->',
                         '<script src="/js/%s.js" defer></script>'
                         % spec['file'].replace('.html', '')))
        # 菜单高亮（class 在前，更简短的替换）
        menu_file = 'chapter-Preface.html' if spec['id'] == 'book' else spec['file']
        html = html.replace('<a href="%s"' % menu_file,
                            '<a href="%s" class="on"' % menu_file)
        out = WEB / spec['file']
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding='utf-8')
    # 生成旧跳板 book.html
    (WEB / 'book.html').write_text('''<!DOCTYPE html>
<html><head><meta charset=utf-8><meta http-equiv=refresh content="0;url=chapter-Preface.html">
</head><body><a href=chapter-Preface.html>学案原文</a></body></html>''', encoding='utf-8')
    n_pages = len(PAGES)
    total = sum((WEB / spec['file']).stat().st_size for spec in PAGES)
    print('  %d 页 · %.2f MB · (%.1fs)'
          % (n_pages, total / 1048576, time.time() - start))


# ===================================================================
# main
# ===================================================================
def main():
    t0 = time.time()
    print('\n== 在线版 (web/) 构建 %s ==' % time.strftime('%H:%M:%S'))
    copy_assets()
    prerender_volumes()
    build_web()
    print('全部完成 %.1fs' % (time.time() - t0))
    return 0


if __name__ == '__main__':
    sys.exit(main())
