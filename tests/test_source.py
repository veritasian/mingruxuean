#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_source.py —— 架构约束的自动检查

模块化不是把文件拆开就完事了，拆完还得有人守着分层不被慢慢磨平。
这些用例就是那个守门的：

  · 单文件 ≤300 行            —— 明确要求
  · 分层只能自上而下引用        —— view 不许 import controller，engine 谁都不许 import
  · fetch 只许出现在 repository —— 数据入口唯一
  · location.hash 只许出现在 router —— 跳转入口唯一
  · 控制器要的 DOM id 必须在 shell.html 里 —— 防止两边悄悄对不上

规则写死在这里，比写在文档里管用：违反了 CI 直接红。
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import ROOT, check, check_eq, sample, main  # noqa: E402

SRC = ROOT / 'src'
MAX_LINES = 300

# 每层允许 import 的层。engines 是空集合 —— 引擎必须是纯的，谁都不认
ALLOWED = {
    'core': {'core'},
    'engines': set(),
    'data': {'core', 'data'},
    'router': {'core'},
    'views': {'core', 'data', 'engines'},
    'controllers': {'core', 'data', 'engines', 'views', 'router', 'controllers'},
    'pages': {'core', 'data', 'engines', 'views', 'router', 'controllers'},  # 每页入口
    '': {'core', 'data', 'controllers'},          # 顶层入口（如有）
}
RE_IMPORT = re.compile(r"^\s*import\s.*?from\s+['\"]([^'\"]+)['\"]", re.M)


def js_files():
    return sorted(SRC.rglob('*.js'))


def css_files():
    return sorted(SRC.rglob('*.css'))


def layer_of(path):
    rel = path.relative_to(SRC)
    return rel.parts[0] if len(rel.parts) > 1 else ''


def resolve_layer(src_file, spec):
    target = (src_file.parent / spec).resolve()
    try:
        rel = target.relative_to(SRC.resolve())
    except ValueError:
        return '外部'
    return rel.parts[0] if len(rel.parts) > 1 else ''


def test_js_line_limit():
    """每个 JS 文件 ≤300 行"""
    over = ['%s(%d)' % (f.relative_to(ROOT), len(f.read_text(encoding='utf-8').split('\n')))
            for f in js_files() if len(f.read_text(encoding='utf-8').split('\n')) > MAX_LINES]
    check(not over, '超长：%s' % sample(over))
    longest = max(js_files(), key=lambda f: len(f.read_text(encoding='utf-8').split('\n')))
    return '%d 个文件，最长 %s %d 行' % (
        len(js_files()), longest.name, len(longest.read_text(encoding='utf-8').split('\n')))


def test_css_line_limit():
    """每个 CSS 文件 ≤300 行"""
    over = ['%s(%d)' % (f.relative_to(ROOT), len(f.read_text(encoding='utf-8').split('\n')))
            for f in css_files() if len(f.read_text(encoding='utf-8').split('\n')) > MAX_LINES]
    check(not over, '超长：%s' % sample(over))
    longest = max(css_files(), key=lambda f: len(f.read_text(encoding='utf-8').split('\n')))
    return '%d 个文件，最长 %s %d 行' % (
        len(css_files()), longest.name, len(longest.read_text(encoding='utf-8').split('\n')))


def test_layering():
    """分层引用方向不倒挂"""
    bad = []
    for f in js_files():
        layer = layer_of(f)
        allowed = ALLOWED.get(layer)
        if allowed is None:
            bad.append('%s 位于未登记的层' % f.relative_to(SRC))
            continue
        for spec in RE_IMPORT.findall(f.read_text(encoding='utf-8')):
            tgt = resolve_layer(f, spec)
            if tgt not in allowed:
                bad.append('%s → %s' % (f.relative_to(SRC), spec))
    check(not bad, '越层引用：%s' % sample(bad))
    return '%d 个文件方向正确' % len(js_files())


def test_engines_are_pure():
    """引擎不 import 任何东西，也不碰全局 DOM 查询"""
    bad = []
    for f in sorted((SRC / 'engines').glob('*.js')):
        text = f.read_text(encoding='utf-8')
        if RE_IMPORT.search(text):
            bad.append('%s 有 import' % f.name)
        if 'document.querySelector' in text or 'document.getElementById' in text:
            bad.append('%s 自己查 DOM' % f.name)
    check(not bad, '引擎不纯：%s' % sample(bad))
    return '%d 个引擎' % len(list((SRC / 'engines').glob('*.js')))


def test_fetch_only_in_repository():
    """全站只有 repository.js 碰 fetch"""
    bad = [str(f.relative_to(SRC)) for f in js_files()
           if 'fetch(' in f.read_text(encoding='utf-8') and f.name != 'repository.js']
    check(not bad, '越权取数：%s' % sample(bad))
    return '数据入口唯一'


def test_hash_only_in_router():
    """只有 router 直接改 location.hash"""
    ok = {'index.js'}
    bad = [str(f.relative_to(SRC)) for f in js_files()
           if 'location.hash' in f.read_text(encoding='utf-8') and f.name not in ok]
    check(not bad, '绕过路由跳转：%s' % sample(bad))
    return '跳转入口唯一'


def test_views_do_not_hold_state():
    """视图不自己存全局状态（store 只许控制器碰）"""
    bad = [str(f.relative_to(SRC)) for f in sorted((SRC / 'views').glob('*.js'))
           if "core/store.js" in f.read_text(encoding='utf-8')]
    check(not bad, '视图直接读写 store：%s' % sample(bad))
    return '%d 个视图皆无状态' % len(list((SRC / 'views').glob('*.js')))


def test_no_stray_console_log():
    """没有调试用的 console.log 残留"""
    bad = []
    for f in js_files():
        for i, line in enumerate(f.read_text(encoding='utf-8').split('\n'), 1):
            if 'console.log' in line and not line.strip().startswith('//'):
                bad.append('%s:%d' % (f.relative_to(SRC), i))
    check(not bad, '残留：%s' % sample(bad))
    return '干净'


def test_dom_ids_exist_in_shell():
    """控制器要的 #id 必须在 shell.html + 各 section 里"""
    shell = (SRC / 'shell.html').read_text(encoding='utf-8')
    for f in sorted((SRC / 'sections').glob('*.html')):
        shell += '\n' + f.read_text(encoding='utf-8')
    have = set(re.findall(r'id="([^"]+)"', shell))
    # 运行期动态生成的容器，不在骨架里
    dynamic = {'pc'}
    want, bad = set(), []
    for f in js_files():
        for i, line in enumerate(f.read_text(encoding='utf-8').split('\n'), 1):
            for hit in re.findall(r"""\$\(\s*['"]#([A-Za-z][\w-]*)['"]""", line):
                want.add(hit)
                if hit not in have and hit not in dynamic:
                    bad.append('%s:%d #%s' % (f.relative_to(SRC), i, hit))
    check(not bad, '骨架里没有：%s' % sample(bad))
    return '%d 个 id 对得上' % len(want)


def test_css_files_all_bundled():
    """styles/ 下的文件都被页面清单收录，没有漏网"""
    sys.path.insert(0, str(ROOT / 'scripts' / 'build'))
    import bundle as B                                  # noqa: N813
    on_disk = {f.stem for f in css_files()}
    listed = {n for p in B.PAGES for n in p['css']}
    check(not on_disk - listed, '写了却没打包：%s' % sample(on_disk - listed))
    check(not listed - on_disk, '打包清单里有但文件不存在：%s' % sample(listed - on_disk))
    return '%d 份样式全部收录' % len(listed)


def test_shell_has_placeholders():
    """shell.html 保留着全部注入点"""
    shell = (SRC / 'shell.html').read_text(encoding='utf-8')
    for mark in ('<!--STYLES-->', '<!--SCRIPTS-->', '<!--SECTION-->', '<!--SEO-->'):
        check(mark in shell, '缺少注入点 %s' % mark)
    return 'STYLES / SCRIPTS / SECTION / SEO 就位'


def test_every_page_has_entry_and_section():
    """bundle.PAGES 里每个页面：入口模块 + section + 样式齐全"""
    sys.path.insert(0, str(ROOT / 'scripts' / 'build'))
    import bundle as B                                  # noqa: N813
    bad = []
    for p in B.PAGES:
        entry = SRC / p['entry']
        sec = SRC / 'sections' / ('%s.html' % p['id'])
        if not entry.exists():
            bad.append('缺入口 %s' % p['entry'])
        if not sec.exists():
            bad.append('缺 section %s' % p['id'])
    check(not bad, '页面清单与源码对不上：%s' % sample(bad))
    files = sorted({p['file'] for p in B.PAGES})
    check_eq(len(files), len(B.PAGES), '页面文件名重复')
    return '%d 个页面：%s' % (len(B.PAGES), '、'.join(files))


def test_docs_present():
    """四份文档都在，且 README 的目录树跟真实分层对得上"""
    need = ['README.md', 'CHANGELOG.md', 'docs/ARCHITECTURE.md', 'docs/DATA.md']
    missing = [p for p in need if not (ROOT / p).exists()]
    check(not missing, '缺文档：%s' % sample(missing))

    readme = (ROOT / 'README.md').read_text(encoding='utf-8')
    layers = sorted(d.name for d in SRC.iterdir() if d.is_dir())
    absent = [x for x in layers if ('%s/' % x) not in readme]
    check(not absent, 'README 目录树漏了这些层：%s' % sample(absent))

    # CHANGELOG 顶部必须有版本条目，不能只剩个标题
    log = (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8')
    ver = re.search(r'^## \[([\d.]+)\] — (\d{4}-\d{2}-\d{2})', log, re.M)
    check(ver is not None, 'CHANGELOG 缺形如「## [8.0.0] — 2026-08-08」的版本条目')
    return '齐备，最新 v%s（%s）' % (ver.group(1), ver.group(2))


if __name__ == '__main__':
    main(sys.modules[__name__], '源码结构')
