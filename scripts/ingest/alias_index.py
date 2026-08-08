#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
alias_index.py —— 人物别名索引

《明儒学案》原文极少直呼姓名，绝大多数用「号」或「姓+号」：
    「先生师事欧阳南野」  →  欧阳德（姓 欧阳 + 号 南野）
    「令其师事龙溪、绪山」→  王畿（号 龙溪）、钱德洪（号 绪山）
不建别名表就抽不到任何关系，这是补关系的地基。

歧义处理：一个别名指向多人时直接丢弃（宁缺毋滥），并记入 ambiguous 供人工审。
"""

# 复姓表：用于「姓+号」的正确切分
COMPOUND_SURNAMES = {"欧阳", "司马", "诸葛", "上官", "夏侯", "皇甫", "尉迟", "公孙"}

# 这些字若单独作别名会大量误命中，禁用。
# 注意：「阳明」曾被误列于此，导致王守仁的核心称呼解析不出来 —— 原文
# 「师事阳明」「及阳明之门」满篇皆是，禁掉等于把王门师承整片抹掉。
# 谥号（文成/文正…）只禁裸用，「姓+谥号」（王文成）仍然保留。
STOPWORDS = {
    "先生", "夫子", "有道", "文成", "文正", "文庄", "文清", "文敏", "文端",
    "处士", "布政", "教谕", "文选", "侍郎", "尚书", "御史", "主事", "郎中",
    "山人", "居士", "征君", "徵君", "太常", "少师", "学正", "同知", "知府",
    "员外", "给事", "佥事", "参政", "按察", "恭简", "襄文", "忠介",
}


def surname_of(name):
    if len(name) >= 3 and name[:2] in COMPOUND_SURNAMES:
        return name[:2]
    return name[:1]


def build_alias_index(persons):
    """返回 (alias -> person_id, ambiguous: alias -> [ids])。"""
    buckets = {}

    def add(alias, pid, weight):
        if not alias or len(alias) < 2 or alias in STOPWORDS:
            return
        buckets.setdefault(alias, {})[pid] = max(
            buckets.get(alias, {}).get(pid, 0), weight)

    for pid, p in persons.items():
        name, zi, hao = p["name"], p.get("zi", ""), p.get("hao", "")
        title = p.get("title", "")
        sn = surname_of(name)
        add(name, pid, 100)                       # 王艮
        if hao:
            add(sn + hao, pid, 95)                # 王心斋 / 欧阳南野
            add(hao, pid, 80)                     # 心斋
            add(hao + "先生", pid, 90)
            add(sn + hao + "先生", pid, 96)       # 王龙溪先生
        if title:                                 # 谥号：王文成 = 王守仁
            add(sn + title, pid, 92)
        if zi:
            add(sn + zi, pid, 70)                 # 王汝止
            add(zi, pid, 50)                      # 汝止（弱，易撞）
        # 名讳单字 + 先生：「畿先生」；仅对双字名生效，避免噪音
        if len(name) == 2:
            add(name[1] + "先生", pid, 60)

    index, ambiguous = {}, {}
    for alias, owners in buckets.items():
        if len(owners) == 1:
            pid = next(iter(owners))
            index[alias] = {"id": pid, "weight": owners[pid]}
        else:
            # 同一别名多人共用：若某人权重明显更高（姓名 > 号 > 字）则取之
            ranked = sorted(owners.items(), key=lambda kv: -kv[1])
            if ranked[0][1] >= ranked[1][1] + 20:
                index[alias] = {"id": ranked[0][0], "weight": ranked[0][1] - 15}
            else:
                ambiguous[alias] = [pid for pid, _ in ranked]
    return index, ambiguous


def alias_pattern(index):
    """构造按长度降序的正则择一分支，保证长别名优先匹配。"""
    keys = sorted(index.keys(), key=lambda s: (-len(s), s))
    return "(?:" + "|".join(keys) + ")"
