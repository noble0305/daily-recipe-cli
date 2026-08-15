<!-- Sync Impact Report:
- Version change: (none) → 1.0.0
- Initial ratification: all sections new
- Modified principles: n/a
- Added sections: Core Principles (I-V), 技术约束, 开发工作流, Governance
- Removed sections: n/a
- Deferred TODOs: none
-->

# Daily Recipe CLI Constitution

## Core Principles

### I. 极简优先
每个命令只解决「今天/本周带什么饭」这一个问题。V1 只包含：今日推荐、周批量规划、食谱增删查、偏好设置。不引入食材匹配、菜谱详情展示、外部 API 等 V1 之外的功能（YAGNI）。新增功能前必须论证与核心目标的直接关联。

### II. 数据可读
食谱库 `recipes.json` 是纯文本数据，任何时刻都允许直接手改；`recipe add` 只是便捷入口而非唯一途径。数据结构保持轻量：菜名、主要食材、标签、一句话做法，不存冗长的做法步骤。

### III. 推荐可复现
同一随机种子与同一状态（食谱库 + 历史记录）必须产出同一推荐结果，保证可测试、可解释。推荐逻辑默认避开最近已推荐的菜，确保轮换不腻；该行为必须有明确规则而非玄学随机。

### IV. 核心逻辑必须有测试
推荐算法、轮换去重、数据校验、历史记录读写是核心逻辑，必须覆盖单元测试。CLI 参数解析等薄层不强制测试，但不得因加参数破坏核心逻辑的测试。

### V. 规格先行
遵循 spec-kit 的 Spec-Driven Development 流程：`specs/` 下的规格说明是唯一事实源，代码实现必须与规格一致。任何功能变更必须先更新规格，再修改代码。

## 技术约束

- Python 3.11+；用 `uv` 管理项目与虚拟环境；
- 运行时仅使用标准库（argparse / json / random / pathlib 等），不引入第三方运行时依赖；
- 工具完全离线可用，无网络请求；
- 推荐结果与数据文件路径支持 `--seed` 等显式参数覆写，便于测试与复现。

## 开发工作流

- 功能变更遵循 spec-kit 流程：`specify → plan → tasks → implement → converge`；
- 每次变更同步更新 `specs/` 对应文档与 `CHANGELOG.md`；
- 提交信息遵循 Conventional Commits（`feat:` `fix:` `docs:` `chore:` 等）。

## Governance

本文档为本项目最高规则；与 `specs/` 中任何文档冲突时，以本文档为准。修订本文档必须：记录版本号变更（MAJOR 破坏性变更 / MINOR 新增原则 / PATCH 措辞澄清）、更新 Last Amended 日期，并在文件顶部维护 Sync Impact Report。

**Version**: 1.0.0 | **Ratified**: 2026-08-15 | **Last Amended**: 2026-08-15
