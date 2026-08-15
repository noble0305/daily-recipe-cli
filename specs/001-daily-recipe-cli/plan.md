# Implementation Plan: daily-recipe-cli

**Branch**: `001-daily-recipe-cli` | **Date**: 2026-08-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-daily-recipe-cli/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

一个单用户本机命令行工具，解决「每天带饭不知道做什么」的决策痛点。用户运行 `recipe today` 得到 1~3 道候选菜（避开最近 7 天已选），选中后写入历史；`recipe week` 一次生成未来 5 个工作日的菜单。食谱库以 JSON 纯文本存储、可手改、可 `recipe add` 自增，内置 12~15 道「带饭友好」初始食谱。技术路线：Python 3.11+ + uv，运行时仅标准库，完全离线。详见 [research.md](./research.md)。

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: 运行时零第三方依赖（argparse / json / random / pathlib / datetime 标准库）；开发期仅 pytest

**Storage**: 本地 JSON 文件，数据目录 `~/.daily-recipe-cli/`，含 `recipes.json`（用户库）与 `history.json`（历史记录）；包内捆绑 `default_recipes.json` 作为首次运行的初始库

**Testing**: pytest（核心逻辑单元测试：推荐、轮换去重、数据校验、历史读写）

**Target Platform**: macOS 命令行（本机，跨平台可移植）

**Project Type**: cli 工具（Python 包，`uv run recipe` 调用）

**Performance Goals**: 命令秒级返回（本地文件读写，无网络）

**Constraints**: 完全离线；运行时无第三方依赖；输出与错误提示为中文；食谱库数据可手改

**Scale/Scope**: 单用户；食谱库预期数十~上百条；历史记录按天一条

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原则 | 符合性 | 说明 |
|------|--------|------|
| I. 极简优先 | ✅ | 仅 V1 范围（今日推荐/周规划/增删查/偏好过滤），无食材匹配、无外部服务 |
| II. 数据可读 | ✅ | recipes.json 纯文本可手改；`recipe add` 仅便捷入口；数据仅 菜名/食材/标签/一句话做法 |
| III. 推荐可复现 | ✅ | `--seed` 显式参数 + 默认按日期种子，同种子同状态产出同结果；去重窗口 7 天有明确规则 |
| IV. 核心逻辑必须有测试 | ✅ | 推荐、去重、校验、历史读写均为核心逻辑，plan 中明确测试覆盖 |
| V. 规格先行 | ✅ | 本流程即规格先行；后续变更先改 spec 再改代码 |
| 技术约束（3.11+/uv/标准库/离线） | ✅ | 运行时仅标准库，uv 管理，完全离线 |

**无违规项**，无需复杂度豁免。

## Project Structure

### Documentation (this feature)

```text
specs/001-daily-recipe-cli/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/
│   └── data-schema.md   # Phase 1 output: JSON 数据契约说明
├── checklists/
│   └── requirements.md  # 规格质量校验
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/daily_recipe_cli/
├── __init__.py          # 包版本号
├── __main__.py          # python -m daily_recipe_cli 入口
├── cli.py               # argparse 子命令注册与分发（薄层）
├── storage.py           # 数据目录解析、JSON 读写、合法性校验、错误抛出
├── recipes.py           # 食谱库操作：add/list/remove/按标签过滤/查重
├── recommend.py         # 核心推荐逻辑：候选生成、去重窗口、周规划
└── data/
    └── default_recipes.json   # 初始食谱库（12~15 道带饭友好食谱）

tests/
├── test_storage.py      # 数据读写与非法数据处理（FR-011）
├── test_recipes.py      # 增删查与重名处理（FR-004/005/006）
├── test_recommend.py    # 推荐、去重、种子可复现、周规划（FR-001/003/008/009）
└── test_history.py      # 历史写入与快照（FR-002/010）

pyproject.toml           # uv 项目定义，[project.scripts] recipe = daily_recipe_cli.cli:main
CHANGELOG.md             # 变更日志（spec-kit 工作流补充，随规格同步）
```

**Structure Decision**: 采用单项目结构（Option 1），核心逻辑与 CLI 薄层分离：`cli.py` 只做参数解析与分发，业务逻辑在 `recommend.py` / `recipes.py` / `storage.py`，保证核心逻辑可独立单元测试（对应原则 IV）。包内 `data/default_recipes.json` 捆绑初始库，首次运行时拷贝到用户数据目录（`~/.daily-recipe-cli/recipes.json`），此后用户数据与包数据分离。

## Complexity Tracking

无违规项，无需复杂度豁免表。
