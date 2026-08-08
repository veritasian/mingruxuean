#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_data.py —— 数据层体检

管的是「数据自己站不站得住」：
  · 引用完整性 —— 关系两端的人必须真的存在，否则图上会凭空多出幽灵节点
  · 分类自洽   —— 孤点的判读结果必须和关系表算出来的孤点完全一致
  · 出处可溯   —— 标了 cited 的关系必须真的带得出卷次与原文
不管渲染，那是 smoke.mjs 的活。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import ROOT, check, check_eq, sample, main  # noqa: E402

DATA = ROOT / 'data'
_cache = {}


def load(name):
    if name not in _cache:
        _cache[name] = json.loads((DATA / ('%s.json' % name)).read_text(encoding='utf-8'))
    return _cache[name]


def rels():
    r = load('relations')
    return r['relations'] if isinstance(r, dict) else r


def test_files_present():
    """七份核心 JSON 齐全"""
    need = ['persons', 'schools', 'relations', 'orphans', 'geo', 'timeline', 'toc']
    missing = [n for n in need if not (DATA / ('%s.json' % n)).exists()]
    check(not missing, '缺文件：%s' % sample(missing))
    return '%d 份' % len(need)


def test_volumes_complete():
    """63 卷正文齐全且非空"""
    files = sorted((DATA / 'volumes').glob('v*.json'))
    check_eq(len(files), 63, '卷数')
    thin = []
    for f in files:
        v = json.loads(f.read_text(encoding='utf-8'))
        if len(v.get('text', '')) < 1000:
            thin.append('%s(%d字)' % (f.stem, len(v.get('text', ''))))
    check(not thin, '正文过短：%s' % sample(thin))
    return '63 卷，最短 %d 字' % min(
        len(json.loads(f.read_text(encoding='utf-8'))['text']) for f in files)


def test_front_matter():
    """卷前三篇（原序、发凡、师说）齐备，且排在卷一之前"""
    toc = load('toc')
    front = toc.get('front') or []
    check_eq([f['id'] for f in front], ['x1', 'x2', 'x3'], '卷前篇编号')
    # 卷前篇另编号，绝不能占用 1–63，否则「六十三卷」这个不变量就破了
    nums = {v['volume'] for v in toc['volumes']}
    check(not ({f['id'] for f in front} & {str(n) for n in nums}), '卷前篇号与卷号相撞')
    for f in front:
        p = DATA / 'volumes' / ('%s.json' % f['id'])
        check(p.exists(), '缺正文文件 %s' % p.name)
        text = json.loads(p.read_text(encoding='utf-8')).get('text', '')
        check(len(text) > 800, '%s 正文过短（%d 字）' % (f['label'], len(text)))
        check_eq(len(text), f['chars'], '%s 的 chars 与正文不符' % f['label'])
        unknown = set(f.get('persons') or []) - set(load('persons'))
        check(not unknown, '%s 关联了未知人物：%s' % (f['label'], sample(unknown)))
    return '原序 %d · 发凡 %d · 师说 %d 字（评 %d 人）' % (
        front[0]['chars'], front[1]['chars'], front[2]['chars'], len(front[2]['persons']))


def test_person_keys_match_id():
    """人物表的键与 id 一致"""
    bad = [k for k, p in load('persons').items() if p.get('id') != k]
    check(not bad, '键与 id 不符：%s' % sample(bad))
    return '%d 人' % len(load('persons'))


def test_relation_endpoints_exist():
    """关系两端的人都在人物表里"""
    persons = load('persons')
    miss = {r[k] for r in rels() for k in ('from', 'to') if r[k] not in persons}
    check(not miss, '关系指向了不存在的人：%s' % sample(miss))
    return '%d 条关系全部有主' % len(rels())


def test_no_self_loop():
    """没有自己师承自己"""
    loops = [r['from'] for r in rels() if r['from'] == r['to']]
    check(not loops, '自环：%s' % sample(loops))
    return '无自环'


def test_no_duplicate_edge():
    """同一对师徒不重复登记"""
    seen, dup = set(), []
    for r in rels():
        key = (r['from'], r['to'], r['type'])
        if key in seen:
            dup.append('%s→%s' % (r['from'], r['to']))
        seen.add(key)
    check(not dup, '重复关系：%s' % sample(dup))
    return '%d 条唯一' % len(seen)


def test_school_membership_closed():
    """学案成员都在人物表里，且人人有归属"""
    persons, schools = load('persons'), load('schools')
    listed = set()
    ghost = []
    for s in schools:
        for m in s['members']:
            listed.add(m)
            if m not in persons:
                ghost.append('%s/%s' % (s['id'], m))
    check(not ghost, '成员不在人物表：%s' % sample(ghost))
    homeless = set(persons) - listed
    check(not homeless, '无所属：%s' % sample(homeless))
    return '%d 学案 %d 人' % (len(schools), len(listed))


def test_school_count_field():
    """member_count 与实际成员数对得上"""
    bad = ['%s(%d≠%d)' % (s['id'], s['member_count'], len(s['members']))
           for s in load('schools') if s['member_count'] != len(s['members'])]
    check(not bad, '计数不符：%s' % sample(bad))
    return 'ok'


# 谱系图真会画出来的边。三处必须一致：
#   scripts/build/analyze_orphans.EDGE_TYPES · src/data/model.edgeList() · 这里
EDGE_TYPES = {'师承', '私淑'}


def test_orphan_set_matches_relations():
    """孤点判读结果 == 由关系表实算的孤点"""
    linked = set()
    for r in rels():
        if r['type'] not in EDGE_TYPES:
            continue          # 附见只是编排位置，不是师承边，图上本来就不连
        linked.add(r['from'])
        linked.add(r['to'])
    computed = set(load('persons')) - linked
    declared = {o['id'] for o in load('orphans')['orphans']}
    only_c, only_d = computed - declared, declared - computed
    check(not only_c, '实算是孤点却没登记：%s' % sample(only_c))
    check(not only_d, '登记了但其实有连线：%s' % sample(only_d))
    return '%d 个孤点两边一致' % len(computed)


def test_orphan_kinds_declared():
    """每个孤点都有归类，且归类都有释义"""
    o = load('orphans')
    kinds = set(o['kinds'])
    unknown = {x['kind'] for x in o['orphans']} - kinds
    check(not unknown, '未定义的类别：%s' % sample(unknown))
    naked = [k for k, v in o['kinds'].items() if not v.get('label') or not v.get('desc')]
    check(not naked, '类别缺释义：%s' % sample(naked))
    tally = {}
    for x in o['orphans']:
        tally[x['kind']] = tally.get(x['kind'], 0) + 1
    check_eq(tally, o['meta']['by_kind'], 'by_kind 统计')
    return '、'.join('%s %d' % (o['kinds'][k]['label'], n) for k, n in sorted(tally.items()))


def test_orphan_gap_is_the_small_half():
    """真缺口应远少于「非缺口」—— 这是孤点现象一页的立论"""
    by = load('orphans')['meta']['by_kind']
    gap = by.get('gap', 0)
    other = sum(v for k, v in by.items() if k != 'gap')
    check(gap < other, '真缺口 %d 反而多于其它 %d，结论要重写' % (gap, other))
    return '真缺口 %d / 有由来 %d' % (gap, other)


def test_provenance_of_cited():
    """标了 cited 的关系必须给得出卷次和原文"""
    bad = []
    for r in rels():
        if not r.get('cited'):
            continue
        pv = r.get('provenance') or []
        if not any(p.get('volume') and p.get('quote') for p in pv):
            bad.append('%s→%s' % (r['from'], r['to']))
    check(not bad, '声称有出处却拿不出：%s' % sample(bad))
    n = sum(1 for r in rels() if r.get('cited'))
    return '%d 条有原文出处 / 共 %d 条' % (n, len(rels()))


def test_provenance_volume_in_range():
    """出处卷次落在合法范围：学案来源 1–63，《明史》来源 282–283"""
    bad = []
    for r in rels():
        for p in (r.get('provenance') or []):
            v = p.get('volume')
            if not v:
                continue
            if p.get('source') == 'mingshi':
                ok = int(v) in (282, 283)
            else:
                ok = 1 <= int(v) <= 63
            if not ok:
                bad.append('%s→%s %s卷%s' % (r['from'], r['to'], p.get('source'), v))
    check(not bad, '卷次越界：%s' % sample(bad))
    return 'ok'


def test_relation_meta_consistent():
    """relations.json 的 meta 计数与实际相符"""
    r = load('relations')
    meta = r.get('meta', {})
    check_eq(meta.get('count'), len(rels()), 'meta.count')
    check_eq(meta.get('cited'), sum(1 for x in rels() if x.get('cited')), 'meta.cited')
    # 孤点数只登记在 orphans.json，这里不该再存一份
    check('orphan_count' not in meta, 'relations.meta 不应重复登记 orphan_count')
    return '%d 条 / %d 有据' % (meta.get('count'), meta.get('cited'))


def test_mingshi_direction_and_source():
    """《明史》来源：方向 from=徒/to=师，且每一条都带卷次引文"""
    rs = [r for r in rels() if 'mingshi' in (r.get('sources') or [])]
    check(bool(rs), '没有任何《明史》来源的关系')
    # 明史原文已知的师徒对：from 必须是弟子
    known = [
        ('陈献章', '吴与弼'), ('湛若水', '陈献章'), ('娄谅', '吴与弼'),
        ('王阳明', '娄谅'), ('钱德洪', '王阳明'), ('王畿', '王阳明'),
        ('王艮', '王阳明'), ('颜钧', '徐樾'), ('罗汝芳', '颜钧'),
        ('许孚远', '唐枢'), ('刘宗周', '许孚远'), ('尤时熙', '刘魁'),
        ('孟化鲤', '尤时熙'), ('王时槐', '刘文敏'), ('罗洪先', '李中'),
        ('吕柟', '薛敬之'), ('胡居仁', '吴与弼'), ('阎禹锡', '薛瑄'),
    ]
    got = {(r['from'], r['to']) for r in rs if r['type'] == '师承'}
    bad = [p for p in known if p not in got]
    check(not bad, '明史已知师承缺方向：%s' % sample(bad))
    # 每条 mingshi provenance 都带卷次与引文
    no_ev = [(r['from'], r['to']) for r in rs
             if not any(p.get('source') == 'mingshi' and p.get('volume') and p.get('quote')
                        for p in (r.get('provenance') or []))]
    check(not no_ev, 'mingshi 边缺卷次/引文：%s' % sample(no_ev))
    return '%d 条《明史》来源' % len(rs)


def test_toc_covers_63():
    """目录 63 卷，卷号连续"""
    vols = [v['volume'] for v in load('toc')['volumes']]
    check_eq(sorted(vols), list(range(1, 64)), '目录卷号')
    return '1–63 连续'


def test_geo_and_period_keys_known():
    """籍贯与生卒挂的都是已知人物"""
    persons = load('persons')
    for label, table in (('籍贯', load('geo')['places']), ('生卒', load('timeline')['period'])):
        unknown = set(table) - set(persons)
        check(not unknown, '%s表出现未知人物：%s' % (label, sample(unknown)))
    return '籍贯 %d 人 · 生卒 %d 人' % (len(load('geo')['places']), len(load('timeline')['period']))


# 只挑「简繁写法确实不同」的字；像「案、承、明」简繁同形，拿来判定会误报
TRAD_ONLY = '學師陽東鄒謝復劉張楊錢顧縣傳書論語齋憲儀執給議舉聶羅馮鄧韓'


def test_simplified_chinese():
    """索引类数据用简体（原文与 name_original 除外）"""
    hits = []
    for name in ('persons', 'schools', 'orphans', 'geo'):
        raw = (DATA / ('%s.json' % name)).read_text(encoding='utf-8')
        hits += ['%s.json 含「%s」' % (name, ch) for ch in TRAD_ONLY if ch in raw]
    check(not hits, '出现繁体：%s' % sample(hits))
    return '4 份索引数据已转简'


def test_yangming_content():
    """阳明心学专页：14 章齐备，章节号连续，三种形态数据完整"""
    ym = load('yangming')
    chapters = ym.get('chapters') or []
    check_eq(len(chapters), 14, '章节数')
    check_eq([c['id'] for c in chapters],
             ['ch%d' % i for i in range(1, 15)], '章节号')
    check_eq(len(ym.get('hero', [])), 4, '四句教句数')
    check(all(c.get('title') and c.get('num') for c in chapters), '缺篇名/序号')
    by_id = {c['id']: c for c in chapters}
    for c in chapters:
        if c['kind'] == 'quad':
            q = c.get('quad') or {}
            check(len(q.get('q', [])) == 4, '%s 四象限应 4 格' % c['id'])
            check(all(x.get('pos') for x in q['q']), '%s 缺象限位' % c['id'])
        elif c['kind'] == 'matrix':
            m = c.get('matrix') or {}
            check(len(m.get('rows', [])) == 3 and len(m.get('cols', [])) == 3,
                  '%s 矩阵应 3×3' % c['id'])
        elif c['kind'] == 'flow':
            check(bool(c.get('flow', {}).get('awakeCols')) and bool(c['flow'].get('deludeCols')),
                  '%s 镜像两路缺失' % c['id'])
    check(ym.get('meta', {}).get('chars', 0) > 1000, '正文量过小')
    check(ym.get('outro'), '缺尾注')
    return '14 章 · 三形态 · %d 字' % ym['meta']['chars']


if __name__ == '__main__':
    main(sys.modules[__name__], '数据层')
