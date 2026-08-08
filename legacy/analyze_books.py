#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分析《明儒學案》63 卷原文（v3）：人物/锚点/师承关系 三抽取。输出 analysis.json。"""
import json, os, re

BASE = os.path.dirname(os.path.abspath(__file__))
books = json.load(open(os.path.join(BASE, "resources", "volumes", "all.json"), encoding="utf-8"))
d = json.load(open(os.path.join(BASE, "data_final.json"), encoding="utf-8"))
DATA_NAMES = set(p["name"] for p in d["people"].values())

GAN = "甲乙丙丁戊己庚辛壬癸"; ZHI = "子丑寅卯辰巳午未申酉戌亥"
GZ = [g + z for g in GAN for z in ZHI]
def year_of_gz(gz, era_start):
    if gz not in GZ: return None
    idx = GZ.index(gz); return era_start + (idx - (era_start - 4) % 60) % 60
ERA_START = {"洪武":1368,"建文":1398,"永乐":1402,"永楽":1402,"永樂":1402,"洪熙":1424,"宣德":1425,"正统":1435,"正統":1435,"景泰":1449,"天顺":1457,"天順":1457,"成化":1464,"弘治":1487,"正德":1505,"嘉靖":1521,"隆庆":1566,"隆慶":1566,"万历":1572,"萬曆":1572,"萬历":1572,"天启":1620,"天啟":1620,"崇祯":1627,"崇禎":1627}

T2S = {}
def build_t2s():
    from toc_data import TOC
    for item in TOC:
        pt = re.sub(r"（[^）]*）", "", item[2]).replace(" ", "")
        ps = item[3].replace(" ", "")
        if len(pt) == len(ps):
            for a, b in zip(pt, ps):
                if a != b: T2S[a] = b
build_t2s()
EXTRA = "讚赞齡龄複复樹树飛飞劉刘歲岁恆恒義义專专們们羅罗欽钦順顺張张陳陈劉刘馬马韓韩楊杨黃黄鄭郑趙赵顧顾錢钱鄒邹聶聂歐欧陽阳蔣蒋萬万閻阎啟启寧宁龍龙凤凤許许馮冯龔龚韋韦蕭萧嚴严蘇苏範范溫温莊庄衛卫鐘钟賈贾譚谭賀贺葉叶薛薛蔡蔡徐徐吳吴呂吕餘余嶽岳湯汤謝谢董董陸陆魯鲁貢贡魏魏霍霍孫孙沈沈宋宋袁袁唐唐曹曹崔崔孟孟金金秦秦焦焦毛毛邱邱熊熊穆穆盧卢華华婁娄應应夏夏陶陶潘潘杜杜林林梅梅段段殷殷白白耿耿章章趙赵尹尹常常畢毕盛盛塗涂駱骆鮑鲍戚戚方方施施洪洪張张闞阚單单宰宰雷雷翟翟龐庞丁丁鄧邓靳靳倪倪呂吕陳陈戴戴裴裴季季顧顾陸陆聞闻遊游逯逯樂乐鄺邝蒼苍蓋盖儲储黎黎虞虞褚褚郭郭朱朱湛湛曾曾冀冀霍霍舒舒來来鹿鹿郝郝執执禦御鉉铉聲声麟麟逢逢憲宪攀攀龍龙錢钱慎慎行行允允永永澄澄敷敷茂茂才才世世卿卿橘橘珍珍尊尊素素森森巒峦誠诚正正典典瑩莹盧卢可可惟惟熙熙顏颜鯨鲸塗涂玘玘"
for i in range(0, len(EXTRA), 2):
    T2S[EXTRA[i]] = EXTRA[i + 1]
def to_simple(s): return "".join(T2S.get(c, c) for c in s)

COMMON_SURNAMES = set("赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳酆鲍史唐费廉岑薛雷贺倪汤滕殷罗毕郝邬安常乐于时傅皮卞齐康伍余元卜顾孟平黄和穆萧尹姚邵湛汪祁毛禹狄米贝明臧计伏成戴谈宋茅庞熊纪舒屈项祝董梁杜阮蓝闵席季麻强贾路娄危江童颜郭梅盛林刁钟徐邱骆高夏蔡田樊胡凌霍虞万支柯昝管卢莫经房裘缪干解应宗丁宣贲邓郁单杭洪包诸左石崔吉钮龚程嵇邢滑裴陆荣翁荀羊於惠甄曲家封芮羿储靳汲邴糜松井段富巫乌焦巴弓牧隗山谷车侯宓蓬全郗班仰秋仲伊宫宁仇栾暴甘斜厉戎祖武符刘景詹束龙叶幸司韶郜黎蓟薄印宿白怀蒲台从鄂索咸籍赖卓蔺屠蒙池乔阴胥能苍双闻莘党翟谭贡劳逄姬申扶堵冉宰郦雍却璩桑桂濮牛寿通边扈燕冀郏浦尚农温别庄晏柴瞿阎充慕连茹习宦艾鱼容向古易慎戈廖庾终暨居衡步都耿满弘匡国文寇广禄阙东欧殳沃利蔚越夔隆师巩厍聂晁勾敖融冷訾辛阚那简饶空曾毋沙乜养鞠须丰巢关蒯相查后荆红游竺权逯盖益桓公万俟司马上官欧阳夏侯诸葛闻人东方赫连皇甫尉迟公羊澹台公冶宗政濮阳淳于单于太叔申屠公孙仲孙轩辕令狐钟离宇文长孙慕容鲜于闾丘司徒司空亓官司寇仉督子车颛孙端木巫马公西漆雕乐正壤驷公良拓跋夹谷宰父谷梁晋楚闫法汝鄢涂钦段干百里东郭南门呼延归海羊舌微生岳帅缑亢况后有琴梁丘左丘东门西门商牟佘佴伯赏南宫墨哈谯笪年爱阳佟第五言福")

VOL_SCHOOL = {
 "崇仁":"崇仁学案","白沙":"白沙学案","河東":"河东学案","河东":"河东学案","三原":"三原学案","姚江":"姚江学案",
 "浙中":"浙中王门学案","江右":"江右王门学案","南中":"南中王门学案","北方":"北方王门学案","粵閩":"粤闽王门学案","粤闽":"粤闽王门学案",
 "止修":"止修学案","泰州":"泰州学案","甘泉":"甘泉学案","東林":"东林学案","东林":"东林学案","蕺山":"蕺山学案",
}
def school_of(name):
    for k, v in VOL_SCHOOL.items():
        if name.startswith(k): return v
    if name.startswith("諸儒") or name.startswith("诸儒"): return "诸儒学案"
    if name.startswith("附案"): return "浙中王门学案"
    return None

from toc_data import TOC
known_pt = []
for item in TOC:
    pt = re.sub(r"（[^）]*）", "", item[2]).replace(" ", "")
    ps = item[3].replace(" ", "")
    known_pt.append((pt, ps))
for nm in DATA_NAMES: known_pt.append((nm, nm))

ALIAS = {}
def add_alias(tok, ps):
    tok = (tok or "").strip()
    if not tok or len(tok) > 4: return
    ALIAS[tok] = ps
    ALIAS[to_simple(tok)] = ps
for pt, ps in known_pt:
    if len(pt) >= 2: add_alias(pt, ps)
for p in d["people"].values():
    nm = p["name"]
    for f in (p.get("zi", ""), p.get("hao", "")):
        for tok in re.split(r"[，,、；;｜| ]", f):
            tok = re.sub(r"^(字|號|号|別號|別号)", "", tok).strip()
            if tok and len(tok) <= 3: add_alias(tok, nm)
CURATED = {
 "陽明":"王守仁","文成":"王守仁","姚江":"王守仁","康齋":"吴与弼","敬軒":"薛瑄","文清":"薛瑄",
 "涇野":"吕柟","石渠":"王恕","白沙":"陈献章","甘泉":"湛若水","龍溪":"王畿","緒山":"钱德洪",
 "東廓":"邹守益","雙江":"聂豹","念菴":"罗洪先","念庵":"罗洪先","心齋":"王艮","見羅":"李材",
 "天台":"耿定向","天臺":"耿定向","楚倥":"耿定理","楚侗":"耿定理","涇陽":"顾宪成","景逸":"高攀龙",
 "念臺":"刘宗周","念台":"刘宗周","蕺山":"刘宗周","石簣":"陶望龄","石篑":"陶望龄","波石":"徐樾",
 "東崖":"王襞","一菴":"王栋","近溪":"罗汝芳","南野":"欧阳德","塘南":"王时槐","大洲":"赵贞吉",
 "復所":"杨起元","畏所":"杨起元","荊川":"唐顺之","鹿門":"唐顺之","考功":"唐顺之","少墟":"冯从吾",
 "敬菴":"许孚远","敬庵":"许孚远","忠憲":"高攀龙","端文":"顾宪成","師泉":"胡直","念菴":"罗洪先",
 "念臺":"刘宗周","忠節":"金铉","涇陽":"顾宪成","方山":"薛应旂","爾瞻":"邹元标","見素":"林俊",
}
for k, v in CURATED.items(): add_alias(k, v)

JINSHI_RE = re.compile(r"(?:登|成)?(洪武|建文|永樂|永楽|宣德|正統|景泰|天順|成化|弘治|正德|嘉靖|隆慶|萬曆|天啟|崇禎)?([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])?(?:(元|二|三|四|五|六|七|八|九|十|十一|十二|十三|十四|十五|十六|十七|十八|十九|二十|廿|三十|四十|四十五|四十八)年)?進士")
DEATH_RE = re.compile(r"卒(?:於|年)(洪武|建文|永樂|永楽|宣德|正統|景泰|天順|成化|弘治|正德|嘉靖|隆慶|萬曆|天啟|崇禎)?([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])?(?:(元|二|三|四|五|六|七|八|九|十|十一|十二|十三|十四|十五|十六|十七|十八|十九|二十|廿|三十|四十|四十五|四十八)年)?")
AGE_RE = re.compile(r"(?:享|壽)?年([一二三四五六七八九十百]+)(?:歲|而卒|而終|而歿|，卒|卒|終)")
CN2N = {"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9,"十":10,"十一":11,"十二":12,"十三":13,"十四":14,"十五":15,"十六":16,"十七":17,"十八":18,"十九":19,"二十":20,"廿":20,"三十":30,"四十":40,"五十":50,"六十":60,"七十":70,"八十":80,"九十":90,"百":100}
def parse_era_year(era, gz, num):
    if era in ERA_START:
        s = ERA_START[era]
        if gz: return year_of_gz(gz, s)
        if num: return s + CN2N.get(num, 0) - 1 if num in CN2N else None
        return s + 2
    if gz: return year_of_gz(gz, 1368)
    return None

SKIP_GIVEN = {"語","錄","录","語錄","语录","集","書","书","傳","传","年譜","年谱","學","学","記","记","草","語要","論學書","论学书","劄記","札记","文","序","跋","詩","诗","譜","谱","遺","遗","例","問答","问"}
analysis = {"people": {}, "new_names": {}, "anchors": [], "relations": []}

def rel_scan(subject, body):
    out = []
    STRONG = ["師事","受學於","受業於","問學於","卒業於","執贄","親炙於","親炙","學出於","受知於","少從","以.*為師","以.*为师"]
    for tok, tgt in sorted(ALIAS.items(), key=lambda x: -len(x[0])):
        if len(tok) < 2: continue
        start = 0
        while True:
            i = body.find(tok, start)
            if i < 0: break
            start = i + len(tok)
            pre = body[max(0, i - 5):i]
            post = body[i + len(tok):i + len(tok) + 6]
            hit = None
            for k in STRONG:
                if re.search(k, pre[-5:]):
                    hit = k; break
            if not hit and post.startswith("之門人"):
                stu_raw = post[3:9]
                stu = None
                for a2, s2 in sorted(ALIAS.items(), key=lambda x: -len(x[0])):
                    if len(a2) >= 2 and stu_raw.startswith(a2):
                        stu = s2; break
                if stu:
                    hit = "门人"
                    if stu != tgt and (stu in DATA_NAMES or stu in analysis["new_names"]):
                        out.append({"tgt": stu, "kind": "门人", "raw": body[max(0, i - 10):i + 14].replace("\n", " ")})
                continue
            if not hit and (pre.endswith("從") or pre.endswith("从")) and (post.startswith("學") or post.startswith("学") or post.startswith("遊") or post.startswith("游")):
                hit = "从学"
            if hit:
                tgt = {"王守仁": "王阳明"}.get(tgt, tgt)
                if tgt != subject and (tgt in DATA_NAMES or tgt in analysis["new_names"]):
                    out.append({"tgt": tgt, "kind": hit, "raw": body[max(0, i - 12):i + 16].replace("\n", " ")})
    return out

for item in books:
    vol = item["v"]; text = item["text"]; school = school_of(item["name"])
    sections = re.split(r"==([^=]{2,40})==", text)
    for i in range(1, len(sections) - 1, 2):
        title = sections[i].strip()
        body = sections[i + 1]
        if title.startswith(("前言", "讀法", "读法", "师说", "師說")):
            continue
        # --- 标题解析：...姓号先生名 ---
        subject = None
        jx = title.find("先生")
        if jx >= 2 and jx < len(title) - 1:
            given_raw = re.sub(r"[（(【].*", "", title[jx + 2:])
            given_raw = re.sub(r"[^一-鿿]", "", given_raw)
            if given_raw and given_raw not in SKIP_GIVEN:
                if jx >= 4 and title[jx - 4:jx - 2] in ("歐陽", "欧阳"):
                    surname = title[jx - 4:jx - 2]
                    hao = title[jx - 2:jx]
                else:
                    surname = title[jx - 3:jx - 2]
                    hao = title[jx - 2:jx]
                cand = to_simple(surname + given_raw[:3])
                cand = {"王守仁": "王阳明", "王陽明": "王阳明"}.get(cand, cand)
                if cand in DATA_NAMES:
                    subject = cand
                add_alias(hao, cand)
                add_alias(surname + hao, cand)
                add_alias(given_raw, cand)
                # 新人物：通用姓校验 + 去非人名标题
                JUNK_CHARS = set("祀或語錄記傳集序跋草問答書譜文詩") 
                if not subject and cand[0] in COMMON_SURNAMES and not any(ch in cand for ch in JUNK_CHARS):
                    subject = cand
        if not subject:
            for pt, ps in known_pt:
                if len(pt) >= 2 and (title.endswith(pt) or pt in title):
                    subject = ps; break
        if not subject:
            continue
        head = body[:220]
        birth_raw = ""
        for br in re.findall(r"([\u4e00-\u9fff]{1,12}人也)", head):
            birth_raw = br[:-1]; break
        if not birth_raw:
            mbr = re.search(r"，([\u4e00-\u9fff]{1,12})人。", head)
            if mbr: birth_raw = mbr.group(1)
        zi_raw = ""
        mzi = re.search(r"字([\u4e00-\u9fff]{1,3})", head)
        if mzi: zi_raw = mzi.group(1)
        hao_raw = to_simple(hao) if hao else ""
        if subject in DATA_NAMES:
            pid = next(k for k, v in d["people"].items() if v["name"] == subject)
            analysis["people"].setdefault(subject, {}).update({"name": subject, "school": d["people"][pid]["school"], "vol": vol, "birth_raw": birth_raw, "zi_raw": zi_raw, "hao_raw": hao_raw})
        else:
            analysis["new_names"].setdefault(subject, {"school": school or "诸儒学案", "vol": vol, "birth_raw": birth_raw, "zi_raw": zi_raw, "hao_raw": hao_raw})
        for mm in JINSHI_RE.finditer(body):
            y = parse_era_year(mm.group(1), mm.group(2), mm.group(3))
            if y: analysis["anchors"].append({"name": subject, "vol": vol, "kind": "jinshi", "year": y, "raw": mm.group(0)[:22]})
        for mm in DEATH_RE.finditer(body):
            y = parse_era_year(mm.group(1), mm.group(2), mm.group(3))
            if y: analysis["anchors"].append({"name": subject, "vol": vol, "kind": "death", "year": y, "raw": mm.group(0)[:22]})
        for mm in AGE_RE.finditer(body):
            if mm.group(1) in CN2N:
                analysis["anchors"].append({"name": subject, "vol": vol, "kind": "age", "age": CN2N[mm.group(1)], "raw": mm.group(0)[:22]})
        seen = set()
        for rel in rel_scan(subject, body):
            key = (subject, rel["tgt"], rel["kind"])
            if key in seen: continue
            seen.add(key)
            analysis["relations"].append({"sub": subject, **rel, "vol": vol})

json.dump(analysis, open(os.path.join(BASE, "analysis.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("known sections:", len(analysis["people"]))
print("new names:", len(analysis["new_names"]))
print("anchors:", len(analysis["anchors"]))
print("relations:", len(analysis["relations"]))
