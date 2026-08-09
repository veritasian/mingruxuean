#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_build.py —— 多页面产物体检

打包这一步最容易出的不是崩溃，是「静悄悄地少了点什么」：
占位符没替换、某个页面没被收进去、数据切片串了页、
数据里有个 </script> 把文件截断了。这些错在浏览器里往往只表现为
「某一页空白」，很难往打包上想。所以在这里逐条钉死：

  · 8 个页面都在，体量正常
  · 每页只有自己的 section，其他分类的内容不出现
  · 每页的 __MRXA__ 数据切片正确（volumes 只进 book、yangming 只进阳明页）
  · 每页 title 唯一、description/keywords/canonical/JSON-LD 齐备
  · d3 只进知识图谱页；无外链；无 </script> 截断
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
from bundle import PAGES  # noqa: E402

SRC = ROOT / 'src'
DIST = ROOT / 'dist'
NODE = '/Users/andy/.workbuddy/binaries/node/versions/22.22.2/bin/node'
_html = {}


def html(spec):
    f = DIST / spec['file']
    if spec['file'] not in _html:
        check(f.exists(), '缺产物 %s，先跑 scripts/build/bundle.py' % f)
        _html[spec['file']] = f.read_text(encoding='utf-8')
    return _html[spec['file']]


def data_of(spec):
    h = html(spec)
    m = re.search(r'window\.__MRXA__ = JSON\.parse\(`(.*?)`\);</script>', h, re.S)
    check(m is not None, '%s 找不到 __MRXA__ 数据块' % spec['id'])
    raw = m.group(1).replace('<\\/script', '</script').replace('\\`', '`') \
                    .replace('\\${', '${').replace('\\\\', '\\')
    return json.loads(raw)


def test_pages_built():
    """71 个页面都在，体量正常"""
    big = []
    for spec in PAGES:
        f = DIST / spec['file']
        check(f.exists(), '缺 %s' % spec['file'])
        mb = f.stat().st_size / 1048576
        if not (0.05 < mb < 8.0):
            big.append('%s %.2fMB' % (spec['file'], mb))
    check(not big, '体量异常：%s' % sample(big))
    n_ch = sum(1 for p in PAGES if p.get('book_vol') and p['book_vol'] != 'front')
    return '%d 页（卷前 1 + 正编 %d 卷各 1 页）' % (len(PAGES), n_ch)


def test_placeholders_replaced():
    """注入点都已替换，SEO 块在位"""
    for spec in PAGES:
        h = html(spec)
        for mark in ('<!--STYLES-->', '<!--SCRIPTS-->', '<!--SECTION-->'):
            check(mark not in h, '%s 残留 %s' % (spec['id'], mark))
        check('<style>' in h, '%s 没有内联样式' % spec['id'])
        check('<!--SEO-->' in h and '<!--/SEO-->' in h, '%s 缺 SEO 块' % spec['id'])
    return 'ok'


def test_single_section_per_page():
    """每页只有自己的 section，其他分类的内容不出现"""
    for spec in PAGES:
        h = html(spec)
        check('id="sec-%s"' % spec['id'] in h, '%s 缺自己的 section' % spec['id'])
        check('class="tab on"' in h, '%s section 未点亮' % spec['id'])
        stray = [p['id'] for p in PAGES if p['id'] != spec['id']
                 and ('id="sec-%s"' % p['id']) in h]
        check(not stray, '%s 混入了其他分类：%s' % (spec['id'], sample(stray)))
    return 'ok'


def test_menu_highlight():
    """菜单里当前页链接带 .on，且只有一处（JS 代码里的字符串不算）"""
    pat = re.compile(r'data-page="[^"]+" class="on"')
    for spec in PAGES:
        h = html(spec)
        anchor = 'book/index.html' if spec['id'] == 'book' else spec['file']
        check('<a href="%s" data-page="%s" class="on">' % (anchor, spec['id']) in h,
              '%s 菜单未高亮' % spec['file'])
        check_eq(len(pat.findall(h)), 1, '%s 菜单高亮数量' % spec['file'])
    return 'ok'


def test_data_slices():
    """每页数据切片正确：核心 7 份都在；book 64 页各带本页卷；yangming 只进阳明页"""
    for spec in PAGES:
        d = data_of(spec)
        for k in ('persons', 'schools', 'relations', 'orphans', 'geo', 'timeline', 'toc'):
            check(k in d, '%s 缺核心数据 %s' % (spec['file'], k))
        has_vol = 'volumes' in d
        has_ym = 'yangming' in d
        if spec.get('book_vol'):
            check(has_vol, '%s 缺 volumes' % spec['file'])
            vols = d['volumes']
            if spec['book_vol'] == 'front':
                check_eq(sorted(vols.keys()), ['x1', 'x2', 'x3'], '卷前页应只带 3 篇')
                for k in ('x1', 'x2', 'x3'):
                    check(len(vols[k].get('text', '')) > 500, '卷前 %s 缺失或过短' % k)
            else:
                check_eq(list(vols.keys()), [spec['book_vol']], '卷页应只带本卷')
                check(len(vols[spec['book_vol']].get('text', '')) > 500,
                      '卷 %s 正文缺失' % spec['book_vol'])
        else:
            check(not has_vol, '%s 页不该有 volumes' % spec['file'])
        if spec['id'] == 'yangming':
            check(has_ym and len(d['yangming'].get('chapters', [])) >= 14,
                  'yangming 页数据不全')
        else:
            check(not has_ym, '%s 页不该有 yangming' % spec['file'])
    return '核心 7 份 × 71 页 · book 64 页各带本卷 · yangming→阳明页'


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


def test_d3_only_on_kg():
    """d3 只进知识图谱页（graph 用自研布局，不需要）"""
    for spec in PAGES:
        has = 'd3 v3.5.17' in html(spec)
        if spec['id'] == 'kg':
            check(has, 'kg 页缺 d3')
        else:
            check(not has, '%s 页不该带 d3' % spec['id'])
    return 'ok'


def test_no_external_net():
    """没有任何页面依赖外网资源"""
    for spec in PAGES:
        net = re.findall(r'src="https?://[^"]+"', html(spec))
        check(not net, '%s 仍在联网取资源：%s' % (spec['id'], sample(net)))
    return '离线可用'


def test_no_script_break():
    """数据里的 </script> 已转义，不会把文件截断"""
    for spec in PAGES:
        body = html(spec).split('window.__MRXA__')[1].split('</script>')[0]
        check('</script' not in body, '%s 数据块内出现未转义的 </script>' % spec['id'])
    return 'ok'


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
        probe = [ln.strip() for ln in code.split('\n')
                 if ln.strip().startswith('__def(')]
        stale = [p for p in probe if p not in html(spec)]
        check(not stale, '%s 产物落后于源码，重新跑 bundle.py：%s' % (
            spec['id'], sample(stale, 3)))
    return '一致'


if __name__ == '__main__':
    main(sys.modules[__name__], '打包产物')
