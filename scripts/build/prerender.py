# -*- coding: utf-8 -*-
"""
prerender.py —— 构建期把数据预渲染成静态 HTML 正文（SEO + 无 JS 可读）

仅文本类页需要预渲染（book / roster / orphan / yangming / geo 表）。
可视化页（kg / graph / time / geo 图）由 JS 运行时渲染 SVG，无法预渲染，
只给 <noscript> 兜底（见 online.py）。

wikitext_to_html 与前端 src/data/wikitext.js 的 toHTML 保持同逻辑：
先剥模板/脚注/表格，再转标题/诗行/粗斜体，顺序反了会把标签自己转掉。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data'

_H = '\x01H\x01'
_POEM_A = '\x01P\x01'
_POEM_B = '\x01/P\x01'


def esc(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))


# 原创研究权利声明（阳明心学 + 心学文献三篇），构建期注入页脚。
# 与 RESEARCH-LICENSE.md 一致：作者原创学术研究，依 CC BY-NC 4.0 授权。
_YM_RIGHTS_DEFAULT = ('原创学术研究 · CC BY-NC 4.0 —— 本页（阳明心学）由 Andy'
                     '（keniskey@gmail.com）原创撰写。依知识共享「署名—非商业性使用'
                     ' 4.0 国际」许可发布：允许非商业性引用、复制与改编，须注明作者'
                     '与来源；禁止商业用途（含商业性 AI 训练）。'
                     '详见仓库 RESEARCH-LICENSE.md。')
_LIT_RIGHTS_TEXT = ('本文为作者原创研究文字，依 CC BY-NC 4.0 许可授权 —— 由 Andy'
                   '（keniskey@gmail.com）撰写。允许非商业性引用、复制与改编，须注明'
                   '作者与来源；禁止商业用途（含商业性 AI 训练）。'
                   '详见仓库 RESEARCH-LICENSE.md。')


def rights_footer_html(text, cls='ym-rights', label='原创学术研究 · CC BY-NC 4.0'):
    """统一的「CC BY-NC 4.0」页脚（阳明/文献共用），返回静态 HTML 片段。"""
    return ('<footer class="%s"><span class="%s-tag">%s</span>'
            '<p class="%s-text">%s</p></footer>'
            % (cls, cls, esc(label), cls, esc(text)))


def wikitext_to_html(src):
    """移植 src/data/wikitext.js 的 toHTML（纯文本 → 语义化 HTML）"""
    s = str(src or '')
    s = re.sub(r'<!--[\s\S]*?-->', '', s)
    s = re.sub(r'<ref[\s\S]*?</ref>', '', s)
    s = re.sub(r'<ref[^>]*?/>', '', s)
    s = re.sub(r'</?(only|no|)include(only)?>', '', s, flags=re.I)
    s = re.sub(r'\{\|[\s\S]*?\|\}', '', s)
    for _ in range(8):
        nxt = re.sub(r'\{\{[^{}]*\}\}', '', s)
        if nxt == s:
            break
        s = nxt
    s = re.sub(r'\[\[(File|Image|文件|图像|圖像|Category|分类|分類|作者|Author):[\s\S]*?\]\]', '', s, flags=re.I)
    s = re.sub(r'\[\[([^[\]|]*)\|([^[\]]*)\]\]', r'\2', s)
    s = re.sub(r'\[\[([^[\]]*)\]\]', r'\1', s)
    s = re.sub(r'^(={2,4})\s*(.*?)\s*\1\s*$', r'\n%s\2\n' % _H, s, flags=re.M)
    s = re.sub(r'<poem>([\s\S]*?)</poem>', lambda m: '\n%s%s\n%s\n' % (_POEM_A, m.group(1), _POEM_B), s)
    s = esc(s)
    s = re.sub(r"'''''([^']+)'''''", r'<b><i>\1</i></b>', s)
    s = re.sub(r"'''([^']+)'''", r'<b>\1</b>', s)
    s = re.sub(r"''([^']+)''", r'<i>\1</i>', s)
    out = []
    in_poem = False
    for raw in re.split(r'\n+', s):
        line = raw.strip()
        if not line:
            continue
        if line.startswith(_POEM_A):
            out.append('<div class="poem">')
            in_poem = True
            continue
        if line.startswith(_POEM_B):
            out.append('</div>')
            in_poem = False
            continue
        if line.startswith(_H):
            out.append('<h4>%s</h4>' % line[len(_H):])
            continue
        out.append(('%s<br/>' % line) if in_poem else '<p class="par">%s</p>' % line)
    if in_poem:
        out.append('</div>')
    return '\n'.join(out)


def book_html(volume_json):
    """一卷正文 → reader-body 静态 HTML（卷前 3 篇同构，x1/x2/x3 各传入一次）"""
    try:
        d = volume_json if isinstance(volume_json, dict) else json.loads(volume_json)
    except Exception:
        return ''
    name = d.get('name') or ('卷%s' % d.get('volume', '?'))
    body = wikitext_to_html(d.get('text', ''))
    head = ('<div class="reader-head"><h3>%s</h3></div>' % esc(name))
    return '%s<div class="reader-body">%s</div>' % (head, body)


def roster_html(persons):
    """人物按学案（school）编次，列出姓名与字号 —— 爬虫直接读到名录"""
    groups = {}
    for name, p in (persons.items() if isinstance(persons, dict) else []):
        school = p.get('school') or '其他'
        groups.setdefault(school, []).append(p)
    parts = []
    for school in sorted(groups):
        items = sorted(groups[school], key=lambda x: x.get('seq', 0))
        parts.append('<section class="roster-group"><h3>%s</h3><ul>'
                     % esc(school))
        for p in items:
            zi = p.get('zi') and '（%s）' % p.get('zi') or ''
            origin = p.get('origin', {})
            raw = isinstance(origin, dict) and origin.get('raw') or ''
            parts.append('<li><strong>%s</strong>%s%s%s</li>'
                         % (esc(p.get('name', '')), esc(zi),
                            ' · ' + esc(raw) if raw else '',
                            ' · %s' % esc(p.get('role')) if p.get('role') else ''))
        parts.append('</ul></section>')
    return '\n'.join(parts)


def orphan_html(orphans):
    """孤点人物：按类别（kinds）列出姓名与缘由"""
    if isinstance(orphans, str):
        try:
            orphans = json.loads(orphans)
        except Exception:
            return ''
    parts = []
    kinds = orphans.get('kinds') or {}
    for kid, label in kinds.items():
        people = orphans.get('by_kind', {}).get(kid) if isinstance(orphans.get('by_kind'), dict) else None
        if not people:
            people = [o for o in orphans.get('orphans', []) if o.get('kind') == kid]
        if not people:
            continue
        parts.append('<section class="orphan-group"><h3>%s（%d）</h3><ul>'
                     % (esc(label), len(people)))
        for o in people:
            nm = o.get('name') if isinstance(o, dict) else o
            parts.append('<li>%s</li>' % esc(nm))
        parts.append('</ul></section>')
    return '\n'.join(parts)


_SKIP_KEYS = {'id', 'kind', 'cls', 'pos', 'num', 'emph', 'know', 'title', 'sub'}


def _text_leaves(node, out, skip_first_level=False):
    """摘出嵌套结构里的文本叶子

    阳明 14 章每章 kind 不同（flow / quad / ladder …），各自嵌套形状也不同。
    给每种 kind 写一套静态模板不划算 —— 交互版由 JS 按 kind 精确渲染，
    这里只需要把文字捞干净，让爬虫和无 JS 的读者拿到内容。
    """
    if isinstance(node, str):
        s = node.strip()
        if s and s not in out:
            out.append(s)
    elif isinstance(node, list):
        for v in node:
            _text_leaves(v, out)
    elif isinstance(node, dict):
        skip = _SKIP_KEYS if skip_first_level else {'id', 'kind', 'cls', 'pos'}
        for k, v in node.items():
            if k in skip:
                continue
            _text_leaves(v, out)


def yangming_html(ym):
    """阳明心学 14 章：标题、副题与每章要点文字，供爬虫与无 JS 场景索引"""
    if isinstance(ym, str):
        try:
            ym = json.loads(ym)
        except Exception:
            return ''
    parts = ['<header class="ym-head"><h2>%s</h2><p>%s</p>'
             % (esc(ym.get('title', '')), esc(ym.get('subtitle', '')))]
    if ym.get('hero'):
        parts.append('<p class="ym-hero">%s</p>' % esc(ym['hero']))
    if ym.get('heroSub'):
        parts.append('<p class="ym-hero-sub">%s</p>' % esc(ym['heroSub']))
    parts.append('</header>')
    for c in ym.get('chapters', []):
        parts.append('<section class="ym-chapter" id="%s"><h3>%s %s</h3><p>%s</p>'
                     % (esc(c.get('id', '')), esc(c.get('num', '')),
                        esc(c.get('title', '')), esc(c.get('sub', ''))))
        leaves = []
        _text_leaves(c, leaves, skip_first_level=True)
        if leaves:
            parts.append('<ul class="ym-points">%s</ul>'
                         % ''.join('<li>%s</li>' % esc(s) for s in leaves))
        parts.append('</section>')
    for key, cls in (('outro', 'ym-outro'), ('note', 'ym-note')):
        val = ym.get(key)
        if isinstance(val, str) and val.strip():
            parts.append('<p class="%s">%s</p>' % (cls, esc(val)))
        elif isinstance(val, (list, dict)):
            leaves = []
            _text_leaves(val, leaves)
            if leaves:
                parts.append('<div class="%s">%s</div>'
                             % (cls, ''.join('<p>%s</p>' % esc(s) for s in leaves)))
    parts.append(rights_footer_html(ym.get('rights') or _YM_RIGHTS_DEFAULT,
                                    cls='ym-rights'))
    return '\n'.join(parts)


def geo_html(geo):
    """籍贯 → 人物 对照表（省→人物），爬虫与无 JS 场景可读"""
    if isinstance(geo, str):
        try:
            geo = json.loads(geo)
        except Exception:
            return ''
    places = geo.get('places') or {}
    prov_people = {}
    for name, info in places.items():
        if not isinstance(info, dict):
            continue
        prov = info.get('prov') or '不详'
        prov_people.setdefault(prov, []).append(name)
    parts = ['<table class="geo-table"><thead><tr><th>省</th><th>人物</th></tr></thead><tbody>']
    for prov in sorted(prov_people):
        people = '、'.join(sorted(prov_people[prov]))
        parts.append('<tr><td>%s</td><td>%s</td></tr>' % (esc(prov), esc(people)))
    parts.append('</tbody></table>')
    return '\n'.join(parts)


# ---------------------------------------------------------------------------
# 心学文献：Markdown（子集）→ 静态 HTML
# 三篇外部文章（体用论 / 磨镜喻 / 病药论）原封不动作为文章展示。
# 只做安全转义 + 结构转换，不改写任何文字。支持子集：
#   #/##/### 标题（带锚点）、> 引用（可内嵌列表/粗体）、表格、--- 分割、
#   **粗体** / *斜体*、- 列表、普通段落。
# ---------------------------------------------------------------------------

def _inline_md(s):
    """行内格式：先转义，再处理 **粗体** 与 *斜体*"""
    s = esc(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'\*(.+?)\*', r'<i>\1</i>', s)
    return s


def _is_table_sep(line):
    s = line.strip()
    if '|' not in s:
        return False
    inner = s.strip('|').replace(' ', '')
    # 分隔行只可能是 | - : 三种字符（去掉首尾 | 后内部仍含列分隔 |）
    return bool(inner) and set(inner) <= set('-:|')


def _is_block_start(s):
    if re.match(r'^#{1,6}\s', s):
        return True
    if s.startswith('>'):
        return True
    if re.match(r'^(?:---|\*\*\*|___)\s*$', s):
        return True
    if re.match(r'^[-*+]\s+', s) or re.match(r'^\d+[.)]\s+', s):
        return True
    return False


def _md_blocks(text):
    """把 markdown 文本切成块序列；标题带递增锚点 id（正文与目录共用）"""
    lines = text.split('\n')
    blocks, hc = [], [0]
    n = len(lines)

    def next_anchor():
        hc[0] += 1
        return 'h-%d' % hc[0]

    i = 0
    while i < n:
        stripped = lines[i].strip()
        if not stripped:
            i += 1
            continue
        m = re.match(r'^(#{1,6})\s+(.*)$', stripped)          # 标题
        if m:
            blocks.append(('h', len(m.group(1)), m.group(2).strip(), next_anchor()))
            i += 1
            continue
        if re.match(r'^(?:---|\*\*\*|___)\s*$', stripped):    # 分割线
            blocks.append(('hr',))
            i += 1
            continue
        if '|' in stripped and i + 1 < n and _is_table_sep(lines[i + 1]):  # 表格
            rows, j = [], i
            while j < n and '|' in lines[j]:
                r = lines[j].strip()
                if _is_table_sep(r):
                    j += 1
                    continue
                cells = [c.strip() for c in r.strip('|').split('|')]
                rows.append(cells)
                j += 1
            i = j
            if rows:
                blocks.append(('table', rows))
            continue
        if stripped.startswith('>'):                           # 引用（可多行）
            q = []
            while i < n and lines[i].strip().startswith('>'):
                q.append(re.sub(r'^>\s?', '', lines[i].strip()))
                i += 1
            blocks.append(('quote', q))
            continue
        if re.match(r'^[-*+]\s+', stripped) or re.match(r'^\d+[.)]\s+', stripped):  # 列表
            items = []
            while i < n and (re.match(r'^[-*+]\s+', lines[i].strip())
                             or re.match(r'^\d+[.)]\s+', lines[i].strip())):
                items.append(re.sub(r'^(?:[-*+]|\d+[.)])\s+', '', lines[i].strip()))
                i += 1
            blocks.append(('list', items))
            continue
        para = []                                              # 段落
        while i < n and lines[i].strip() and not _is_block_start(lines[i].strip()) \
                and '|' not in lines[i]:
            para.append(lines[i].strip())
            i += 1
        if para:
            blocks.append(('p', ' '.join(para)))
    return blocks


def _render_table(rows):
    head = rows[0]
    th = ''.join('<th>%s</th>' % _inline_md(c) for c in head)
    trs = ''.join('<tr>%s</tr>'
                  % ''.join('<td>%s</td>' % _inline_md(c) for c in r)
                  for r in rows[1:])
    return ('<table class="lit-table"><thead><tr>%s</tr></thead>'
            '<tbody>%s</tbody></table>' % (th, trs))


def _render_blocks(blocks, toc=None):
    out = []
    seen_title = False
    for b in blocks:
        kind = b[0]
        if kind == 'h':
            level, txt, aid = b[1], b[2], b[3]
            if level == 1:
                if not seen_title:
                    seen_title = True   # 首行 H1 → 左栏标题，正文不重复渲染
                    continue
                # 后续 H1（如「卷一…」「卷二…」）→ 大节标题，进正文也进目录
                out.append('<h1 id="%s" class="lit-vol">%s</h1>' % (aid, _inline_md(txt)))
                if toc is not None:
                    toc.append('<li class="lit-toc-l1"><a href="#%s">%s</a></li>'
                               % (aid, _inline_md(txt)))
                continue
            out.append('<h%d id="%s">%s</h%d>' % (level, aid, _inline_md(txt), level))
            if toc is not None and level in (2, 3):
                cls = 'lit-toc-l%d' % level
                toc.append('<li class="%s"><a href="#%s">%s</a></li>'
                           % (cls, aid, _inline_md(txt)))
        elif kind == 'hr':
            out.append('<hr class="lit-hr"/>')
        elif kind == 'quote':
            inner = _render_blocks(_md_blocks('\n'.join(b[1])), None)
            out.append('<blockquote class="lit-quote">%s</blockquote>' % inner)
        elif kind == 'list':
            out.append('<ul class="lit-list">%s</ul>'
                       % ''.join('<li>%s</li>' % _inline_md(it) for it in b[1]))
        elif kind == 'table':
            out.append(_render_table(b[1]))
        else:                          # p
            out.append('<p class="lit-par">%s</p>' % _inline_md(b[1]))
    return ''.join(out)


def literature_html(md_path):
    """一篇文献 markdown → (body_html, toc_html, title)

    body：除 H1 外的全部正文（标题带锚点，供左栏目录跳转）。
    toc：## / ### 两级目录（带锚点）。
    title：首行 H1 文本（注入左栏 #litTitle）。
    内容原封不动，仅做转义与结构转换。
    """
    text = Path(md_path).read_text(encoding='utf-8')
    blocks = _md_blocks(text)
    toc = []
    body = _render_blocks(blocks, toc)
    title = ''
    for b in blocks:
        if b[0] == 'h' and b[1] == 1:
            title = b[2]
            break
    body = body + rights_footer_html(_LIT_RIGHTS_TEXT, cls='lit-rights')
    return body, toc, title
