#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_persons.py —— 人物规范化（数据层第一步）

输入：legacy/data_final.json（drawio 抽取的旧结构，id 不稳定）
      legacy/data_geo.json（籍贯解析结果）
输出：data/persons.json     稳定 id 的人物库
      data/schools.json     学案（学派）定义
      data/id_map.json      旧 id → 新 id 的映射（可溯源、可回滚）

设计要点
1. 稳定 id：直接用人物姓名（汉字）作为 id，重名时按学案后缀区分。
   旧 id 形如 aZOgffvFExYyYC5foWOi-213，是 drawio 内部编号，换一次源图就全变，
   不能作为数据库主键。
2. 重复人物合并：同名同学案的多条记录（drawio 画了两个框）合并为一条，
   字段取并集，seq 取有值者。
3. 每个字段带来源标记，写入 provenance。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from normalize import norm_text, canonical_name  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LEGACY = os.path.join(ROOT, "legacy")
DATA = os.path.join(ROOT, "data")


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def dump(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    print("  写出 %-28s %8.1f KB" % (os.path.relpath(path, ROOT), os.path.getsize(path) / 1024))


def make_stable_id(name, school, used):
    """姓名作主键；重名则加学案短名后缀。"""
    base = name
    if base not in used:
        return base
    short = school.replace("学案", "").replace("王门", "")
    cand = "%s-%s" % (base, short)
    n = 2
    while cand in used:
        cand = "%s-%s%d" % (base, short, n)
        n += 1
    return cand


def merge_records(a, b):
    """合并同名重复记录：非空优先，列表取并集。"""
    out = dict(a)
    for k, v in b.items():
        if isinstance(v, list):
            merged = list(out.get(k) or [])
            for item in v:
                if item not in merged:
                    merged.append(item)
            out[k] = merged
        elif not out.get(k) and v:
            out[k] = v
    return out


def main():
    final = load(os.path.join(LEGACY, "data_final.json"))
    geo = load(os.path.join(LEGACY, "data_geo.json")).get("geo", {})
    people = final["people"]

    # ---- 1. 规范化姓名（繁简+异体+已核对讹字），按 (规范名, 学案) 合并 ----
    groups, notes = {}, []
    for old_id, rec in people.items():
        rec = dict(rec)
        raw = rec["name"]
        cname, reason = canonical_name(raw)
        if cname != raw:
            notes.append({"legacy_id": old_id, "raw": raw, "canonical": cname,
                          "reason": reason or "繁简/异体字归一"})
        rec["name"] = cname
        rec["zi"] = norm_text(rec.get("zi") or "")
        rec["hao"] = norm_text(rec.get("hao") or "")
        rec["head"] = norm_text(rec.get("head") or "")
        rec["_old_ids"] = [old_id]
        key = (cname, rec.get("school", ""))
        groups[key] = merge_records(groups[key], rec) if key in groups else rec

    merged_count = len(people) - len(groups)

    # 跨学案同名：不自动合并，只登记待人工复核（宁可保留也不误并）
    seen = {}
    review = []
    for (nm, sch) in groups:
        if nm in seen and seen[nm] != sch:
            review.append({"name": nm, "schools": [seen[nm], sch],
                           "action": "需人工判定是否同一人"})
        seen[nm] = sch

    # ---- 2. 分配稳定 id ----
    used = set()
    id_map = {}       # old id -> new id
    persons = {}
    for (name, school), rec in groups.items():
        new_id = make_stable_id(name, school, used)
        used.add(new_id)
        for old in rec["_old_ids"]:
            id_map[old] = new_id
        persons[new_id] = rec

    # ---- 3. 归一化字段 + 挂籍贯 ----
    out = {}
    for new_id, rec in persons.items():
        g = {}
        for old in rec["_old_ids"]:
            if old in geo:
                g = geo[old]
                break
        life = rec.get("life") or ""
        birth_year = death_year = None
        if "–" in life:
            a, b = life.split("–", 1)
            birth_year = int(a) if a.strip().isdigit() else None
            death_year = int(b) if b.strip().isdigit() else None
        out[new_id] = {
            "id": new_id,
            "name": rec["name"],
            "zi": rec.get("zi") or "",
            "hao": rec.get("hao") or "",
            "title": rec.get("title") or "",
            "role": rec.get("role") or "",
            "head": rec.get("head") or "",
            "school": rec.get("school") or "",
            "seq": rec.get("seq"),
            "life": {"raw": life, "birth": birth_year, "death": death_year,
                     "age": rec.get("age") or ""},
            "origin": {"raw": rec.get("birth") or "", "province": g.get("prov") or "",
                       "city": g.get("city") or "", "county": g.get("note") or ""},
            "legacy_ids": sorted(rec["_old_ids"]),
        }

    # ---- 4. 学案定义 ----
    founders = final.get("founders", {})
    members = final.get("school_members", {})
    schools = []
    for i, s in enumerate(final["schools"]):
        raw_members = members.get(s, [])
        schools.append({
            "id": s,
            "name": s,
            "order": i,
            "founders": [canonical_name(f)[0] for f in founders.get(s, [])],
            "members": [id_map[m] for m in raw_members if m in id_map],
        })

    os.makedirs(DATA, exist_ok=True)
    dump(out, os.path.join(DATA, "intermediate", "persons.stage1.json"))
    dump(schools, os.path.join(DATA, "intermediate", "schools.stage1.json"))
    dump(id_map, os.path.join(DATA, "id_map.json"))
    dump({"normalized": notes, "cross_school_same_name": review},
         os.path.join(DATA, "intermediate", "persons_review.json"))

    print("  人物 %d 条（合并重复 %d 条）· 学案 %d 个" % (len(out), merged_count, len(schools)))
    print("  姓名规范化 %d 处 · 跨学案同名待复核 %d 组" % (len(notes), len(review)))
    unresolved = [m for s in members.values() for m in s if m not in id_map]
    if unresolved:
        print("  !! 未能映射的成员 id: %d" % len(unresolved), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
