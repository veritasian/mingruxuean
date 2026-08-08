#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_relations.py —— 合并四路关系源，产出 data/relations.json

四路来源，可信度与可溯源程度不同，必须分别标注而不是混成一团：

  drawio    167 条  谱系总图手绘边。人工梳理过、覆盖面广，但没引文。
                    ⚠ 总图方向是「师→徒」，与本库约定（from=徒、to=师）相反，
                    导入时统一翻转，方向语义才与 mined/mingshi 一致。
  legacy     43 条  前一轮抽取，带原文片段和卷次。
  mined      89 条  本轮抽取，带章节、正则、原文引文、别名命中、置信度。
  mingshi   108 条  《明史》卷282/283 儒林传人工精读（scripts/ingest/mingshi_data.py），
                    带卷次与原文引文，方向 from=徒、to=师。

同一条边被多源印证 → 置信度上调（互证）；只有 drawio 一源 → 标 needs_citation，
将来补上原文出处再升级。这样「哪条边靠得住」在数据里是明写的，不靠猜。
"""
import json
import os
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "data")
MID = os.path.join(DATA, "intermediate")
LEGACY = os.path.join(ROOT, "legacy")
MINGSHI = os.path.join(ROOT, "resources", "mingshi", "mingshi.json")

sys.path.insert(0, os.path.join(ROOT, "scripts", "ingest"))
from normalize import canonical_name                              # noqa: E402


def load(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    persons = load(os.path.join(DATA, "persons.json"))
    id_map = load(os.path.join(DATA, "id_map.json"))
    mined = load(os.path.join(MID, "relations.mined.json"))
    legacy = load(os.path.join(LEGACY, "data_final.json"))
    analysis = load(os.path.join(LEGACY, "analysis.json"))
    mingshi = load(MINGSHI)
    today = date.today().isoformat()

    def resolve(x):
        """legacy drawio id 或姓名 → 新 person id。"""
        if x in persons:
            return x
        if x in id_map and id_map[x] in persons:
            return id_map[x]
        n = canonical_name(x)[0]
        return n if n in persons else None

    bucket = {}

    def put(a, b, kind, src, prov):
        if not a or not b or a == b:
            return
        k = (a, b, kind)
        rec = bucket.setdefault(k, {"from": a, "to": b, "type": kind,
                                    "sources": [], "provenance": []})
        if src not in rec["sources"]:
            rec["sources"].append(src)
        rec["provenance"].append(prov)

    # --- 1. 上一轮抽取（带原文片段）---
    for r in analysis.get("relations", []):
        put(resolve(r.get("sub")), resolve(r.get("tgt")), "师承", "legacy-mining",
            {"source": "legacy-mining", "method": "regex-mining-v1",
             "pattern": r.get("kind"), "volume": r.get("vol"),
             "quote": r.get("raw", "")})

    # --- 2. 本轮抽取（带章节/正则/引文/别名）---
    for r in mined:
        put(r["from"], r["to"], r["type"], "mined", dict(r["provenance"],
                                                         source="mined"))

    # --- 3. 《明史》儒林传人工精读（卷282/283，带原文引文）---
    # 端点（许谦、饶鲁等元儒）不在人物库的边不写进 relations.json，
    # 否则会产生前端画不出来的幽灵边。人物档案仍完整留在 mingshi.json。
    for r in mingshi.get("relations", []):
        if r["from"] not in persons or r["to"] not in persons:
            continue
        put(r["from"], r["to"], r["type"], "mingshi",
            {"source": "mingshi", "method": "manual-reading",
             "volume": r.get("volume"), "quote": r.get("quote", ""),
             "note": "《明史》儒林传" + ("卷%d" % r["volume"] if r.get("volume") else "")})

    # --- 4. drawio 谱系总图（兜底/印证源，最后处理）---
    # 原图方向是「师→徒」，翻转为 徒→师 与全局约定一致。
    # 若该对（任意类型）已有更精确来源（legacy/mined/mingshi）→ 并入印证，
    # 不另建方向或类型冲突的边。例如 邓以赞 私淑王阳明（mined），
    # drawio 原图画成直传，翻转后并入私淑边而非生成一条假「师承」。
    for a, b in legacy.get("edges", []):
        ra, rb = resolve(a), resolve(b)
        if not ra or not rb or ra == rb:
            continue
        fa, fb = rb, ra          # 翻转为 徒→师
        prov = {"source": "drawio", "method": "hand-drawn-graph",
                "legacy_from": a, "legacy_to": b,
                "note": "谱系总图连线（原图师→徒，已翻转为徒→师），暂无原文出处"}
        existing = [bucket[x] for x in bucket if x[0] == fa and x[1] == fb]
        if existing:
            rec = existing[0]
            if "drawio" not in rec["sources"]:
                rec["sources"].append("drawio")
            rec["provenance"].append(prov)
        else:
            put(fa, fb, "师承", "drawio", prov)

    # --- 置信度：多源互证加权 ---
    conf_by_src = {"mined": 0.0, "legacy-mining": 0.80, "drawio": 0.70,
                   "mingshi": 0.95}   # 人工精读+原文引文，可信度最高
    mined_conf = {(r["from"], r["to"], r["type"]): r["confidence"] for r in mined}

    out = []
    for k, rec in bucket.items():
        base = max([mined_conf.get(k, 0)] +
                   [conf_by_src[s] for s in rec["sources"] if s != "mined"])
        if len(rec["sources"]) > 1:                # 互证
            base = min(0.99, base + 0.06 * (len(rec["sources"]) - 1))
        rec["confidence"] = round(base, 3)
        rec["cited"] = any(s != "drawio" for s in rec["sources"])
        rec["needs_citation"] = not rec["cited"]
        out.append(rec)

    out.sort(key=lambda r: (-r["confidence"], r["from"], r["to"]))

    # --- 度数统计 ---
    # 只数谱系图真会画出来的边（师承/私淑）。「附见」是原书的编排位置，
    # 不是师徒授受，图上不连线 —— 若在这里把它算作边，就会出现
    # 「图上明明是孤点，孤点表里却查无此人」。规则见 analyze_orphans.EDGE_TYPES。
    edge_types = {"师承", "私淑"}
    deg = {pid: 0 for pid in persons}
    for r in out:
        if r["type"] not in edge_types:
            continue
        deg[r["from"]] = deg.get(r["from"], 0) + 1
        deg[r["to"]] = deg.get(r["to"], 0) + 1
    orphans = sorted([p for p in persons if deg[p] == 0])

    doc = {
        "$schema": "./schema/relations.schema.json",
        "meta": {
            "built_at": today,
            "count": len(out),
            "by_type": _tally(out, "type"),
            "by_source": _tally_multi(out, "sources"),
            "cited": sum(1 for r in out if r["cited"]),
            "needs_citation": sum(1 for r in out if r["needs_citation"]),
            "note": "confidence 为综合置信度；provenance 保留每一路来源的原始证据；"
                    "孤点数以 orphans.json 为准，不在此处重复登记",
        },
        "relations": out,
    }
    _dump(doc, os.path.join(DATA, "relations.json"))
    _dump({"built_at": today, "degree": deg, "orphans": orphans},
          os.path.join(MID, "degree.json"))

    print("  关系 %d 条 %s" % (len(out), doc["meta"]["by_type"]))
    print("  来源分布 %s" % doc["meta"]["by_source"])
    print("  有原文出处 %d 条 · 仅谱系图待补证 %d 条"
          % (doc["meta"]["cited"], doc["meta"]["needs_citation"]))
    print("  孤点 %d / %d 人" % (len(orphans), len(persons)))
    return 0


def _tally(rows, key):
    d = {}
    for r in rows:
        d[r[key]] = d.get(r[key], 0) + 1
    return d


def _tally_multi(rows, key):
    d = {}
    for r in rows:
        for v in r[key]:
            d[v] = d.get(v, 0) + 1
    return d


def _dump(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    print("  写出 %-30s %8.1f KB" % (os.path.relpath(path, ROOT),
                                     os.path.getsize(path) / 1024))


if __name__ == "__main__":
    sys.exit(main())
