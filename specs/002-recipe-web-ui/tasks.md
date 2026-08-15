---

description: "功能实现的任务清单模板"

---

# 任务清单：页面化访问（recipe-web-ui）

**输入（Input）**: 来自 `/specs/002-recipe-web-ui/` 的设计文档

**前置条件（Prerequisites）**: plan.md（必需）、spec.md（用户故事必需）、research.md、data-model.md、contracts/api.md

**测试（Tests）**: 本规格明确要求新增页面相关测试（SC-004：现有 `uv run pytest` 全部通过且新增页面相关测试；宪法 IV 核心逻辑必须有测试），因此每个用户故事包含测试任务。

**组织方式（Organization）**: 任务按用户故事分组，以便每个故事可独立实现与测试。

## 格式：`[ID] [P?] [Story] 描述`

- **[P]**: 可并行（不同文件、无依赖）
- **[Story]**: 该任务属于哪个用户故事（例如 US1、US2、US3）
- 描述中必须包含精确的文件路径

## 路径约定（Path Conventions）

- **单项目**: `src/`、`tests/` 位于仓库根目录
- 本功能路径：`src/daily_recipe_cli/server.py`（新增）、`src/daily_recipe_cli/static/index.html`（新增）、`src/daily_recipe_cli/cli.py`（改）、`tests/test_server.py`（新增）

---

## 阶段 1：搭建（共享基础设施）

**目的**: 测试基础设施与模块骨架——后续所有阶段共用

- [X] T001 创建 `tests/test_server.py` 骨架：`data_dir` fixture（`monkeypatch.setenv("RECIPE_CLI_DIR", str(tmp_path))`，沿用 tests/test_storage.py 模式）+ `server_client` fixture（启动 `serve()` 于随机端口、返回 `http.client` 客户端、teardown 关闭）
- [X] T002 创建 `src/daily_recipe_cli/server.py` 模块骨架（空 handler 类与 serve 函数占位，import 可用）

**检查点**: `uv run pytest tests/test_server.py` 可运行（空测试通过）

---

## 阶段 2：基础（阻塞性前置条件）

**目的**: HTTP 服务核心——生命周期、错误语义、聚合状态。任何用户故事依赖它（research.md 决策 1/3/4）

**⚠️ 关键**: 本阶段未完成前，任何用户故事工作都不能开始

- [X] T003 在 `src/daily_recipe_cli/server.py` 实现服务生命周期：`serve()` 用 `ThreadingHTTPServer` 绑定 `127.0.0.1` + 随机端口（`socket.bind(0)`）、`webbrowser.open()` 打开页面、`/api/bye` 收到后 `server.shutdown()`、10 分钟空闲超时兜底、Ctrl+C 可退出（research.md 决策 3）
- [X] T004 在 `src/daily_recipe_cli/server.py` 实现 API 通用层：JSON 编解码、`DataError` → HTTP 400 + 中文消息（含字段/位置）、写操作 `threading.Lock` 串行化、成功响应 `{ok:true,data:...}`（contracts/api.md 通用约定）
- [X] T005 在 `src/daily_recipe_cli/server.py` 实现 `GET /api/state`：聚合 `storage.load_recipes()` + `storage.load_history()` + `history.decided_for_date(今天)` → TodayState + recipes 列表（contracts/api.md）
- [X] T006 [P] 在 `src/daily_recipe_cli/cli.py` 添加 `serve` 子命令入口（薄层：`add_parser("serve", ...)` 转发到 `server.serve()`，不含业务逻辑）
- [X] T007 在 `tests/test_server.py` 编写基础测试：服务启动/`/api/bye` 退出、`GET /api/state` 返回正确聚合（含今日未确定）、损坏 JSON 时返回 400 中文错误

**检查点**: `uv run pytest` 全绿；`recipe serve` 能启动并打开页面，`/api/state` 返回正确数据

---

## 阶段 3：用户故事 1 - 在页面上完成今日带饭决策（优先级 P1）🎯 MVP

**目标（Goal）**: 打开页面 → 今日推荐 → 确认选择 → 显示已确定（spec US1 全流程）

**独立测试（Independent Test）**: 打开页面 → 展示候选菜 → 点击确认 → 页面显示「今日已确定」并出现在历史中；全程无需输入任何命令（spec US1 Independent Test）

### 用户故事 1 的测试 ⚠️

> **注意：先写这些测试，确保在实现前它们是失败的（FAIL）**

- [X] T008 [P] [US1] 在 `tests/test_server.py` 编写 `POST /api/today` 测试：`recommend`（候选 1~3 道 + 理由）、`confirm`（写历史 source=today、越界序号 400 中文错误）、`force`（已确定时重推覆盖旧记录）

### 用户故事 1 的实现

- [X] T009 [US1] 在 `src/daily_recipe_cli/server.py` 实现 `POST /api/today`：`recommend` 调 `recommend.candidates()`（传 tags/days/count/seed）、`confirm` 调 `history.add(今天, 菜名, "today")`、`force` 覆盖当日旧记录（contracts/api.md）
- [X] T010 [US1] 创建 `src/daily_recipe_cli/static/index.html` 页面骨架：四大视图容器（今日/食谱库/周计划/历史）+ 今日区域（状态展示、今日推荐按钮、候选列表、确认按钮、已确定态）+ `fetch` 调 API（渲染层，零业务逻辑，research.md 决策 4）
- [X] T011 [US1] 在 `src/daily_recipe_cli/server.py` 实现 `GET /`：经 `importlib.resources` 返回 `static/index.html`；页面 `pagehide`/`beforeunload` 时 `sendBeacon` 发 `POST /api/bye`（research.md 决策 3）

**检查点**: 打开页面即可完成「今日推荐 → 确认」全流程（spec SC-001 ≤ 30 秒）；US1 可独立演示

---

## 阶段 4：用户故事 2 - 在页面上管理食谱库（优先级 P1）

**目标（Goal）**: 页面查看/筛选/添加/删除食谱，结果即时反映（spec US2 全流程）

**独立测试（Independent Test）**: 在页面添加一道菜 → 列表立即出现；删除该菜 → 列表消失且历史记录不受影响（spec US2 Independent Test）

### 用户故事 2 的测试 ⚠️

- [X] T012 [P] [US2] 在 `tests/test_server.py` 编写 `POST /api/add` 与 `POST /api/remove` 测试：添加成功、重名 400「已存在」、删除成功且历史不受影响、删除不存在 400 中文错误

### 用户故事 2 的实现

- [X] T013 [US2] 在 `src/daily_recipe_cli/server.py` 实现 `POST /api/add`（调 `recipes.add()`，重名 DataError → 400）与 `POST /api/remove`（调 `recipes.remove()`）（contracts/api.md）
- [X] T014 [US2] 在 `src/daily_recipe_cli/static/index.html` 实现食谱库区域：列表（菜名/食材/标签/做法）、标签筛选（前端渲染）、添加表单、删除按钮+确认（操作后刷新 `GET /api/state`）

**检查点**: 页面食谱库管理全流程可用，与 `recipe list/add/remove` 行为一致（spec SC-002）

---

## 阶段 5：用户故事 3 - 在页面上规划一周菜单（优先级 P2）

**目标（Goal）**: 页面生成并预览 5 个工作日菜单，确认后一次性写入（spec US3 全流程）

**独立测试（Independent Test）**: 点击周计划 → 预览 5 天菜单 → 确认 → 历史中出现 5 条记录且互不重复（spec US3 Independent Test）

### 用户故事 3 的测试 ⚠️

- [X] T015 [P] [US3] 在 `tests/test_server.py` 编写 `POST /api/week` 测试：`preview` 返回 5 天不重复菜单、`confirm` 写入 5 条 source=week、候选不足时 400 且不写入

### 用户故事 3 的实现

- [X] T016 [US3] 在 `src/daily_recipe_cli/server.py` 实现 `POST /api/week`：`preview` 调 `recommend.week_plan()`（传 tags/days/seed）、`confirm` 逐日调 `history.add(日期, 菜名, "week")`（contracts/api.md）
- [X] T017 [US3] 在 `src/daily_recipe_cli/static/index.html` 实现周计划区域：生成预览按钮、5 天菜单展示、确认/取消按钮（确认后刷新状态）

**检查点**: 页面周计划预览与写入全流程可用，行为与 `recipe week` 一致

---

## 阶段 6：用户故事 4 - 在页面上查看历史记录（优先级 P2）

**目标（Goal）**: 页面按日期倒序查看历史，可调时间范围（spec US4 全流程）

**独立测试（Independent Test）**: 打开历史区域 → 按日期倒序展示最近 30 天记录（含来源标注）→ 调整范围后列表相应变化（spec US4 Independent Test）

### 用户故事 4 的测试 ⚠️

- [X] T018 [P] [US4] 在 `tests/test_server.py` 编写 `GET /api/history` 测试：默认 30 天倒序、`days` 参数生效、source 标注正确（today/week）

### 用户故事 4 的实现

- [X] T019 [US4] 在 `src/daily_recipe_cli/server.py` 实现 `GET /api/history?days=N`：历史查询（倒序、默认 30、含来源标注）（contracts/api.md）
- [X] T020 [US4] 在 `src/daily_recipe_cli/static/index.html` 实现历史区域：倒序列表（日期/菜名/来源标签）、时间范围调整控件

**检查点**: 页面历史查看全流程可用，行为与 `recipe history` 一致

---

## 阶段 7：打磨与横切关注点（Polish & Cross-Cutting Concerns）

**目的**: 影响多个用户故事的改进

- [X] T021 运行 `uv run pytest` 全量回归：现有测试 + 新增 test_server.py 全部通过（spec SC-004）
- [X] T022 按 `specs/002-recipe-web-ui/quickstart.md` 逐场景验证：5 个场景（今日推荐 / 食谱库 / 周计划 / 历史 / 数据契约与边界）全部符合预期
- [X] T023 更新 `CHANGELOG.md`：追加页面化访问功能条目（中文，含 `recipe serve` 用法）
- [X] T024 更新 `README.md`：补充 `recipe serve` 命令用法与页面功能说明

---

## 依赖与执行顺序（Dependencies & Execution Order）

### 阶段依赖

- **搭建（阶段 1）**: 无依赖——可立即开始
- **基础（阶段 2）**: 依赖搭建完成——阻塞所有用户故事（服务生命周期与 API 通用层是所有故事的公共底座）
- **用户故事（阶段 3~6）**: 全部依赖基础阶段完成
  - US1（阶段 3）完成后即可独立演示（MVP）
  - US2/3/4 依赖 US1 的页面骨架（T010 的视图容器），可在 US1 后并行或按序推进
- **打磨（阶段 7）**: 依赖所有用户故事完成

### 用户故事依赖

- **用户故事 1（P1）**: 基础完成后即可开始——不依赖其他故事（MVP 核心）
- **用户故事 2（P1）**: 基础完成后 + US1 页面骨架（T010）完成后即可开始
- **用户故事 3（P2）**: 基础完成后 + US1 页面骨架（T010）完成后即可开始——可与 US2 并行
- **用户故事 4（P2）**: 基础完成后 + US1 页面骨架（T010）完成后即可开始——可与 US2/US3 并行

### 每个用户故事内部

- 测试（T008/T012/T015/T018）必须先编写并使其失败（FAIL），再开始实现
- 先 API 实现（server.py），再页面区域（index.html）
- 一个故事完成后再进入下一个优先级

### 并行机会

- T006（cli.py 入口）与 T003~T005（server.py 核心）可并行（不同文件）
- 所有标记 [P] 的测试任务（T008/T012/T015/T018）在基础完成后可并行
- US2/US3/US4 的 API 实现（T013/T016/T019）在 US1 页面骨架完成后可并行（不同端点）
- T023/T024（文档）在实现稳定后可并行

---

## 并行示例：用户故事 1

```bash
# 一起启动用户故事 1 的测试（先失败）：
任务："T008 在 tests/test_server.py 编写 POST /api/today 测试"
任务："T012 在 tests/test_server.py 编写 POST /api/add 与 POST /api/remove 测试"

# 一起启动用户故事 1 的实现：
任务："T009 在 src/daily_recipe_cli/server.py 实现 POST /api/today"
任务："T010 创建 src/daily_recipe_cli/static/index.html 页面骨架与今日区域"
```

---

## 实现策略（Implementation Strategy）

### 先 MVP（仅用户故事 1）

1. 完成阶段 1：搭建（T001~T002）
2. 完成阶段 2：基础（T003~T007，关键——阻塞所有故事）
3. 完成阶段 3：用户故事 1（T008~T011）
4. **停下并验证**: `recipe serve` 打开页面完成今日推荐全流程
5. 就绪则演示（MVP = 页面可完成今日带饭决策）

### 增量交付

1. 完成搭建 + 基础 → 服务骨架可用（`/api/state` 可查）
2. 添加用户故事 1 → 今日推荐全流程 → 演示（MVP！）
3. 添加用户故事 2 → 食谱库管理 → 演示
4. 添加用户故事 3 → 周计划 → 演示
5. 添加用户故事 4 → 历史 → 演示
6. 打磨 → 全量回归 + 文档

### 并行团队策略

多人开发时：

1. 团队共同完成搭建 + 基础（T001~T007 顺序）
2. 基础完成后：
   - 开发者 A：用户故事 1（页面骨架 + 今日）
   - 开发者 B：用户故事 2（食谱库 API + 页面）
   - 开发者 C：用户故事 3（周计划）
3. 各故事独立完成并集成（共用 `index.html` 时注意协调视图容器）

---

## 备注（Notes）

- [P] 任务 = 不同文件、无依赖
- [Story] 标签将任务映射到具体用户故事，便于追溯
- 每个用户故事应可独立完成与测试
- 实现前验证测试是失败的
- 每个任务或逻辑分组完成后提交（中文提交信息 + Conventional Commits 前缀）
- 可在任意检查点停下，独立验证故事
- 避免：含糊任务、同文件冲突、破坏独立性的跨故事依赖
- 核心模块（storage.py / recipes.py / history.py / recommend.py）**零改动**——页面只经 server.py 调用，违反此约定需先更新 spec/plan