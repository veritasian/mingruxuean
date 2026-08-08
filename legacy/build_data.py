#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply canonical 明儒学案 school assignment + clean names onto parsed data.

Source-of-truth edges come from parse_drawio.py (only arrowed edges).
3 NO-ARROW edges go to `tongmen` (同门).
"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(BASE, "xuean_data.json"), encoding="utf-8"))

# Name normalisation: raw parsed name -> canonical display name
NAME_FIX = {
    "聘与弼": "吴与弼", "督廷言": "万廷言", "同邦采": "刘邦采", "尚秋": "孟秋",
    "樵夫朱恕": "朱恕", "布樾": "徐樾", "陶匠韩乐吾": "韩乐吾", "田夫夏叟": "夏廷美",
    "太塙": "刘塙", "諯时乔": "杨时乔", "西樵名献夫，": "霍韬", "知本": "季本",
    "主枢": "唐枢", "襄顺之": "唐顺之", "举应诏": "杨天游", "萧彦号念渠": "萧彦",
    "章时鸾号孟泉，": "章时鸾", "尚士藻": "潘士藻", "尚汝登": "周汝登",
    "宗锺峦": "吴钟峦", "同敬之": "薛敬之", "吕楠": "吕柟", "明衡": "王明衡",
    # aliases that the parser left as-is
    "白沙": "陈献章", "龙溪": "王畿", "甘泉": "湛若水",
    "邹东廓": "邹守益", "唐荆川": "唐顺之", "徐波石": "徐樾",
    "刘师泉": "刘邦采", "耿天台": "耿定向", "罗近溪": "罗汝芳",
    "聂双江": "聂豹", "刘晴川": "刘魁", "钱绪山": "钱德洪",
    "仲枢": "唐枢",
    "城南": "周冲",  # 城南格致 related
}

# Canonical school membership (clean name -> 学案 label)
SCHOOLS = {
    "崇仁学案": ["吴与弼","胡居仁","娄谅","谢复","郑伉","胡九韶","魏校","馀佑","夏尚朴"],
    "白沙学案": ["陈献章","张诩","贺钦","邹智","林光","陈庸","李孔修","谢佑","文廷矩"],
    "河东学案": ["薛瑄","阎禹锡","张鼎","张杰","王鸿儒","薛敬之","李锦","潘润","陈茂烈",
                 "史桂芳","王道","段坚","周蕙","吕柟"],
    "三原学案": ["王恕","王承裕","马理","韩邦奇","杨爵","王之士","张节","李挺","郭蒙泉"],
    "姚江学案": ["王阳明"],
    "浙中王门学案": ["徐爱","王畿","季本","黄绾","董澐","程文德","张元冲","万表","王宗沭",
                   "张元忭","陆澄","顾应祥","黄宗明","胡瀚","董谷","徐用检","钱德洪"],
    "江右王门学案": ["欧阳德","邹守益","聂豹","罗洪先","刘文敏","黄弘纲","刘魁","何廷仁","陈九川",
              "魏良弼","万廷言","刘元卿","胡直","邹元标","罗大紘","章潢","冯应京","邓元锡",
              "宋仪望","刘阳","刘邦采","刘秉监","王钦","刘晓","魏良器","魏良政","王时槐",
              "邓以赞","陈嘉谟"],
    "南中王门学案": ["贡安国","戚贤","查铎","程默","姜宝","黄省曾","周冲","朱得之","周怡",
                   "薛应旗","薛甲","唐顺之","徐阶","杨豫孙","唐鹤徵","殷迈"],
    "楚中王门学案": ["蒋信","冀元亨","沈宠","萧彦","戚衮","萧良干","张棨","章时鸾","程大宾",
                   "郑烛","孟秋","杨东明","南大吉","杨天游"],
    "北方王门学案": ["穆孔晖","张后觉","尤时熙","孟化鲤"],
    "粤闽王门学案": ["霍韬","杨骥","薛尚贤","梁焯","郑一初","王明衡","薛侃","周坦"],
    "止修学案": ["李材"],
    "泰州学案": ["王艮","王襞","朱恕","韩乐吾","夏廷美","徐樾","王栋","林春","颜钧","梁汝元",
               "邓豁渠","方与时","程学颜","钱同文","管志道","罗汝芳","姚汝循","赵贞吉",
               "杨起元","耿定向","耿定理","焦竑","潘士藻","方学渐","何祥","祝世禄","周汝登",
               "陶望龄","刘塙"],
    "甘泉学案": ["湛若水","吕怀","唐枢","何迁","许孚远","洪垣","冯从吾","唐伯元","杨时乔"],
    "蕺山学案": ["刘宗周","黄尊素","陈龙正","华允诚","刘永澄","史孟鳞","薛敷教"],
    "东林学案": ["顾宪成","高攀龙","孙慎行","钱一本","顾允成","叶茂才","刘元珍","耿橘",
               "许世卿","吴钟峦"],
}

# 各学派创始人
FOUNDERS = {
    "崇仁学案": ["吴与弼"],
    "白沙学案": ["陈献章"],
    "河东学案": ["薛瑄","吕柟"],
    "三原学案": ["王恕"],
    "姚江学案": ["王阳明"],
    "浙中王门学案": ["徐爱","王畿","钱德洪"],
    "江右王门学案": ["邹守益","欧阳德","聂豹","罗洪先"],
    "南中王门学案": ["黄省曾"],
    "泰州学案": ["王艮","颜钧"],
    "甘泉学案": ["湛若水"],
    "蕺山学案": ["刘宗周"],
}
NAME_TO_SCHOOL = {}
for sch, names in SCHOOLS.items():
    for n in names:
        NAME_TO_SCHOOL[n] = sch

people = {}
for pid, p in d["people"].items():
    clean = NAME_FIX.get(p["name"], p["name"])
    sch = NAME_TO_SCHOOL.get(clean)
    if not sch:
        sch = p.get("school", "未详")
    new_p = dict(p)
    new_p["name"] = clean
    new_p["school"] = sch
    people[pid] = new_p

schools = list(SCHOOLS.keys())
school_members = {s: [] for s in schools}
for pid, p in people.items():
    school_members.setdefault(p["school"], []).append(pid)

# ----- 补建王阳明（drawio 缺）+ 各王门创始直传 -----
WY_ID = "wang_yangming"
people[WY_ID] = {
    "id": WY_ID, "name": "王阳明", "zi": "伯安", "hao": "阳明",
    "birth": "浙江余姚人", "age": "年五十七", "title": "文成",
    "role": "", "head": "阳明王先生守仁", "school": "姚江学案",
    "teachers": [], "students": [],
}
name_to_pid = {p["name"]: pid for pid, p in people.items()}
WY_DIRECT = ["徐爱","王畿","钱德洪","邹守益","欧阳德","聂豹","罗洪先","黄省曾","王艮"]
arrow_edges = list(d["edges"])  # 62 source arrow edges, in (id, id) form
for tid, sid in arrow_edges:
    if sid not in people or tid not in people: continue
    people[sid].setdefault("teachers", []).append(tid)
    people[tid].setdefault("students", []).append(sid)

for nm in WY_DIRECT:
    sid = name_to_pid.get(nm)
    if sid and sid != WY_ID and WY_ID not in people[sid]["teachers"]:
        people[sid]["teachers"] = [WY_ID] + people[sid]["teachers"]
        people[WY_ID]["students"].append(sid)
        if not any(e[0] == WY_ID and e[1] == sid for e in arrow_edges):
            arrow_edges.append([WY_ID, sid])
school_members.setdefault("姚江学案", []).append(WY_ID)

# ----- 用户已批准的 backfill -----
def add_edge(tname, sname):
    tid=name_to_pid.get(tname)
    sid=name_to_pid.get(sname)
    if not tid or not sid: print(f'  ! skip {tname}→{sname}'); return
    if any(e[0]==tid and e[1]==sid for e in arrow_edges): return
    arrow_edges.append([tid, sid])
    people[tid].setdefault("students", []).append(sid)
    people[sid].setdefault("teachers", []).append(tid)

def remove_edge(tname, sname):
    tid=name_to_pid.get(tname)
    sid=name_to_pid.get(sname)
    if not tid or not sid: return
    arrow_edges[:] = [e for e in arrow_edges if not (e[0]==tid and e[1]==sid)]
    people[tid]["students"] = [s for s in people[tid].get("students",[]) if s!=sid]
    people[sid]["teachers"] = [t for t in people[sid].get("teachers",[]) if t!=tid]

# 创始人直传 backfill（学界公认、用户已批）
HISTORICAL_BACKFILL = [
    ("吴与弼","娄谅"),("吴与弼","胡居仁"),("吴与弼","谢复"),("吴与弼","郑伉"),
    ("陈献章","张诩"),
    ("薛瑄","薛敬之"),("薛瑄","阎禹锡"),("薛瑄","段坚"),("薛瑄","王鸿儒"),
    ("段坚","周蕙"),
    ("王恕","王承裕"),("王承裕","王之士"),("王恕","韩邦奇"),
]
for t, s in HISTORICAL_BACKFILL:
    add_edge(t, s)

# ----- 同门（仅 user-msg 明确指出；当前源数据中 3 对 tongmen 都已在数据中存为 tongmen 字段）-----

# build tongmen using source's paired names
tongmen = []
for a, b in d.get("tongmen", []):
    # resolve a, b -> ids
    pass

# Convert source's tongmen from id-pairs to name-pairs and back to id-pairs using our name_to_pid
src_tongmen_names = []
for a_id, b_id in d.get("tongmen", []):
    na = d["people"].get(a_id, {}).get("name")
    nb = d["people"].get(b_id, {}).get("name")
    if na and nb:
        src_tongmen_names.append((na, nb))
# apply NAME_FIX
tongmen_pairs = []
for na, nb in src_tongmen_names:
    na_clean = NAME_FIX.get(na, na)
    nb_clean = NAME_FIX.get(nb, nb)
    a = name_to_pid.get(na_clean)
    b = name_to_pid.get(nb_clean)
    if a and b and a != b:
        tongmen_pairs.append([a, b])

out = {"schools": schools, "school_members": school_members,
       "people": people, "edges": arrow_edges,
       "tongmen": tongmen_pairs, "founders": FOUNDERS}
json.dump(out, open(os.path.join(BASE, "data_final.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("Reassigned. School sizes:")
for s in schools:
    print("  %-12s %d" % (s, len(school_members[s])))
print("Edges (teacher-student):", len(arrow_edges))
print("Tongmen (same-pace):", len(tongmen_pairs))
for a, b in tongmen_pairs:
    print("  %s <-> %s" % (people[a]["name"], people[b]["name"]))
orphan = [p["name"] for p in people.values() if p["school"] not in SCHOOLS]
print("Orphans (not in canonical):", orphan)
