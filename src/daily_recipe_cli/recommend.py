"""推荐核心逻辑：候选生成、去重窗口、周规划。

所有随机操作使用注入的 seed（字符串）构造 random.Random，保证
同一种子与同一数据状态下产出同一结果（constitution 原则 III）。
"""

from __future__ import annotations

import random
from datetime import date, timedelta


def candidates(
    recipes: list[dict],
    history: list[dict],
    today: date,
    tags: list[str] | None = None,
    days: int = 7,
    count: int = 3,
    seed: str | None = None,
) -> tuple[list[dict], bool]:
    """从食谱库中选出候选菜。

    规则：先按标签过滤，再排除去重窗口内已选的菜；候选不足时逐步
    放宽窗口（翻倍直至覆盖全部历史）。返回 (候选列表, 是否放宽过窗口)。
    """
    tag_set = set(tags or [])
    pool = [r for r in recipes if _match_tags(r, tag_set)]
    if not pool:
        return [], False

    window = max(days, 1)
    widened = False
    avail = _unseen(pool, history, window, today)
    while len(avail) < count and window > 0:
        # 候选不足时逐步缩小去重窗口（7→3→1→0），允许近期重复以凑足候选
        window = window // 2
        avail = _unseen(pool, history, window, today)
        widened = True

    rng = random.Random(seed if seed is not None else today.isoformat())
    shuffled = sorted(avail, key=lambda r: rng.random())
    return shuffled[:count], widened


def week_plan(
    recipes: list[dict],
    history: list[dict],
    today: date,
    tags: list[str] | None = None,
    days: int = 7,
    seed: str | None = None,
) -> tuple[list[tuple[date, dict | None]], bool]:
    """生成未来 5 个工作日的周计划。

    返回 [(日期, 菜), ...]；天与天之间互不重复，并避开去重窗口内已选的
    菜。某天候选不足时逐步缩小去重窗口（批内仍不重复）；窗口缩到 0 仍
    不足时该天为 None。第二返回值标记是否发生过窗口放宽。
    """
    tag_set = set(tags or [])
    pool = [r for r in recipes if _match_tags(r, tag_set)]
    dates = [_next_weekday(today, offset) for offset in range(5)]

    rng = random.Random(seed if seed is not None else today.isoformat() + "-week")
    window = max(days, 1)
    batch_used: set[str] = set()
    relaxed = False

    plan: list[tuple[date, dict | None]] = []
    for d in dates:
        recent = _recent_names(history, window, today)
        used = recent | batch_used
        avail = [r for r in pool if r["name"] not in used]
        while not avail and window > 0:
            window = window // 2
            recent = _recent_names(history, window, today)
            used = recent | batch_used
            new_avail = [r for r in pool if r["name"] not in used]
            if new_avail:
                relaxed = True
            avail = new_avail
        if not avail:
            plan.append((d, None))
            continue
        rng.shuffle(avail)
        chosen = avail[0]
        batch_used.add(chosen["name"])
        plan.append((d, chosen))
    return plan, relaxed


def _match_tags(recipe: dict, tag_set: set[str]) -> bool:
    return tag_set <= set(recipe["tags"]) if tag_set else True


def _unseen(pool: list[dict], history: list[dict], window: int, today: date) -> list[dict]:
    recent = _recent_names(history, window, today)
    return [r for r in pool if r["name"] not in recent]


def _recent_names(history: list[dict], window: int, today: date) -> set[str]:
    cutoff = today - timedelta(days=window)
    return {e["recipe"] for e in history if _parse_date(e["date"]) >= cutoff}


def _parse_date(s: str) -> date:
    return date.fromisoformat(s)


def _next_weekday(today: date, offset: int) -> date:
    """返回下一个工作周的周一（若今天恰为周一则从今天起）起的第 offset 天。"""
    days_until_monday = (1 - today.isoweekday()) % 7
    return today + timedelta(days=days_until_monday + offset)
