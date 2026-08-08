#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seo.py —— SEO 注入：title / description / keywords / JSON-LD

在 bundle.py 之后跑：读 data/ 的真实统计 → 生成
「核心关键词 + 长尾 + 吸引力」文案 → 把 <title>、<meta description/keywords>、
JSON-LD（WebSite + Book）注入 dist/明儒学案.html 的 <head>，并写 dist/seo.json 供检查。

幂等：整块用 <!--SEO-->…<!--/SEO--> 标记，重复运行只替换不叠加。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data'
DIST = ROOT / 'dist'
SITE_URL = 'https://mingruxuean.vercel.app/'
SE = '<!--SEO-->', '<!--/SEO-->'


def read(p):
    return Path(p).read_text(encoding='utf-8')


def build_copy():
    persons = json.loads(read(DATA / 'persons.json'))
    relations = json.loads(read(DATA / 'relations.json'))
    schools = json.loads(read(DATA / 'schools.json'))
    orphans = json.loads(read(DATA / 'orphans.json'))
    meta = relations.get('meta', {})
    n_p, n_s = len(persons), len(schools)
    n_r = len(relations.get('relations', relations))
    n_cited = meta.get('cited', 0)
    o = orphans.get('meta', {}).get('orphan_count', 0)

    title = ('名儒学案图谱 | 黄宗羲《明儒学案》师承脉络知识图谱'
             ' · %d 位明代大儒 · 六十三卷全文在线阅读' % n_p)
    desc = ('一键看懂明代儒学的师承脉络：%d 个学案、%d 位学者、%d 条师承关系'
            '（%d 条附原文出处），点击任何一位大儒即可查看其师承谱系；'
            '另有《明史》儒林传补强与阳明心学总纲，六十三卷全文离线可读、断网可用。'
            % (n_s, n_p, n_r, n_cited))
    keywords = ('明儒学案,黄宗羲,师承图谱,知识图谱,阳明心学,'
                '明代儒学,儒林传,名儒学案图谱,明儒,师承谱系')
    ld = {
        '@context': 'https://schema.org',
        '@graph': [
            {'@type': 'WebSite', 'url': SITE_URL, 'name': '名儒学案图谱',
             'alternateName': '明儒学案师承知识图谱',
             'description': desc, 'inLanguage': 'zh-CN'},
            {'@type': 'Book', 'name': '明儒学案', 'alternateName': '名儒学案图谱',
             'author': {'@type': 'Person', 'name': '黄宗羲'},
             'inLanguage': 'zh-CN', 'about': '明代儒学',
             'keywords': keywords, 'url': SITE_URL,
             'isAccessibleForFree': True},
        ],
    }
    return title, desc, keywords, ld, {
        'schools': n_s, 'persons': n_p, 'relations': n_r,
        'cited': n_cited, 'orphans': o,
    }


def inject(html, block):
    open_tag, close_tag = SE
    new = '%s\n%s\n%s' % (open_tag, block, close_tag)
    pat = re_compile()
    if pat.search(html):
        return pat.sub(lambda m: new, html, count=1)
    # 兜底：没找到标记则插在 </head> 前
    return html.replace('</head>', new + '\n</head>', 1)


def re_compile():
    import re
    open_tag, close_tag = SE
    return re.compile(re.escape(open_tag) + r'.*?' + re.escape(close_tag), re.S)


def main():
    title, desc, keywords, ld, stats = build_copy()
    block = ('<title>%s</title>\n'
             '<meta name="description" content="%s"/>\n'
             '<meta name="keywords" content="%s"/>\n'
             '<script type="application/ld+json">%s</script>'
             % (title, desc, keywords, json.dumps(ld, ensure_ascii=False)))

    out = DIST / '明儒学案.html'
    html = inject(out.read_text(encoding='utf-8'), block)
    out.write_text(html, encoding='utf-8')
    (DIST / 'index.html').write_text(html, encoding='utf-8')  # Vercel 入口同名

    meta = {'siteUrl': SITE_URL, 'title': title, 'description': desc,
            'keywords': keywords, 'jsonLd': ld, 'stats': stats}
    (DIST / 'seo.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1),
                                   encoding='utf-8')
    print('  SEO 注入：%s' % title)
    print('  统计：%d 学案 · %d 人 · %d 关系（%d 有出处）· 孤点 %d'
          % (stats['schools'], stats['persons'], stats['relations'],
             stats['cited'], stats['orphans']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
