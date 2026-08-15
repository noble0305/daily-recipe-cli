#!/usr/bin/env python3
"""生成 Spec Kit 开发工作流 · Bento 演示 deck 的文档 JSON。

内容源头：docs/spec-kit-workflow.md（SOP）。产出 deck.json 后由
qiaomu-bento-ppt skill 的 bento_deck.py 构建 .bento.html。
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "deck.json"

W, H = 1280, 720
MARGIN = 96
RIGHT = W - MARGIN  # 1184

INK = "#101418"
PAPER = "#F2F0EA"
CORAL = "#FF9E8A"
MUTED = "#A8A49D"
CARD = "#191D24"
LINE = "rgba(242,240,234,0.14)"
FONT = "ui-sans-serif, -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'PingFang SC', sans-serif"


def text(
    eid: str,
    x: float,
    y: float,
    w: float,
    h: float,
    html: str,
    size: float,
    color: str,
    *,
    weight: int = 500,
    align: str = "left",
    valign: str = "top",
    lh: float = 1.2,
    ls: float | None = None,
    fx: dict[str, Any] | None = None,
    link: str | None = None,
) -> dict[str, Any]:
    el: dict[str, Any] = {
        "id": eid, "type": "text", "x": x, "y": y, "w": w, "h": h,
        "rotation": 0, "opacity": 1,
        "html": html, "fontSize": size, "fontFamily": FONT,
        "fontWeight": weight, "color": color, "align": align,
        "valign": valign, "lineHeight": lh,
    }
    if ls is not None:
        el["letterSpacing"] = ls
    if fx:
        el["fx"] = fx
    if link:
        el["link"] = link
    return el


def rect(
    eid: str,
    x: float,
    y: float,
    w: float,
    h: float,
    fill: str,
    *,
    stroke: str = "none",
    stroke_width: float = 0,
    radius: float = 0,
    fx: dict[str, Any] | None = None,
    link: str | None = None,
) -> dict[str, Any]:
    el: dict[str, Any] = {
        "id": eid, "type": "shape", "shape": "rect", "x": x, "y": y,
        "w": w, "h": h, "rotation": 0, "opacity": 1,
        "fill": fill, "stroke": stroke, "strokeWidth": stroke_width,
        "radius": radius,
    }
    if fx:
        el["fx"] = fx
    if link:
        el["link"] = link
    return el


def line(
    eid: str,
    x: float,
    y: float,
    w: float,
    h: float,
    color: str,
    *,
    width: float = 2,
    dashed: bool = False,
    fx: dict[str, Any] | None = None,
) -> dict[str, Any]:
    el: dict[str, Any] = {
        "id": eid, "type": "shape", "shape": "line", "x": x, "y": y,
        "w": w, "h": h, "rotation": 0, "opacity": 1,
        "fill": color, "stroke": "none", "strokeWidth": 0, "radius": 0,
    }
    if dashed:
        el["strokeStyle"] = "dashed"
    if fx:
        el["fx"] = fx
    return el


def table(
    eid: str,
    x: float,
    y: float,
    w: float,
    h: float,
    header: list[str],
    rows: list[list[str]],
    *,
    weights: list[float] | None = None,
    font_size: float = 14,
) -> dict[str, Any]:
    columns = [{"w": 1} for _ in header] if weights is None else [{"w": v} for v in weights]
    all_rows: list[dict[str, Any]] = []
    for i, row in enumerate([header, *rows]):
        cells = []
        for j, cell in enumerate(row):
            c: dict[str, Any] = {"html": cell}
            if i == 0:
                c["align"] = "left"
            cells.append(c)
        all_rows.append({"cells": cells})
    return {
        "id": eid, "type": "table", "x": x, "y": y, "w": w, "h": h,
        "rotation": 0, "opacity": 1,
        "header": True, "columns": columns, "rows": all_rows,
        "style": {
            "headerBg": "#232A34", "headerColor": PAPER,
            "zebra": "rgba(255,255,255,0.03)",
            "borderColor": LINE, "borderWidth": 1,
            "cellPadX": 12, "cellPadY": 8, "fontSize": font_size,
            "fontFamily": FONT, "color": PAPER, "radius": 8,
        },
    }


def card(eid: str, x: float, y: float, w: float, h: float) -> dict[str, Any]:
    return rect(eid, x, y, w, h, CARD, stroke=LINE, stroke_width=1, radius=10)


def slide(sid: str, notes: str, elements: list[dict[str, Any]], *,
          transition: str = "fade", bg: str = INK,
          state_of: str | None = None, name: str | None = None) -> dict[str, Any]:
    s: dict[str, Any] = {
        "id": sid, "background": bg, "transition": transition,
        "notes": notes, "elements": elements,
    }
    if state_of:
        s["stateOf"] = state_of
    if name:
        s["name"] = name
    return s


def kicker(sid: str, label: str) -> dict[str, Any]:
    return text(f"{sid}-kicker", MARGIN, 64, 500, 28, label, 18, CORAL,
                weight=700, ls=2)


def title(sid: str, html: str, *, size: float = 44) -> dict[str, Any]:
    return text(f"{sid}-title", MARGIN, 100, 900, 60, html, size, PAPER, weight=800)


def back_rect(sid: str, parent: str) -> dict[str, Any]:
    """全屏透明点击热区，点击返回父页（state 页专用）。"""
    return rect(f"{sid}-back", 0, 0, W, H, "rgba(0,0,0,0)", link=parent)


# ---------------------------------------------------------------------------
# 主线页
# ---------------------------------------------------------------------------

cover_orb = rect("cover-orb", 1060, 90, 96, 96, "rgba(255,158,138,0.16)",
                 stroke="rgba(255,158,138,0.5)", stroke_width=1, radius=48,
                 fx={"loop": {"type": "motion-path",
                              "path": "M0,0 C 40,-60 90,-50 110,0 C 120,50 70,70 30,40 C -10,10 0,20 0,0",
                              "duration": 26, "ease": "linear"}})

s_cover = slide(
    "s-cover",
    "开场白：今天讲一个让「需求 → 代码」可追溯的六步工作流。左边三个数字是这份 deck 的规模：10 个命令、6 步主链路、8 次提交走完一轮。目标不是说服，而是让团队以后每个项目都这么跑。",
    [
        cover_orb,
        text("cover-kicker", MARGIN, 180, 700, 32, "TEAM PRACTICE GUIDE · 团队实践分享",
             20, CORAL, weight=700, ls=3),
        text("cover-title", MARGIN, 232, 1088, 130, "Spec Kit 开发工作流", 92, PAPER, weight=800, lh=1.05),
        text("cover-sub", MARGIN, 380, 1088, 40, "从需求到代码的可追溯流水线 —— 一份可执行的团队 SOP",
             24, MUTED),
        rect("cover-rule", MARGIN, 452, 64, 4, CORAL, radius=2),
        text("cover-n1", 96, 520, 330, 60, "10", 72, PAPER, weight=800,
             fx={"countUp": True, "enter": "fade-up", "order": 0}),
        text("cover-n1l", 96, 600, 330, 30, "命令 · 覆盖全流程", 16, MUTED),
        text("cover-n2", 496, 520, 330, 60, "6", 72, PAPER, weight=800,
             fx={"countUp": True, "enter": "fade-up", "order": 1}),
        text("cover-n2l", 496, 600, 330, 30, "主链路 · 一步一产物", 16, MUTED),
        text("cover-n3", 896, 520, 300, 60, "8", 72, PAPER, weight=800,
             fx={"countUp": True, "enter": "fade-up", "order": 2}),
        text("cover-n3l", 896, 600, 300, 30, "提交 · 八步走完一轮", 16, MUTED),
        text("cover-meta", MARGIN, 668, 700, 26, "2026-08-15 · 案例：daily-recipe-cli（specs/001）",
             13, MUTED),
    ],
)

agenda_items = [
    ("01", "为什么用 Spec Kit", "痛点 → 答案 → 实战验证", "s-why"),
    ("02", "产物全景", "工作区结构 · 命令全景 · 三条规则", "s-map"),
    ("03", "主链路六步", "specify → analyze，点击看细节", "s-flow"),
    ("04", "团队协作规约", "宪法 · 入仓评审 · 提交约定", "s-rules"),
    ("05", "踩坑 FAQ", "四个高频问题，点击展开答案", "s-faq"),
    ("06", "快速参考", "一页速记 + 评审检查单", "s-cheatsheet"),
]

s_agenda = slide(
    "s-agenda",
    "这一页是整份 deck 的导航：六个章节都可点击直达（演示模式下）。先点给听众看一遍结构，再回到 03 主链路重点讲。",
    [
        kicker("s-agenda", "目录 CONTENTS"),
        title("s-agenda", "6 个章节 · 点击直达"),
        *[card(f"ag-card{i}", 96 + (i % 2) * 584, 200 + (i // 2) * 132, 504, 104)
          for i, _ in enumerate(agenda_items)],
        *[text(f"ag-num{i}", 120 + (i % 2) * 584, 220 + (i // 2) * 132, 60, 30,
               it[0], 18, CORAL, weight=800)
          for i, it in enumerate(agenda_items)],
        *[text(f"ag-t{i}", 190 + (i % 2) * 584, 212 + (i // 2) * 132, 380, 36,
               it[1], 24, PAPER, weight=700)
          for i, it in enumerate(agenda_items)],
        *[text(f"ag-d{i}", 190 + (i % 2) * 584, 252 + (i // 2) * 132, 380, 30,
               it[2], 15, MUTED)
          for i, it in enumerate(agenda_items)],
        *[rect(f"ag-hit{i}", 96 + (i % 2) * 584, 200 + (i // 2) * 132, 504, 104,
               "rgba(0,0,0,0)", link=it[3])
          for i, it in enumerate(agenda_items)],
        text("s-agenda-hint", MARGIN, 648, 1000, 30,
             "演示模式下点击章节直接跳转 · ← 返回上一页", 14, MUTED),
    ],
)

s_why = slide(
    "s-why",
    "痛点有四条：需求口头化、实现黑盒、验收缺失、AI 协作失控。Spec Kit 的答案是把开发拆成规格驱动的流水线。底部表格是 daily-recipe-cli 的真实提交历史——八次提交完美对应了流水线的各个阶段，这是最有说服力的证据。",
    [
        kicker("s-why", "01 · 为什么"),
        title("s-why", "先写规格，再写代码"),
        text("s-why-pl", MARGIN, 178, 520, 30, "痛点", 20, PAPER, weight=700),
        text("s-why-p1", MARGIN, 220, 520, 30, "需求口头化 —— 实现时才发现理解不一致", 16, PAPER),
        text("s-why-p2", MARGIN, 258, 520, 30, "实现黑盒 —— 三个月后没人说得清取舍", 16, PAPER),
        text("s-why-p3", MARGIN, 296, 520, 30, "验收缺失 —— 「做完了」只是「看起来能跑」", 16, PAPER),
        text("s-why-p4", MARGIN, 334, 520, 30, "AI 协作失控 —— 一句含糊需求就开始写码", 16, PAPER),
        text("s-why-al", 664, 178, 520, 30, "Spec Kit 给的答案", 20, PAPER, weight=700),
        text("s-why-a1", 664, 220, 520, 30, "① 需求不确定就不写代码 —— 规格先行", 16, PAPER),
        text("s-why-a2", 664, 258, 520, 30, "② 文档是前置产物，随代码入仓可评审", 16, PAPER),
        text("s-why-a3", 664, 296, 520, 30, "③ 人机同一套产物协作，AI 不再随机发挥", 16, PAPER),
        text("s-why-ev", MARGIN, 384, 1088, 30, "实战验证 —— daily-recipe-cli 一轮完整走完，提交历史即工作流证据",
             16, MUTED),
        table("s-why-tb", MARGIN, 424, 1088, 210,
              ["阶段", "提交示例", "对应环节"],
              [
                  ["规格", "ecee0ee · 88316c5 · c15e9b2", "初始化 + spec / plan / tasks"],
                  ["实现", "61e42ca · b5bc9c4", "存储层 / 六命令 + 测试"],
                  ["收尾", "df3857f · eb3e4f8", "文档打磨 / 非交互修复"],
                  ["治理", "67e6cbe", "AGENTS.md 工作区指南"],
              ],
              weights=[0.7, 1.6, 1.6], font_size=14),
    ],
)

s_map = slide(
    "s-map",
    "产物全景分三块：工作区结构（三个目录各自职责）、命令全景（10 个命令按阶段分类）、三条规则（命令文件是单一事实来源、产物入仓、语言跟随 AGENTS.md）。",
    [
        kicker("s-map", "02 · 产物"),
        title("s-map", "工作区里多了什么"),
        text("s-map-wl", MARGIN, 172, 520, 28, "工作区结构", 19, PAPER, weight=700),
        table("s-map-wt", MARGIN, 206, 520, 190,
              ["路径", "作用"],
              [
                  [".speckit/commands/", "命令定义 · 单一事实来源"],
                  [".specify/", "配置 · 宪法 · 模板 · 脚本"],
                  ["specs/NNN-xxx/", "每个功能的规格产物"],
              ],
              weights=[1.4, 1.6], font_size=14),
        text("s-map-cl", 664, 172, 520, 28, "命令全景（10 个）", 19, PAPER, weight=700),
        table("s-map-ct", 664, 206, 520, 300,
              ["命令", "入口", "阶段"],
              [
                  ["specify", "/speckit-specify", "主链路"],
                  ["clarify", "/speckit-clarify", "主链路"],
                  ["plan", "/speckit-plan", "主链路"],
                  ["tasks", "/speckit-tasks", "主链路"],
                  ["implement", "/speckit-implement", "主链路"],
                  ["analyze", "/speckit-analyze", "主链路"],
                  ["constitution", "/speckit-constitution", "初始化"],
                  ["converge / checklist / taskstoissues", "…", "按需"],
              ],
              weights=[1.6, 1.5, 0.9], font_size=13),
        rect("s-map-rule", MARGIN, 536, 1088, 1, LINE),
        text("s-map-rl", MARGIN, 556, 1088, 30, "三条规则", 19, PAPER, weight=700),
        text("s-map-r1", MARGIN, 600, 1088, 28, "① 命令文件是单一事实来源 —— 封装只做入口，不自行增删步骤", 15, PAPER),
        text("s-map-r2", MARGIN, 634, 1088, 28, "② 产物按阶段落盘入仓 —— 与代码同库、同步演进", 15, PAPER),
        text("s-map-r3", MARGIN, 668, 1088, 28, "③ 语言与提交跟随 AGENTS.md —— 中文文档 + 中文提交", 15, PAPER),
    ],
)

flow_steps = [
    ("specify", "规格", "spec.md", "s-flow-specify"),
    ("clarify", "澄清", "歧义消除", "s-flow-clarify"),
    ("plan", "计划", "plan.md", "s-flow-plan"),
    ("tasks", "任务", "tasks.md", "s-flow-tasks"),
    ("implement", "实现", "代码 + 测试", "s-flow-implement"),
    ("analyze", "回顾", "核对 + 收尾", "s-flow-analyze"),
]

s_flow = slide(
    "s-flow",
    "主链路六步：specify → clarify → plan → tasks → implement → analyze。每个节点都可点击进入细节页（演示模式），展示何时调用、做什么、产出什么、本项目示例。这是整份 deck 的核心页。",
    [
        kicker("s-flow", "03 · 主链路"),
        title("s-flow", "六步流水线 · 点击节点看细节"),
        *[line(f"flow-line{i}", 96 + i * 184 + 152, 336, 48, 2, "rgba(255,158,138,0.4)",
               fx={"loop": {"type": "dash-march", "distance": 8, "duration": 1.4}})
          for i in range(5)],
        *[card(f"flow-card{i}", 96 + i * 184, 300, 152, 100) for i in range(6)],
        *[text(f"flow-en{i}", 96 + i * 184 + 12, 314, 128, 26, it[0], 17, CORAL, weight=700)
          for i, it in enumerate(flow_steps)],
        *[text(f"flow-cn{i}", 96 + i * 184 + 12, 344, 128, 30, it[1], 21, PAPER, weight=800)
          for i, it in enumerate(flow_steps)],
        *[text(f"flow-out{i}", 96 + i * 184 + 12, 376, 128, 26, it[2], 13, MUTED)
          for i, it in enumerate(flow_steps)],
        *[rect(f"flow-hit{i}", 96 + i * 184, 300, 152, 100, "rgba(0,0,0,0)", link=it[3])
          for i, it in enumerate(flow_steps)],
        text("s-flow-tip", MARGIN, 440, 1088, 30,
             "① 规格 → ② 澄清 → ③ 计划 → ④ 任务 → ⑤ 实现 → ⑥ 回顾", 16, MUTED),
        text("s-flow-hint", MARGIN, 640, 1088, 30,
             "演示模式下点击任意节点查看该步骤细节 · ← 返回本页", 14, MUTED),
    ],
)

rules_list = [
    ("宪法约束", "/speckit-constitution 初始化；原则变更走评审，不随意改"),
    ("产物入仓", "specs/ 随代码提交，spec / plan / tasks 参与 PR 评审"),
    ("提交约定", "中文提交 + Conventional Commits 前缀，一个任务一个提交"),
    ("AI 接入", "命令文件是单一事实来源，skill 只做入口；测试不碰真实数据"),
    ("文档同步", "用户可见变更追加 CHANGELOG；AGENTS.md 是落地操作手册"),
]

s_rules = slide(
    "s-rules",
    "规约五条全部是强制的，不是建议：宪法约束、产物入仓并评审、提交约定、AI 接入约定、文档同步。这些都已经固化在仓库文件里（constitution.md / AGENTS.md），新人照着走即可。",
    [
        kicker("s-rules", "04 · 规约"),
        title("s-rules", "团队协作规约 · 强制项"),
        *[rect(f"rule-n{i}", MARGIN, 186 + i * 92, 44, 44, CORAL, radius=8)
          for i in range(5)],
        *[text(f"rule-num{i}", MARGIN, 192 + i * 92, 44, 34, str(i + 1), 19, INK,
               weight=800, align="center")
          for i in range(5)],
        *[text(f"rule-t{i}", 164, 184 + i * 92, 420, 30, it[0], 21, PAPER, weight=700)
          for i, it in enumerate(rules_list)],
        *[text(f"rule-d{i}", 164, 218 + i * 92, 700, 28, it[1], 15, MUTED)
          for i, it in enumerate(rules_list)],
        rect("s-rules-rule", MARGIN, 660, 1088, 1, LINE),
        text("s-rules-foot", MARGIN, 674, 1088, 26,
             "规约文件：.specify/memory/constitution.md · AGENTS.md", 13, MUTED),
    ],
)

faq_items = [
    ("命令文件与 skill 封装冲突怎么办？", "以命令文件为准 —— 封装 frontmatter 已声明", "s-faq1"),
    ("非交互场景（CI）下确认会崩吗？", "捕获 EOFError 视为「否」，不崩溃", "s-faq2"),
    ("手改 JSON 把数据弄坏了怎么办？", "抛 DataError（中文 + 字段/位置），绝不静默容错", "s-faq3"),
    ("做完才发现需求理解错了？", "回 clarify → 更新 spec/plan/tasks，不绕过文档", "s-faq4"),
]

s_faq = slide(
    "s-faq",
    "四个从本项目真实提炼的高频问题，点击可展开答案（演示模式）。每一个都对应一条写入文档的规则，讲的时候点到即可。",
    [
        kicker("s-faq", "05 · 踩坑"),
        title("s-faq", "四个高频问题 · 点击展开答案"),
        *[card(f"faq-card{i}", 96 + (i % 2) * 584, 200 + (i // 2) * 160, 504, 128)
          for i in range(4)],
        *[text(f"faq-q{i}", 120 + (i % 2) * 584, 222 + (i // 2) * 160, 450, 34,
               it[0], 19, PAPER, weight=700)
          for i, it in enumerate(faq_items)],
        *[text(f"faq-a{i}", 120 + (i % 2) * 584, 266 + (i // 2) * 160, 450, 30,
               it[1], 14, MUTED)
          for i, it in enumerate(faq_items)],
        *[rect(f"faq-hit{i}", 96 + (i % 2) * 584, 200 + (i // 2) * 160, 504, 128,
               "rgba(0,0,0,0)", link=it[2])
          for i, it in enumerate(faq_items)],
        text("s-faq-hint", MARGIN, 640, 1088, 30,
             "演示模式下点击问题卡片展开答案 · ← 返回本页", 14, MUTED),
    ],
)

s_cheatsheet = slide(
    "s-cheatsheet",
    "收尾一页：左侧是主链路速记和关键文件，右侧是评审检查单。分享结束时把这一页留给听众截图，就能直接开始用。",
    [
        kicker("s-cheatsheet", "06 · 参考"),
        title("s-cheatsheet", "一页速记"),
        text("s-cs-fl", MARGIN, 176, 520, 28, "主链路速记", 19, PAPER, weight=700),
        text("s-cs-flow", MARGIN, 216, 520, 120,
             "specify → clarify → plan<br/>→ tasks → implement → analyze", 20, PAPER, weight=700, lh=1.5),
        text("s-cs-files", MARGIN, 384, 520, 26, "关键文件", 19, PAPER, weight=700),
        text("s-cs-fl1", MARGIN, 424, 520, 26, "命令定义：.speckit/commands/speckit.*.md", 14, MUTED),
        text("s-cs-fl2", MARGIN, 456, 520, 26, "项目宪法：.specify/memory/constitution.md", 14, MUTED),
        text("s-cs-fl3", MARGIN, 488, 520, 26, "案例产物：specs/001-daily-recipe-cli/", 14, MUTED),
        text("s-cs-fl4", MARGIN, 520, 520, 26, "工作区指南：AGENTS.md", 14, MUTED),
        text("s-cs-cl", 664, 176, 520, 28, "评审检查单（PR 逐项打勾）", 19, PAPER, weight=700),
        *[text(f"cs-c{i}", 664, 214 + i * 34, 520, 28,
               f"☐ {t}", 15, PAPER)
          for i, t in enumerate([
              "spec.md 验收场景可执行（Given/When/Then）",
              "plan.md 技术取舍有理由",
              "tasks.md 任务与 spec 故事一一对应",
              "代码与数据契约（contracts/）一致",
              "核心逻辑有单元测试且通过",
              "提交信息中文 + Conventional Commits",
              "用户可见变更已追加 CHANGELOG.md",
              "spec / plan / tasks 与最终行为一致",
          ])],
    ],
)

# ---------------------------------------------------------------------------
# state 细节页：主链路六步
# ---------------------------------------------------------------------------

flow_details = [
    ("s-flow-specify", "s-flow", "主链路 · ① 规格", "specify",
     "新功能启动 / 需求变更时",
     "把模糊需求转成 spec.md：用户故事、优先级、Given/When/Then 验收场景",
     "specs/001-daily-recipe-cli/spec.md",
     "User Story 1 - 前一晚定第二天的饭（P1）<br/>Given 食谱库 ≥3 道菜且无历史，When 运行今日推荐，<br/>Then 展示 1~3 道候选并说明推荐理由。"),
    ("s-flow-clarify", "s-flow", "主链路 · ② 澄清", "clarify",
     "spec 存在歧义 / 多解 / 冲突时",
     "向干系人提问，把模糊表述收敛成确定结论并回写 spec",
     "更新后的 spec.md（状态推进）",
     "案例：week 的非交互确认——无输入时怎么办，必须澄清并写进代码行为（捕获 EOFError 视为「否」）。"),
    ("s-flow-plan", "s-flow", "主链路 · ③ 计划", "plan",
     "spec 稳定（至少 P1 清晰）后",
     "确定技术路线：语言 / 依赖 / 存储 / 测试 / 平台；数据契约先行",
     "plan.md + research.md + data-model.md + contracts/",
     "Python 3.11+ · 运行时零第三方依赖 · JSON 存储 · pytest<br/>数据契约写进 contracts/data-schema.md，先于实现。"),
    ("s-flow-tasks", "s-flow", "主链路 · ④ 任务", "tasks",
     "plan 评审通过后",
     "按用户故事拆任务，标注 [P] 并行标记与所属 Story；一任务一提交",
     "tasks.md",
     "[001] [US1] 实现 storage 层：原子 JSON 写入、校验、默认食谱库<br/>[P] 表示可并行（不同文件、无依赖）。"),
    ("s-flow-implement", "s-flow", "主链路 · ⑤ 实现", "implement",
     "tasks 拆解完成，逐任务实现",
     "严格按任务范围写代码 + 测试；中文提交 + Conventional Commits；不扩大范围",
     "应用代码 + 测试 + 中文提交历史",
     "61e42ca feat: storage layer with atomic JSON writes,<br/>validation, and default recipe library"),
    ("s-flow-analyze", "s-flow", "主链路 · ⑥ 回顾", "analyze",
     "所有任务完成、合入 / 发布前",
     "对照 spec 与核对表回顾；补 README / CHANGELOG；遗漏需求回写 spec",
     "checklists/requirements.md 勾选完成 + 收尾提交",
     "df3857f docs: polish - add README, CHANGELOG,<br/>spec FR-013, mark tasks complete"),
]

state_flow = []
for sid, parent, kicker_label, cmd, when, do, out, example in flow_details:
    state_flow.append(slide(
        sid, f"{cmd} 步骤的细节页：何时调用 / 做什么 / 产出 / 本项目示例。演示时从流程页点进来，讲完按 ← 返回。",
        [
            back_rect(sid, parent),
            rect(f"{sid}-panel", MARGIN, 120, 1088, 520, CARD, stroke=LINE, stroke_width=1, radius=12),
            text(f"{sid}-kicker", MARGIN + 36, 148, 800, 28, kicker_label, 17, CORAL, weight=700, ls=2),
            text(f"{sid}-cmd", MARGIN + 36, 190, 800, 60, cmd, 44, PAPER, weight=800),
            text(f"{sid}-w", MARGIN + 36, 280, 300, 26, "何时调用", 16, MUTED, weight=700),
            text(f"{sid}-wv", MARGIN + 36, 312, 1000, 30, when, 17, PAPER),
            text(f"{sid}-d", MARGIN + 36, 366, 300, 26, "做什么", 16, MUTED, weight=700),
            text(f"{sid}-dv", MARGIN + 36, 398, 1000, 30, do, 17, PAPER),
            text(f"{sid}-o", MARGIN + 36, 452, 300, 26, "产出", 16, MUTED, weight=700),
            text(f"{sid}-ov", MARGIN + 36, 484, 1000, 30, out, 17, CORAL),
            rect(f"{sid}-sep", MARGIN + 36, 540, 1016, 1, LINE),
            text(f"{sid}-ex", MARGIN + 36, 558, 1016, 60, example, 16, MUTED, lh=1.45),
            text(f"{sid}-back-hint", MARGIN, 668, 800, 26,
                 "点击任意处或 ← 返回主链路页", 13, MUTED),
        ],
        transition="morph",
        state_of=parent, name=cmd,
    ))

# ---------------------------------------------------------------------------
# state 细节页：FAQ 四条
# ---------------------------------------------------------------------------

faq_details = [
    ("s-faq1", "s-faq", "命令文件与 skill 封装冲突怎么办？",
     "以命令文件为准。skill 封装在 frontmatter 里明确写了「若文件流程与本封装冲突，以命令文件为准」。",
     "升级工作流 = 更新 .speckit/commands/*.md 并提交，全员自动生效，无需重新分发封装。"),
    ("s-faq2", "s-faq", "非交互场景（CI / 管道）下确认会崩吗？",
     "会，所以必须有兜底。week 命令用 input() 读确认，捕获 EOFError（非交互时 input 抛异常）视为「否」。",
     "凡是涉及交互的行为，spec 里都要写明非交互时的默认行为。"),
    ("s-faq3", "s-faq", "手改 JSON 把数据弄坏了怎么办？",
     "不静默容错。任何命令加载数据时发现非法数据都抛带中文信息的 DataError（含出错字段 / 位置）。",
     "写入用「先写 .tmp 再 os.replace()」的原子方式；宁可报错，不可悄悄覆盖用户数据。"),
    ("s-faq4", "s-faq", "做完才发现需求理解错了？",
     "这正是流水线的价值——需求在 spec 阶段成本最低。回到 /speckit-clarify 澄清 → 更新 spec.md → 更新 plan / tasks → 继续。",
     "不要用代码补丁绕过文档，否则三个月后没人知道当初为什么这么做。"),
]

state_faq = []
for sid, parent, q, a, rule in faq_details:
    state_faq.append(slide(
        sid, f"FAQ：{q}。答案是：{a}。对应的规则：{rule}。",
        [
            back_rect(sid, parent),
            rect(f"{sid}-panel", MARGIN, 120, 1088, 520, CARD, stroke=LINE, stroke_width=1, radius=12),
            text(f"{sid}-kicker", MARGIN + 36, 148, 800, 28, "FAQ · 踩坑与答案", 17, CORAL, weight=700, ls=2),
            text(f"{sid}-q", MARGIN + 36, 200, 1000, 60, q, 32, PAPER, weight=800),
            rect(f"{sid}-sep", MARGIN + 36, 290, 1016, 1, LINE),
            text(f"{sid}-a", MARGIN + 36, 320, 1016, 120, a, 20, PAPER, lh=1.5),
            text(f"{sid}-rule", MARGIN + 36, 470, 1016, 60, "对应规则：" + rule, 16, CORAL, lh=1.5),
            text(f"{sid}-back-hint", MARGIN, 668, 800, 26,
                 "点击任意处或 ← 返回 FAQ 页", 13, MUTED),
        ],
        transition="morph",
        state_of=parent, name=q[:12],
    ))

doc = {
    "format": "bento/slides",
    "version": 1,
    "title": "Spec Kit 开发工作流 · 团队实践分享",
    "meta": {
        "author": "daily-recipe-cli",
        "company": "团队实践",
        "subject": "Spec Kit 开发工作流团队实践指南",
        "event": "团队技术分享",
        "keywords": "spec-kit, workflow, SOP",
    },
    "size": {"width": W, "height": H},
    "theme": {
        "background": INK,
        "color": PAPER,
        "accent": CORAL,
        "fontFamily": FONT,
        "chartPalette": [CORAL, "#5B7CFF", "#D9F06B", PAPER],
    },
    "present": {"slideNumber": True, "controls": False, "progress": True},
    "slides": [
        s_cover, s_agenda, s_why, s_map, s_flow, s_rules, s_faq, s_cheatsheet,
        *state_flow, *state_faq,
    ],
    "modified": "2026-08-15T00:00:00Z",
}

# 不预置 docId：build 时由 --new-document 铸造
OUTPUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[ok] {OUTPUT.name} 共 {len(doc['slides'])} 页")
