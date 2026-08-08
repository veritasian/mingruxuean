#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
link_book_sections.py —— 把人物锚定到《明儒学案》原书章节（权威来源）

背景：原来的学派归属来自 drawio 手绘图，有错。核对原文发现：
    刘永澄 / 史孟鳞  drawio 记为「蕺山学案」，原书在 卷60 东林学案三
    邹元标          drawio 记为「东林学案」，原书在 卷23 江右王门学案八
所以正确做法是**以原书章节为准**，drawio 只作补充属性。

章节标题文法： [尊称/官职]{0,4} [姓][号或字] 先生 [名]
    忠介邹南臬先生元标   → 姓邹 · 号南臬 · 名元标 → 邹元标
    处士王心斋先生艮     → 姓王 · 号心斋 · 名艮   → 王艮

输出 data/book_index.json： person_id -> {volume, volume_name, section, seq, school}
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from normalize import norm_text, canonical_name  # noqa: E402
from alias_index import surname_of               # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "data")


def split_sections(text):
    parts = re.split(r"^==([^=\n]+)==\s*$", text, flags=re.M)
    return [(parts[i].strip(), parts[i + 1]) for i in range(1, len(parts) - 1, 2)]


def school_of_volume(vol_name):
    """『东林学案三』→『东林学案』"""
    m = re.match(r"(.+?学案)", norm_text(vol_name))
    return m.group(1) if m else norm_text(vol_name)


def parse_heading(title):
    """返回 (左段, 名)。无『先生』时右段为空。"""
    t = norm_text(re.sub(r"[（(].*?[)）]", "", title)).strip()
    if "先生" in t:
        left, given = t.split("先生", 1)
        return left, given.strip()
    return t, ""


def appendix_names(title):
    m = re.search(r"[（(](.*?)[)）]", title)
    if not m:
        return []
    inner = norm_text(m.group(1)).replace("附", "")
    return [x for x in re.split(r"[　\s、,，]+", inner) if len(x) >= 2]


def main():
    persons = json.load(open(os.path.join(DATA, "intermediate", "persons.stage1.json"), encoding="utf-8"))
    volumes = json.load(open(os.path.join(ROOT, "resources", "volumes", "all.json"),
                             encoding="utf-8"))

    by_given = {}
    for pid, p in persons.items():
        nm = p["name"]
        sn = surname_of(nm)
        by_given.setdefault(nm[len(sn):], []).append((pid, sn, p))

    index, unmatched, seq = {}, [], 0
    for vol in sorted(volumes, key=lambda v: v["v"]):
        school = school_of_volume(vol["name"])
        for title, body in split_sections(vol["text"]):
            if re.match(r"^(前言|序|小引|附录)$", norm_text(title)):
                continue
            seq += 1
            left, given = parse_heading(title)
            pid = None
            for cand_given in ([given] if given else []):
                for cpid, sn, p in by_given.get(cand_given, []):
                    if sn in left or (p["hao"] and p["hao"] in left):
                        pid = cpid
                        break
                if pid:
                    break
            if not pid:                       # 退化：整名直接出现在标题里
                for cpid, p in persons.items():
                    if p["name"] in norm_text(title):
                        pid = cpid
                        break
            if not pid:
                unmatched.append({"volume": vol["v"], "school": school, "title": title})
                continue
            index[pid] = {"volume": vol["v"], "volume_name": norm_text(vol["name"]),
                          "section": norm_text(title), "seq": seq, "school": school,
                          "chars": len(body), "appendix": appendix_names(title)}

    json.dump(index, open(os.path.join(DATA, "intermediate", "book_index.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump(unmatched, open(os.path.join(DATA, "intermediate", "book_unmatched.json"), "w",
                              encoding="utf-8"), ensure_ascii=False, indent=1)

    conflicts = [(pid, persons[pid]["school"], v["school"])
                 for pid, v in index.items() if persons[pid]["school"] != v["school"]]
    print("  原书章节 %d 个 · 对齐人物 %d 人 · 未对齐章节 %d 个"
          % (seq, len(index), len(unmatched)))
    print("  学派归属冲突（以原书为准）%d 处：" % len(conflicts))
    for pid, old, new in conflicts[:20]:
        print("     %-10s drawio=%-12s → 原书=%s" % (pid, old, new))
    return 0


if __name__ == "__main__":
    sys.exit(main())
