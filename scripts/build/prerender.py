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
