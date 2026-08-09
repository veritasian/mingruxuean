#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wikitext_html.py —— Python 移植 src/data/wikitext.js 的 toHTML()

构建 web/ 在线版时，书卷正文需要在 Python 侧预渲染成静态 HTML 嵌进页面，
避免依赖浏览器端 JS 渲染内容（搜索引擎不可见）。
逻辑与 wikitext.js 逐行对应，正则一致，不接受功能偏差。
"""
import re

_H = '\u0001H\u0001'
_PA = '\u0001P\u0001'
_PB = '\u0001/P\u0001'


def to_html(src):
    """wikitext → HTML 段落（div.poem、h4 章节标题、p.par 正文段）"""
    s = str(src or '')

    s = re.sub(r'<!--[\s\S]*?-->', '', s)
    s = re.sub(r'<ref[\s\S]*?</ref>', '', s)
    s = re.sub(r'<ref[^>]*/\s*>', '', s)
    s = re.sub(r'</?(only|no|)include(only)?>', '', s, flags=re.IGNORECASE)
    s = re.sub(r'\{\|[\s\S]*?\|\}', '', s)
    # 模板可能嵌套，反复剥（JS 版封顶 8 轮）
    for _ in range(8):
        nxt = re.sub(r'\{\{[^{}]*\}\}', '', s)
        if nxt == s:
            break
        s = nxt
    s = re.sub(
        r'\[\[(File|Image|文件|图像|圖像|Category|分类|分類|作者|Author):[\s\S]*?\]\]',
        '', s, flags=re.IGNORECASE)
    s = re.sub(r'\[\[([^[\]|]*)\|([^[\]]*)\]\]', r'\2', s)
    s = re.sub(r'\[\[([^[\]]*)\]\]', r'\1', s)
    s = re.sub(r'^(={2,4})\s*(.*?)\s*\1\s*$', r'\n' + _H + r'\2\n', s, flags=re.M)
    s = re.sub(r'<poem>([\s\S]*?)</poem>', r'\n' + _PA + r'\1\n' + _PB + '\n', s)

    # HTML 转义（与 JS dom.esc 一致）
    s = s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    s = re.sub(r"'''''([^']+)'''''", r'<b><i>\1</i></b>', s)
    s = re.sub(r"'''([^']+)'''", r'<b>\1</b>', s)
    s = re.sub(r"''([^']+)''", r'<i>\1</i>', s)

    out = []
    in_poem = False
    for line in [ln.strip() for ln in s.split('\n')]:
        if not line:
            continue
        if line.startswith(_PA):
            out.append('<div class="poem">')
            in_poem = True
            continue
        if line.startswith(_PB):
            out.append('</div>')
            in_poem = False
            continue
        if line.startswith(_H):
            out.append('<h4>%s</h4>' % line[len(_H):])
            continue
        out.append('%s<br/>' % line if in_poem else '<p class="par">%s</p>' % line)
    if in_poem:
        out.append('</div>')
    return '\n'.join(out)


# quick smoke
if __name__ == '__main__':
    test = "'''粗体'''文字。\n\n== 第一章 =="
    print(to_html(test))
