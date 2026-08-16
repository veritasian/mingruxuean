# 架构说明

上一版是一个 3.1 MB 的单文件，改一处炸一处。这版的全部设计动机只有一句：
**让「改 A 不会碰坏 B」这件事由机器保证，而不是靠记性。**

---

## 一、分层与引用方向

```
                 ┌──────────────────────────────┐
   app.js ─────► │        controllers/          │  编排层
                 │  听事件 · 取数据 · 喂视图      │
                 └───┬───────┬────────┬─────────┘
                     │       │        │
          ┌──────────▼─┐  ┌──▼─────┐  ▼
          │  views/    │  │router/ │  （controllers 之间可互相引用）
          │  只管画     │  │地址栏  │
          └──┬──────┬──┘  └───┬────┘
             │      │         │
        ┌────▼──┐ ┌─▼────────┐│
        │data/  │ │engines/  ││   engines 零 import，纯函数
        │领域模型│ │布局与交互 ││
        └───┬───┘ └──────────┘│
            │                 │
        ┌───▼─────────────────▼───┐
        │        core/            │  总线 / 状态 / DOM 工具
        │      不认识任何业务       │
        └─────────────────────────┘
```

允许关系写死在 `tests/test_source.py` 的 `ALLOWED` 里，违反即测试红：

| 层 | 可以 import |
|---|---|
| `core` | `core` |
| `engines` | **什么都不许** |
| `data` | `core`、`data` |
| `router` | `core` |
| `views` | `core`、`data`、`engines` |
| `controllers` | 除自己外全部 |
| `app.js` | `core`、`data`、`controllers` |

### 为什么 engines 必须是空集合

`tree-layout` / `pan-zoom` / `force` / `search` 四个引擎回答的都是纯计算问题：
「给我一批节点和边，算出每个点的坐标」「给我一个变换矩阵和一次滚轮事件，算出新矩阵」。
这些问题跟明儒学案没关系，跟 DOM 也没关系。一旦引擎里出现 `import { persons }`，
它就再也不能被单独测试、单独替换了。所以这条限制卡得最死。

---

## 二、三个「唯一入口」

模块化最容易失败的方式，是拆完之后每个模块都自己偷偷做同一件事。
三处高危动作各留一个口子：

| 动作 | 唯一出口 | 违反的后果 |
|---|---|---|
| `fetch` 拉数据 | `data/repository.js` | 数据来源散落，改成内联数据时要改十几处 |
| 改 `location.hash` | `router/index.js` | 跳转逻辑各说各话，回退键行为不可预测 |
| 写全局状态 | `controllers/*`（视图不许碰 `store`） | 视图之间隐式耦合，一个视图的渲染影响另一个 |

`repository.js` 内部做了一件关键的事：**同一个接口，两种数据源**。
开发时走 `fetch('data/persons.json')`，打包后走 `window.__MRXA__.persons`。
上层代码完全不知道区别，所以开发模式和产物模式跑的是同一份逻辑。

---

## 三、通信方式：事件总线，不是互相调用

```
用户点了「王阳明」
   │
   ├─ view 只负责 emit(EV.PERSON_PICKED, '王阳明')
   │
   ├─ app.controller 听到 → router.go('kg', ['王阳明'])
   │
   ├─ router dispatch → emit(EV.ROUTE_CHANGED, {name:'kg', params:['王阳明']})
   │
   └─ kg.controller 听到 → 取数据 → kg.view.focus('王阳明')
```

视图从不知道「点了之后会发生什么」，控制器从不知道「是哪个视图点的」。
站点是**一分类一页面**的菜单结构（8 个页面），每页只带自己的视图与数据。
加新页面时不需要修改任何现有视图——在 `scripts/build/bundle.py` 的 `PAGES` 清单里登记一条
（入口模块 `src/pages/x.js` + 内容块 `src/sections/x.html` + 样式），再写视图文件即可。
页面间跳转用普通 `<a>`，跨页聚焦用查询参数（`?focus=` / `?v=` / `?orphans`）。

---

## 四、路由（多页面）

站点是**一分类一页面**：页面间用普通 `<a>` 互链，地址就是文件名，没有客户端路由。
深链用查询参数，由每页启动器（`app.controller.js` 的 `boot`）统一解析成控制器认识的 `{params, query}`：

```
index.html?focus=王阳明      知识图谱聚焦某人
index.html?orphans=1         知识图谱只看孤点
graph.html?all=1             师承总图全览
book.html?v=12               学案原文第 12 卷
book.html?v=x2               卷前 · 发凡
```

`src/router/` 只剩 `redirectLegacy()`：启动时把旧版哈希链接重定向到新页面
（`#content/kg` → `index.html`、`#v12` → `book.html?v=12`、`#kgf王阳明` → `index.html?focus=王阳明`、
`#all` → `graph.html?all=1`），老书签不会 404。

---

## 五、打包：自己写的 170 行

没引 rollup / esbuild。原因很实际：这个项目要能在一台只有 python3 的机器上从零构建，
多一个 node_modules 就多一个「明年跑不起来」的理由。

`scripts/build/esm_bundle.py` 做三件事：

1. **`transform(mod_id, source)`** —— 正则改写单个模块。
   `import { a, b } from './x.js'` → `const {a, b} = __req('x.js')`；
   `export function f(){}` → 保留声明，末尾追加 `Object.assign(__exp, {f})`。
2. **`collect(entry, root)`** —— 从入口深度遍历依赖，拓扑排序，**顺带检测环**。
   有环直接构建失败，不留到运行时变成 `undefined is not a function`。
3. **`bundle(entry, root)`** —— 输出运行时（`__M` 模块表 / `__def` 注册 / `__req` 求值）
   + 每个模块一个 IIFE + 入口调用。

**IIFE 包裹解决的具体问题**：`core/bus.js` 和 `core/dom.js` 都导出了叫 `clear` 的函数。
简单拼接会后者覆盖前者。包一层作用域后各自独立——`test_build.py` 里专门有一条用例钉这个。

`scripts/build/bundle.py` 负责组装成品：

- CSS 按固定顺序拼接（`tokens` 必须最先，它定义 CSS 变量）。
- 数据序列化成 `JSON.parse(\`…\`)` 内联。**这里有个坑**：如果某卷正文里出现字符串
  `</script`，浏览器会当场截断文件。所以 `js_literal()` 除了转义反引号和 `${`，
  还要转义 `</script` 和 U+2028 / U+2029（JS 里这俩是换行符，JSON 里不是）。
- d3 从 `vendor/` 读进来内联，不留任何网络 URL。

---

## 六、数据链路

```
resources/volumes/all.json  (63 卷原文)
resources/toc.json          (原书目录 204 章节)
legacy/data_final.json      (drawio 谱系 + 旧版挖掘结果)
        │
        │  scripts/ingest/
        ├─ build_persons        规范化姓名、字号、籍贯、生卒
        ├─ link_book_sections   对齐原书章节，学派归属以原书为准
        ├─ reconcile_persons    合并重名、订正学派、补号
        └─ extract_relations    正文正则挖师承（师事/受业/从游/问学…）
        │
        │  scripts/build/
        ├─ build_relations      四路来源合并（drawio/legacy/mined/mingshi）、算置信度、标 cited
        ├─ analyze_orphans      孤点判读（5 类）
        ├─ build_aux            地理 / 时间轴 / 目录 / 分卷正文
        └─ bundle               → dist/ 8 个页面（一分类一页，数据按页切片）
        └─ seo                  → 逐页注入 title/description/keywords/JSON-LD
```

一条命令：`python3 scripts/pipeline.py`。任一步失败即中断，不产出半成品。

---

## 七、单一真相原则

孤点数只登记在 `orphans.json` 一处。这不是洁癖——

> 事故复盘：`relations.json` 的 `meta.orphan_count` 和 `degree.json` 的度数表
> 曾经各算各的。前者把「附见」算作一条边，后者不算，于是樵夫朱恕在一处是孤点、
> 在另一处不是。页面上显示 52，图上数出来 53，谁也说不清哪个对。

现在的规则：**孤点 = 在 `{师承, 私淑}` 两类边上度数为 0 的人**。
附见是原书的编排位置（「附于他人传后」），不是一条师承边——
所以朱恕确实是孤点，只是孤得有原因，归入 `appendix` 类。
这条规则在 `src/data/model.js` 的 `edgeList()` 和
`scripts/build/analyze_orphans.py` 的 `EDGE_TYPES` 里各写一遍，
`test_data.py` 有一条用例专门比对两者是否一致。

---

## 八、测试为什么这么分

| 文件 | 管什么 | 失败时说明 |
|---|---|---|
| `test_data.py` | 数据自身是否自洽 | 抽取脚本出错了，或者手工订正打错字 |
| `test_source.py` | 架构有没有被磨平 | 有人图省事，在 view 里直接 fetch 了 |
| `test_build.py` | 产物有没有静悄悄少东西 | 打包器的问题，通常表现为「某一页空白」 |
| `smoke.mjs` | 真浏览器里到底画出来没有 | 前三层全绿也可能这里红——CSS 写错、SVG 尺寸算错 |

前三套是纯 python，零依赖，几百毫秒跑完。
`smoke.mjs` 用 puppeteer-core 驱动系统 Chrome——jsdom 量不了 `getBBox()`，
而这个项目一半的 bug 都藏在 SVG 尺寸里。没装 Chrome 就 `--no-web`。
