#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sections.py —— 卷 → 章节 → 人物 的切分与对齐（link 与 extract 共用）

单独抽出来是为了保证「建索引」和「抽关系」用的是同一套切分规则，
否则两边各写一份，改了一处另一处就悄悄错位。
"""
import re

from normalize import norm_text
from alias_index import surname_of

SKIP_TITLES = re.compile(r"^(前言|序|小引|附录|凡例)$")


def split_sections(text):
    """一卷正文 → [(标题, 正文), ...]，标题形如 ==文庄欧阳南野先生德=="""
    parts = re.split(r"^==([^=\n]+)==\s*$", text, flags=re.M)
    return [(parts[i].strip(), parts[i + 1]) for i in range(1, len(parts) - 1, 2)]


def school_of_volume(vol_name):
    m = re.match(r"(.+?学案)", norm_text(vol_name))
    return m.group(1) if m else norm_text(vol_name)


def parse_heading(title):
    """[尊称/官职][姓][号]先生[名] → (左段, 名)"""
    t = norm_text(re.sub(r"[（(].*?[)）]", "", title)).strip()
    if "先生" in t:
        left, given = t.split("先生", 1)
        return left, given.strip()
    return t, ""


def appendix_names(title):
    """『（附樵夫朱恕　陶匠韩乐吾）』→ ['樵夫朱恕', '陶匠韩乐吾']"""
    m = re.search(r"[（(](.*?)[)）]", title)
    if not m:
        return []
    inner = norm_text(m.group(1)).replace("附", "")
    return [x for x in re.split(r"[　\s、,，]+", inner) if len(x) >= 2]


def build_given_index(persons):
    """名（去姓）→ [(pid, 姓, person)]，用于标题对齐。"""
    idx = {}
    for pid, p in persons.items():
        sn = surname_of(p["name"])
        idx.setdefault(p["name"][len(sn):], []).append((pid, sn, p))
    return idx


def match_section(title, persons, given_index):
    """把章节标题对齐到人物 id，匹配不上返回 None。"""
    left, given = parse_heading(title)
    if given:
        for pid, sn, p in given_index.get(given, []):
            if sn in left or (p.get("hao") and p["hao"] in left):
                return pid
    # 兜底：标题里恰好只出现一个人名时才采信，出现多个说明是附传，宁可不认
    whole = norm_text(title)
    hits = [pid for pid, p in persons.items() if p["name"] in whole]
    return hits[0] if len(hits) == 1 else None


# 段首「某某字某某」= 附传，本段主语换人
_LEAD_NAME = re.compile(r"^[　\s]*([\u4e00-\u9fa5]{2,4})[，,]?字")


def bio_paragraphs(body, section_pid, name_map):
    """
    产出 (段落主语 pid, 段落正文)。

    只取「传」的部分，不碰语录和书信——那里的『受业于某某』说的是别人，
    照抽必然张冠李戴（实测 魏校→胡居仁 就是从一封信里误抽的）。
    判定规则：
      · 遇到 === 子标题（语录/论学书）即停止
      · 段首是「某某字…」→ 该段是附传，主语换成那个人
      · 段首是「先生…」或首段 → 主语是本节人物
      · 其余段落（评论、引文）一律跳过
    """
    zone = re.split(r"^={3,}[^=\n]+={3,}\s*$", body, maxsplit=1, flags=re.M)[0]
    for i, para in enumerate([p for p in zone.split("\n") if p.strip()]):
        m = _LEAD_NAME.match(para)
        if m and m.group(1) in name_map:
            other = name_map[m.group(1)]
            if other != section_pid:
                yield other, para
                continue
        stripped = para.strip()
        if i == 0 or stripped.startswith("先生"):
            yield section_pid, para
