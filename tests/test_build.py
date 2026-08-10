#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_build.py —— 多页面产物体检（在线版）

打包这一步最容易出的不是崩溃，是「静悄悄地少了点什么」：
占位符没替换、某个页面没被收进去、外链指纹对不上、
数据目录里躺着上一版的冗余副本。这些错在浏览器里往往只表现为
「某一页空白」或「首屏特别慢」，很难往打包上想。所以在这里逐条钉死：

  · 71 个页面都在，体量正常（HTML 只装结构与正文，样式脚本数据全外链）
  · 每页只有自己的 section，其他分类的内容不出现
  · CSS/JS 外链且带内容指纹，内容相同的页面共用同一个 URL（63 卷共一套）
  · 数据层全站共用 /data/，不存在按页切片的副本
  · 文本类页正文已预渲染进 HTML，无 JS、爬虫也读得到
  · 每页 title 唯一、description/keywords/canonical/JSON-LD 齐备
  · d3 只进知识图谱页（外链 /js/d3.v3.min.js）；无外网资源；无大块内联脚本
"""
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts' / 'build'))
from harness import ROOT, check, check_eq, sample, main  # noqa: E402
from esm_bundle import bundle, transform  # noqa: E402
from bundle import PAGES, CORE_JSON  # noqa: E402

SRC = ROOT / 'src'
DIST = ROOT / 'dist'
NODE = '/Users/andy/.workbuddy/binaries/node/versions/22.22.2/bin/node'
_html = {}

ASSET_PAT = {
    'js': re.compile(r'<script src="(/js/[^"]+\.js)" defer>'),
    'css': re.compile(r'<link rel="stylesheet" href="(/styles/[^"]+\.css)"'),
}
FINGERPRINT = re.compile(r'^[a-z0-9-]+\.[0-9a-f]{10}\.(?:js|css)$')
# 内联脚本里只允许留 window.__BOOK__ 这类一行开关，JSON-LD 由 SEO 块负责
INLINE_JS = re.compile(r'<script(?![^>]*\bsrc=)(?![^>]*ld\+json)[^>]*>([\s\S]*?)</script>')


def html(spec):
    f = DIST / spec['file']
    if spec['file'] not in _html:
        check(f.exists(), '缺产物 %s，先跑 scripts/build/online.py' % f)
        _html[spec['file']] = f.read_text(encoding='utf-8')
    return _html[spec['file']]


def asset_url(spec, kind):
    """页面头尾外链的那个 /js/*.js 或 /styles/*.css"""
    m = ASSET_PAT[kind].search(html(spec))
    check(m is not None, '%s 没有外链 %s' % (spec['id'], kind))
    return m.group(1)


def asset_text(spec, kind):
    f = DIST / asset_url(spec, kind).lstrip('/')
    check(f.exists(), '%s 外链的 %s 不在盘上' % (spec['id'], f))
    return f.read_text(encoding='utf-8')


def test_pages_built():
    """71 个页面都在，体量正常（在线版 HTML 只装结构与正文）"""
    odd = []
    for spec in PAGES:
        f = DIST / spec['file']
        check(f.exists(), '缺 %s' % spec['file'])
        kb = f.stat().st_size / 1024
        if not (1.5 < kb < 400):
            odd.append('%s %.1fKB' % (spec['file'], kb))
    check(not odd, '体量异常：%s' % sample(odd))
    n_ch = sum(1 for p in PAGES if p.get('book_vol') and p['book_vol'] != 'front')
    total = sum((DIST / p['file']).stat().st_size for p in PAGES) / 1048576
    return '%d 页（卷前 1 + 正编 %d 卷各 1 页）· HTML 合计 %.1fMB' % (
        len(PAGES), n_ch, total)


def test_placeholders_replaced():
    """注入点都已替换，样式走外链，SEO 块在位"""
    for spec in PAGES:
        h = html(spec)
        for mark in ('<!--STYLES-->', '<!--SCRIPTS-->', '<!--SECTION-->'):
            check(mark not in h, '%s 残留 %s' % (spec['id'], mark))
        check('<style>' not in h, '%s 仍在 <head> 内联样式' % spec['id'])
        check('<link rel="stylesheet"' in h, '%s 没有外链样式' % spec['id'])
        check('<!--SEO-->' in h and '<!--/SEO-->' in h, '%s 缺 SEO 块' % spec['id'])
    return '样式外链 · SEO 块齐'


def test_assets_fingerprinted():
    """CSS/JS 带内容指纹；内容相同的页面共用同一个 URL，且没有孤儿产物"""
    book_js = set()
    for kind, sub in (('js', 'js'), ('css', 'styles')):
        used = set()
        for spec in PAGES:
            url = asset_url(spec, kind)
            name = url.rsplit('/', 1)[1]
            check(FINGERPRINT.match(name) is not None,
                  '%s 的 %s 没带内容指纹：%s' % (spec['id'], kind, name))
            check((DIST / url.lstrip('/')).exists(), '%s 外链 %s 不存在' % (spec['id'], url))
            used.add(name)
            if kind == 'js' and spec.get('book_vol'):
                book_js.add(url)
        on_disk = {p.name for p in (DIST / sub).glob('*.' + kind)} - {'d3.v3.min.js'}
        orphan = on_disk - used
        check(not orphan, '%s 目录有没人引用的旧产物：%s' % (sub, sample(sorted(orphan))))
    check_eq(len(book_js), 1, '64 个卷页应共用同一份 book.js')
    n_book = sum(1 for p in PAGES if p.get('book_vol'))
    return '8 套 js + 8 套 css 覆盖 %d 页（%d 个卷页共用一套）' % (len(PAGES), n_book)


def test_shared_data_layer():
    """数据层全站共用 /data/，没有按页切片的副本"""
    check(not (DIST / 'data' / 'page').exists(),
          '存在按页切片目录 dist/data/page —— 同一批核心数据会被复制 %d 份' % len(PAGES))
    for name in CORE_JSON:
        f = DIST / 'data' / ('%s.json' % name)
        check(f.exists(), '缺核心数据 %s' % f)
        json.loads(f.read_text(encoding='utf-8'))
    vols = {p.stem for p in (DIST / 'data' / 'volumes').glob('*.json')}
    check_eq(len(vols), 66, '分卷数量（卷前 3 + 正编 63）')
    for spec in PAGES:
        bv = spec.get('book_vol')
        if not bv:
            continue
        keys = ['x1', 'x2', 'x3'] if bv == 'front' else ['v%02d' % int(bv)]
        for k in keys:
            check(k in vols, '%s 依赖的 %s.json 不在数据层' % (spec['file'], k))
            text = json.loads((DIST / 'data' / 'volumes' / ('%s.json' % k))
                              .read_text(encoding='utf-8')).get('text', '')
            check(len(text) > 500, '卷 %s 正文缺失或过短' % k)
    ym = json.loads((DIST / 'data' / 'yangming.json').read_text(encoding='utf-8'))
    check(len(ym.get('chapters', [])) >= 14, 'yangming 数据不全')
    mb = sum(f.stat().st_size for f in (DIST / 'data').rglob('*.json')) / 1048576
    return '核心 %d 份 + 分卷 66 + 阳明 1 · 全站共用 %.1fMB' % (len(CORE_JSON), mb)


def test_prerendered_body():
    """文本类页正文已在 HTML 里，无 JS、爬虫也读得到"""
    def text_len(h, marker):
        seg = h.split(marker, 1)
        check(len(seg) == 2, '缺容器 %s' % marker)
        body = re.sub(r'<[^>]+>', '', seg[1][:200000])
        return len(body.strip())

    checked = 0
    for spec in PAGES:
        h = html(spec)
        if spec.get('book_vol'):
            check(text_len(h, 'id="reader"') > 500, '%s 正文未预渲染' % spec['file'])
        elif spec['id'] == 'roster':
            check(text_len(h, 'id="roster"') > 2000, 'roster 名录未预渲染')
        elif spec['id'] == 'orphan':
            check(text_len(h, 'id="orphanBody"') > 500, 'orphan 正文未预渲染')
        elif spec['id'] == 'yangming':
            check(text_len(h, 'id="yangmingRoot"') > 1000, 'yangming 正文未预渲染')
        elif spec['id'] == 'geo':
            check('geo-noscript' in h, 'geo 缺 <noscript> 对照表')
        else:
            continue
        checked += 1
    return '%d 页带静态正文（可视化页由 JS 现画，geo 另给 noscript）' % checked


def test_single_section_per_page():
    """每页只有自己的 section，其他分类的内容不出现（心学文献 3 篇共用 sec-literature）"""
    for spec in PAGES:
        h = html(spec)
        secid = spec.get('section', spec['id'])
        check('id="sec-%s"' % secid in h, '%s 缺自己的 section' % spec['id'])
        check('class="tab on"' in h, '%s section 未点亮' % spec['id'])
        stray = [p['id'] for p in PAGES if p.get('section', p['id']) != secid
                 and ('id="sec-%s"' % p.get('section', p['id'])) in h]
        check(not stray, '%s 混入了其他分类：%s' % (spec['id'], sample(stray)))
    return 'ok'


def test_menu_highlight():
    """菜单里当前页链接带 .on，且只有一处（JS 代码里的字符串不算）

    共享分类（学案原文 64 页 / 心学文献 3 篇）的菜单指向该分类首页，
    而非当前页文件；高亮按 data-page 匹配，三页都高亮同一条菜单。"""
    pat = re.compile(r'data-page="[^"]+" class="on"')
    for spec in PAGES:
        h = html(spec)
        dp = spec.get('data-page', spec['id'])
        anchor = ('chapter-Preface.html' if dp == 'book'
                  else 'lit-tiyong.html' if dp == 'literature'
                  else spec['file'])
        check('<a href="%s" data-page="%s" class="on">' % (anchor, dp) in h,
              '%s 菜单未高亮' % spec['file'])
        check_eq(len(pat.findall(h)), 1, '%s 菜单高亮数量' % spec['file'])
    return 'ok'


def test_seo_per_page():
    """每页 title 唯一，description/keywords/canonical/JSON-LD 齐备"""
    titles = []
    for spec in PAGES:
        h = html(spec)
        t = re.search(r'<title>(.*?)</title>', h, re.S)
        check(t is not None and len(t.group(1).strip()) > 8, '%s 缺 title' % spec['id'])
        titles.append(t.group(1))
        for meta in ('name="description"', 'name="keywords"', 'rel="canonical"',
                     'application/ld+json', 'og:title'):
            check(meta in h, '%s 缺 %s' % (spec['id'], meta))
    check_eq(len(set(titles)), len(titles), 'title 有重复')
    return '%d 页 SEO 独立' % len(titles)


def test_sitemap_and_robots():
    """sitemap 收全 71 页，robots 指向它（卷 2–63 只在页内目录里链着，靠这个才被抓全）"""
    sm = DIST / 'sitemap.xml'
    check(sm.exists(), '缺 sitemap.xml')
    import xml.etree.ElementTree as ET
    root = ET.parse(sm).getroot()
    ns = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
    locs = [u.findtext(ns + 'loc') for u in root.findall(ns + 'url')]
    check_eq(len(locs), len(PAGES), 'sitemap 条目数')
    listed = {u.rsplit('/', 1)[1] for u in locs}
    missing = {p['file'] for p in PAGES} - listed
    check(not missing, 'sitemap 漏了：%s' % sample(sorted(missing)))
    rb = DIST / 'robots.txt'
    check(rb.exists(), '缺 robots.txt')
    txt = rb.read_text(encoding='utf-8')
    check('Sitemap: ' in txt and 'sitemap.xml' in txt, 'robots.txt 未声明 sitemap')
    check('Disallow: /book.html' in txt, 'book.html 是跳板，不该进索引')
    return 'sitemap %d 条 · robots 已声明' % len(locs)


def test_d3_only_on_kg():
    """d3 只进知识图谱页（graph 用自研布局，不需要）"""
    for spec in PAGES:
        has = '/js/d3.v3.min.js' in html(spec)
        if spec['id'] == 'kg':
            check(has, 'kg 页缺 d3')
        else:
            check(not has, '%s 页不该带 d3' % spec['id'])
    check((DIST / 'js' / 'd3.v3.min.js').exists(), 'd3 产物不在')
    return 'ok'


def test_no_external_net():
    """没有任何页面依赖外网资源（canonical / og:url 是声明，不算加载）"""
    for spec in PAGES:
        h = html(spec)
        net = re.findall(r'src="https?://[^"]+"', h)
        net += re.findall(r'<link rel="stylesheet"[^>]*href="https?://[^"]+"', h)
        check(not net, '%s 仍在联网取资源：%s' % (spec['id'], sample(net)))
    return '资源全部同源'


def test_no_inline_data():
    """HTML 不再用 <script> 搬运数据，只剩一行页面开关"""
    for spec in PAGES:
        h = html(spec)
        check('window.__MRXA__' not in h, '%s 仍在内联全量数据' % spec['id'])
        big = [s.strip() for s in INLINE_JS.findall(h) if len(s.strip()) > 120]
        check(not big, '%s 仍有大块内联脚本（%d 字符）'
              % (spec['id'], len(big[0]) if big else 0))
    return '内联脚本仅 window.__BOOK__ 一行'


def test_bundle_syntax_ok():
    """每个页面入口打出来的业务代码能通过 node 语法检查"""
    tmp = ROOT / 'dist' / '.syntax-check.js'
    tmp.parent.mkdir(exist_ok=True)
    try:
        for spec in PAGES:
            code, _ = bundle(SRC / spec['entry'], SRC)
            tmp.write_text(code, encoding='utf-8')
            r = subprocess.run([NODE, '--check', str(tmp)], capture_output=True, text=True)
            check(r.returncode == 0, '%s 语法错误：%s' % (
                spec['id'], r.stderr.strip().split('\n')[0] if r.stderr else '未知'))
    finally:
        tmp.unlink(missing_ok=True)
    return '%d 页入口全部通过' % len(PAGES)


def test_no_cycles():
    """每个页面入口的模块图无环"""
    for spec in PAGES:
        bundle(SRC / spec['entry'], SRC)      # 有环时 collect() 会直接抛
    return 'ok'


def test_transform_keeps_scope():
    """同名导出不会互相覆盖 —— bus 和 dom 都导出 clear"""
    for name in ('core/bus.js', 'core/dom.js'):
        code, _ = transform(name, (SRC / name).read_text(encoding='utf-8'))
        check('function clear(' in code, '%s 的 clear 没保住' % name)
        check('Object.assign(__exp' in code, '%s 没生成导出' % name)
    return '各自作用域独立'


def test_dist_and_src_in_sync():
    """产物是用当前源码打的，不是旧的"""
    for spec in PAGES:
        code, _ = bundle(SRC / spec['entry'], SRC)
        js = asset_text(spec, 'js')
        probe = [ln.strip() for ln in code.split('\n')
                 if ln.strip().startswith('__def(')]
        stale = [p for p in probe if p not in js]
        check(not stale, '%s 产物落后于源码，重新跑 online.py：%s' % (
            spec['id'], sample(stale, 3)))
    return '一致'


if __name__ == '__main__':
    main(sys.modules[__name__], '打包产物')
