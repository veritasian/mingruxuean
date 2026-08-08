#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
normalize.py —— 文字规范化（全流程共用）

《明儒学案》原始语料是繁体明清古籍，同一个人在不同地方会写成：
    羅大紘 / 罗大纮      （繁简）
    吳鍾峦 / 吴钟峦      （繁简）
    謝佑  / 谢祐         （异体字，t2s 不处理）
不统一就会把一个人拆成两条记录，师承边自然连不上。
"""
try:
    from opencc import OpenCC
    _CC = OpenCC("t2s")

    def t2s(s):
        return _CC.convert(s) if s else s
except Exception:                                     # 无 opencc 时降级为原样
    def t2s(s):
        return s


# t2s 覆盖不到的异体字（人名用字），成对归一到左侧
VARIANTS = {
    "祐": "佑", "昇": "升", "崑": "昆", "峯": "峰", "蹟": "迹",
    "曬": "晒", "菴": "庵", "巖": "岩", "羣": "群", "牀": "床",
    "馀": "余", "彞": "彝", "畧": "略", "羗": "羌", "尙": "尚",
}

# 明确认定的同一人异写（经人工核对原书章节后写死，并记录理由）
NAME_ALIASES = {
    "职永澄": ("刘永澄", "『职』为『刘』之形近讹字；原书卷60东林学案三『职方刘静之先生永澄』"),
    "文廷矩": ("何廷矩", "『文』为『何』之形近讹字，白沙何廷矩"),
    "邹南": ("邹元标", "『邹南』为『邹南臬』脱字；原书卷23『忠介邹南臬先生元标』"),
    "王宗沭": ("王宗沐", "『沭』为『沐』之讹；原书卷15『侍郎王敬所先生宗沐』"),
    "邓豁渠初名鹤": ("邓豁渠", "解析残留，『初名鹤』为注文非姓名"),
}


def norm_char(s):
    if not s:
        return s
    return "".join(VARIANTS.get(c, c) for c in s)


def norm_text(s):
    """繁→简 + 异体字归一。用于比对，不用于展示。"""
    return norm_char(t2s(s or ""))


def canonical_name(name):
    """返回 (规范姓名, 归并理由或 None)。"""
    n = norm_text(name)
    if n in NAME_ALIASES:
        target, reason = NAME_ALIASES[n]
        return norm_text(target), reason
    return n, None
