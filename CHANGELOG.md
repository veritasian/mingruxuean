# 更新日志

格式参照 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循语义化版本。

---

## [10.0.1] — 2026-08-09

Web 版（web/）可视化页修复：知识图谱等四张图恢复渲染。

### 修复：web 版图谱消失
- 根因：`web_build.py` 的 `section_static` 对 kg / graph / time / geo 只输出裸
  `<svg>`，缺少控制器绑定工具栏所需的 DOM（`#kgZoomIn` `#legend` `#tline`
  `#geoSum` 等）。控制器一 `addEventListener` 就遇到 `null` 抛错、整页中断，图不绘制。
- 修复：改为复用与离线版一致的 `src/sections/*.html`（含完整工具栏）；geo 额外
  保留 `<noscript>` 省→人物对照表，供搜索引擎与无 JS 场景使用。
- 影响页：知识图谱（index.html）、谱系总图（graph.html）、时间线索（time.html）、
  地理线索（geo.html）。
- 验证：64 项冒烟测试全绿。

## [9.2.0] — 2026-08-09

学案原文 URL 平铺 + 菜单跳转 bug 修复 + 卷页标题精简。

### 修复：book 页面点菜单跳转 404
- 根因：菜单链接是相对路径，`book/` 子目录里的页面点「阳明心学」会解析成
  `book/yangming.html` → 404（人物卡「在图谱聚焦」等跨页链接同理受影响）。
- 修复方式：直接取消 `book/` 二级目录，全部页面平铺到站点根（见下），相对链接不再失效。

### 变更：学案原文 URL 平铺（去掉 book 二级分类）
- `book/index.html` → **`chapter-Preface.html`**（卷前三篇，三个 tab）
- `book/chapter-twelve.html` → **`chapter-twelve.html`**（63 卷各一页，全在根目录）
- 深链：`chapter-Preface.html?p=x2`（卷前发凡）、`chapter-twelve.html`（卷十二）
- `vercel.json` 加 rewrite：旧 `/book/*` 链接自动转到新平铺页（老书签不 404）
- `dist/book.html` 旧跳板同步指向平铺页

### 变更：卷页标题前置（页面标题在前）
- 从「名儒学案图谱 · 学案原文 | 卷12 浙中王门学案二 · 黄宗羲《明儒学案》全文」
  改为「**卷12 浙中王门学案二 · 黄宗羲《明儒学案》全文**」
- 卷前页：**黄梨洲先生原序 · 发凡 · 师说 · 黄宗羲《明儒学案》全文**

### 测试
- 新增回归「菜单跨页跳转」：卷页点菜单必须到根级 yangming.html
- 测试总数 109 → **110**，全绿 33 s

---

## [9.1.0] — 2026-08-08

三项改进：

### 1. 顶部「明儒学案」改为 home 链接
- `<h1 class="title"><a href="index.html">明儒学案</a></h1>`，颜色与装饰继承，hover 降低透明度。

### 2. 学案原文按卷分页（64 页）
原 1.28 MB 单页 → 卷前一篇 + 63 卷各一页，每页只内联自己那份正文。
- `dist/book/index.html`：卷前三篇（原序/发凡/师说），页内三个 tab 切换
- `dist/book/chapter-one.html` … `chapter-sixty-three.html`：每卷独立页（URL 用英文数字 one/two/…/sixty-three）
- `dist/book.html`：保留为旧版跳板（带 ?v= 自动跳到对应卷页），老书签不 404
- 数据按页切片：核心 7 份 JSON 每页都有；book 页只内联自己那一卷正文（卷前页 3 篇、卷页 1 篇）
- 每页独立 title/description/keywords/JSON-LD（围绕该卷主题：卷名、前五人名、字数）
- 左目录点击正编卷号 → 跳到对应独立页（sibling URL）；点卷前篇 → 本页内切 tab
- 卷内检索只建本卷索引；搜索文案改为「本卷检索」
- `dist/` 产物：71 个页面（原 8 个 + 63 卷页），每个卷页约 0.31 MB

### 3. 阳明心学四句教下加读图说明块
- 边框 + 淡蓝透明背景（`rgba(173,216,230,.32)`）
- 6 段笔者心得：「读图先读此：学贵自得…惟精惟一」（含三论、五派、修证不二、再看四句教、顿知渐修）
- 数据存 `data/yangming.json` 的 `note` 字段

### 测试
- 新增卷前 tab、卷页加载、目录跨页跳转、阳明读图说明 6 项；重写 book 族断言（缓存按文件、菜单锚点按 id）
- 测试总数 103 → **109**，全绿 33 s

---

## [9.0.0] — 2026-08-08

**架构变更：单文件 + 哈希路由 → 一分类一页面的多页站点。**

重构动机：原「一个 HTML 内联 8 个视图」的形态上线后问题明显——8 个分类共用一份
meta（SEO 无法按分类优化）、首屏要下载全部 3.4MB、所有视图的 CSS/JS 挤在同一页。

### 变更

- **新增 8 个独立页面**：`dist/index.html`（知识图谱，默认首页）、`graph.html`（谱系总图）、
  `roster.html`（人物线索）、`time.html`（时间线索）、`geo.html`（地理线索）、
  `orphan.html`（孤点现象）、`book.html`（学案原文）、`yangming.html`（阳明心学）。
  菜单为普通 `<a>` 互链，当前页高亮；每页只渲染自己的 section，其他分类内容不出现。
- **数据按页切片**：`window.__MRXA__` 每页只内联所需数据——volumes（63 卷 + 卷前三篇）
  只进 book 页、yangming 只进阳明页、d3 只进知识图谱页；其余 6 页体积从 3.4MB 降到 ~0.3MB。
- **逐页 SEO**（`scripts/build/seo.py` 重写）：每页独立 title/description/keywords/canonical/
  og/JSON-LD，文案围绕该分类（核心关键词 + 长尾 + 吸引力），数字实时读 data/。
- **深链改查询参数**：`book.html?v=12`、`index.html?focus=王阳明`、`index.html?orphans=1`、
  `graph.html?all=1`；旧哈希链接（`#content/kg`、`#v12`、`#kgf王阳明`、`#all`、`#/graph`）
  由 `src/router/` 的 `redirectLegacy()` 自动重定向到新页面。
- **结构**：新增 `src/pages/`（每页入口，只引自己的控制器）与 `src/sections/`（每页内容块）；
  `app.controller.js` 改为每页启动器（boot：主题/人物卡/参数解析/enter）；删除 `src/app.js` 单入口。
- **页面间跳转**：人物卡「在总图定位 / 在图谱聚焦」改为 `?focus=` 跨页导航，目标页自动定位并弹卡。
- 测试重构：`smoke.mjs` 改为逐页真浏览器体检（内容纯净/菜单高亮/SEO 独立/数据切片/跨页聚焦/旧链接重定向），
  `test_build.py` 改为 8 页产物检查。测试总数 **79 → 103**，全绿。

### 兼容

- 旧书签 `#content/kg`、`#v12`、`#kgf王阳明`、`#all`、`#/graph` 自动跳转，不 404。
- `dist/明儒学案.html` 单文件形态取消，改由 `dist/index.html` 等 8 页替代。

---

## [8.8.1] — 2026-08-08

修复：带 hash 刷新（如 `#content/kg`）页面空白。

### 修正

- **带 hash 刷新页面空白**（用户报告）。两个根因：
  1. `migrateLegacyHash()` 把新格式 `#content/kg`（不以 `/` 开头）误当旧链接，改写成 `#content/content/kg` →
     路由解析出未知 `content`，视图不激活。修复：跳过 `content/` 前缀（与 `/` 前缀同样交由 parse 处理）。
  2. `app.controller.js` 里 `on(EV.ROUTE_CHANGED, …)` 注册在 `router.start()` **之后**，首帧 dispatch 的事件
     落在监听器注册前 → 页签/视图永远拿不到 `.on`，整页空白（首次加载与刷新都受影响，此前靠用户点页签触发
     hashchange 才恢复显示）。修复：把订阅挪到 `router.start()` 之前。
- 新增 smoke 回归「带hash刷新」：直接以 `#content/kg` 载入，断言 hash 不变且 `sec-kg` 激活。测试 **78 → 79**，全绿 16.2s。
- README 测试数 78→79、smoke 33→34。

---

## [8.8.0] — 2026-08-08

首页默认知识图谱并置顶菜单；菜单更名（线索化）；URL 改为 `#content/` 单词组合；新增 SEO 注入脚本。

### 变更

- **首页默认知识图谱**。`VIEWS` 重排：知识图谱置首、谱系总图第二（原谱系总图在前）；路由 `DEFAULT` 仍为 `kg`，
  首次打开落在 `#content/kg`。
- **菜单更名**：人物总录 → **人物线索**、时间线 → **时间线索**、地理分布 → **地理线索**
  （其余：知识图谱/谱系总图/孤点现象/学案原文/阳明心学 不变）。
- **URL 调整为 `#content/<视图>`**（`src/router/index.js`）。新增 `PREFIX='content'`：
  `stringify` 一律输出 `#content/graph`、`#content/book/12`、`#content/kg/王阳明` 这类单词组合；
  `parse` 兼容旧格式 `#/graph` 与旧链接 `#v12`/`#all`/`#kgf王阳明`（migrateLegacyHash 改写为 `#content/…`）。
- **SEO 注入脚本**（`scripts/build/seo.py`，bundle 之后跑，幂等 `<!--SEO-->` 块）：
  - `<title>`：核心关键词（名儒学案图谱/明儒学案师承）+ 长尾（黄宗羲 · 260 位明代大儒 · 六十三卷全文）+ 吸引力（在线阅读）。
  - `<meta description>`：核心关键词 + 长尾 + 吸引力文案（含真实统计：17 学案 · 260 人 · 247 关系 · 174 有出处）。
  - `<meta keywords>` + **JSON-LD**（WebSite + Book @graph，inLanguage zh-CN，指向 `https://mingruxuean.vercel.app/`）。
  - 统计数字实时读 `data/`，不硬编码；另写 `dist/seo.json` 供检查；`shell.html` 静态 `<title>` 同步为 SEO 标题。
- 测试 **76 → 78**：`smoke.mjs` +2（默认首页 = `#content/kg`、菜单次序与名称）。全绿 14.9s。
- README 路由表改 `#content/…` + 新视图名；smoke 描述同步。

---

## [8.7.0] — 2026-08-08

阳明心学「章节目录」从左悬浮侧边栏改为置顶横向导航，正文真正居中。

### 变更

- **章节目录置顶**。`.ym-shell` 从 grid `196px 1fr` 改为普通块容器 + `max-width:1200px; margin:0 auto`；
  删掉 `.ym-side / .ym-side-cap / .ym-toggle / 移动端抽屉` 全部样式；新增 `.ym-nav`（`display:flex; flex-wrap:wrap;
  justify-content:center; position:sticky; top:10px; border-radius:99px`，胶囊药丸风格，桌面粘附在视口顶部）。
  正文 `max-width:880px; margin:0 auto` 真正居中，不再受左侧导航偏移。
- **滚动监听**：控制器逻辑不变（依旧 `view.markSide`），`.ym-link.on` 在导航条上高亮当前章节。
- **跳转偏移**：`.ym-chapter / .ym-outro` 加 `scroll-margin-top:74px`，粘附的目录不会遮住章节头。
- **移动端**：`.ym-nav` 改为 `flex-wrap:nowrap; overflow-x:auto` 横向滚动条，删除 ☰ 折叠抽屉逻辑。
- 视图 `side()` → `nav()`，DOM 由左栏块换成顶部 `<nav.ym-nav>`；控制器删 `onTap`（无折叠抽屉）。
- smoke 检查「侧边栏 / 移动折叠」改为「章节目录 / 目录置顶」（`navTop < mainTop`）；测试总数 76 不变。
- README 路由表与 smoke 描述同步更新（顶部章节目录 + 移动端横滑）；shell.html tab-head 小字「左侧章节随滚动高亮」→「置顶章节目录随滚动高亮」。

---

## [8.6.0] — 2026-08-08

阳明心学专页整体居中；叁·体用论换成与下面章节同款通用四象限（内容与便签不变）。

### 变更

- **壹~拾肆 章节内容与底部文字整体居中**。`.ym-shell` 改为 grid（`196px 1fr`）+ `max-width:1200px; margin:0 auto`，
  成为页面里一张居中卡片；左侧边栏 flush left，`.ym-main` `justify-self:center` 在右栏内居中（max 880）。
  桌面下「左边菜单悬浮侧边栏」形态不变，移动端折叠抽屉保持原样。
- **叁·体用论换成通用四象限**。数据从 `axis` → `quad`（use/body 改为「用」「体」圆 + hint「觉 · 心」「离 · 性」，
  q 改为 4 格 title+lines）。四便签（红 有觉无离/落于功利 · 金 觉离不二/圣境 · 绿 不觉不离/凡 · 红 有离无觉/落于枯寂）
  与尾注「Progress × Result = 体用合一之阶。」原样保留。
- 视图去掉 `renderAxis`（ch3 走 quad 分支），`yangming-quad.css` 去掉坐标轴/进度条/轴标签 全部样式（仍保留通用四象限 + 三色便签）。
- smoke 检查「原版结构」改成「色带 2 · 矩阵 1 · 四象板 12 · 小人 3」；test_data「阳明心学专页」描述与 `return` 改为「三形态」。
- README 测试总数 76 不变（未增减用例）。

---

## [8.5.0] — 2026-08-08

阳明心学专页视觉复刻原手稿页：镜像双带 / 3×3 矩阵 / 坐标轴 / 四象限 / 渐入 / 卡片倾斜 / 便签随机旋转，全部还原，只把颜色换成站内浅色系。

### 变更

- **视觉结构忠实于原版**。`yangming.view.js` 改为生成与原手稿页完全一致的 DOM：
  - **壹·思维模型** 镜像布局（左侧竖排标签+SVG 箭头 / 右侧黄绿双带 + 子盒 + 反向弧形虚线 + 红圆「致知」「格物」 + 底部红长弧）。
  - **贰·根器论** 3×3 矩阵（带 run/walk/crawl 人形小图 SVG、三色圆点儒/佛/道，行标 + 单元格强字 + 行内 hover 3D 倾斜）。
  - **叁·体用论** 觉/离 坐标轴（顶部「用」圆 + 垂直短线 / 右侧「体」圆 + 水平短线 / 坐标板 + 四象限便签 + Progress/Result 灰条）。
  - **肆~拾肆** 通用四象限（顶部 use 圆+hint / 右侧 body 圆+hint / 坐标板 + 四便签 / 横轴为体·纵轴为用·中道合一 尾注）。
- **动效全部复刻**：`IntersectionObserver` 渐入（`.ym-reveal → .is-in`）、hero 四句教逐句升起（rise 关键帧 0.1→0.7s 错开）、hero 滚动竖线循环（scrollDrop）、卡片 mousemove 3D 透视倾斜、便签随机旋转（CSS 变量 `--peel` 替代原版的内联 transform，hover 仍可归正放大）。
- **配色换站内浅色系**。原版深色（`#0e1014` 墨底 + 黄/绿/红/青 四点缀）→ 站内纸色：`--ym-y:#C9A24B / --ym-y-d:#B5762A / --ym-g:#3F7A4E / --ym-r:#A23B2E / --ym-c:#2E6F73 / --ym-b:#2F5D8C`，三套主题（zen/ink/white）下都协调。
- 数据补 `eyebrow`（Wang Yangming · Philosophy of Mind）与 flow 行重音（`emph`/`know`），`scripts/ingest/yangming_data.py` 从存档 HTML 提眉标。
- 样式拆为两份：`yangming.css`（hero/壳/镜像/矩阵/尾注/响应式）+ `yangming-quad.css`（坐标轴/四象限/响应式），各 ≤300 行。

### 变更

- 测试总数 **74 → 76**：`smoke.mjs` +2（阳明心学 原版结构、渐入）。
- `bundle.py` CSS_ORDER 加 `'yangming-quad'`。

---

## [8.4.0] — 2026-08-08

新增「阳明心学」页签：用户手稿页整合进学案站，左悬浮侧边栏 + 滚动监听 + 移动端折叠。

### 新增

- **阳明心学专页**（第 8 个页签，`#/yangming`）。内容转录自用户手稿页
  （`resources/yangming/` 存档 index.html + main.js），`scripts/ingest/yangming_data.py`
  从存档读出章节标题结构、转录四象限数据（交叉校验，标题对不上会报错），
  产物 `data/yangming.json`：四句教 + 14 章 + 尾注，四种形态：
  - **flow**（壹·思维模型）明镜/磨镜两路卡流；
  - **matrix**（贰·根器论）三教 × 三阶矩阵；
  - **axis**（叁·体用论）觉/离 四象限坐标；
  - **quad**（肆~拾肆）体/用 四象限，正文照搬手稿原意（心即理、知行合一、中庸、大学、
    定慧、止观、有无、性命、虚实、正奇、形势 十一组「不二」）。
- **左悬浮侧边栏**（Sticky Sidebar）。`yangming.view.js` 渲染章节导航，`position:sticky`
  悬停在内容左侧；**ScrollSpy** 由控制器监听滚动，取视口 30% 处章节高亮侧边栏，
  滚到底自动亮最后一项「附」；点链接平滑滚动到对应章节。
- **移动端折叠**（Mobile Collapse）。≤860px 时侧边栏收起为抽屉，点「☰ 章节目录」展开，
  点章节后自动收起。
- 配色全部走站内 token（`--accent` 朱红 / `--card` 纸色 / `--line` 边框），四象限便签
  用红/黄/绿三种固定纸色（A23B2E / B5762A / 3F7A4E），三套主题下均可读。
- 数据链路：`bundle.py` 把 yangming 内联进 `__MRXA__`，离线单文件不联网；
  `repository.loadYangming()` 是唯一取数口（开发版走 fetch，打包版走内联）。

### 变更

- 测试总数 **68 → 74**：`test_data.py` +1（14 章齐备、四形态数据完整）、
  `smoke.mjs` +5（页签 8 个、阳明心学 内容/侧边栏/移动折叠/滚动监听）。
- 文档：README 路由表与目录树加 yangming、测试数更新；docs/DATA.md 增 yangming.json 一节。

### 已知待办

- （已在 [8.5.0] 复刻原版镜像/矩阵/坐标轴/四象限）

---

## [8.3.0] — 2026-08-08

卷前三篇（原序、发凡、师说）置顶于卷一之前，打开学案原文默认显示 原序。

### 新增

- **卷前第三篇 发凡**（`resources/volumes/front_x2.wiki`，经 7890 代理从 zh.wikisource 抓回原始 wikitext）。
  生成脚本 `scripts/build/build_front.py` 把 师说 的键从 x2 顺延为 x3、发凡 取 x2，
  目录次序为 原序(x1) → 发凡(x2) → 师说(x3) → 卷一，与原书 `previous=莫晉序 / next=師說` 的邻接一致。
  发凡正文 1577 字，黄宗羲总论有明一代学术源流与《明儒学案》编纂体例。
- **目录 `front` 字段扩展为三篇**：`tocEntries()` 先吐 x1/x2/x3 再吐 63 卷；`book.view.js` 目录标题
  由「卷前二篇」改为「卷前三篇」。63 卷不变量不变（目录仍 1–63 连续）。

### 变更

- **打开学案原文（全文页）默认显示 原序**。`book.controller.js` 的 `enter` 在不带篇目参数时
  （`#/book`）默认打开卷前首篇 x1（原序），与原书开篇次序一致；指定卷号或篇目键仍正常跳转。
- 测试总数 **66 → 68**：`smoke.mjs` +2（卷前 发凡、默认页＝原序）。

---

## [8.2.0] — 2026-08-08

卷前二篇（原序 + 师说）置顶于卷一之前，底本署名简化为「据维基文库整理」。

### 新增

- **卷前二篇**（`resources/volumes/front_x1.wiki`、`front_x2.wiki`，经 7890 代理从
  zh.wikisource 抓回原始 wikitext）。生成脚本 `scripts/build/build_front.py` 产出
  `data/volumes/x1.json`（黄梨洲先生原序，1393 字）、`x2.json`（师说，7051 字，链接 25 位明儒），
  并写入 `toc.json["front"]`。
  - **原序**：黄宗羲自序，「一本万殊，学问不必强同」之旨，置于全书最前。
  - **师说**：刘宗周评骘明代儒者二十五家，黄宗羲冠于学案之首，原书即列卷一之前。
- **目录 `front` 字段**。`tocEntries()` 先吐卷前二篇（key=x1/x2）再吐 63 卷，`volumeInfo()`
  同时认数字卷号与 x1/x2 字符串键；**63 卷不变量不变**（目录仍 1–63 连续，卷前二篇单列，不挤占卷号）。
- **路由/仓储适配字符串键**：`#/book/x1`、`#/book/x2` 可读；repository 对数字键走 `volumes/vNN`、
  字符串键走 `volumes/xN`。
- **师说人物挂接**：`==方正學孝孺==` 这类「姓+号+名」标题经 `guess_id()` 还原为规范人物 id，
  点条目跳人物卡。
- **wikitext 解析补 `<onlyinclude>/<noinclude>/<includeonly>` 剥离**，避免 wikisource 模板标签漏进正文。
- smoke 新增 3 项：卷前 原序（828 字 · 关联 0 人）、卷前 师说（6579 字 · 关联 25 人）、
  卷前次序（原序 → 师说 → 卷一）。

### 变更

- **底本署名简化**。`src/shell.html` 页脚由「据原 drawio 图谱与维基文库整理」改为
  「据维基文库（zh.wikisource.org）整理」——数据现以维基文库为底本，drawio 仅作早期来源之一，
  不再单列。
- 测试总数 **62 → 66**：`test_data.py` +1（卷前二篇齐备、排在卷一之前）、`smoke.mjs` +3（卷前三项）。

### 已知待办

- 卷前二篇暂未做逐字校对（与维基文库在线版比对），如需可补一项 wikitext 差异校验。

---

## [8.1.0] — 2026-08-08

《明史》儒林传（卷282/283）作为第二来源入库，师承关系方向统一。

### 新增

- **《明史》儒林传数据源**（`resources/mingshi/`）。原文（`v282.wiki`、`v283.wiki`）
  与人工精读产物（`mingshi.json`）：133 人档案（姓名+字+号+籍贯+学问风格，卷282 儒林一 / 卷283 儒林二）
  + 114 条师承关系，每条带卷次与原文引文。生成脚本 `scripts/ingest/mingshi_data.py`。
- **第四路关系来源 `mingshi`**。`build_relations.py` 现在合并四路来源
  （drawio / legacy-mining / mined / mingshi），明史来源可信度 0.95（人工精读+原文引文）。
  103 条明史来源关系入库，其中 18 条是**全新师承边**（如 王阳明→娄谅 首次从《明史》坐实、
  罗洪先→李中、孟化鲤→尤时熙、颜钧→徐樾、魏校 私淑 胡居仁、刘宗周→许孚远 等）。
- **23 位明史补充人物入库**（`add_mingshi_persons.py`）。陈琛、邵宝、杨廉、王应电、王敬臣、
  应良、蔡悉、赵维新、欧阳瑜、娄忱、邹善、邹德涵、丁元荐、王爵等——都是明史明确师承、
  能连进现有图谱的节点，挂到对应学案。人物库 237 → 260。
- **人物卡学问风格**。明史补充人物在人物卡显示「学问 …（《明史》儒林传）」。
- **明史出处显示**。人物卡出处区分两个卷次体系：学案卷 1–63 显示「卷N」，
  《明史》卷 282/283 显示「《明史》卷N」。

### 修正

- **师承方向全局统一**。谱系总图（drawio）原是「师→徒」，与系统约定
  「from=徒、to=师」相反，导致同一对师徒出现两条反向记录（如 娄谅↔夏尚朴 双线）。
  现在 drawio 边在合并时统一翻转为「徒→师」，与 mined/mingshi 合并去重；
  与更精确来源冲突时并入该条（如 邓以赞 私淑王阳明 的 drawio 直传边并入私淑边，
  不再生成假「师承」）。重跑后：270 条 → 247 条（消除重复与幽灵边），
  **反向共存对 0、重复对 0**，箭头朝向测试覆盖全部 245 条连线。
- **孤点重判**：53 → 52（明史新边连上了 2 个原孤点），其中真缺口仍是 9，未变。
- **带原文出处的关系**：108 → 174 条。

### 变更

- `tests/test_data.py` 新增 2 项：明史来源方向校验（18 条已知师徒对）、
  卷次范围分体系（学案 1–63 / 明史 282–283）。测试总数 59 → 62。

### 已知待办

- 9 个真数据缺口（`gap`）仍未补。
- 仍以 drawio 为唯一来源的 73 条关系待补原文出处（`needs_citation`）。
- 明史中另有 30+ 位人物（范祖干、谢应芳、汪克宽、梁寅、赵汸、陈谟等元末诸儒，
  及黄淳耀、来知德、吴悌等）档案已收入 `mingshi.json`，因无学案归属/师承链
  未并入主图；将来若要展示「明史儒林全貌」，可从该文件一键扩展。

---

## [8.0.0] — 2026-08-08

一次彻底的重做。上一版是一个 3.1 MB 的单文件，HTML、CSS、JS、数据全焊在一起，
改一处炸一处。这版把它拆成分层源码 + JSON 数据库 + 打包脚本 + 自动化测试。

### 新增

- **分层前端架构**（`src/`）。core / data / engines / router / controllers / views / styles
  七层，30 个 JS 模块 + 10 份 CSS，**每个文件都在 300 行以内**（最长 `kg.view.js` 188 行）。
  引擎层（tree-layout、pan-zoom、force、search）是纯函数，不 import 任何东西，
  可以单独拿去用。
- **哈希路由**（`src/router/index.js`）。`#/graph`、`#/book/12`、`#/kg/王阳明`、`#/graph?all`。
  地址栏成为应用状态的唯一书面记录，视图之间不再互相调用「你先关掉我再打开」。
  旧链接 `#v12` / `#kgf王阳明` / `#all` 自动改写，不 404。
- **「孤点现象」视图**（第 8 个页签，`#/orphan`）。回答「图上那些不连线的圆点是怎么回事」：
  53 个孤点按 5 类拆开——编纂设计 29 / 横向结社 8 / 附于他人传后 1 / 原书未立本传 6 /
  真数据缺口 9。类别与结论全部从 `orphans.json` 读，页面不硬编码。
- **可溯源 JSON 数据库**（`data/`）。7 份核心数据 + 63 卷正文 + 7 份 JSON Schema。
  每条关系带 `provenance` 数组，记录卷次、篇目、匹配模式、原文引文、命中的别名；
  `confidence` 综合置信度，`cited` / `needs_citation` 标明证据状态。
  270 条关系中 108 条已附原文引文。
- **自定义 ES module 打包器**（`scripts/build/esm_bundle.py`，170 行，零第三方依赖）。
  不引 rollup / esbuild：每个模块包一层 IIFE 保作用域，import 改写成 `__req()`，
  export 收进 `__exp`。打包时顺带检测循环依赖。
- **单文件离线产物**（`dist/明儒学案.html`，3.4 MB）。d3 v3 内联、数据内联、代码内联，
  双击即开，断网可用。同时产出开发版 `index.html`（5.4 KB，走原生 ES module + fetch，
  改完刷新即可，不用重打包）。
- **自动化测试 59 项**（`tests/`）。
  - `test_data.py` 17 项——外键、自环、重边、学案闭包、孤点自洽、出处卷次范围、简体一致。
  - `test_source.py` 12 项——分层方向、行数上限、`fetch` 唯一入口、`location.hash` 唯一入口、
    视图无状态、无残留 `console.log`。
  - `test_build.py` 12 项——占位符已替换、30 个模块一个不少、d3 已内联无网络 URL、
    数据里的 `</script>` 已转义、产物能过 `node --check`、模块图无环、产物与源码同步。
  - `smoke.mjs` 19 项——puppeteer-core 驱动真 Chrome，7 个视图逐个验渲染、点人物卡、
    验箭头朝向、验旧链接迁移、验卷次正文加载、验控制台无 error。
  - `run.py` 串起四套，源码比产物新时自动重打包。
- **数据链路一条命令**（`scripts/pipeline.py`）。`ingest`（规范化 → 对齐原书章节 →
  订正合并 → 抽取师承）+ `build`（合并来源 → 孤点判读 → 辅助数据 → 打包）。
- **d3 本地化**（`vendor/d3.v3.min.js`，151 KB）。原先从 jsdelivr 拉，断网即白屏。

### 修正

- **知识图谱的箭头指反了**。`kg.view.js` 原来 `source = r.from`（徒）、`target = r.to`（师），
  箭头从徒指向师，跟总图 `edgePath(b, a)` 的方向相反。同一份数据两处画法不一致，
  是那种「看着别扭但说不上哪儿不对」的 bug。已改为师 → 徒，268 条全部校验通过。
- **孤点判定的口径打架**。`degree.json` 把「附见」算作一条边，而图的 `edgeList()` 不画附见，
  于是樵夫朱恕在度数表里有邻居、在图上却是孤点，两边对不上。
  统一到单一规则 `{师承, 私淑}`：附见是编排位置，不是一条边。
  连带三处改动——`build_relations.py` 度数不再计入附见（孤点 52 → 53）；
  `analyze_orphans.py` 直接从关系表实算、并新增 `appendix` 类别；
  `relations.json` 的 `meta` 不再存 `orphan_count`（两处存同一个数，迟早会漂）。
- **地理视图选中态不同步**。省份条形图不跟着 chip 一起高亮，加了 `.geobar.on` 规则。
- **打包器路径解析**。`_norm(base, spec)` 原来没有正确切分 base 的路径段，
  `../` 跨层引用会解析错。

### 变更

- 原单体版 `明儒学案.v7.10.html` 及其全部脚本移入 `legacy/`，只读留档，不再维护。
- 根目录那份与 `legacy/明儒学案.v7.10.html` 逐字节相同的旧产物已移除，
  新入口统一为 `dist/明儒学案.html`。
- 视图高度改为跟随浏览器窗口自适应，不再显示固定高度数值。
- 数据文件统一简体（OpenCC 转换），`test_data.py` 会检查；
  原文引文保留原始字形，不强转。

### 已知待办

- 162 条关系来自原书谱系结构，尚无原文引文，`needs_citation: true` 标着。
- 9 个真数据缺口待补。

---

## [7.10] — 2026-08-07

单文件版最后一版，见 `legacy/明儒学案.v7.10.html`。
7 个视图、237 人、drawio 谱系 + 正则挖掘的师承关系，全部内联在一个 HTML 里。
