#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_orphans.py —— 给孤点定性，产出 data/orphans.json

图上那些不连线的圆点，不能一律当成「数据没做完」。把 52 个孤点摊开看，
分布本身就是一条结论：

    诸儒学案  29/40 = 72%      东林学案  9/16 = 56%
    泰州学案  10/29 = 34%      白沙/河东/甘泉 合计 5

黄宗羲编《明儒学案》，最后立「诸儒学案」，收的正是「不能归入各家门户」者
——方孝孺、罗钦顺、王廷相、吕坤、黄道周皆在其中。它的孤点率高，不是抽漏，
是编纂意图在图上的投影：这一卷本来就没有师承可连。

东林则是另一种。它的凝聚力是横的不是纵的：东林书院的讲会、「同志」相呼，
而非师徒授受。孤点率高说明用师承一种边去画东林，本来就画不出它的样子。

于是把孤点分成五类，各自给出判读，而不是笼统算作缺陷：
    structural   编纂设计使然（诸儒学案）
    horizontal   以讲会、同志相联，非师徒纵贯（东林学案）
    appendix     原书附于他人传后，未立专条（樵夫朱恕、陶匠韩乐吾）
    no_record    原书未立本传，仅见于他人传中，史料本身无征
    gap          有本传却未抽出师承，属本项目的数据缺口，待补

关于「谁算孤点」：以谱系图实际会画出的边为准 —— 即 EDGE_TYPES 之内的边。
「附见」是原书的编排位置（某人附于某传之后），不是师徒授受，图上不连线，
所以只有附见记载的人在图上仍是孤点。这条规则必须和前端 model.edgeList()
完全一致，tests/test_data.py 会逐个人物比对；一旦两边分叉，测试立刻报错。
"""
import json
import os
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "data")
MID = os.path.join(DATA, "intermediate")

# 谱系图会画出来的边；与 src/data/model.js 的 edgeList() 同步
EDGE_TYPES = {"师承", "私淑"}

KINDS = {
    "structural": {
        "label": "编纂设计使然",
        "desc": "《诸儒学案》是黄宗羲专为「不能归入各家门户」者所立。"
                "方孝孺、罗钦顺、王廷相、吕坤、黄道周皆在此卷。"
                "此处无师承边，是原书的编纂意图，不是抽取的疏漏。",
    },
    "horizontal": {
        "label": "横向结社，非师徒纵贯",
        "desc": "东林以书院讲会相聚、以「同志」相呼，凝聚力是横的。"
                "用师承一种边去画东林，本来就画不全它的样子。",
    },
    "appendix": {
        "label": "附于他人传后",
        "desc": "原书未给他们立专条，而是附在别人的传后 —— 如「处士王东崖先生襞"
                "（附樵夫朱恕　陶匠韩乐吾　田夫夏叟）」。附见是编排位置，"
                "不是师徒授受，故图上不连线。其人其学皆在，只是不占一条边。",
    },
    "no_record": {
        "label": "原书未立本传",
        "desc": "仅见于他人传中的附带记载，原书没有给出师承线索，史料本身无征。",
    },
    "gap": {
        "label": "数据缺口，待补",
        "desc": "原书立有本传，但本轮未能抽出师承。属于本项目的已知缺口。",
    },
}


def classify(p, appendix_of):
    """先看有没有实证（附见记载），再看学案的编纂性质，最后才归为缺口"""
    if p["id"] in appendix_of:
        return "appendix"
    if p["school"] == "诸儒学案":
        return "structural"
    if p["school"] == "东林学案":
        return "horizontal"
    if not p.get("has_biography"):
        return "no_record"
    return "gap"


def compute_orphans(persons, relations):
    """孤点 = 不在任何一条「会画出来的边」上的人"""
    linked = set()
    appendix_of = {}
    for r in relations:
        if r["type"] in EDGE_TYPES:
            linked.add(r["from"])
            linked.add(r["to"])
        elif r["type"] == "附见":
            appendix_of.setdefault(r["from"], r["to"])
    return sorted(set(persons) - linked), appendix_of


def main():
    persons = json.load(open(os.path.join(DATA, "persons.json"), encoding="utf-8"))
    rel_doc = json.load(open(os.path.join(DATA, "relations.json"), encoding="utf-8"))
    relations = rel_doc["relations"]
    orphans, appendix_of = compute_orphans(persons, relations)

    deg_file = os.path.join(MID, "degree.json")
    if os.path.exists(deg_file):
        raw = json.load(open(deg_file, encoding="utf-8"))["orphans"]
        extra = sorted(set(orphans) - set(raw))
        if extra:
            print("  注：%s 只有附见记载，图上不连线，计入孤点" % "、".join(extra))

    items, by_kind, by_school = [], {}, {}
    for pid in orphans:
        p = persons[pid]
        k = classify(p, appendix_of)
        items.append({"id": pid, "name": p["name"], "school": p["school"],
                      "kind": k, "has_biography": p.get("has_biography", False),
                      "volume": (p.get("anchor") or {}).get("volume"),
                      "appendix_of": appendix_of.get(pid)})
        by_kind[k] = by_kind.get(k, 0) + 1
        by_school.setdefault(p["school"], {"orphans": 0, "total": 0})
        by_school[p["school"]]["orphans"] += 1

    for p in persons.values():
        by_school.setdefault(p["school"], {"orphans": 0, "total": 0})
        by_school[p["school"]]["total"] += 1
    for s, v in by_school.items():
        v["rate"] = round(v["orphans"] / v["total"], 3) if v["total"] else 0

    doc = {
        "$schema": "./schema/orphans.schema.json",
        "meta": {
            "built_at": date.today().isoformat(),
            "orphan_count": len(orphans),
            "person_count": len(persons),
            "by_kind": by_kind,
            "headline": "孤点不等于数据缺失：%d 个孤点中 %d 个是编纂设计、编排位置"
                        "或史料本身无征，真正待补的只有 %d 个。"
                        % (len(orphans),
                           len(orphans) - by_kind.get("gap", 0),
                           by_kind.get("gap", 0)),
        },
        "kinds": KINDS,
        "by_school": dict(sorted(by_school.items(),
                                 key=lambda kv: -kv[1]["rate"])),
        "orphans": sorted(items, key=lambda x: (x["kind"], x["school"], x["name"])),
    }

    out = os.path.join(DATA, "orphans.json")
    json.dump(doc, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  写出 %-30s %8.1f KB" % (os.path.relpath(out, ROOT),
                                     os.path.getsize(out) / 1024))
    print("  孤点 %d：%s" % (len(orphans), by_kind))
    print("  " + doc["meta"]["headline"])
    for s, v in list(doc["by_school"].items())[:5]:
        if v["orphans"]:
            print("    %-12s %2d/%2d = %.0f%%" % (s, v["orphans"], v["total"],
                                                  v["rate"] * 100))
    return 0


if __name__ == "__main__":
    sys.exit(main())
