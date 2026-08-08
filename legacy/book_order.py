#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按《明儒学案》卷文书写顺序排序每个学案的成员（v3）。

标题格式（简体原文）：==谥/职+姓+号+先生+名==，如「文恭胡敬斋先生居仁」。
做法：
1. 逐卷抽取标题 → 按卷内出现顺序得 per-volume 人物次序。
2. 卷 → 所属学案（由该卷标题人物的多数派别判定）。
3. 每人取「首次出现的卷 + 卷内序号」。
4. 学案内排序：(本学案卷内有过标题 → 按卷内序号) 在前；(不在本学案卷中
   立传者——如 drawio 与书分派不同的人物 → 按姓名排末尾)。
输出：data_final.json 的 school_members 重排；每人新增 seq（全局顺序，备查）。
"""
import json, os, re
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
books = json.load(open(os.path.join(BASE, "resources", "volumes", "all.json"), encoding="utf-8"))
d = json.load(open(os.path.join(BASE, "data_final.json"), encoding="utf-8"))
P = d["people"]
NAME2ID = {}
for pid, p in P.items():
    NAME2ID.setdefault(p["name"], pid)

SKIP_GIVEN = {"语", "录", "语录", "集", "书", "传", "年谱", "学", "记", "草", "语要", "论学书",
              "劄记", "札记", "文", "序", "跋", "诗", "谱", "遗", "例", "问答", "问", "宗", "纲"}


def resolve(title):
    """标题 → 人物 id（先生 模式优先，标题含名回退）。"""
    jx = title.find("先生")
    if jx >= 2 and jx < len(title) - 1:
        given_raw = re.sub(r"[（(【].*", "", title[jx + 2:])
        given_raw = re.sub(r"[^一-鿿]", "", given_raw)
        if given_raw and given_raw not in SKIP_GIVEN:
            if jx >= 4 and title[jx - 4:jx - 2] in ("欧阳", "歐陽"):
                surname, hao = title[jx - 4:jx - 2], title[jx - 2:jx]
            else:
                surname, hao = title[jx - 3:jx - 2], title[jx - 2:jx]
            cand = surname + given_raw[:3]
            cand = {"王守仁": "王阳明", "王陽明": "王阳明"}.get(cand, cand)
            if cand in NAME2ID:
                return NAME2ID[cand]
    for nm, pid in NAME2ID.items():
        if len(nm) >= 2 and (title.endswith(nm) or nm in title):
            return pid
    return None


vol_heads = {}      # v -> [ids in heading order]
for item in sorted(books, key=lambda b: b["v"]):
    ids_in_vol = []
    sections = re.split(r"==([^=]{2,40})==", item["text"])
    for i in range(1, len(sections) - 1, 2):
        title = sections[i].strip()
        if title.startswith(("前言", "读法", "师说")):
            continue
        sid = resolve(title)
        if sid:
            ids_in_vol.append(sid)
    vol_heads[item["v"]] = ids_in_vol

# 卷 → 学案（多数派别）
vol_school = {}
for v, ids in vol_heads.items():
    cnt = Counter(P[i]["school"] for i in ids if i in P)
    vol_school[v] = cnt.most_common(1)[0][0] if cnt else None

# 每人：首次出现的卷 + 卷内序号
first_vol, first_idx = {}, {}
for v in sorted(vol_heads):
    for idx, sid in enumerate(vol_heads[v]):
        if sid not in first_vol:
            first_vol[sid], first_idx[sid] = v, idx

seq_counter = 0
for v in sorted(vol_heads):
    for sid in vol_heads[v]:
        if sid not in P:
            continue
        if "seq" not in P[sid]:
            seq_counter += 1
            P[sid]["seq"] = seq_counter

listed = sum(1 for pid, p in P.items() if "seq" in p)
print("有书序人物:", listed, "/", len(P))

for sch, ids in (d.get("school_members") or {}).items():
    # 分组：本学案卷内立传者优先；组内按全局书序（seq）排；无书序者按姓名
    ids.sort(key=lambda a: (
        0 if (a in first_vol and vol_school.get(first_vol[a]) == sch) else 1,
        P[a].get("seq", 10 ** 9),
        P[a]["name"],
    ))

json.dump(d, open(os.path.join(BASE, "data_final.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("school_members 已按书序排序。抽查：")
for sch, ids in list(d["school_members"].items())[:8]:
    print("  ", sch, "→", [P[i]["name"] for i in ids[:8]])
