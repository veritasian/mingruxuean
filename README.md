# 名儒学案图谱

> 把黄宗羲《明儒学案》六十三卷读成一张网，再用《明史》儒林传补强。

17 个学案、260 位学者、247 条师承关系（174 条带原文出处），
每一条关系都能点回原文出处。**一分类一页面**的菜单式站点：
8 个页面各自独立、只带自己的内容与 SEO，每个页面都能双击打开、断网可用。

```
dist/index.html           ← 首页（知识图谱），双击即开，无需服务器、无需联网
dist/graph.html           谱系总图 · roster.html 人物线索 · time.html 时间线索
dist/geo.html             地理线索 · orphan.html 孤点现象
dist/yangming.html        阳明心学
dist/book/               学案原文：按卷分页（64 页 = 卷前一篇 + 63 卷各一页）
  index.html                卷前三篇（原序/发凡/师说，三个 tab）
  chapter-one.html …        63 卷各一页（chapter-sixty-three.html）
  ../book.html              旧版单文件跳板（自动跳转 → book/ 分页）
```

---

## 快速开始

```bash
# 看成品（首页 = 知识图谱）
open dist/index.html

# 改完源码重新打包（8 个页面一次生成）
python3 scripts/build/bundle.py
python3 scripts/build/seo.py           # 逐页注入 title/description/keywords/JSON-LD

# 数据也要重跑（改了抽取规则、订正了人物时）
python3 scripts/pipeline.py          # ingest + build 全跑
python3 scripts/pipeline.py build    # 数据已就绪，只重打包

# 跑测试（109 项：数据 / 架构 / 产物 / 浏览器）
python3 tests/run.py
python3 tests/run.py --no-web        # 跳过浏览器冒烟，快

# 开发模式：原生 ES module + fetch，改完刷新即可，不用打包
python3 -m http.server 8080 && open http://localhost:8080/
```

---

## 目录

```
.
├── LICENSE                MIT 许可证
├── src/                    前端源码（分层，每个文件 ≤300 行）
│   ├── core/               总线 / 状态 / DOM 工具——不认识业务
│   ├── data/               仓库 / 领域模型 / 图模型 / 古文渲染
│   ├── engines/            布局与交互引擎（纯函数，零 import）
│   ├── router/             旧链接重定向（多页面下已无哈希路由）
│   ├── controllers/        编排：听事件、取数据、喂视图；app.controller = 每页启动器
│   ├── views/              只管画，不存状态
│   ├── pages/              每页入口（只引自己的控制器，控制本页打包体积）
│   ├── sections/           每个分类一个 <section> 内容块
│   ├── styles/             一视图一份 CSS
│   └── shell.html          页面骨架（菜单 / 页脚）+ 四个注入点
├── data/                   ★ JSON 数据库（可溯源）
│   ├── persons.json        260 人：字号、籍贯、生卒、学案归属
│   ├── relations.json      247 条关系 + 每条的 provenance
│   ├── orphans.json        52 个孤点的判读结论
│   ├── schools/geo/timeline/toc.json
│   ├── volumes/x1,x2,x3.json    卷前三篇（原序、发凡、师说）
│   ├── volumes/v01–v63.json  63 卷正文
│   ├── yangming.json         阳明心学专页（四句教 + 14 章：镜像/矩阵/四象）
│   ├── schema/             7 份 JSON Schema
│   └── intermediate/       中间产物，可删可重生成
├── scripts/
│   ├── ingest/             原文 → 结构化（抽取、订正、对齐、明史精读）
│   ├── build/              结构化 → 判读 → 打包
│   └── pipeline.py         一条命令跑完
├── tests/                  自动化测试
├── resources/              原始素材（63 卷原文、原书目录、明史儒林传、阳明心学手稿页）
├── vendor/                 d3.v3.min.js（本地化，不走 CDN）
├── legacy/                 v7.10 单体版及其脚本，只读留档
├── docs/                   架构说明 / 数据字典
└── dist/                   打包产物
```

---

## 71 个页面（菜单互链，一分类一页；学案原文按卷分页）

| 页面 | 分类 | 看什么 | 本页专属 SEO |
|---|---|---|---|
| `index.html` | 知识图谱 | d3 力导向，可聚焦某人的关系网（默认首页） | 师承知识图谱 |
| `graph.html` | 谱系总图 | 纵向树，一眼看清代际 | 师承树状总览 |
| `roster.html` | 人物线索 | 17 学案分组展开 | 儒者名录 |
| `time.html` | 时间线索 | 按生卒年排布 | 生卒年时间轴 |
| `geo.html` | 地理线索 | 17 省份，可与名录联动 | 籍贯地理分布 |
| `orphan.html` | **孤点现象** | 52 个孤点为什么孤——见下 | 孤点因由详解 |
| `book/` | 学案原文（64 页） | 卷前三篇（原序/发凡/师说，三个 tab）+ 63 卷各一页 | 每卷独立标题 |
| `yangming.html` | 阳明心学 | 四句教 + 14 章（镜像/矩阵/四象），顶部章节目录随滚动高亮 | 四句教图解 |

**学案原文 64 页拆页**：卷前一篇 `book/index.html`（三个 tab 切原序/发凡/师说）+ 63 卷各一页
（`book/chapter-one.html` … `book/chapter-sixty-three.html`），每页只内联本卷正文 + 自己的
title/description/keywords。加载更快（单页 ~0.31 MB）、互不影响。深链：
`book/chapter-twelve.html`（直接进卷十二）、`book/index.html?p=x2`（卷前发凡）。

页面之间用普通 `<a>` 互链；每页只带自己的 CSS/JS/数据，meta 标题、描述、关键词、
JSON-LD 都围绕本分类生成（`scripts/build/seo.py`）。其他深链用查询参数：
`index.html?focus=王阳明`（图谱聚焦）、`graph.html?all=1`（全览）、`index.html?orphans=1`（只看孤点）。

旧版哈希链接（`#content/kg`、`#v12`、`#kgf王阳明`、`#all`、`#/graph`、`book.html?v=12`）会自动重定向到
对应新页面，老书签不会 404。

---

## 「孤点」不是数据缺失

图上 52 个不连线的点，很容易被误读成「没抽全」。实际拆开看：

| 类别 | 数量 | 说明 |
|---|---|---|
| 编纂设计使然 | 27 | 诸儒学案本就是收录「不列于宗派者」，无师承是它的定义 |
| 横向结社 | 8 | 东林诸子是同人讲会，不是师徒纵贯 |
| 附于他人传后 | 2 | 樵夫朱恕、陶匠韩乐吾之类，原书附见，不另立传 |
| 原书未立本传 | 6 | 黄宗羲只提名字，未记学脉 |
| **真数据缺口** | **9** | 这 9 个才是待补的 |

结论写在数据里（`data/orphans.json` 的 `meta.headline`），不是硬编码在页面上——
以后补齐了 9 个缺口，页面文案会自己变。

---

## 每条关系都能溯源

```json
{
  "from": "冯应京", "to": "邹元标", "type": "师承",
  "sources": ["legacy-mining", "mined"],
  "confidence": 0.99,
  "cited": true,
  "provenance": [{
    "volume": 24,
    "volume_name": "江右王门学案九",
    "section": "佥事冯慕冈先生应京",
    "pattern": "师事",
    "quote": "……先生师事邹南臬，其拘幽书草，皆从忧患之际……",
    "alias_hit": "邹南",
    "method": "regex-mining"
  }]
}
```

247 条里 174 条带原文出处，来源四路：

| 来源 | 说明 | 可信度 |
|---|---|---|
| `mingshi` | 《明史》卷282/283 儒林传**人工精读**，带卷次+原文引文 | 0.95 |
| `mined` | 63 卷学案正文正则抽取，带章节+引文 | 依置信度 |
| `legacy-mining` | 上一轮抽取，带卷次+片段 | 0.80 |
| `drawio` | 谱系总图手绘边，无引文（`needs_citation` 标着） | 0.70 |

多条来源互相印证会加权，上限 0.99。点开人物卡就能看到出处（明史出处显示为《明史》卷N，
与学案卷 1–63 区分开）。

---

## 三条不许破的规矩

1. **每个 js / css 文件 ≤300 行**，测试会卡。
2. **分层不许倒挂**：engines 不 import 任何东西；views 不碰 store；
   只有 `data/repository.js` 能 `fetch`，只有 `router/index.js` 能改 `location.hash`。
3. **数据只有一个真相**：孤点数只登记在 `orphans.json`，
   `relations.json` 不重复存——重复的字段迟早会打架。

这三条都由 `tests/test_source.py` 和 `tests/test_data.py` 自动执行，不靠自觉。

---

## 人物称呼：姓名+字

古人以「姓名+字」记录（如 陈献章，字公甫；娄谅，字克贞；湛若水，字元明），
称呼时以「姓+字」为主。人物库的 `zi` 字段照此补齐（明史儒林传提供了大量字的考据），
人物卡与花名册会显示「字X」。图谱节点与搜索仍用通行名（王阳明），
避免「王伯安」这种生疏称谓割裂认知——通行名与字在数据里并存，互不覆盖。

《明史》补充人物的档案（字号、籍贯、学问风格、所在卷）存于
`resources/mingshi/mingshi.json`，人物卡会显示其学问风格并标注「《明史》儒林传」。

---

## 测试

```
tests/
├── harness.py       零依赖的极简测试框架
├── test_data.py     20 项：数据完整性、外键、孤点自洽、明史方向、卷前三篇、阳明心学、简体一致
├── test_source.py   13 项：分层方向、行数上限、页面清单与源码对账、文档在不在
├── test_build.py    13 项：71 页产物完整、数据切片正确、逐页 SEO、无模块环、语法可过
├── smoke.mjs        63 项：真浏览器逐个开 8 页 + book 族深检，验内容纯净/菜单高亮/SEO 独立、
│                    跨页聚焦（?focus/?v/?orphans）、旧链接重定向、卷前 3 tab、阳明心学读图说明
└── run.py           串起来，源码比产物新时自动重打包
```

浏览器冒烟用 puppeteer-core 驱动系统 Chrome（jsdom 量不了 SVG 的 `getBBox`）。
没装 Chrome 就加 `--no-web`。

更新记录见 [CHANGELOG.md](CHANGELOG.md)，架构细节见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)，
字段含义见 [docs/DATA.md](docs/DATA.md)。

---

## 许可证

[MIT License](LICENSE)。可以自由使用、修改、商用（含衍生作品），保留版权声明即可；
作者不对软件作任何担保。数据内容（《明儒学案》六十三卷、卷前三篇、阳明心学）整理自
维基文库（zh.wikisource.org）与《明史》儒林传等公开文献。
