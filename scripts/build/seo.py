#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seo.py —— 逐页 SEO 注入：title / description / keywords / canonical / JSON-LD

在 bundle.py 之后跑：站点是多页面结构，每一页都要围绕「自己的分类」写
「核心关键词 + 长尾 + 吸引力」文案，不能 8 页共用一份 meta。

数字实时读 data/（学案数、人数、关系数、有出处数、孤点数），不硬编码。
对 dist/ 下每一页幂等注入 <!--SEO-->…<!--/SEO--> 块，并写 dist/seo.json 供检查。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bundle import PAGES  # noqa: E402  页面清单的唯一出处

DATA = ROOT / 'data'
DIST = ROOT / 'dist'
SITE_URL = 'https://mingruxuean.vercel.app/'
SE = '<!--SEO-->', '<!--/SEO-->'


def read(p):
    return Path(p).read_text(encoding='utf-8')


def stats():
    persons = json.loads(read(DATA / 'persons.json'))
    relations = json.loads(read(DATA / 'relations.json'))
    schools = json.loads(read(DATA / 'schools.json'))
    orphans = json.loads(read(DATA / 'orphans.json'))
    meta = relations.get('meta', {})
    return {
        'schools': len(schools), 'persons': len(persons),
        'relations': len(relations.get('relations', relations)),
        'cited': meta.get('cited', 0),
        'orphans': orphans.get('meta', {}).get('orphan_count', 0),
    }


def page_copy(spec, s):
    """每页一套文案：title 核心词+长尾+吸引力；desc 带真实数字；keywords 围绕本分类"""
    if spec.get('book_vol'):
        return book_copy(spec, s)
    p = s['persons']; sc = s['schools']; r = s['relations']; c = s['cited']; o = s['orphans']
    name = {
        'kg': '知识图谱', 'graph': '谱系总图', 'roster': '人物线索', 'time': '时间线索',
        'geo': '地理线索', 'orphan': '孤点现象', 'yangming': '阳明心学',
    }[spec['id']]
    titles = {
        'kg': ('名儒学案图谱 | 黄宗羲《明儒学案》师承知识图谱'
               ' · %d 位明代大儒关系网一图看懂' % p),
        'graph': ('名儒学案图谱 · 谱系总图 | 明代儒学师承树状总览'
                  ' · %d 学案 %d 儒者代际脉络' % (sc, p)),
        'roster': ('名儒学案图谱 · 人物线索 | %d 位明代儒者名录'
                   ' · 按学案编次快速检索' % p),
        'time': ('名儒学案图谱 · 时间线索 | 明代大儒生卒年时间轴'
                 ' · 洪武至崇祯 276 年儒学史'),
        'geo': ('名儒学案图谱 · 地理线索 | 明代儒者籍贯地理分布'
                ' · 明代地名对照今省市'),
        'orphan': ('名儒学案图谱 · 孤点现象 | %d 位不与师承相连的学者'
                   ' · 因由逐类详解' % o),
        'yangming': ('名儒学案图谱 · 阳明心学 | 王阳明四句教与心学思维模型图解'
                     ' · 致良知体系一页通'),
    }
    descs = {
        'kg': ('明代儒学师承关系全景：%d 个学案、%d 位学者、%d 条师承关系'
               '（%d 条附原文出处）。点击任意大儒即聚合其师承网络，'
               '知识图谱一图看懂黄宗羲《明儒学案》的学派源流。' % (sc, p, r, c)),
        'graph': ('按原书编次把 %d 个学案、%d 位儒者排成师承树：'
                  '列内自上而下、连线自师指向徒，可切换师承代次排序，'
                  '一眼看清明代儒学的代际脉络。' % (sc, p)),
        'roster': ('%d 位明代儒者按学案编次整理成人物线索，'
                   '每位附生卒、字、号、籍贯、师承与弟子；'
                   '点击任何一人弹出完整人物卡与关系出处。' % p),
        'time': ('以明代年号（洪武 1368 — 崇祯 1644）为轴，'
                 '%d 位儒者按活动年代落位成时间线索，'
                 '可筛选某朝人物，看清哪一朝涌现了哪些大儒。' % p),
        'geo': ('把 %d 位儒者的明代籍贯换算成今省市区，'
                '省份/地市/柱状图三种视角看明代儒学的南北分布，'
                '附明地→今地对照表。' % p),
        'orphan': ('%d 个不与任何师承相连的「孤点」各有来由：'
                   '传记不全、门派开山、外来学者、关联存疑……'
                   '逐类解读，是读《明儒学案》时最容易被忽略的一页。' % o),
        'yangming': ('四句教、明镜喻、三教九阶、一体四用：'
                     '把王阳明心学拆成思维模型、根器论、体用论十四讲，'
                     '图文并茂，适合入门也适合温故。'),
    }
    keywords = {
        'kg': '明儒学案,知识图谱,师承关系,黄宗羲,明代儒学,名儒学案图谱',
        'graph': '明儒学案,谱系总图,师承树,学案,黄宗羲,明代儒林',
        'roster': '明儒学案,人物线索,明代儒者名录,学案人物,黄宗羲',
        'time': '明儒学案,时间线索,明代年号,生卒年,时间轴,明代儒学史',
        'geo': '明儒学案,地理线索,籍贯分布,明代地名,今省市对照',
        'orphan': '明儒学案,孤点现象,师承断链,孤点学者,黄宗羲',
        'yangming': '阳明心学,王阳明,四句教,致良知,心学,思维模型',
    }
    return titles[spec['id']], descs[spec['id']], keywords[spec['id']]


def book_copy(spec, s):
    """学案原文 64 页：卷前一篇（3 tab）+ 63 卷各一页，每页独立文案"""
    toc = json.loads(read(DATA / 'toc.json'))
    vols = {str(v['volume']): v for v in toc.get('volumes', [])}
    if spec['book_vol'] == 'front':
        title = '黄梨洲先生原序 · 发凡 · 师说 · 黄宗羲《明儒学案》全文'
        desc = ('《明儒学案》卷前三篇：黄梨洲先生原序（一本万殊）、发凡（编纂体例）、'
                '师说（刘宗周评骘明儒二十五家）。据维基文库整理，离线可读，'
                '全书六十三卷按卷分页、卷内可检索。')
        keywords = '明儒学案,黄梨洲先生原序,发凡,师说,黄宗羲,维基文库'
        return title, desc, keywords
    v = spec['book_vol']
    info = vols.get(v)
    if not info:
        return '卷%s · 黄宗羲《明儒学案》全文' % v, '', '明儒学案'
    people = '、'.join((info.get('persons') or [])[:5])
    more = ' 等' if len(info.get('persons') or []) > 5 else ''
    title = '卷%s %s · 黄宗羲《明儒学案》全文' % (info['volume'], info['name'])
    desc = ('黄宗羲《明儒学案》卷%s「%s」：%s%s，共 %s 字。'
            '据维基文库整理，按卷分页、离线可读，卷内全文可检索。'
            % (info['volume'], info['name'], people, more, info.get('chars', 0)))
    keywords = '明儒学案,卷%s,%s,黄宗羲,全文阅读' % (info['volume'], info['name'])
    return title, desc, keywords


def json_ld(spec, title, desc, keywords, s):
    url = SITE_URL + spec['file']
    nodes = [{
        '@type': 'WebSite', 'url': SITE_URL, 'name': '名儒学案图谱',
        'alternateName': '明儒学案师承知识图谱',
        'description': desc, 'inLanguage': 'zh-CN',
    }]
    if spec.get('book_vol'):
        # 学案原文按卷分页：每卷一个 Book/WebPage 节点
        nodes.append({'@type': 'Book', 'name': '明儒学案', 'url': url,
                      'author': {'@type': 'Person', 'name': '黄宗羲'},
                      'inLanguage': 'zh-CN', 'about': title, 'isAccessibleForFree': True})
    elif spec['id'] == 'yangming':
        nodes.append({'@type': 'Article', 'headline': title, 'url': url,
                      'inLanguage': 'zh-CN', 'about': '阳明心学'})
    else:
        nodes.append({'@type': 'CollectionPage', 'name': title, 'url': url,
                      'inLanguage': 'zh-CN', 'keywords': keywords})
    return {'@context': 'https://schema.org', '@graph': nodes}


def inject(html, block):
    open_tag, close_tag = SE
    new = '%s\n%s\n%s' % (open_tag, block, close_tag)
    pat = re_compile()
    if pat.search(html):
        return pat.sub(lambda m: new, html, count=1)
    return html.replace('</head>', new + '\n</head>', 1)


def re_compile():
    import re
    open_tag, close_tag = SE
    return re.compile(re.escape(open_tag) + r'.*?' + re.escape(close_tag), re.S)


def main():
    s = stats()
    out_meta = {}
    TARGET = DIST
    for spec in PAGES:
        title, desc, keywords = page_copy(spec, s)
        ld = json_ld(spec, title, desc, keywords, s)
        file_url = SITE_URL + spec['file']
        block = ('<title>%s</title>\n'
                 '<meta name="description" content="%s"/>\n'
                 '<meta name="keywords" content="%s"/>\n'
                 '<link rel="canonical" href="%s"/>\n'
                 '<meta property="og:type" content="website"/>\n'
                 '<meta property="og:title" content="%s"/>\n'
                 '<meta property="og:description" content="%s"/>\n'
                 '<meta property="og:url" content="%s"/>\n'
                 '<script type="application/ld+json">%s</script>'
                 % (title, desc, keywords, file_url, title, desc, file_url,
                    json.dumps(ld, ensure_ascii=False)))
        f = TARGET / spec['file']
        f.write_text(inject(f.read_text(encoding='utf-8'), block), encoding='utf-8')
        out_meta[spec['file']] = {'title': title, 'description': desc,
                                  'keywords': keywords, 'jsonLd': ld}
        print('  SEO[%s] %s' % (spec['file'], title[:50]))

    (TARGET / 'seo.json').write_text(
        json.dumps({'siteUrl': SITE_URL, 'stats': s, 'pages': out_meta},
                   ensure_ascii=False, indent=1), encoding='utf-8')
    write_sitemap(TARGET)
    print('  统计：%d 学案 · %d 人 · %d 关系（%d 有出处）· 孤点 %d'
          % (s['schools'], s['persons'], s['relations'], s['cited'], s['orphans']))
    return 0


def write_sitemap(target):
    """sitemap.xml + robots.txt

    71 个页面全都是独立可索引的内容页，光有 canonical 不够 —— 卷 2 到卷 63
    只在页内目录里链着，爬虫要靠 sitemap 才能一次看全。
    首页权重最高，八个分类页次之，卷页再次之。
    """
    from datetime import date
    today = date.today().isoformat()
    urls = []
    for spec in PAGES:
        if spec['file'] == 'index.html':
            prio, freq = '1.0', 'weekly'
        elif spec.get('book_vol'):
            prio, freq = '0.6', 'yearly'
        else:
            prio, freq = '0.8', 'monthly'
        urls.append('  <url><loc>%s%s</loc><lastmod>%s</lastmod>'
                    '<changefreq>%s</changefreq><priority>%s</priority></url>'
                    % (SITE_URL, spec['file'], today, freq, prio))
    (target / 'sitemap.xml').write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n'
        % '\n'.join(urls), encoding='utf-8')
    # book.html 是老书签跳板，本身没内容，别让它进索引
    (target / 'robots.txt').write_text(
        'User-agent: *\nAllow: /\nDisallow: /book.html\nDisallow: /seo.json\n'
        '\nSitemap: %ssitemap.xml\n' % SITE_URL, encoding='utf-8')
    print('  sitemap.xml %d 条 · robots.txt' % len(urls))


if __name__ == '__main__':
    sys.exit(main())
