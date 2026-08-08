#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
guards.py —— 抽取结果的证伪层

正则抽出来的东西，一半的功夫要花在「把不该要的踢掉」。实抽中遇到四类坑：

1. 否定句被当成肯定
   「吾虽不及白沙之门，幸在其乡」  → 何廷仁明说没进白沙门
   「以不得及阳明之门为憾」        → 卢宁忠明说没赶上
   不拦掉就会凭空造出师承。

2. 谈学派 ≠ 本人属该学派
   「独怪阳明门下解之者曰……」     → 这是黄宗羲在评论阳明后学
   「阳明门下，自双江、念庵以外」   → 同上
   传主本人根本不在这句话里。

3. 中间隔着别人
   「罗一峰、章枫山、庄定山、贺医闾皆恨相见之晚……问学」
   松散的 {0,30} 间隔会跨过好几个人名连错。

4. 地名/前缀撞别名
   「受业天台郑四表之门」→「天台」是地名，真正的老师是紧随其后的郑四表。

另外把「私淑」从「师承」里分出来：慕其学而未及见，是明代学术史里一个
有分量的类别（邓以赞、唐枢皆是），混进师承会失真。
"""
import re

# 否定/未遂/见而不合（张岳「谒阳明于绍兴，与语多不契」——见了面但没拜师）
NEGATION = re.compile(r"不及|不得及|未及|未得|恨不|无缘|不曾|未尝|不获|未获|不果|"
                      r"不契|龃龉|不相能|不合而")

# 私淑标记：慕其学而无师承之实
SIWEN = re.compile(r"私淑|遥契|闻风而起")

# 评论口吻：后面跟这些字说明在谈学派而非谈传主
DISCOURSE = re.compile(r"^(?:[之]?(?:解|谈|论|说|学者|诸子|后学|中人|士|云|曰|多|皆|自))")

WINDOW_BEFORE = 14
WINDOW_AFTER = 10


def negated(para, m):
    """匹配点前后窗口内出现否定词。"""
    s = max(0, m.start() - WINDOW_BEFORE)
    e = min(len(para), m.end() + WINDOW_AFTER)
    return bool(NEGATION.search(para[s:e]))


def private_learning(para, m):
    s = max(0, m.start() - WINDOW_BEFORE)
    return bool(SIWEN.search(para[s:m.end()]))


def discoursing(para, m):
    """「阳明门下，自双江……」这类议论。"""
    return bool(DISCOURSE.match(para[m.end():m.end() + 4]))


def person_between(para, m, alias_rx):
    """老师别名与关系动词之间还夹着别的人名 → 判为连错。"""
    span = para[m.end("t"):m.end()] if "t" in (m.groupdict() or {}) else ""
    if len(span) < 2:
        return False
    for hit in alias_rx.finditer(span):
        if len(hit.group(0)) >= 2:
            return True
    return False


def retarget(para, m, index, alias_rx):
    """别名紧跟另一个别名（受业[天台]郑四表之门）→ 改指后者。"""
    tail = para[m.end("t"):m.end("t") + 4]
    hit = alias_rx.match(tail)
    if hit and hit.group(0) in index:
        return index[hit.group(0)]["id"], hit.group(0)
    return None, None


def apply(para, m, tag, index, alias_rx):
    """返回 (keep, rel_type, penalty, note)。keep=False 表示丢弃。"""
    note = ""
    rel_type = "师承"
    penalty = 1.0

    if discoursing(para, m) and tag in ("门下", "某门人", "某弟子"):
        return False, None, 0, "议论学派而非传主师承"

    if person_between(para, m, alias_rx):
        return False, None, 0, "师名与关系词之间夹有他人"

    if private_learning(para, m):
        rel_type, penalty, note = "私淑", 0.85, "私淑，非亲炙"
    elif negated(para, m):
        if tag in ("闻某之学", "禀学"):
            rel_type, penalty, note = "私淑", 0.8, "慕其学而未及见"
        else:
            return False, None, 0, "否定句：明言未及师门"

    return True, rel_type, penalty, note
