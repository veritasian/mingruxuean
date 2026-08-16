# 数据字典

`data/` 是这个项目的数据库。7 份核心文件 + 卷前三篇 + 63 卷正文 + 阳明心学专页 + 7 份 JSON Schema。
所有文件都是简体（原文引文除外，保留原始字形）。

> 想加数据 / 改数据，改 `data/` 下的文件，然后 `python3 scripts/build/bundle.py`
> 重新打包即可，不用碰前端代码。改完记得跑 `python3 tests/run.py`。

---

## persons.json — 260 位学者

顶层是一个以人名为键的字典（人名即主键，全书唯一）。

```json
"王阳明": {
  "id": "王阳明",
  "name": "王阳明",
  "zi": "伯安",              // 字
  "hao": "阳明",             // 号
  "title": "文成",           // 谥号
  "role": "",                // 官职（多数为空）
  "head": "阳明王先生守仁",    // 原书篇目标题
  "school": "姚江学案",       // 归属学案，以原书为准
  "seq": 44,                 // 全书出场序
  "life": {
    "raw": "1472–1529",
    "birth": 1472, "death": 1529,
    "age": "年五十七"
  },
  "origin": {
    "raw": "浙江余姚人",       // 原文表述，不改
    "province": "浙江", "city": "宁波", "county": "余姚市"
  },
  "legacy_ids": ["wang_yangming"],   // 旧版 id，用于回溯比对
  "anchor": {                        // 定位到原书哪一卷哪一篇
    "volume": 10,
    "volume_name": "姚江学案",
    "section": "文成王阳明先生守仁",
    "text_chars": 23694
  },
  "has_biography": true,     // 原书是否为其立本传
  "hao_source": "legacy"     // 号的来源：原文抽取 / legacy / 人工补
}
```

**`has_biography: false` 的人要留意**：这些人黄宗羲只提了名字，没有本传。
他们没有 `anchor`，多半也没有师承边——不是漏抽，是原书就没有。

---

## relations.json — 247 条关系

```json
{
  "meta": {
    "count": 247,
    "by_type":   {"师承": 242, "附见": 2, "私淑": 3},
    "by_source": {"drawio": 162, "mined": 97, "legacy-mining": 42, "mingshi": 103},
    "cited": 174, "needs_citation": 73
  },
  "relations": [ … ]
}
```

单条：

```json
{
  "from": "冯应京",        // 徒
  "to":   "邹元标",        // 师
  "type": "师承",
  "sources": ["legacy-mining", "mined"],   // 哪几路来源都指向它
  "confidence": 0.99,                      // 综合置信度
  "cited": true,                           // 有原文引文
  "needs_citation": false,
  "provenance": [                          // 每一路来源各留一条证据
    {
      "source": "mined",
      "method": "regex-mining",
      "volume": 24,
      "volume_name": "江右王门学案九",
      "section": "佥事冯慕冈先生应京",
      "pattern": "师事",                    // 命中的词
      "quote": "……先生师事邹南臬，其拘幽书草……",  // 原文上下文
      "alias_hit": "邹南",                  // 正文里用的是别名，映射到 邹元标
      "extracted_at": "2026-08-08"
    }
  ]
}
```

### 方向约定（重要）

**`from` 是徒，`to` 是师。** 画图时箭头从师指向徒（知识的流向）。
`kg.view.js` 里 `source = nd(r.to)`、`target = nd(r.from)` 就是为了这个。
曾经这里两个视图画反了，`smoke.mjs` 现在有一条用例专门盯着 245 条边的朝向。
drawio 谱系原图是「师→徒」，合并时统一翻转为「徒→师」——见 ARCHITECTURE.md 的来源合并节。

### 四路来源

| source | 数量 | 怎么来的 | 可信度 |
|---|---|---|---|
| `mingshi` | 103 | 《明史》卷282/283 儒林传**人工精读**（`mingshi_data.py`），带卷次+原文引文 | 0.95 |
| `drawio` | 162 | 原书谱系结构（学案归属、师承脉络），方向已归一 | 高，但**无原文引文** |
| `mined` | 97 | 63 卷正文正则抽取（师事/受业/从游/问学/及门…） | 有引文，可核 |
| `legacy-mining` | 42 | 旧版单体的抽取结果，保留作交叉验证 | 有引文（繁体） |

两路以上都命中的，`confidence` 拉到 0.99。
`needs_citation: true` 的 73 条是待办——结构上成立，但还没在正文里找到原句。

出处卷次分两个体系：学案来源的 `volume` 是 1–63（学案卷），
`mingshi` 来源的 `volume` 是 282/283（《明史》卷），人物卡据此分开显示。

### 关系类型

- `师承`（242）—— 明确的师徒。**画边。**
- `私淑`（3）—— 未及门而宗其学（如 魏校→胡居仁）。**画边。**
- `附见`（2）—— 原书把此人附在他人传后。**不画边**，它是编排位置，不是学脉。

---

## orphans.json — 52 个孤点的判读

**孤点的定义**：在 `{师承, 私淑}` 两类边上度数为 0 的人。这个定义在
`src/data/model.js` 的 `edgeList()` 和 `scripts/build/analyze_orphans.py` 的
`EDGE_TYPES` 里各写一遍，`test_data.py` 比对两者一致。

```json
{
  "meta": {
    "orphan_count": 52, "person_count": 260,
    "by_kind": {"structural": 27, "horizontal": 8, "no_record": 6, "appendix": 2, "gap": 9},
    "headline": "孤点不等于数据缺失：52 个孤点中 43 个是编纂设计、编排位置或史料本身无征，真正待补的只有 9 个。"
  },
  "kinds": { "structural": {"label": "编纂设计使然", "desc": "…"}, … },
  "by_school": { "诸儒学案": {"orphans": 27, "total": 48, "rate": 0.563}, … },
  "orphans": [
    {"id": "朱恕", "name": "朱恕", "school": "泰州学案",
     "kind": "appendix", "has_biography": false,
     "volume": null, "appendix_of": "王襞"}
  ]
}
```

| kind | 数量 | 含义 |
|---|---|---|
| `structural` | 29 | 《诸儒学案》专收「不能归入各家门户」者，无师承是它的定义 |
| `horizontal` | 8 | 东林诸子是同人讲会，横向结社不是师徒纵贯 |
| `appendix` | 1 | 附于他人传后（樵夫朱恕附于王襞），有 `appendix_of` 字段 |
| `no_record` | 6 | 原书只提名字，未立本传 |
| `gap` | 9 | **真数据缺口**，待补 |

孤点集中度：诸儒学案 29/40（72.5%）、东林学案 8/16（50%）——
两个高的都有明确的编纂学理由，不是抽取质量问题。

**`meta.orphan_count` 只在这一份文件里存。** `relations.json` 不重复登记，
`degree.json` 只作中间产物。同一个数存两处，迟早会漂。

---

## schools.json — 17 个学案

数组，按原书顺序：

```json
{"id": "崇仁学案", "name": "崇仁学案", "order": 0,
 "founders": ["吴与弼"],
 "members": ["吴与弼", "胡居仁", "娄谅", …],
 "member_count": 10,
 "with_biography": 10}
```

`test_data.py` 检查两件事：`members` 里的人都在 `persons.json` 里（外键闭合）；
每个人的 `person.school` 都能在对应学案的 `members` 里找到（双向一致）。

---

## geo.json — 籍贯

```json
"places": {
  "欧阳德": {"prov": "江西", "city": "吉安", "note": "泰和县", "raw": "江西泰和人"}
},
"birth_patterns": { … }   // 原文籍贯表述的解析规则，便于回溯
```

`raw` 永远保留原文表述。解析出的 `prov` / `city` 是推断结果，会错；
`raw` 是事实，不会错。出问题时以 `raw` 为准重解析。

---

## timeline.json — 纪年与生卒

```json
"emperors": [{"n": 1, "era": "洪武", "name": "朱元璋", "start": 1368, "end": 1398}],
"period": {
  "欧阳德": {"birth": 1496, "death": 1554,
             "method": "史载",         // 史载 / 推算 / 存疑
             "active": [1514, 1554]}   // 活跃区间，用于时间轴排布
}
```

`method` 说明这组年份的把握程度。`推算` 的多是由中举年、卒年倒推的，
时间轴上照画，但不该拿去做精确论证。

---

## toc.json + volumes/ — 原书正文

```json
// toc.json
"volumes": [{"volume": 1, "name": "崇仁学案一",
             "name_original": "崇仁學案一",   // 原始繁体卷名
             "chars": 8722,
             "persons": ["吴与弼"]}]

// volumes/v12.json
{"volume": "12", "name": "浙中王门学案二", "text": "{{header|title=明儒学案|…}}…"}
```

`text` 是维基文库的 wikitext 原文，前端由 `src/data/wikitext.js` 渲染
（处理 `{{header}}`、`{{*}}`、注释块、段落分割）。**不预先转成 HTML**——
wikitext 保留了原书的结构信息（标题层级、注文），转早了就丢了。

---

## yangming.json — 阳明心学专页

学案之外附设的一篇心学总纲页（菜单「阳明心学」）。内容转录自
`resources/yangming/` 的手稿页存档，结构化为三类：

```json
{
  "hero": ["无善无恶心之体", "有善有恶意之动", "知善知恶是良知", "为善去恶是格物"],
  "chapters": [
    {"id": "ch1", "num": "壹", "title": "思维模型", "sub": "顿悟和渐修的逻辑",
     "kind": "flow", "flow": {"awakeCols": [...], "deludeCols": [...]}},
    {"id": "ch2", "num": "贰", "title": "根器论", "kind": "matrix",
     "matrix": {"cols": [3 教], "rows": [3 阶 × 3 格]}},
    {"id": "ch3", "num": "叁", "title": "体用论（中道）", "kind": "quad",
     "quad": {"body": ["体", "离·性"], "use": ["用", "觉·心"], "q": [4 格]}},
    {"id": "ch4", ..., "kind": "quad", "quad": {"body": [理,体], "use": [心,用], "q": [4 格]}}
    // ch5–ch14 同 quad
  ],
  "outro": ["名相异途  一心同体", "天命之谓性，率性之谓道，修道之谓教。"]
}
```

章节 id 与「序号+篇名」由 `scripts/ingest/yangming_data.py` 从存档 HTML 直接读出，
四象限正文转录自存档 `main.js` 的 QUADS；两者交叉校验，不一致会直接报错。

---

## schema/

7 份 JSON Schema，与上面一一对应。目前是文档性质（描述字段契约），
没有接进 CI 做校验——`test_data.py` 的检查比 schema 更严（它查外键和业务一致性，
schema 只能查类型）。加数据时可以拿来对照字段名。

---

## intermediate/

中间产物，**可以整个删掉**，跑一遍 `python3 scripts/pipeline.py` 就会重生成。

| 文件 | 用途 |
|---|---|
| `persons.stage1.json` | 规范化后、订正前的人物 |
| `reconcile_changes.json` | 订正了哪些（合并了谁、改了谁的学案）——审计用 |
| `relations.mined.json` | 正文抽取的原始结果，含未采信的候选 |
| `extract_report.json` | 抽取统计：命中哪些词、多少条被别名映射消歧 |
| `degree.json` | 度数表 |
| `book_index.json` / `book_unmatched.json` | 原书 204 章节的对齐结果与未匹配项 |
| `persons_review.json` | 需人工复核的条目 |

`book_unmatched.json` 和 `persons_review.json` 值得定期翻——
里面是机器不敢下判断的东西，也是最可能藏着新数据的地方。
