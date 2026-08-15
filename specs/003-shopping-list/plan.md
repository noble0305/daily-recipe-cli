# 实现计划：购物清单生成（Implementation Plan: shopping-list）

**分支（Branch）**: `003-shopping-list` | **日期（Date）**: 2026-08-15 | **规格（Spec）**: [spec.md](./spec.md)

**输入（Input）**: 来自 `/specs/003-shopping-list/spec.md` 的功能规格

**说明（Note）**: 本模板由 `/speckit.plan` 命令填写；其定义描述了执行工作流。

## 摘要（Summary）

为 daily-recipe-cli 新增「购物清单生成」能力：用户基于已确定的带饭安排（今日 `today` 记录 + 未来 `week` 计划），运行 `recipe shopping-list` 聚合指定时间窗口内所有菜品的食材，去重合并、按名称排序，并标注每种食材的来源菜。CLI 与 `recipe serve` 页面双入口，页面与 CLI 共享同一份数据、输出完全一致。纯计算视图，不引入新的持久化数据文件。

## 技术背景（Technical Context）

**语言/版本（Language/Version）**: Python 3.11+（与既有代码一致，`from __future__ import annotations`）

**主要依赖（Primary Dependencies）**: 运行时零第三方依赖（复用标准库 argparse / datetime / json）；开发期仅 pytest

**存储（Storage）**: 复用现有 `recipes.json` 与 `history.json`（`~/.daily-recipe-cli/`，可用 `RECIPE_CLI_DIR` 覆写）。**不引入新数据文件**——购物清单是纯计算视图，每次命令/请求时实时聚合。

**测试（Testing）**: pytest。核心聚合逻辑（时间窗口过滤、食材去重合并、来源标注、排序）必须有单元测试；CLI 与 API 层做薄集成测试。

**目标平台（Target Platform）**: macOS / Linux / Windows 命令行（跨平台，纯标准库）；`recipe serve` 本地回环 HTTP 服务。

**项目类型（Project Type）**: cli 工具（Python 包）+ 一次性本地 web 服务

**性能目标（Performance Goals）**: 命令秒级返回（本地小文件读写 + 内存聚合）；未来 7 天窗口内菜品数十道级，纯内存操作无性能压力。

**约束（Constraints）**: 完全离线；运行时无第三方依赖；输出与错误提示为中文；页面与 CLI 行为一致；遵守数据契约（菜名快照、非法数据抛 `DataError` 不静默容错）。

**规模/范围（Scale/Scope）**: 单用户；窗口默认 7 天；聚合的菜数量级为数十道（每道 ≤ 数十个食材），纯内存可处理。

## 宪法检查（Constitution Check）

*门槛（GATE）：必须在 Phase 0 调研之前通过。Phase 1 设计后复查。*

| 原则 | 符合性 | 说明 |
|------|--------|------|
| I. 极简优先 | ✅ | 购物清单是对「已确定带饭安排」的纯计算聚合，无新增持久化数据、无外部服务、无食材语义归一；直接服务核心痛点「知道做什么但不知道买什么」 |
| II. 数据可读 | ✅ | 复用 `recipes.json` / `history.json`，不引入新文件；食材以 `ingredients` 原始字符串为据，不做语义改写 |
| III. 推荐可复现 | ✅ | 聚合是确定性计算（无随机源）；同数据状态必然产出同清单，天然可测试 |
| IV. 核心逻辑必须有测试 | ✅ | 聚合逻辑（窗口过滤 / 去重合并 / 来源标注 / 排序）为核心逻辑，plan 中明确单元测试覆盖；CLI/API 薄层做集成测试 |
| V. 规格先行 | ✅ | 本流程即规格先行；规格见 `spec.md`，本 plan 不偏离规格 |
| 技术约束（3.11+/uv/标准库/离线） | ✅ | 运行时仅标准库，uv 管理，完全离线 |

**无违规项**，无需复杂度豁免。

## 项目结构（Project Structure）

### 文档（本功能）

```text
specs/003-shopping-list/
├── plan.md              # 本文件（/speckit.plan 命令输出）
├── research.md          # Phase 0 输出（/speckit.plan 命令）
├── data-model.md        # Phase 1 输出（/speckit.plan 命令）
├── quickstart.md        # Phase 1 输出（/speckit.plan 命令）
├── contracts/           # Phase 1 输出（/speckit.plan 命令）
│   └── api.md           # 购物清单 API 契约（GET /api/shopping-list）
└── tasks.md             # Phase 2 输出（/speckit.tasks 命令 - 不由 /speckit.plan 创建）
```

### 源码（仓库根目录）

```text
# 方案 1：单项目（默认，与既有 001/002 一致）
src/daily_recipe_cli/
├── cli.py               # 新增 shopping-list 子命令解析与分发（薄层）
├── shopping.py          # 【新增】核心聚合逻辑：时间窗口过滤、食材去重合并、来源标注、排序
├── server.py            # 新增 GET /api/shopping-list 端点（薄层转调 shopping.py）
├── recommend.py         # 不变（可能复用 _next_weekday 等工具函数）
└── static/index.html    # 新增「购物清单」页面区域与 fetch 调用

tests/
├── test_shopping.py     # 【新增】聚合逻辑单元测试（核心）
├── test_cli_shopping.py # 【新增】shopping-list 命令集成测试
├── test_server.py       # 扩展：GET /api/shopping-list 端点测试
└── test_smoke.py        # 不变
```

**结构决策（Structure Decision）**: 与既有代码一致的单项目布局。核心逻辑放入独立模块 `shopping.py`（纯计算、零 I/O，便于单元测试），CLI 与 server 仅做参数解析与数据装载的薄层转调，保证「页面与 CLI 行为一致」（spec SC-004）。所有数据装载经 `storage.load_recipes()` / `storage.load_history()`，非法数据统一以 `DataError` 暴露。

## 复杂度跟踪（Complexity Tracking）

> 无宪法违规项，本表留空。

| 违规项 | 为何需要 | 拒绝更简方案的原因 |
|--------|----------|-------------------|
| （无） | — | — |
