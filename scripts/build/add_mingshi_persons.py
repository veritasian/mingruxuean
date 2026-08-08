#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
add_mingshi_persons.py —— 《明史》儒林传人物并入人物库

从 resources/mingshi/mingshi.json 读明史人物档案，把「师承链上必要」
且不在现有 237 人库的人物并入 data/persons.json，并挂到对应学案
（schools.json members）。幂等：已存在的人物跳过。

只并入有明史师承边、能连进现有图谱的人物 —— 无师承的元末诸儒
（范祖干、谢应芳等）留在 mingshi.json 档案里，不塞进主图，
避免制造新的孤点。
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "data")
MINGSHI = os.path.join(ROOT, "resources", "mingshi", "mingshi.json")

# 新增人物 → 学案归属（按其师承线所在学案）
SCHOOL_OF = {
    # 蔡清（诸儒学案）门人
    "陈琛": "诸儒学案", "王宣": "诸儒学案", "易时中": "诸儒学案",
    "赵逮": "诸儒学案", "蔡烈": "诸儒学案", "林同": "诸儒学案",
    # 庄昶（诸儒学案）门人邵宝，邵宝门人王问
    "邵宝": "诸儒学案", "王问": "诸儒学案",
    # 胡九韶（崇仁学案）——杨廉承其家学；魏校（崇仁）门人；娄谅子
    "杨廉": "崇仁学案", "王应电": "崇仁学案", "王敬臣": "崇仁学案", "娄忱": "崇仁学案",
    # 王守仁弟子（浙中）
    "应良": "浙中王门学案", "程粹": "浙中王门学案",
    # 卢可久→杜惟熙→陈时芳/陈正道（浙中）
    "陈时芳": "浙中王门学案", "陈正道": "浙中王门学案",
    # 欧阳德族人、邹守益子/孙（江右）
    "欧阳瑜": "江右王门学案", "邹善": "江右王门学案", "邹德涵": "江右王门学案",
    # 罗汝芳（泰州）门人
    "蔡悉": "泰州学案",
    # 张后觉（北方）门人
    "赵维新": "北方王门学案",
    # 许孚远（甘泉）门人
    "丁元荐": "甘泉学案",
    # 周蕙（河东）门人
    "王爵": "河东学案",
}


def load(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def dump(obj, p):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def main():
    persons = load(os.path.join(DATA, "persons.json"))
    schools = load(os.path.join(DATA, "schools.json"))
    ms = load(MINGSHI)
    ms_persons = ms["persons"]

    # 各学案当前 seq 上限（新增人物排在学案末尾）
    max_seq = {}
    for pid, p in persons.items():
        s = p.get("school", "")
        max_seq[s] = max(max_seq.get(s, 0), p.get("seq", 0))

    added, skipped = [], []
    for name, school in SCHOOL_OF.items():
        if name in persons:
            skipped.append(name)
            continue
        info = ms_persons.get(name, {})
        max_seq[school] = max_seq.get(school, 0) + 1
        persons[name] = {
            "id": name,
            "name": name,
            "zi": info.get("zi", ""),
            "hao": info.get("hao", ""),
            "title": "",
            "role": "",
            "head": name,
            "school": school,
            "seq": max_seq[school],
            "origin": {"raw": info.get("origin", ""), "province": "", "city": "", "county": ""},
            "mingshi": {
                "volume": info.get("volume"),
                "style": info.get("style", ""),
            },
            "has_biography": False,   # 明儒学案无本传（明史有传）
            "note": "《明史》儒林传卷%d 补充人物，挂%s（师承线归属）"
                    % (info.get("volume", 282), school),
        }
        added.append(name)

    # 学案 members 同步（member_count 更新，with_biography 不变）
    by_id = {s["id"]: s for s in schools}
    for name in added:
        s = by_id[persons[name]["school"]]
        if name not in s["members"]:
            s["members"].append(name)
            s["member_count"] = len(s["members"])

    dump(persons, os.path.join(DATA, "persons.json"))
    dump(schools, os.path.join(DATA, "schools.json"))

    print("  新增人物 %d：%s" % (len(added), "、".join(added) or "无"))
    print("  已存在跳过 %d：%s" % (len(skipped), "、".join(skipped) or "无"))
    print("  人物库现有 %d 人 · %d 学案" % (len(persons), len(schools)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
