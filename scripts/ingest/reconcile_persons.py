#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reconcile_persons.py —— 以原书为准，产出最终人物库

处理三件事：
1. 学派归属冲突：drawio 与原书不一致时以原书章节为准，并把改动记进 provenance。
2. 跨学案重名：一方能锚定到原书章节、另一方不能 → 判为同一人，合并。
3. 补齐 seq（原书出场顺序）与 anchor（卷次/章节），这是「可溯源」的核心字段。

输出 data/persons.json、data/schools.json
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hao as haomod                                     # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "data")
MID = os.path.join(DATA, "intermediate")


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def dump(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    print("  写出 %-32s %8.1f KB" % (os.path.relpath(path, ROOT),
                                     os.path.getsize(path) / 1024))


def main():
    persons = load(os.path.join(MID, "persons.stage1.json"))
    schools = load(os.path.join(MID, "schools.stage1.json"))
    book = load(os.path.join(MID, "book_index.json"))

    changes = []

    # ---- 1. 跨学案重名合并（书中有传者为主）----
    by_name = {}
    for pid, p in persons.items():
        by_name.setdefault(p["name"], []).append(pid)
    alias_to_primary = {}
    for name, ids in by_name.items():
        if len(ids) < 2:
            continue
        anchored = [i for i in ids if i in book]
        if len(anchored) == 1:
            primary = anchored[0]
            for other in ids:
                if other == primary:
                    continue
                alias_to_primary[other] = primary
                for k, v in persons[other].items():
                    if isinstance(v, list) and k == "legacy_ids":
                        persons[primary]["legacy_ids"] = sorted(
                            set(persons[primary]["legacy_ids"]) | set(v))
                changes.append({"type": "merge_duplicate", "removed": other,
                                "kept": primary,
                                "reason": "重名且仅『%s』在原书卷%s有传" %
                                          (primary, book[primary]["volume"])})
    for dead in alias_to_primary:
        persons.pop(dead, None)

    # ---- 2. 学派以原书为准 + 写入锚点 ----
    for pid, p in persons.items():
        anchor = book.get(pid)
        if anchor:
            if p["school"] != anchor["school"] and anchor["school"] != "附案":
                changes.append({"type": "school_override", "person": pid,
                                "from": p["school"], "to": anchor["school"],
                                "reason": "原书卷%s《%s》设有本传"
                                          % (anchor["volume"], anchor["section"])})
                p["school"] = anchor["school"]
            p["seq"] = anchor["seq"]
            p["anchor"] = {"volume": anchor["volume"],
                           "volume_name": anchor["volume_name"],
                           "section": anchor["section"],
                           "text_chars": anchor["chars"]}
            p["has_biography"] = True
        else:
            p["anchor"] = None
            p["has_biography"] = False
            p.setdefault("seq", None)

    # ---- 2b. 补「号」：原书标题 > zi 内嵌 > head ----
    # 原文极少直呼姓名，「白沙」「甘泉」「龙溪」才是常用称呼；
    # 号缺失 → 别名索引建不出来 → 师承一条都抽不到。
    filled = 0
    for pid, p in persons.items():
        section = (book.get(pid) or {}).get("section", "")
        old = p.get("hao", "")
        h, src = haomod.derive(p, section)
        if not h:
            h, src = haomod.hao_from_head_text(p.get("head", "")), "head_text"
        if h and h != old:
            p["hao"] = h
            p["hao_source"] = src
            filled += 1
            changes.append({"type": "hao_fixed" if old else "hao_filled",
                            "person": pid, "hao": h, "was": old, "source": src,
                            "reason": "原书章节《%s》" % section if src == "book_section"
                                      else "由『%s』还原" % src})
        elif h:
            p["hao_source"] = src
        # 字段里混入的「号X」要从 zi 中摘掉，否则 姓+字 别名是脏的
        z, embedded = haomod.split_zi_hao(p.get("zi", ""))
        if embedded and z != p.get("zi"):
            p["zi"] = z

    # 无本传者排到本学案末尾，保持稳定顺序
    max_seq = max([p["seq"] for p in persons.values() if p["seq"]] or [0])
    for i, pid in enumerate(sorted(p for p in persons if persons[p]["seq"] is None)):
        persons[pid]["seq"] = max_seq + 1 + i

    # ---- 3. 重建学案成员（按原书顺序）----
    grouped = {}
    for pid, p in persons.items():
        grouped.setdefault(p["school"], []).append(pid)
    out_schools = []
    known = {s["id"]: s for s in schools}
    for sid in sorted(grouped, key=lambda s: known.get(s, {}).get("order", 99)):
        base = known.get(sid, {"id": sid, "name": sid, "order": 99, "founders": []})
        members = sorted(grouped[sid], key=lambda i: persons[i]["seq"])
        out_schools.append({"id": sid, "name": sid, "order": base.get("order", 99),
                            "founders": [f for f in base.get("founders", [])
                                         if f in persons],
                            "members": members,
                            "member_count": len(members),
                            "with_biography": sum(1 for m in members
                                                  if persons[m]["has_biography"])})
    for i, s in enumerate(out_schools):
        s["order"] = i

    dump(persons, os.path.join(DATA, "persons.json"))
    dump(out_schools, os.path.join(DATA, "schools.json"))
    dump(changes, os.path.join(MID, "reconcile_changes.json"))

    n_bio = sum(1 for p in persons.values() if p["has_biography"])
    print("  人物 %d 人（有本传 %d · 仅见于他人传中 %d）"
          % (len(persons), n_bio, len(persons) - n_bio))
    print("  学派归属订正 %d 处 · 重名合并 %d 处 · 补号 %d 处"
          % (sum(1 for c in changes if c["type"] == "school_override"),
             sum(1 for c in changes if c["type"] == "merge_duplicate"), filled))
    print("  仍无号者 %d 人" % sum(1 for p in persons.values() if not p.get("hao")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
