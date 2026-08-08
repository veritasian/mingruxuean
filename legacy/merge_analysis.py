#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将 analysis.json（书卷文本挖掘结果）合并进 data_final.json / data_timeline.json / data_geo.json：
 1) 新增书中人物（60 人）及其 籍贯/字/号
 2) 补师承边（书证）
 3) 用 进士年/生卒/享年 锚点修正人物所处皇帝时期
 4) 回填无籍贯人物的籍贯
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.dirname(os.path.abspath(__file__))

d = json.load(open(os.path.join(BASE, "data_final.json"), encoding="utf-8"))
a = json.load(open(os.path.join(BASE, "analysis.json"), encoding="utf-8"))
tl = json.load(open(os.path.join(BASE, "data_timeline.json"), encoding="utf-8"))
geo = json.load(open(os.path.join(BASE, "data_geo.json"), encoding="utf-8"))
from enrich_extra import G  # 明地→今地 映射

P = d["people"]
names = {p["name"]: k for k, p in P.items()}

def cn_int2zh(n):
    units = ["", "十", "百"]
    if n < 10: return "一二三四五六七八九"[n-1] if n else ""
    if n < 20: return "十" + ("一二三四五六七八九"[n-11] if n > 10 else "")
    tens, ones = n // 10, n % 10
    s = "一二三四五六七八九"[tens-1] + "十"
    if ones: s += "一二三四五六七八九"[ones-1]
    return s

# ---- 1) 新增人物 ----
new_added = 0
for nm, info in a["new_names"].items():
    if nm in names: continue
    pid = "bk%02d" % info["vol"] + nm
    base = pid
    k = 1
    while pid in P: pid = base + str(k); k += 1
    birth = info.get("birth_raw", "")
    P[pid] = {
        "name": nm, "school": info["school"], "birth": birth,
        "zi": info.get("zi_raw", ""), "hao": info.get("hao_raw", ""),
        "age": "", "life": "", "from_book": True, "vol": info["vol"],
    }
    names[nm] = pid
    # 学校成员表
    d["school_members"].setdefault(info["school"], []).append(pid)
    new_added += 1
print("新增人物:", new_added)

# ---- 2) 师承边 ----
edge_set = set(tuple(e) for e in d["edges"])
added_edges = 0
for r in a["relations"]:
    t = names.get(r["tgt"]); s = names.get(r["sub"])
    if not t or not s or t == s: continue
    if (t, s) in edge_set or (s, t) in edge_set: continue
    # 方向：t(师) → s(生)
    edge_set.add((t, s))
    d["edges"].append([t, s])
    P[t].setdefault("students", []); P[s].setdefault("teachers", [])
    if s not in P[t]["students"]: P[t]["students"].append(s)
    if t not in P[s]["teachers"]: P[s]["teachers"].append(t)
    added_edges += 1
print("新增师承边:", added_edges, "| 总边:", len(d["edges"]))

# ---- 3) 锚点 → 时期 ----
anchors = {}
for x in a["anchors"]:
    nm = x["name"]
    nm = {"王守仁": "王阳明"}.get(nm, nm)
    pid = names.get(nm)
    if not pid: continue
    anchors.setdefault(pid, []).append(x)
period = tl["period"]
updated = 0
for pid, lst in anchors.items():
    jin = [x["year"] for x in lst if x["kind"] == "jinshi"]
    dea = [x["year"] for x in lst if x["kind"] == "death"]
    ages = [x["age"] for x in lst if x["kind"] == "age"]
    cur = period.get(pid, {"birth": None, "death": None, "method": "不详", "active": None})
    if cur.get("method") == "史载":
        continue  # 已史载，不覆盖
    jin_y = max(jin) if jin else None
    dea_y = max(dea) if dea else None
    age = max(ages) if ages else None
    birth = None
    if dea_y and age:
        birth = dea_y - age
        method = "书载·生卒"
    elif jin_y:
        birth = jin_y - 30
        dea_y = min(1644, jin_y + 28)
        method = "书载·进士"
    else:
        continue
    if not (1350 <= birth <= 1650): continue
    active = [max(1350, birth + 18), min(1644, dea_y or birth + 60)]
    period[pid] = {"birth": birth, "death": dea_y, "method": method, "active": active}
    # 写 life/age 字段
    p = P[pid]
    if dea_y and age:
        p["life"] = "%d–%d" % (birth, dea_y)
        p["age"] = "年" + cn_int2zh(age)
    elif jin_y:
        p["age"] = ""
    updated += 1
print("时期更新/新增:", updated)

# ---- 4) 籍贯回填 + 新人物地理 ----
geo_map = geo["geo"]
filled = 0
for pid, p in P.items():
    g = geo_map.get(pid)
    if g and g["prov"] != "不详": continue
    br = p.get("birth", "")
    if not br: continue
    if br in G:
        gg = G[br]
        geo_map[pid] = {"prov": gg[0], "city": gg[1], "note": gg[2], "raw": br}
        filled += 1
    else:
        geo_map[pid] = {"prov": "待考", "city": "", "note": br, "raw": br}
print("籍贯地理补充:", filled)

# ---- 保存 ----
d["schools"] = [s for s in d["schools"] if s in d["school_members"]] + \
               [s for s in d["school_members"] if s not in d["schools"]]
json.dump(d, open(os.path.join(BASE, "data_final.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(tl, open(os.path.join(BASE, "data_timeline.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(geo, open(os.path.join(BASE, "data_geo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("保存完成: people=%d schools=%d edges=%d tongmen=%d" %
      (len(P), len(d["schools"]), len(d["edges"]), len(d.get("tongmen", []))))
print("时期覆盖: %d/%d" % (sum(1 for v in period.values() if v["active"]), len(P)))
