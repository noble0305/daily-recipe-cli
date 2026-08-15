---

description: "功能实现的任务清单模板"

---

# 任务清单：购物清单生成（Tasks: shopping-list）

**输入（Input）**: 来自 `/specs/003-shopping-list/` 的设计文档

**前置条件（Prerequisites）**: plan.md（必需）、spec.md（用户故事必需）、data-model.md、contracts/api.md

**测试（Tests）**: 聚合逻辑是核心逻辑，必须覆盖单元测试（宪法原则 IV）；CLI 与 API 做薄集成测试。

**组织方式（Organization）**: 任务按用户故事分组，以便每个故事可独立实现与测试。

## 格式：`[ID] [P?] [Story] 描述`

- **[P]**: 可并行（不同文件、无依赖）
- **[Story]**: 该任务属于哪个用户故事（例如 US1、US2、US3）
- 描述中必须包含精确的文件路径

## 路径约定（Path Conventions）

- **单项目**: `src/`、`tests/` 位于仓库根目录

---

## 阶段 1：搭建（共享基础设施）

**目的**: 本功能无新建文件结构的搭建——购物清单为纯计算模块，融入既有单项目布局。

- [x] T001 [P] 在 `specs/003-shopping-list/` 完成规格文档（spec.md / plan.md / data-model.md / contracts/api.md）
- [x] T002 [P] 创建规格质量清单 `specs/003-shopping-list/checklists/requirements.md` 并校验通过

**检查点**: 规格就绪，可实现

---

## 阶段 2：基础（阻塞性前置条件）

**目的**: 核心聚合模块，任何用户故事（CLI / 页面）都依赖它

- [x] T003 在 `src/daily_recipe_cli/shopping.py` 创建购物清单聚合模块（纯计算、零 I/O）：
  - `build_list(recipes, history, today, days=7, merge=True) -> dict`
  - 窗口过滤（`[today, today+days-1]` 闭区间）、食材去重合并、来源标注、按食材名排序
  - 菜名不在食谱库或 `ingredients` 缺失时跳过并记入 `skippedRecipes`（不中断整体）
- [x] T004 在 `tests/test_shopping.py` 编写聚合逻辑单元测试（先写先红）：
  - 窗口过滤边界（今日、窗口末日、窗口外、历史含未来日期）
  - 跨菜去重合并与来源标注（`番茄` 来自两道菜只出现一次）
  - `merge=False` 时同一食材按来源分别列出
  - 排序稳定性（同食材多来源时的顺序）
  - 跳过逻辑（菜不在库 / `ingredients` 非法 / 空窗口 `empty=true`）
  - 确定性（同输入两次调用结果一致）

**检查点**: 聚合模块可独立验证，CLI 与页面均可转调

---

## 阶段 3：用户故事 1 - CLI 一键生成购物清单（优先级 P1）🎯 MVP

**目标（Goal）**: `recipe shopping-list` 命令可用，默认聚合未来 7 天，去重排序并标注来源。

**独立测试（Independent Test）**: 预先写入今日与未来几天历史（today/week），运行 `recipe shopping-list`，验证输出食材集合等于各菜食材去重并集且每项带来源。

### 用户故事 1 的实现

- [x] T005 [US1] 在 `src/daily_recipe_cli/cli.py` 注册 `shopping-list` 子命令：
  - `--days N`（默认 7）、`--today`（等价 `--days 1`）、`--no-merge`（关闭合并）
  - `--days` 非正整数时报中文 `DataError`
  - 通过 `_HANDLERS` 分发到新处理函数（薄层，不写业务逻辑）
- [x] T006 [US1] 在 `src/daily_recipe_cli/cli.py` 实现 `_cmd_shopping_list` 处理函数：
  - 装载数据 → 调 `shopping.build_list` → 中文输出（含空态提示与 `today`/`week` 指引、跳过提示）
  - 空态退出码 0（规格 FR-007）
- [x] T007 [P] [US1] 在 `tests/test_cli_shopping.py` 编写命令集成测试：
  - 正常输出（去重排序、来源标注、空态提示、`--days`/`--today`/`--no-merge` 各自行为）
  - `--days 0` 报中文错误、退出码 1
  - 用 `data_dir` fixture 隔离真实数据目录

**检查点**: 用户故事 1 完成——CLI 侧 MVP 可用，可独立测试

---

## 阶段 4：用户故事 2 - 页面化购物清单（优先级 P2）

**目标（Goal）**: `recipe serve` 页面新增「购物清单」区域，与 CLI 输出一致。

**独立测试（Independent Test）**: 启动 `recipe serve`，页面购物清单区域展示与 `recipe shopping-list` 一致的结果；命令行修改数据后刷新页面立即更新。

### 用户故事 2 的实现

- [x] T008 [P] [US2] 在 `src/daily_recipe_cli/server.py` 新增 `GET /api/shopping-list` 端点：
  - 解析 `days` / `merge` 查询参数（带默认值与校验，非法值抛中文 `DataError`）
  - 转调 `shopping.build_list`，只读，无写锁
  - 在 `do_GET` 路由中加入该路径
- [x] T009 [P] [US2] 在 `tests/test_server.py` 扩展购物清单端点测试：
  - 返回结构（`items` / `skippedRecipes` / `empty`）、排序、去重、`merge=false`、非法 `days` 报 400
- [x] T010 [US2] 在 `src/daily_recipe_cli/static/index.html` 新增「购物清单」区域：
  - 加载后 `fetch("/api/shopping-list")` 渲染（食材 + 来源标注），含空态与跳过提示
  - 提供「仅今日」切换（`days=1`）与「合并/不合并」切换（`merge`）

**检查点**: 用户故事 2 完成——页面购物清单可用，与 CLI 输出一致

---

## 阶段 5：用户故事 3 - 精确控制清单范围（优先级 P3）

**目标（Goal）**: 高级参数（`--days` / `--no-merge` / 页面切换）完整可用，适配不同采购节奏。

**独立测试（Independent Test）**: 带 `--days` / `--no-merge` 运行命令，验证范围与合并行为正确。

### 用户故事 3 的实现

- [x] T011 [P] [US3] 在 `tests/test_shopping.py` 补齐边界用例：
  - `--days` 跨周、`--no-merge` 多来源并列、空窗口、单菜窗口
- [x] T012 [US3] 在 `README.md` 新增 `recipe shopping-list` 用法说明（含参数示例、与页面入口的对应关系）
- [x] T013 [P] [US3] 在 `CHANGELOG.md` 追加本功能变更条目（用户可见行为变更需记录）

**检查点**: 全部用户故事完成，功能完整可用

---

## 阶段 6：打磨与横切关注点（Polish & Cross-Cutting Concerns）

**目的**: 收尾验证

- [x] T014 运行 `uv run pytest` 全量测试，确认无回归
- [x] T015 按 `specs/003-shopping-list/quickstart.md`（实现阶段生成的快速上手）手工验证 CLI 与页面两条路径

---

## 依赖与执行顺序（Dependencies & Execution Order）

### 阶段依赖

- **搭建（阶段 1）**: 无依赖——已完成
- **基础（阶段 2）**: 依赖搭建完成——阻塞所有用户故事
- **用户故事（阶段 3+）**: 全部依赖基础阶段完成
  - US1（P1）→ US2（P2）→ US3（P3）按优先级顺序推进
- **打磨（最后阶段）**: 依赖所有目标用户故事完成

### 用户故事依赖

- **用户故事 1（P1）**: 基础（阶段 2）完成后即可开始——不依赖其他故事
- **用户故事 2（P2）**: 依赖基础 + US1 的 `shopping.py`（T003）——但 API/页面可基于同一聚合函数独立开发
- **用户故事 3（P3）**: 依赖 US1/US2 的参数链路——补充测试与文档

### 每个用户故事内部

- 先核心（`shopping.py`）再薄层（CLI/API）
- 测试先写并使其失败（FAIL），再实现（GREEN）
- 一个故事完成后再进入下一个优先级

### 并行机会

- T004（聚合测试）与 T003（聚合实现）TDD 结对，可同步推进
- T005/T007（CLI）与 T008/T009（API）在 `shopping.py` 就绪后可并行（不同文件）
- T008 与 T009（server 端点 + 测试）可并行

---

## 实现策略（Implementation Strategy）

### 先 MVP（仅用户故事 1）

1. 完成阶段 2：`shopping.py` 聚合模块（TDD）
2. 完成阶段 3：CLI 命令 + 测试
3. **停下并验证**: `uv run pytest` + 手工运行 `recipe shopping-list`
4. 就绪则交付/演示

### 增量交付

1. 阶段 2 基础 → 聚合模块可用
2. 添加用户故事 1 → CLI MVP → 独立测试 → 交付/演示
3. 添加用户故事 2 → 页面入口 → 独立测试 → 交付/演示
4. 添加用户故事 3 → 高级参数打磨 → 文档 → 收尾

---

## 备注（Notes）

- 本功能纯只读（无数据写入），不触碰 `storage.save_json` 与写锁。
- 聚合逻辑严格遵循 `spec.md` 边界情况：单菜跳过不中断、食材精确匹配不做同义归一、空窗口友好空态。
- 页面与 CLI 共用 `shopping.build_list`，保证输出一致（spec SC-004）。
- 用户可见输出、注释、提交信息一律中文（AGENTS.md 约定）。
- [P] 任务 = 不同文件、无依赖；每个任务或逻辑分组完成后提交。
