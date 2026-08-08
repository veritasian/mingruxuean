#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_build.py —— 打包产物体检

打包这一步最容易出的不是崩溃，是「静悄悄地少了点什么」：
占位符没替换、某个模块没被收进去、数据里有个 </script> 把文件截断了。
这些错在浏览器里往往只表现为「某一页空白」，很难往打包上想。
所以在这里逐条钉死。
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

SRC = ROOT / 'src'
DIST = ROOT / 'dist' / '明儒学案.html'
NODE = '/Users/andy/.workbuddy/binaries/node/versions/22.22.2/bin/node'
_html = None


def html():
    global _html
    if _html is None:
        check(DIST.exists(), '产物不存在，先跑 scripts/build/bundle.py')
        _html = DIST.read_text(encoding='utf-8')
    return _html


def test_dist_exists():
    """dist 产物存在且体量正常"""
    html()  # 触发存在性检查
    mb = DIST.stat().st_size / 1048576  # 按磁盘字节算，不是字符数
    check(1.0 < mb < 12.0, '体积异常：%.2f MB' % mb)
    return '%.2f MB（单文件离线）' % mb


def test_placeholders_replaced():
    """两个注入点都已被替换"""
    for mark in ('<!--STYLES-->', '<!--SCRIPTS-->'):
        check(mark not in html(), '%s 没被替换' % mark)
    check('<style>' in html(), '没有内联样式')
    return 'ok'


def test_all_modules_included():
    """30 个模块一个不少地进了产物"""
    _, order = bundle(SRC / 'app.js', SRC)
    missing = [m for m in order if ("__def('%s'" % m) not in html()]
    check(not missing, '漏了：%s' % sample(missing))
    return '%d 个模块' % len(order)


def test_all_css_included():
    """每份样式都进了产物"""
    missing = [f.name for f in sorted((SRC / 'styles').glob('*.css'))
               if ('===== %s =====' % f.name) not in html()]
    check(not missing, '漏了：%s' % sample(missing))
    return 'ok'


def test_d3_inlined():
    """d3 内联了，产物不依赖网络"""
    check('d3.layout.force' in html() or 'layout.force' in html(), '找不到 d3 力导向')
    net = re.findall(r'src="https?://[^"]+"', html())
    check(not net, '仍在联网取资源：%s' % sample(net))
    return '离线可用'


def test_data_inlined():
    """七份核心数据 + 卷前三篇 + 63 卷正文 + 阳明心学都在产物里"""
    m = re.search(r'window\.__MRXA__ = JSON\.parse\(`(.*?)`\);</script>', html(), re.S)
    check(m is not None, '找不到 __MRXA__ 数据块')
    raw = m.group(1).replace('<\\/script', '</script').replace('\\`', '`') \
                    .replace('\\${', '${').replace('\\\\', '\\')
    data = json.loads(raw)
    for k in ('persons', 'schools', 'relations', 'orphans', 'geo', 'timeline', 'toc', 'volumes', 'yangming'):
        check(k in data, '缺 %s' % k)
    vols = data['volumes']
    check_eq(len([k for k in vols if k.isdigit()]), 63, '内联卷数')
    # 卷前篇（原序 x1、发凡 x2、师说 x3）另编号，不占 1–63
    for k in ('x1', 'x2', 'x3'):
        check(k in vols and len(vols[k].get('text', '')) > 500, '卷前篇 %s 缺失或过短' % k)
    ym = data['yangming']
    check(len(ym.get('chapters', [])) >= 14, '阳明心学章节不足')
    check(len(ym.get('hero', [])) == 4, '阳明心学四句教缺失')
    return '%d 人 · %d 卷 + 卷前 3 篇 · 阳明心学 %d 章' % (
        len(data['persons']), len(vols) - 3, len(ym.get('chapters', [])))


def test_no_script_break():
    """数据里的 </script> 已被转义，不会把文件截断"""
    body = html().split('window.__MRXA__')[1].split('</script>')[0]
    check('</script' not in body, '数据块内出现未转义的 </script>')
    return 'ok'


def test_bundle_syntax_ok():
    """产物里的业务代码能通过 node 语法检查"""
    code, _ = bundle(SRC / 'app.js', SRC)
    tmp = ROOT / 'dist' / '.syntax-check.js'
    tmp.parent.mkdir(exist_ok=True)
    tmp.write_text(code, encoding='utf-8')
    try:
        r = subprocess.run([NODE, '--check', str(tmp)], capture_output=True, text=True)
        check(r.returncode == 0, r.stderr.strip().split('\n')[0] if r.stderr else '语法错误')
    finally:
        tmp.unlink(missing_ok=True)
    return '%d 字符通过' % len(code)


def test_no_cycles():
    """模块图无环"""
    _, order = bundle(SRC / 'app.js', SRC)      # 有环时 collect() 会直接抛
    return '拓扑序 %d 层' % len(order)


def test_transform_keeps_scope():
    """同名导出不会互相覆盖 —— bus 和 dom 都导出 clear"""
    for name in ('core/bus.js', 'core/dom.js'):
        code, _ = transform(name, (SRC / name).read_text(encoding='utf-8'))
        check('function clear(' in code, '%s 的 clear 没保住' % name)
        check('Object.assign(__exp' in code, '%s 没生成导出' % name)
    return '各自作用域独立'


def test_dev_page_built():
    """开发版 index.html 同步产出，且走的是模块化源码"""
    dev = ROOT / 'index.html'
    check(dev.exists(), 'index.html 不存在')
    t = dev.read_text(encoding='utf-8')
    check('type="module" src="src/app.js"' in t, '没有引用 src/app.js')
    check('src/styles/tokens.css' in t, '没有引用样式')
    check(len(t) < 20000, '开发版不该内联数据（%d 字符）' % len(t))
    return '%.1f KB' % (len(t) / 1024)


def test_dist_and_src_in_sync():
    """产物是用当前源码打的，不是旧的"""
    code, _ = bundle(SRC / 'app.js', SRC)
    probe = [ln.strip() for ln in code.split('\n')
             if ln.strip().startswith('__def(')]
    stale = [p for p in probe if p not in html()]
    check(not stale, '产物落后于源码，重新跑 bundle.py：%s' % sample(stale, 3))
    return '一致'


if __name__ == '__main__':
    main(sys.modules[__name__], '打包产物')
