# 实现计划：页面化访问（recipe-web-ui）

**分支（Branch）**: `002-recipe-web-ui` | **日期（Date）**: 2026-08-15 | **规格（Spec）**: [spec.md](./spec.md)

**输入（Input）**: 来自 `/specs/002-recipe-web-ui/spec.md` 的功能规格

**说明（Note）**: 本模板由 `/speckit.plan` 命令填写；其定义描述了执行工作流。

## 摘要（Summary）

把现有 CLI 的六大功能（today / week / list / add / remove / history）升级为页面化访问：新增 `recipe serve` 子命令，用标准库 `http.server` 起一次性回环 HTTP 服务（仅监听 127.0.0.1），自动打开浏览器，页面通过 JSON API 调用现有 Python 核心模块（推荐/历史/存储），**不重写任何业务逻辑**。浏览器关闭即退出，零安装、零常驻、完全离线。数据文件与 CLI 完全共享，契约不变。技术路线详见 [research.md](./research.md)。

## 技术背景（Technical Context）

**语言/版本（Language/Version）**: Python 3.11+（沿用项目）

**主要依赖（Primary Dependencies）**: 运行时零第三方依赖；新增使用标准库 `http.server` / `threading` / `socket` / `webbrowser` / `importlib.resources` / `urllib`（`pyproject.toml` 的 `dependencies = []` 不变）

**存储（Storage）**: 沿用 `~/.daily-recipe-cli/recipes.json` 与 `history.json`（`RECIPE_CLI_DIR` 可覆写）；页面与 CLI 共享同一数据文件，无新持久化格式

**测试（Testing）**: pytest；页面相关测试用 `RECIPE_CLI_DIR` 指向临时目录 + `http.client` 打 API（不启动真实浏览器）；核心逻辑测试沿用

**目标平台（Target Platform）**: macOS 本机（浏览器：Chrome / Safari / Edge 任一）

**项目类型（Project Type）**: cli 工具 + 内嵌单页（package 内嵌 HTML/JS 资源）

**性能目标（Performance Goals）**: 页面加载（`/api/state`）≤ 1s（本地回环，数据量小）；操作响应即时

**约束（Constraints）**: 仅监听 127.0.0.1；无跨域头；服务进程随用随起、用完即停（`/api/bye` + 10 分钟空闲超时 + Ctrl+C）；写操作 `threading.Lock` 串行化 + 原子写入；页面零业务逻辑

**规模/范围（Scale/Scope）**: 单用户本机；四大视图（今日 / 食谱库 / 周计划 / 历史）；候选 1~3、去重窗口 7 天（可配）

## 宪法检查（Constitution Check）

*门槛（GATE）：必须在 Phase 0 调研之前通过。Phase 1 设计后复查。*

| 宪法条款 | 检查结果 | 说明 |
|---|---|---|
| I. 极简优先 | ✅ 通过 | 页面化是访问形态变化，不新增业务功能；YAGNI 边界已在 spec 明确（不加食材匹配/详情/外部 API） |
| II. 数据可读 | ✅ 通过 | 页面读写同一份纯文本 JSON，可手改；契约不变 |
| III. 推荐可复现 | ✅ 通过 | 页面经 API 调用同一核心模块（同种子 + 同状态 → 同结果） |
| IV. 核心逻辑必须有测试 | ✅ 通过 | 页面不重写逻辑；核心逻辑测试沿用，新增 API 层测试 |
| V. 规格先行 | ✅ 通过 | spec → research → data-model → contracts 已按序产出 |
| 技术约束：运行时仅标准库 | ✅ 通过 | `http.server` / `webbrowser` 等均为标准库，`dependencies = []` 不变 |
| 技术约束：完全离线、无网络请求 | ✅ 通过 | 仅监听回环地址，无外部请求 |
| 技术约束：完全离线可用 | ✅ 通过 | `recipe serve` 无需网络 |

**Phase 1 设计后复评**: 无违规——唯一张力点（「本机页面 + 读写本地 JSON + 零常驻」）已由 research.md 决策 1 解决：浏览器 CORS 使 file:// 不可行，`recipe serve` 一次性回环服务是唯一同时满足全部约束的方案；其「临时前台进程」形态与「禁止常驻网络服务」不冲突（随用随起、用完即停）。

## 项目结构（Project Structure）

### 文档（本功能）

```text
specs/002-recipe-web-ui/
├── plan.md              # 本文件（/speckit.plan 命令输出）
├── research.md          # Phase 0 输出（页面承载方案调研）
├── data-model.md        # Phase 1 输出（视图/交互模型）
├── quickstart.md        # Phase 1 输出（端到端验证指南）
├── contracts/
│   └── api.md           # Phase 1 输出（页面 API 契约）
└── tasks.md             # Phase 2 输出（/speckit.tasks 命令 - 不由 /speckit.plan 创建）
```

### 源码（仓库根目录）

```text
src/daily_recipe_cli/
├── cli.py               # 现有：新增 `serve` 子命令入口（薄层，转发到 server.py）
├── server.py            # 新增：HTTP 服务（ThreadingHTTPServer + handler + API 路由 + 生命周期）
├── static/
│   └── index.html       # 新增：内嵌单页（渲染层，零业务逻辑；importlib.resources 读取）
├── storage.py           # 现有：数据加载/校验/原子写入（复用，不改）
├── recipes.py           # 现有：食谱增删查（复用，不改）
├── history.py           # 现有：历史读写、当日已确定判断（复用，不改）
└── recommend.py         # 现有：推荐/周计划/去重（复用，不改）

tests/
├── test_server.py       # 新增：API 层测试（http.client 打真实本地服务 + RECIPE_CLI_DIR 临时目录）
└── （现有测试沿用）
```

**结构决策（Structure Decision）**: 采用单项目结构（方案 1）。`server.py` 独立成模块（CLI 薄层转发），静态页面放 `static/index.html` 由 `importlib.resources` 读取（不引入打包工具）。核心模块（storage/recipes/history/recommend）零改动——这是「复用现有核心逻辑、仅新增交互层」的直接体现。

## 复杂度跟踪（Complexity Tracking）

> **仅当宪法检查存在必须说明的违规时才填写**

无违规，无需复杂度说明。
