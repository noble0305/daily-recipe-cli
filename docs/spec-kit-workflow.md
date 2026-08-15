# Spec Kit 开发工作流团队实践指南（SOP）

> 本文档是团队统一采用 **Spec Kit 开发工作流** 的执行标准。目标是让每个功能从需求到代码都走同一条可追溯、可评审、可复用的流水线，而不是各写各的。
>
> 本文以 `daily-recipe-cli` 项目（`specs/001-daily-recipe-cli/`）作为贯穿全篇的真实案例——它完整走完了一轮工作流，文中所有示例都可直接打开对应文件对照。
>
> 适用角色：所有参与本项目或后续采用本工作流的开发者、评审人、AI 编码助手（ZCode / Copilot 等）。

---

## 1. 为什么用 Spec Kit

### 1.1 痛点

团队项目开发常见的问题：

- **需求口头化**：功能靠聊天和脑补，实现时才发现理解不一致，返工成本高。
- **实现黑盒**：代码合入后没人知道"为什么这么做"，三个月后连原作者都说不清当初的取舍。
- **验收缺失**：没有可执行的验收标准，"做完了"只是"看起来能跑"。
- **AI 协作失控**：AI 助手拿到一句含糊需求就开始写代码，写出来的东西经常跑偏。

### 1.2 Spec Kit 给的答案

Spec Kit 把开发过程拆成一条 **Spec（规格）驱动** 的流水线：**先写规格、再写计划、再拆任务、最后实现**，每个环节都有落盘的产物文档，AI 与人类在同一套产物上协作。

它的核心信条：**需求不确定就不写代码**；**文档是代码的先行产物，而不是事后补写**。

### 1.3 本项目跑通后的实际效果

`daily-recipe-cli` 用一轮完整工作流交付了 6 个命令 + 12 个用户故事 + 全套单元测试，全程 8 次提交，git 历史可完美还原工作流各阶段：

```
ecee0ee docs: init spec-kit project scaffold, constitution v1.0.0 and daily-recipe-cli spec   ← specify 阶段
88316c5 docs: add implementation plan, research, data model, contracts, quickstart            ← plan 阶段
c15e9b2 docs: generate task breakdown for daily-recipe-cli                                    ← tasks 阶段
61e42ca feat: storage layer with atomic JSON writes, validation, and default recipe library   ← implement
b5bc9c4 feat: implement today/week/add/list/remove/history commands with tests                 ← implement
df3857f docs: polish - add README, CHANGELOG, spec FR-013, mark tasks complete                 ← 收尾
eb3e4f8 fix: handle non-interactive week confirm and enrich empty-candidate hints               ← 修复
67e6cbe docs: 添加 AGENTS.md 工作区指南                                                         ← 治理沉淀
```

产出物（都在 `specs/001-daily-recipe-cli/` 下）：`spec.md`（功能规格）、`plan.md`（实现计划）、`research.md`（技术调研）、`data-model.md`（数据模型）、`tasks.md`（任务清单）、`contracts/data-schema.md`（数据契约）、`checklists/requirements.md`（需求核对表）。

---

## 2. 核心概念与产物全景

### 2.1 工作区结构

一个启用 Spec Kit 的仓库包含：

| 路径 | 作用 | 是否提交 |
|---|---|---|
| `.speckit/commands/*.md` | 各工作流命令的**单一事实来源**（定义每个命令的流程） | 是 |
| `.specify/` | 初始化配置（`feature.json`、`workflows/`、`memory/constitution.md`、`templates/`、`scripts/`） | 是（初始化后） |
| `specs/<NNN>-<feature>/` | 每个功能的规格产物目录（本文核心资产） | 是 |

`feature.json` 指向当前功能目录，例如本项目：

```json
{"feature_directory": "specs/001-daily-recipe-cli"}
```

### 2.2 三条规则先记住

1. **命令文件是单一事实来源**：`/speckit-specify` 等入口只做分发，执行时以 `.speckit/commands/speckit.specify.md` 的文件流程为准。命令文件怎么写的，就怎么做，不自行增删步骤。
2. **产物按阶段落盘**：每个命令都会产出/更新一个文档，全部入 git 仓库。
3. **语言与提交约定跟随仓库 AGENTS.md**：本项目要求中文文档与中文提交信息，工作流产物同样遵守。

### 2.3 命令全景

Spec Kit 共 10 个命令，本 SOP 只详讲主链路 6 个（见第 4 节），其余在速查表中说明。

| 命令 | skill 入口 | 作用 | 阶段 |
|---|---|---|---|
| `specify` | `/speckit-specify` | 创建/更新功能规格 | 主链路 |
| `clarify` | `/speckit-clarify` | 澄清需求歧义 | 主链路 |
| `plan` | `/speckit-plan` | 编写实现计划 | 主链路 |
| `tasks` | `/speckit-tasks` | 拆解任务清单 | 主链路 |
| `implement` | `/speckit-implement` | 按任务实现代码 | 主链路 |
| `analyze` | `/speckit-analyze` | 实现后回顾与收尾 | 主链路 |
| `constitution` | `/speckit-constitution` | 项目初始化、写入团队宪法 | 初始化 |
| `converge` | `/speckit-converge` | 多方案收敛到单一决策 | 按需 |
| `checklist` | `/speckit-checklist` | 生成/更新需求核对表 | 按需 |
| `taskstoissues` | `/speckit-taskstoissues` | 任务清单转 GitHub Issues | 按需 |

---

## 3. 环境准备（一次性）

### 3.1 仓库初始化（首次启用）

每个新仓库首次启用 Spec Kit 时运行一次：

```bash
# 若仓库尚未安装 Spec Kit：在仓库根目录初始化
uvx --from speckit-ai-cli specify init --ai generic
```

初始化会生成 `.speckit/commands/` 与 `.specify/`，并写入 `constitution.md`（项目宪法，见 5.1）。随后在根目录写入 `AGENTS.md`（工作区指南，见 5.5），把团队的约定固化下来。

### 3.2 安装 skill 封装（每人一次）

命令以 **skill 形式** 提供给 AI 助手（ZCode 等），需要把封装 skill 安装到个人的 `~/.zcode/skills/` 下：

1. 从仓库/共享位置拷贝封装 skill（`speckit-specify`、`speckit-clarify`、`speckit-plan`、`speckit-tasks`、`speckit-implement`、`speckit-analyze`、`speckit-constitution`、`speckit-converge`、`speckit-checklist`、`speckit-taskstoissues`）到 `~/.zcode/skills/`。
2. 命名规则：**命令文件里的点号换成连字符**（`speckit.specify.md` → `speckit-specify`）。
3. 验证：在仓库内输入 `/speckit-specify` 应能正常触发。

> 封装 skill 只是入口，执行逻辑永远读仓库里的 `.speckit/commands/*.md`，所以封装一旦装好，后续工作流升级只改仓库命令文件即可，无需重装。

### 3.3 目录约定

- 新功能目录：`specs/<NNN>-<feature-slug>/`，编号递增（本项目第一个功能是 `001-daily-recipe-cli`）。
- 每轮工作流开始前确认 `feature.json` 指向当前功能目录。

---

## 4. 主链路详解

以下按一次完整功能开发的顺序展开。每个命令都包含：**何时调用 → 做什么 → 产出什么 → 项目示例**。

### 4.1 `/speckit-specify` — 需求 → 功能规格

**何时调用**：新功能启动时；需求变更时。

**做什么**：根据自然语言描述创建或更新 `spec.md`，把模糊需求转成结构化规格：用户故事（User Story）、优先级、可独立验证的验收场景（Acceptance Scenarios）、独立测试（Independent Test）。

**产出**：`specs/<NNN>-<feature>/spec.md`

**示例**（`specs/001-daily-recipe-cli/spec.md`）：

```markdown
# Feature Specification: daily-recipe-cli
**Feature Branch**: 001-daily-recipe-cli
**Status**: Draft
**Input**: 用户描述：为自己解决「每天带饭不知道做什么」的决策痛点……

### User Story 1 - 前一晚定第二天的饭 (Priority: P1)
用户在晚上运行推荐命令，希望快速决定第二天带去公司吃的菜。
**Independent Test**: 运行一次推荐命令，得到候选清单并选中一道，验证……
**Acceptance Scenarios**:
1. **Given** 食谱库中有 ≥3 道菜且无历史记录，**When** 用户运行今日推荐，
   **Then** 展示 1~3 道候选菜，且说明推荐理由。
2. **Given** 用户已经吃过某道菜，**When** 在最近 7 天内再次推荐，
   **Then** 该菜不会出现在候选清单中。
```

**要点**：

- 验收场景全部用 **Given / When / Then** 句式，这是后面写测试的直接输入。
- 优先级用 P1/P2/P3 标注，P1 是该版本必须做的。
- 需求有歧义时先走 `/speckit-clarify` 再回来补全 spec。

### 4.2 `/speckit-clarify` — 消除歧义

**何时调用**：spec 中的需求存在多解、冲突、或团队对某些点理解不一致时。

**做什么**：围绕歧义点向干系人（产品/用户/团队）提问，把模糊表述收敛成确定结论，回写进 `spec.md`。

**产出**：更新后的 `spec.md`（状态从 Draft 推进）。

**要点**：

- 不要替用户做主——不确定的语义必须问出来。
- 每个澄清结论要落到 spec 的对应验收场景里，避免"问过就忘"。
- 本项目 AGENTS.md 中有个现成例子：`week` 命令的非交互确认（见 6.2 FAQ），说明"交互行为在无人输入时怎么处理"这类边界必须澄清并写进代码行为。

### 4.3 `/speckit-plan` — 规格 → 实现计划

**何时调用**：spec 稳定（至少 P1 故事清晰）后。

**做什么**：基于 spec 编写 `plan.md`，确定技术路线：语言/版本、依赖、存储方案、测试策略、目标平台、项目类型；必要时并行产出 `research.md`（技术调研）与 `data-model.md`（数据模型）。

**产出**：`plan.md`（+ 可选 `research.md`、`data-model.md`、`contracts/`）

**示例**（`plan.md` 关键段）：

```markdown
# Implementation Plan: daily-recipe-cli
**Branch**: 001-daily-recipe-cli | **Spec**: spec.md

## Summary
一个单用户本机命令行工具，解决「每天带饭不知道做什么」的决策痛点。……

## Technical Context
**Language/Version**: Python 3.11+
**Primary Dependencies**: 运行时零第三方依赖（argparse / json / random / pathlib / datetime）
**Storage**: 本地 JSON 文件，数据目录 ~/.daily-recipe-cli/
**Testing**: pytest（核心逻辑单元测试：推荐、轮换去重、数据校验、历史读写）
**Project Type**: cli 工具（Python 包，uv run recipe 调用）
```

**要点**：

- **数据契约先行**：涉及持久化的功能，必须在 plan 阶段就把 JSON schema 与错误语义写清楚（本项目写进 `contracts/data-schema.md`）。契约定了，实现和手改数据的用户都不会踩雷。
- 技术方案要给出取舍理由（为什么标准库而不是第三方库、为什么 JSON 而不是 SQLite），这些理由就是将来评审和排错的地图。
- 计划评审通过前不要进入 tasks 阶段。

### 4.4 `/speckit-tasks` — 计划 → 任务清单

**何时调用**：plan 评审通过后。

**做什么**：把 spec 的用户故事 + plan 的技术方案拆成可独立执行、可独立测试的任务。按用户故事分组，标注每个任务属于哪个故事、能否与其他任务并行（`[P]` 标记）。

**产出**：`tasks.md`

**示例**（`tasks.md` 格式）：

```markdown
## Format: `[ID] [P?] [Story] Description`
- [P] 可并行（不同文件、无依赖）的任务
- [Story] 属于哪个用户故事（US1 / US2 / US3）

[001] [US1] 实现 storage 层：原子 JSON 写入、校验、内置默认食谱库
[002] [US1] 实现 today 命令：候选生成 + 历史记录
[003] [P] [US1] 实现 add / list / remove 食谱命令
[004] [P] [US2] 实现 week 周计划命令
[005] [US1-3] 为全部用户故事编写单元测试
```

**要点**：

- 每个任务必须小到能独立完成并验证（一个任务 = 一个提交）。
- 测试任务不是附加项——本项目宪法要求核心逻辑必须覆盖单元测试，因此每个用户故事都带测试任务。
- 任务完成状态在 implement 过程中逐个勾选，最终汇总到 `checklists/requirements.md` 核对表。

### 4.5 `/speckit-implement` — 任务 → 代码

**何时调用**：tasks 拆解完成，从第一个任务开始。

**做什么**：按 `tasks.md` 逐个实现。每次实现对应一个原子提交，提交信息遵循仓库约定（本项目：中文 + Conventional Commits 前缀）。

**产出**：应用代码 + 测试 + 中文提交历史

**示例**（本项目提交历史中的典型形态）：

```
61e42ca feat: storage layer with atomic JSON writes, validation, and default recipe library
b5bc9c4 feat: implement today/week/add/list/remove/history commands with tests
eb3e4f8 fix: handle non-interactive week confirm and enrich empty-candidate hints
```

**要点**：

- 严格遵守 `tasks.md` 的顺序与范围：不扩大实现范围（YAGNI），不跳过测试任务。
- 每个任务结束跑一遍测试套件（本项目 `uv run pytest`），保证绿再提交。
- 发现任务拆解不合理或需求有遗漏时，不要悄悄绕过去——回到对应的 `specify` / `tasks` 阶段更新产物再继续。
- 数据契约相关的实现（本项目 `storage.py`）必须对照 `contracts/data-schema.md`：非法数据绝不静默容错，必须抛带中文信息的 `DataError`。

### 4.6 `/speckit-analyze` — 实现后回顾与收尾

**何时调用**：所有任务完成后、合入/发布前。

**做什么**：对照 spec 与核对表做整体回顾：需求是否全部满足、测试是否覆盖、文档（README/CHANGELOG）是否需要补齐、有没有实现中偏离 spec 的地方需要回写。

**产出**：`checklists/requirements.md` 勾选完成、spec 状态更新、收尾提交。

**示例**（本项目收尾提交）：

```
df3857f docs: polish - add README, CHANGELOG, spec FR-013, mark tasks complete
```

**要点**：

- 用户可见行为变更必须在 `CHANGELOG.md` 追加中文条目。
- 遗漏的需求（如本项目收尾时补的 FR-013）要回写到 `spec.md`，保证 spec 永远反映最终行为。

---

## 5. 团队协作规约（强制）

以下规约随仓库文件固化，全员（含 AI 助手）必须遵守。

### 5.1 项目宪法（constitution）

初始化时用 `/speckit-constitution` 写入团队/项目宪法（`.specify/memory/constitution.md`），内容包括核心原则、技术约束、开发工作流、治理规则。本项目宪法含 5 条核心原则（极简优先、文档先行、离线可用、测试即契约、渐进收敛等），后续功能开发均受其约束。**宪法修改走评审，不随意改。**

### 5.2 specs 产物入仓并参与评审

- `specs/` 下所有产物文档必须提交到 git，与代码同库、同步演进。
- **spec / plan / tasks 的变更走 PR 评审**，与代码评审同等重要。评审人重点看：验收场景是否可执行、技术取舍是否有依据、任务是否可独立验证。
- 禁止"代码合入后补文档"——文档是前置产物。

### 5.3 提交约定

- 提交信息用中文，保留 Conventional Commits 前缀（`feat:` / `fix:` / `docs:` / `test:` / `refactor:`），标题用中文概括改动。
- 一个任务一个提交，提交信息能对应到 `tasks.md` 的任务 ID。
- 用户可见行为变更同步追加 `CHANGELOG.md` 条目（中文）。

### 5.4 AI 助手接入约定

- AI 助手执行工作流时：**命令文件（`.speckit/commands/*.md`）是单一事实来源**，skill 封装只做入口，不自行增删步骤。
- 用户可见输出、代码注释、文档一律中文（遵循 AGENTS.md）。
- 测试绝不能触碰真实用户数据目录（本项目用 `RECIPE_CLI_DIR` 环境变量指向临时目录）。
- 推荐逻辑要求可复现（固定随机种子），实现时不得引入非确定性。

### 5.5 AGENTS.md 工作区指南

每个采用本工作流的仓库必须有一份 `AGENTS.md`，作为 AI 与开发者共享的工作区说明，内容至少覆盖：项目是什么、目录结构、构建测试命令、数据契约、行为规则、测试约定、语言与提交约定。它是工作流落地的"操作手册"，本文档是"方法论"，两者配合使用。

---

## 6. 踩坑与 FAQ

### 6.1 命令文件与 skill 封装冲突怎么办？

**以命令文件为准**。skill 封装在 frontmatter 里明确写了"若文件流程与本封装冲突，以命令文件为准"，因此升级工作流只需更新 `.speckit/commands/*.md` 并提交，全员自动生效，无需重新分发封装。

### 6.2 非交互场景（CI / 管道）下交互式确认会崩吗？

会，所以必须有兜底。本项目 `week` 命令用 `input()` 读确认，捕获 `EOFError`（非交互时 input 抛异常）视为"否"，而不是崩溃。**凡是涉及交互的行为，spec 里都要写明非交互时的默认行为。**

### 6.3 手改 JSON 数据弄坏了文件怎么办？

不要静默容错。按契约实现：任何命令加载数据时发现非法数据（缺字段、类型错、JSON 损坏）都抛带中文信息的 `DataError`（含出错字段/位置），写入用「先写 `.tmp` 再 `os.replace()`」的原子方式。宁可报错，不可悄悄覆盖用户数据。

### 6.4 功能做完才发现需求理解错了？

这正是流水线的价值所在——**需求在 spec 阶段成本最低**。做法：回到 `/speckit-clarify` 澄清 → 更新 `spec.md` → 更新 `plan.md` / `tasks.md` → 再继续实现。不要用代码补丁绕过文档，否则三个月后没人知道当初为什么这么做。

### 6.5 任务拆得太大 / 太小怎么办？

太大：拆到"一个任务 = 一个可独立验证的提交"。太小：合并同类项。判断标准：任务完成时能不能写出一个干净的中文提交信息、跑一次测试。

### 6.6 不写 spec 直接让 AI 写代码行不行？

不推荐。Spec Kit 的价值正是用文档把"AI 的随机性"锁成"可评审的确定性"。直接写代码时 AI 会自己做一堆隐式假设，而这些假设无处评审。至少走一遍 `/speckit-specify` + `/speckit-tasks`，把验收场景和任务边界定下来，再进 implement。

---

## 7. 快速参考

### 主链路速记

```
新功能 ──specify──▶ spec.md ──clarify──▶ 歧义消除
                              │
                              ▼
              plan ──▶ plan.md (+ research / data-model / contracts)
                              │
                              ▼
             tasks ──▶ tasks.md（按用户故事 + 并行标记）
                              │
                              ▼
          implement ──▶ 代码 + 测试 + 中文提交（一个任务一个提交）
                              │
                              ▼
          analyze ──▶ 核对表勾选 + CHANGELOG + spec 回写
```

### 评审检查单（PR 时逐项打勾）

- [ ] `spec.md` 的验收场景可执行（Given/When/Then 完整）
- [ ] `plan.md` 技术取舍有理由
- [ ] `tasks.md` 任务与 spec 故事一一对应
- [ ] 代码与数据契约（`contracts/`）一致
- [ ] 核心逻辑有单元测试且通过
- [ ] 提交信息中文 + Conventional Commits 前缀
- [ ] 用户可见变更已追加 `CHANGELOG.md`
- [ ] spec / plan / tasks 与最终行为一致

### 相关文件

- 命令定义（单一事实来源）：`.speckit/commands/speckit.*.md`
- 项目宪法：`.specify/memory/constitution.md`
- 案例产物：`specs/001-daily-recipe-cli/`
- 工作区指南：`AGENTS.md`
