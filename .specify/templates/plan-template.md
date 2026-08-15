# 实现计划：<功能名>（Implementation Plan: [FEATURE]）

**分支（Branch）**: `<###-feature-name>` | **日期（Date）**: [DATE] | **规格（Spec）**: [link]

**输入（Input）**: 来自 `/specs/[###-feature-name]/spec.md` 的功能规格

**说明（Note）**: 本模板由 `/speckit.plan` 命令填写；其定义描述了执行工作流。

## 摘要（Summary）

[从功能规格提取：主要需求 + 调研得出的技术路线]

## 技术背景（Technical Context）

<!--
  必做：将本节内容替换为项目的技术细节。
  此处结构仅供参考，用于引导迭代过程。
-->

**语言/版本（Language/Version）**: [例如：Python 3.11、Swift 5.9、Rust 1.75 或 NEEDS CLARIFICATION]

**主要依赖（Primary Dependencies）**: [例如：FastAPI、UIKit、LLVM 或 NEEDS CLARIFICATION]

**存储（Storage）**: [如适用，例如：PostgreSQL、CoreData、文件 或 N/A]

**测试（Testing）**: [例如：pytest、XCTest、cargo test 或 NEEDS CLARIFICATION]

**目标平台（Target Platform）**: [例如：Linux 服务器、iOS 15+、WASM 或 NEEDS CLARIFICATION]

**项目类型（Project Type）**: [例如：library/cli/web-service/mobile-app/compiler/desktop-app 或 NEEDS CLARIFICATION]

**性能目标（Performance Goals）**: [领域相关，例如：1000 req/s、10k lines/sec、60 fps 或 NEEDS CLARIFICATION]

**约束（Constraints）**: [领域相关，例如：<200ms p95、<100MB 内存、可离线运行 或 NEEDS CLARIFICATION]

**规模/范围（Scale/Scope）**: [领域相关，例如：1 万用户、100 万行代码、50 个页面 或 NEEDS CLARIFICATION]

## 宪法检查（Constitution Check）

*门槛（GATE）：必须在 Phase 0 调研之前通过。Phase 1 设计后复查。*

[根据宪法文件确定的检查项]

## 项目结构（Project Structure）

### 文档（本功能）

```text
specs/[###-feature]/
├── plan.md              # 本文件（/speckit.plan 命令输出）
├── research.md          # Phase 0 输出（/speckit.plan 命令）
├── data-model.md        # Phase 1 输出（/speckit.plan 命令）
├── quickstart.md        # Phase 1 输出（/speckit.plan 命令）
├── contracts/           # Phase 1 输出（/speckit.plan 命令）
└── tasks.md             # Phase 2 输出（/speckit.tasks 命令 - 不由 /speckit.plan 创建）
```

### 源码（仓库根目录）

<!--
  必做：将下方的占位符树替换为本功能的具体布局。
  删除未使用的选项，并用真实路径（如 apps/admin、packages/something）展开所选结构。
  交付的计划不得包含 Option 标签。
-->

```text
# [如未使用则删除] 方案 1：单项目（默认）
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [如未使用则删除] 方案 2：Web 应用（检测到 "frontend" + "backend" 时）
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [如未使用则删除] 方案 3：移动端 + API（检测到 "iOS/Android" 时）
api/
└── [同上方 backend]

ios/ 或 android/
└── [平台相关结构：功能模块、UI 流程、平台测试]
```

**结构决策（Structure Decision）**: [说明所选结构，并引用上述捕获的真实目录]

## 复杂度跟踪（Complexity Tracking）

> **仅当宪法检查存在必须说明的违规时才填写**

| 违规项 | 为何需要 | 拒绝更简方案的原因 |
|--------|----------|-------------------|
| [例如：第 4 个项目] | [当前需求] | [为何 3 个项目不够] |
| [例如：Repository 模式] | [具体问题] | [为何直接访问数据库不够] |
