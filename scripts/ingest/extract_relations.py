#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_relations.py —— 从 63 卷原文补抽师承关系（每条带出处）

为什么要补：drawio 源图只画了 167 条边，250 人里 85 人一条边都没有，
在知识图谱上成了孤点。但《明儒学案》的「传」里白纸黑字写着师承，
只是从没被抽出来过。

输出 data/intermediate/relations.mined.json，每条形如：
{
  "from": "徐樾", "to": "王艮", "type": "师承", "confidence": 0.93,
  "provenance": {"volume": 32, "section": "布政徐波石先生樾",
                 "pattern": "师事", "quote": "……先生师事心斋……",
                 "method": "regex-mining"}
}
"""
import json
import os
import re
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from normalize import norm_text                                  # noqa: E402
from alias_index import build_alias_index, alias_pattern         # noqa: E402
from sections import (split_sections, build_given_index,         # noqa: E402
                      match_section, appendix_names, SKIP_TITLES,
                      bio_paragraphs)
import guards                                                    # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "data")
MID = os.path.join(DATA, "intermediate")

# 「师事吴子往志远、高忠宪」「受学于张甑山、耿楚倥」——老师常常并列列举，
# 而排在前面的那位往往不在我们的人物表里。只认第一个名字就会整条抽不到，
# 所以允许先跳过至多两个「未知名字、」再去匹配已知别名。
# 必须用惰性 {0,2}?：贪婪会跳过已知的老师去匹配后面的人（师事[甘泉]、某某）。
LIST = r"(?:[^，。；、「」\s]{2,6}、){0,2}?"

# 师承线索：分数越高越可信。(?P<t>…) 捕获老师别名。
RULES = [
    ("师事", r"师事" + LIST + r"(?P<t>{A})", 0.95),
    ("受业于", r"受业(?:于)?" + LIST + r"(?P<t>{A})", 0.93),
    ("受学于", r"受学(?:于)?" + LIST + r"(?P<t>{A})", 0.92),
    ("从学于", r"从学(?:于)?" + LIST + r"(?P<t>{A})", 0.90),
    ("问学于", r"问学(?:于)?" + LIST + r"(?P<t>{A})", 0.88),
    ("执贽", r"执贽(?:于)?" + LIST + r"(?P<t>{A})", 0.90),
    ("卒业于", r"卒业(?:于)?" + LIST + r"(?P<t>{A})", 0.85),
    ("师之", r"(?P<t>{A})[^。；，]{0,6}而师之", 0.85),
    ("从游", r"从(?P<t>{A})游", 0.84),
    ("之门", r"(?:游|出|及|登)(?P<t>{A})之门", 0.86),
    # 「阳明门下解之者曰」是评论学派，不是传主师承 —— 必须要有动词坐实
    ("门下", r"(?:出|入|游|列|及|登|在|从|归)(?:于)?(?P<t>{A})(?:之)?门下", 0.80),
    ("学于", r"(?<![讲教]) *学于(?P<t>{A})", 0.75),
    ("师某先生", r"师(?P<t>{A})先生", 0.78),
    ("从某学", r"从(?P<t>{A})(?:先生)?(?:学|受|问)", 0.86),
    ("事某", r"(?:得|始|尝)事(?P<t>{A})", 0.82),
    ("谒某", r"(?<!称)谒(?P<t>{A})", 0.74),
    ("得某之传", r"得(?P<t>{A})之(?:传|绪)", 0.84),
    ("称弟子", r"(?P<t>{A})[^。；]{0,8}称弟子", 0.80),
    ("某弟子", r"(?P<t>{A})(?:之)?弟子", 0.88),          # 「白沙弟子」
    ("某门人", r"(?P<t>{A})(?:之)?门人", 0.84),
    ("而师之", r"(?P<t>{A})[^。；]{0,24}而师(?:焉|之)", 0.86),
    ("闻某之学", r"(?:闻|慕)(?P<t>{A})(?:之学|之风)", 0.70),
    ("从某归", r"从(?P<t>{A})(?:归|游|于)", 0.78),
    ("禀学", r"(?P<t>{A})[^。；]{0,30}(?:禀学|问学|受教)", 0.68),
    ("私淑", r"私淑(?P<t>{A})", 0.60),
]


def enumerate_more(para, pos, alias_rx, limit=3):
    """从 pos 起吃「、别名」串，返回后续并列的老师别名。"""
    out = []
    while len(out) < limit:
        if pos >= len(para) or para[pos] not in "、及与":
            break
        m = alias_rx.match(para, pos + 1)
        if not m:
            break
        out.append((m.group(0), m.start()))
        pos = m.end()
    return out


def main():
    persons = json.load(open(os.path.join(DATA, "persons.json"), encoding="utf-8"))
    volumes = json.load(open(os.path.join(ROOT, "resources", "volumes", "all.json"),
                             encoding="utf-8"))

    index, ambiguous = build_alias_index(persons)
    A = alias_pattern(index)
    # 用 replace 而非 format：正则里的 {0,6} 会被 format 当成占位符
    compiled = [(tag, re.compile(p.replace("{A}", A)), s) for tag, p, s in RULES]
    given_index = build_given_index(persons)
    name_map = {p["name"]: pid for pid, p in persons.items()}

    alias_rx = re.compile(A)
    today = date.today().isoformat()
    found, unmatched, rejected = [], [], []

    for vol in volumes:
        vname = norm_text(vol["name"])
        for title, body in split_sections(vol["text"]):
            if SKIP_TITLES.match(norm_text(title)):
                continue
            pid = match_section(title, persons, given_index)
            if not pid:
                unmatched.append("%s/%s" % (vname, title))
                continue
            body = norm_text(body)

            # (a) 标题里的「附某某」→ 附见关系（朱恕、韩乐吾这类孤点靠这个连上）
            for cand in appendix_names(title):
                for nm, other in name_map.items():
                    if nm in cand and other != pid:
                        found.append({
                            "from": other, "to": pid, "type": "附见",
                            "confidence": 0.75,
                            "provenance": {"volume": vol["v"], "volume_name": vname,
                                           "section": norm_text(title), "pattern": "附",
                                           "quote": norm_text(title),
                                           "method": "heading-appendix",
                                           "extracted_at": today}})

            # (b) 只在「传」的段落里抽，且逐段判定主语（附传主语会换人）
            for subject, para in bio_paragraphs(body, pid, name_map):
                for tag, rx, score in compiled:
                    for m in rx.finditer(para):
                        alias = m.group("t")
                        tid = index[alias]["id"]
                        # 「受业天台郑四表之门」：前一个别名是地名，改指紧随其后者
                        rt, ralias = guards.retarget(para, m, index, alias_rx)
                        if rt and rt != tid:
                            tid, alias = rt, ralias
                        if tid == subject:
                            continue
                        s, e = max(0, m.start() - 26), min(len(para), m.end() + 16)
                        quote = re.sub(r"\s+", "", para[s:e])
                        keep, rel_type, penalty, note = guards.apply(
                            para, m, tag, index, alias_rx)
                        if not keep:
                            rejected.append({"from": subject, "to": tid,
                                             "pattern": tag, "reason": note,
                                             "quote": quote,
                                             "section": norm_text(title)})
                            continue
                        w = index[alias]["weight"] / 100.0
                        found.append({
                            "from": subject, "to": tid, "type": rel_type,
                            "confidence": round(score * (0.75 + 0.25 * w) * penalty, 3),
                            "provenance": {"volume": vol["v"], "volume_name": vname,
                                           "section": norm_text(title), "pattern": tag,
                                           "quote": quote, "alias_hit": alias,
                                           "note": note,
                                           "method": "regex-mining",
                                           "extracted_at": today}})

                        # 并列的后续老师：「师事东廓、龙溪」「从学于甘泉、阳明」
                        for a2, off in enumerate_more(para, m.end("t"), alias_rx):
                            t2 = index[a2]["id"]
                            if t2 == subject or t2 == tid:
                                continue
                            w2 = index[a2]["weight"] / 100.0
                            found.append({
                                "from": subject, "to": t2, "type": rel_type,
                                "confidence": round(score * 0.96 *
                                                    (0.75 + 0.25 * w2) * penalty, 3),
                                "provenance": {"volume": vol["v"],
                                               "volume_name": vname,
                                               "section": norm_text(title),
                                               "pattern": tag + "·并列",
                                               "quote": quote, "alias_hit": a2,
                                               "note": "与前一位老师并列列举",
                                               "method": "regex-mining",
                                               "extracted_at": today}})

    # 去重：同 (from,to,type) 留最高分，其余出处并入 also_seen
    best = {}
    for r in found:
        k = (r["from"], r["to"], r["type"])
        cur = best.get(k)
        if cur is None:
            best[k] = r
        elif r["confidence"] > cur["confidence"]:
            r["also_seen"] = cur.get("also_seen", []) + [cur["provenance"]]
            best[k] = r
        else:
            cur.setdefault("also_seen", []).append(r["provenance"])

    out = sorted(best.values(), key=lambda r: (-r["confidence"], r["from"]))
    os.makedirs(MID, exist_ok=True)
    json.dump(out, open(os.path.join(MID, "relations.mined.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"ambiguous_aliases": ambiguous, "unmatched_sections": unmatched,
               "alias_count": len(index), "rejected_count": len(rejected),
               "rejected": rejected},
              open(os.path.join(MID, "extract_report.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    kinds = {}
    for r in out:
        kinds[r["type"]] = kinds.get(r["type"], 0) + 1
    print("  别名 %d 个（歧义丢弃 %d）· 未对齐章节 %d 个"
          % (len(index), len(ambiguous), len(unmatched)))
    print("  抽到关系 %d 条：%s · 证伪层拦下 %d 条" % (len(out), kinds, len(rejected)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
