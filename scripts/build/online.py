# -*- coding: utf-8 -*-
"""
online.py —— 在线版构建器（仅线上修正版）

与离线 dist 的关键区别（也是用户要求修掉的三点）：
  1. CSS/JS 外链，不再内联进 <head>/<body>。文件名带内容指纹
     （/styles/<id>.<hash>.css、/js/<id>.<hash>.js），内容相同就是同一个 URL ——
     63 卷正文页共用一套 book 代码，浏览器只下一次，且可长期强缓存。
  2. 数据外链且**全站共用**：/data/ 下 7 份核心 JSON + volumes/ 分卷 + yangming，
     由 repository.js 在运行时按需 fetch。不再把全量 JSON 塞进 window.__MRXA__，
     也不做「按页切片」—— 切片等于把同一批数据在 71 个页面各存一份。
  3. 文本类页（book/roster/orphan/yangming）的正文在构建期预渲染成静态 HTML
     注入容器，爬虫无 JS 也能读到；JS 加载后控制器再增强为交互版。
  可视化页（kg/graph/time/geo 图）由 JS 运行时渲染 SVG，复用与离线一致的
  src/sections/<id>.html 骨架（含工具栏 DOM），geo 额外给 <noscript> 对照表。

产出去向：DIST（vercel.json 的 outputDirectory）。
"""
import hashlib
import json
import re
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bundle import (SRC, DATA, DIST, VENDOR, PAGES, CORE_JSON,  # noqa: E402
                    BOOK_STUB, collect_css, book_pages, lit_pages)
from esm_bundle import bundle                            # noqa: E402
import prerender                                          # noqa: E402

BOOK_VOLS = ['x1', 'x2', 'x3'] + [str(i) for i in range(1, 64)]
RESOURCES = ROOT / 'resources'
LIT_PAGES = lit_pages()


def fingerprint(text):
    return hashlib.sha1(text.encode('utf-8')).hexdigest()[:10]


def write_asset(sub, stem, ext, text, seen):
    """按内容指纹落盘，内容相同复用同一个 URL（返回站点绝对路径）"""
    h = fingerprint(text)
    name = '%s.%s.%s' % (stem, h, ext)
    if name not in seen:
        (DIST / sub / name).write_text(text, encoding='utf-8')
        seen.add(name)
    return '/%s/%s' % (sub, name)


def read(p):
    return Path(p).read_text(encoding='utf-8')


def inject(tag, el_id, inner_html, section):
    """把 <tag id="X">旧</tag> 替换为注入了 inner_html 的版本（X = el_id）"""
    pat = re.compile(r'(<%s[^>]*\bid="%s"[^>]*>)([\s\S]*?)(</%s>)'
                     % (tag, re.escape(el_id), re.escape(tag)), re.I)
    return pat.sub(lambda m: m.group(1) + inner_html + m.group(3), section, count=1)


def book_section(spec):
    sec = read(SRC / 'sections' / 'book.html')
    bv = spec.get('book_vol')
    if bv == 'front':
        vols = {k: json.loads(read(DATA / 'volumes' / ('%s.json' % k))) for k in BOOK_VOLS[:3]}
        body = prerender.book_html(vols['x1'])
        # 卷前 3 篇：默认显示原序，另外两篇藏入 hidden div 供 JS 切 tab
        extra = ('<div hidden id="vol-x2">%s</div><div hidden id="vol-x3">%s</div>'
                 % (prerender.book_html(vols['x2']), prerender.book_html(vols['x3'])))
        body = body + extra
    else:
        key = 'v%02d' % int(bv)
        vol = json.loads(read(DATA / 'volumes' / ('%s.json' % key)))
        body = prerender.book_html(vol)
    sec = inject('div', 'reader', body, sec)  # 注入 #reader
    # TOC 预渲染（导航，SEO 次要但无 JS 也能跳）
    toc = ''.join('<div class="toc-item" data-v="%s">%s</div>'
                  % (k, ('卷前·' + k.upper()) if k in ('x1', 'x2', 'x3')
                     else ('卷%s' % k))
                  for k in BOOK_VOLS)
    sec = inject('div', 'tocPane', toc, sec)  # 注入 #tocPane
    return sec


def text_section(spec):
    sid = spec['id']
    sec = read(SRC / 'sections' / ('%s.html' % sid))
    if sid == 'roster':
        persons = json.loads(read(DATA / 'persons.json'))
        return inject('div', 'roster', prerender.roster_html(persons), sec)
    if sid == 'orphan':
        orph = json.loads(read(DATA / 'orphans.json'))
        return inject('div', 'orphanBody', prerender.orphan_html(orph), sec)
    if sid == 'yangming':
        ym = json.loads(read(DATA / 'yangming.json'))
        return inject('div', 'yangmingRoot', prerender.yangming_html(ym), sec)
    return sec


def geo_section(spec):
    sec = read(SRC / 'sections' / 'geo.html')
    geo = json.loads(read(DATA / 'geo.json'))
    return sec.rstrip() + ('<noscript><div class="geo-noscript">%s</div></noscript>\n'
                           % prerender.geo_html(geo))


def lit_section(spec):
    """心学文献单篇：左栏标题 + 三篇互链 + 目录，右栏正文（均为静态预渲染）"""
    sec = read(SRC / 'sections' / ('%s.html' % spec.get('section', 'literature')))
    body, toc, title = prerender.literature_html(
        RESOURCES / ('literature/%s.md' % spec['lit']))
    # 三篇互链导航（当前篇高亮）：用短名（体用论/功夫论/病药论），菜单只高亮一次
    nav = []
    for lp in LIT_PAGES:
        on = ' on' if lp['file'] == spec['file'] else ''
        nav.append('<a class="lit-nav-item%s" href="%s">%s</a>'
                   % (on, lp['file'], prerender.esc(lp.get('name', lp['title']))))
    sec = inject('h1', 'litTitle', prerender.esc(title), sec)
    sec = inject('nav', 'litNav', ''.join(nav), sec)
    sec = inject('nav', 'litToc', ''.join(toc), sec)
    sec = inject('article', 'litBody', body, sec)
    return sec


def section_html(spec):
    sid = spec['id']
    bv = spec.get('book_vol')
    if bv:
        return book_section(spec)
    if sid in ('kg', 'graph', 'time'):
        return read(SRC / 'sections' / ('%s.html' % sid))
    if sid == 'geo':
        return geo_section(spec)
    if sid in ('roster', 'orphan', 'yangming'):
        return text_section(spec)
    if sid.startswith('lit-'):
        return lit_section(spec)
    return read(SRC / 'sections' / ('%s.html' % sid))


def scripts_html(spec, js_url):
    head = '<script src="/js/d3.v3.min.js"></script>' if spec.get('d3') else ''
    return '%s<script src="%s" defer></script>' % (head, js_url)


def copy_data():
    """全站共用的数据层：核心 7 份 + 63 卷正文 + 阳明专页

    repository.js 的 loadCore / loadVolume / loadYangming 直接 fetch 这些 URL。
    不按页复制 —— 71 个页面共用同一批文件，浏览器缓存才有意义。
    """
    (DIST / 'data' / 'volumes').mkdir(parents=True, exist_ok=True)
    for name in CORE_JSON:
        shutil.copy(DATA / ('%s.json' % name), DIST / 'data' / ('%s.json' % name))
    n_vol = 0
    for vf in sorted((DATA / 'volumes').glob('*.json')):
        shutil.copy(vf, DIST / 'data' / 'volumes' / vf.name)
        n_vol += 1
    if (DATA / 'yangming.json').exists():
        shutil.copy(DATA / 'yangming.json', DIST / 'data' / 'yangming.json')
    return n_vol


def build_online():
    t0 = time.time()
    # 上一版留下的按页切片目录必须清掉，否则 26MB 冗余会跟着一起部署
    shutil.rmtree(DIST / 'data' / 'page', ignore_errors=True)
    for d in ('js', 'styles', 'data'):
        shutil.rmtree(DIST / d, ignore_errors=True)
        (DIST / d).mkdir(parents=True, exist_ok=True)
    # d3 外链（kg 页依赖的全局变量，非模块，单独放）
    d3 = VENDOR / 'd3.v3.min.js'
    if d3.exists():
        shutil.copy(d3, DIST / 'js' / 'd3.v3.min.js')

    shell = read(SRC / 'shell.html')
    seen, n_pages = set(), 0
    for spec in PAGES:
        # 1) CSS / JS 外链，按内容指纹去重（book 的 64 页会落到同一对文件上）
        css_url = write_asset('styles', spec['id'], 'css', collect_css(spec['css']), seen)
        code, order = bundle(SRC / spec['entry'], SRC)
        js_url = write_asset('js', spec['id'], 'js',
                             '/* %d 模块 · 源码见 src/ */\n%s' % (len(order), code), seen)
        # 2) HTML：外链资源 + 预渲染/骨架 section
        scripts = scripts_html(spec, js_url)
        if spec.get('book_vol'):
            bv = spec['book_vol']
            scripts += ('<script>window.__BOOK__ = %s;</script>'
                        % ("'front'" if bv == 'front' else "'%s'" % bv))
        html = (shell
                .replace('<!--SEO-->', '<!--SEO-->\n<title>名儒学案图谱</title>\n<!--/SEO-->')
                .replace('<!--STYLES-->', '<link rel="stylesheet" href="%s"/>' % css_url)
                .replace('<!--SECTION-->', section_html(spec))
                .replace('<!--SCRIPTS-->', scripts))
        # 菜单当前页高亮（构建期注入，避免 JS 接管前闪一下）。
        # 按 data-page 匹配：学案原文 64 页共用 data-page=book；
        # 心学文献 3 页共用 data-page=literature，三页都高亮同一条菜单。
        dp = re.escape(spec.get('data-page', spec['id']))
        html = re.sub(r'(<a href="[^"]*" data-page="%s")>' % dp,
                      r'\1 class="on">', html, count=1)
        (DIST / spec['file']).write_text(html, encoding='utf-8')
        n_pages += 1
    n_vol = copy_data()
    # 旧版跳板：book.html?v=12 → chapter-twelve.html（老书签不失效）。
    # 必须现写，不能指望 dist 里上一次构建留下的那份 —— Vercel 每次都是空目录。
    (DIST / 'book.html').write_text(BOOK_STUB, encoding='utf-8')
    # 站点图标：声明了 <link rel="icon"> 浏览器才不会再去撞 /favicon.ico
    if (SRC / 'favicon.svg').exists():
        shutil.copy(SRC / 'favicon.svg', DIST / 'favicon.svg')
    n_asset = len(seen)
    print('  在线版构建：%d 页 · 静态资源 %d 份（指纹去重）· 共用数据 %d 卷 · %.1fs'
          % (n_pages, n_asset, n_vol, time.time() - t0))


if __name__ == '__main__':
    build_online()
