---

description: "Task list template for feature implementation"

---

# Tasks: daily-recipe-cli

**Input**: Design documents from `/specs/001-daily-recipe-cli/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: 本规格的核心逻辑（推荐、去重、校验、历史）必须覆盖单元测试（constitution 原则 IV），因此每个用户故事含测试任务。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 项目初始化与基础结构

- [x] T001 Create uv 项目骨架：`pyproject.toml`（Python 3.11+，`[project.scripts] recipe = "daily_recipe_cli.cli:main"`），运行 `uv init` + `uv sync`
- [x] T002 [P] Add pytest 开发依赖（`uv add --dev pytest`），创建 `tests/` 目录与最小冒烟测试
- [x] T003 [P] Create 包骨架 `src/daily_recipe_cli/__init__.py`（版本号）、`__main__.py`（`python -m` 入口），根目录 `CHANGELOG.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 存储与校验基础设施，任何用户故事都依赖

**⚠️ CRITICAL**: 本阶段完成前不得开始任何用户故事

- [x] T004 [P] [FND] Implement `src/daily_recipe_cli/storage.py`：数据目录解析（`RECIPE_CLI_DIR` 环境变量覆写，默认 `~/.daily-recipe-cli/`）、`recipes.json`/`history.json` 加载与原子写入（tmp + `os.replace`）
- [x] T005 [P] [FND] Implement `src/daily_recipe_cli/storage.py` 数据校验函数 `validate_recipe` / `validate_history`，按 `contracts/data-schema.md` 规则抛中文错误（含字段定位）
- [x] T006 [P] [FND] Create 初始食谱库 `src/daily_recipe_cli/data/default_recipes.json`（12~15 道「带饭友好」菜：菜名/主要食材/标签[荤素·快慢]/一句话做法）
- [x] T007 [FND] Implement 首次运行初始化：`recipes.json` 不存在时从包内 `default_recipes.json` 拷贝；`history.json` 不存在时创建空数组
- [x] T008 [FND] Write `tests/test_storage.py`：读写、原子性（写入失败不留半截文件）、非法数据中文报错、重名检测

**Checkpoint**: 数据层就绪，用户故事可开始

---

## Phase 3: User Story 1 - 前一晚定第二天的饭 (Priority: P1) 🎯 MVP

**Goal**: `recipe today` 推荐 1~3 道候选（避开最近 7 天已选），确认后写入历史

**Independent Test**: 运行 `recipe today` 得到候选 → 确认选中 → 再次运行不再推荐该菜

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T009 [P] [US1] Write `tests/test_recommend.py`：候选生成数量（1~3）、去重窗口（7 天不重复）、种子可复现（同 seed 同结果）、窗口放宽（不足时依次放宽并提示）
- [x] T010 [P] [US1] Write `tests/test_history.py`：历史写入/读取、当日已确定判断（FR-012）、`--force` 覆盖当天

### Implementation for User Story 1

- [x] T011 [P] [US1] Implement `src/daily_recipe_cli/history.py`：历史记录读写、按日期判断「今日已确定」、写入时菜名快照
- [x] T012 [P] [US1] Implement `src/daily_recipe_cli/recommend.py`：候选生成（标签过滤 + 去重窗口排除 + 日期种子 `random.Random` 打乱取前 N）
- [x] T013 [US1] Implement `src/daily_recipe_cli/cli.py` 的 `recipe today` 子命令（argparse）：展示候选、`today <序号>` 确认选择、`--force`/`--days`/`--seed`/`--tags` 参数、候选不足提示
- [x] T014 [US1] Wire `__main__.py` + `cli.main()`，保证 `uv run recipe today` 可端到端运行

**Checkpoint**: US1 完整可用（MVP 达成）

---

## Phase 4: User Story 2 - 周末批量规划一周 (Priority: P2)

**Goal**: `recipe week` 一次输出未来 5 个工作日的菜单，确认后批量写入历史

**Independent Test**: 运行 `recipe week` 得到 5 天菜单，天与天不重复、且不与最近 7 天已选重复

### Tests for User Story 2 ⚠️

- [x] T015 [P] [US2] Write `tests/test_recommend.py` 周规划用例：5 个工作日（周一至周五）、批内去重、与历史去重、天数不足时提示

### Implementation for User Story 2

- [x] T016 [US2] Implement `recommend.py` 周规划逻辑：从下一个工作周起算 5 天，批内已选集合去重（research.md 决策 4）
- [x] T017 [US2] Implement `cli.py` 的 `recipe week` 子命令：预览 5 天菜单、确认后一次性写入历史（`source="week"`）

**Checkpoint**: US1 + US2 均独立可用

---

## Phase 5: User Story 3 - 食谱库自增与管理 (Priority: P2)

**Goal**: `recipe add` / `recipe list` / `recipe remove` + 内置初始库开箱即用

**Independent Test**: `recipe add` 新菜后 `recipe list` 可见；`recipe remove` 后消失且历史不受影响

### Tests for User Story 3 ⚠️

- [x] T018 [P] [US3] Write `tests/test_recipes.py`：添加（含重名提示 FR-004）、列表（含标签过滤）、删除（历史快照不受影响）

### Implementation for User Story 3

- [x] T019 [P] [US3] Implement `src/daily_recipe_cli/recipes.py`：add/list/remove/按标签过滤/查重（大小写不敏感）
- [x] T020 [P] [US3] Implement `cli.py` 的 `recipe add` / `recipe list` / `recipe remove` 子命令（含参数校验与中文提示）
- [x] T021 [US3] Implement `cli.py` 的 `recipe history [--days N]` 子命令（research.md 决策 7，FR-002 可见性补充）

**Checkpoint**: 食谱库管理闭环可用

---

## Phase 6: User Story 4 - 偏好过滤 (Priority: P3)

**Goal**: 按标签过滤推荐（荤/素、快手/费时），条件可叠加

**Independent Test**: `recipe today --tags 素 快手` 的候选全部同时符合两个标签

### Tests for User Story 4 ⚠️

- [x] T022 [P] [US4] Write `tests/test_recommend.py` 标签过滤用例：单标签、多标签叠加、过滤后不足提示

### Implementation for User Story 4

- [x] T023 [US4] Implement 标签过滤在 `recommend.py` 候选生成的完整接入（过滤条件可叠加，全不满足时提示当前条件下可选菜不足）

**Checkpoint**: 全部用户故事独立可用

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: 收尾与质量

- [x] T024 Run `quickstart.md` 全部命令验证（真实 `uv run` 端到端），修正文档与实现不一致
- [x] T025 [P] Update `specs/001-daily-recipe-cli/spec.md`：补充 FR（history 命令）并更新 checklists/requirements.md
- [x] T026 Write 根目录 `README.md`（安装、常用命令、数据说明）与补全 `CHANGELOG.md`
- [x] T027 Run `uv run pytest` 全量通过；`uv run recipe today` 冒烟；提交最终 commit 并推送 GitHub

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无依赖
- **Foundational (Phase 2)**: 依赖 Setup，阻塞所有用户故事
- **User Stories (Phase 3+)**: 依赖 Foundational
- **Polish (Phase 7)**: 依赖所有用户故事完成

### User Story Dependencies

- **US1 (P1)**: 仅依赖 Foundational
- **US2 (P2)**: 依赖 US1 的推荐/历史基础，但独立可测
- **US3 (P2)**: 依赖 Foundational；与 US1/US2 并行不冲突（不同文件）
- **US4 (P3)**: 依赖 US1 的推荐链路

### Within Each User Story

- Tests 先写并 FAIL，再实现
- storage → history/recommend/recipes → cli

### Parallel Opportunities

- Phase 1 的 T002/T003 可并行
- Phase 2 的 T004/T005/T006 可并行
- US1 的 T009/T010、T011/T012 可并行
- US3 的 T019/T020 可并行

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "T009 tests/test_recommend.py 候选生成与去重用例"
Task: "T010 tests/test_history.py 历史与今日已确定用例"

# Launch all implementation for User Story 1 together:
Task: "T011 src/daily_recipe_cli/history.py"
Task: "T012 src/daily_recipe_cli/recommend.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup
2. Phase 2: Foundational（阻塞）
3. Phase 3: US1 → **STOP and VALIDATE**：`recipe today` 端到端可用
4. 后续增量交付 US2/US3/US4

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 → MVP（今日推荐闭环）
3. US2 → 周规划
4. US3 → 食谱库管理
5. US4 → 偏好过滤

---

## Notes

- [P] tasks = different files, no dependencies
- 每个逻辑组完成后提交（conventional commits）
- 验证测试先失败后通过（red-green）
- 结束前验证 quickstart.md 可完整走通

---

## Phase 8: Convergence

**Purpose**: `/speckit.converge` 核查发现的差距，由 `/speckit.implement` 完成

- [x] T028 修复 `recipe week` 在非交互环境（stdin 关闭）下确认输入抛 EOFError 崩溃，捕获 EOFError 视为取消，per FR-011（partial，HIGH，证据 src/daily_recipe_cli/cli.py:120）
- [x] T029 增强候选为空时的提示：区分「食谱库为空 / 过滤条件下无可用 / 近期无新菜」，并给出全库数量与调整建议，per US1/AC4 与 US4/AC3（partial，MEDIUM，证据 src/daily_recipe_cli/cli.py _cmd_today）
