"""推荐逻辑测试：候选生成、去重窗口、种子可复现、周规划、标签过滤。"""

from __future__ import annotations

from datetime import date

import pytest

from daily_recipe_cli import recommend

TODAY = date(2026, 8, 15)  # 周六

RECIPES = [
    {"name": "A", "ingredients": ["a"], "tags": ["荤", "快手"], "note": ""},
    {"name": "B", "ingredients": ["b"], "tags": ["素", "快手"], "note": ""},
    {"name": "C", "ingredients": ["c"], "tags": ["荤", "费时"], "note": ""},
    {"name": "D", "ingredients": ["d"], "tags": ["素", "费时"], "note": ""},
    {"name": "E", "ingredients": ["e"], "tags": ["荤", "快手"], "note": ""},
    {"name": "F", "ingredients": ["f"], "tags": ["素", "快手"], "note": ""},
]


def history(names: list[str], days_back: int = 1) -> list[dict]:
    from datetime import timedelta

    return [
        {
            "date": (TODAY - timedelta(days=i + 1)).isoformat(),
            "recipe": name,
            "source": "today",
        }
        for i, name in enumerate(names)
    ]


def names(result: list[dict]) -> list[str]:
    return [r["name"] for r in result]


def test_candidates_default_count_and_order():
    result, widened = recommend.candidates(RECIPES, [], TODAY, seed="s1")
    assert len(result) == 3
    assert not widened


def test_candidates_excludes_recent_history():
    result, _ = recommend.candidates(RECIPES, history(["A", "B"]), TODAY, seed="s1")
    assert "A" not in names(result)
    assert "B" not in names(result)
    assert set(names(result)) <= {"C", "D", "E", "F"}


def test_candidates_same_seed_is_reproducible():
    r1, _ = recommend.candidates(RECIPES, [], TODAY, seed="fixed")
    r2, _ = recommend.candidates(RECIPES, [], TODAY, seed="fixed")
    assert names(r1) == names(r2)


def test_candidates_different_seed_differs():
    r1, _ = recommend.candidates(RECIPES, [], TODAY, seed="seed-a")
    r2, _ = recommend.candidates(RECIPES, [], TODAY, seed="seed-b")
    assert names(r1) != names(r2)


def test_candidates_default_seed_by_date_is_stable():
    r1, _ = recommend.candidates(RECIPES, [], TODAY, seed=None)
    r2, _ = recommend.candidates(RECIPES, [], TODAY, seed=None)
    assert names(r1) == names(r2)


def test_candidates_respects_count():
    result, _ = recommend.candidates(RECIPES, [], TODAY, count=2, seed="s1")
    assert len(result) == 2


def test_candidates_widens_window_when_insufficient():
    # 全部菜都在最近 1 天吃过 → 7 天窗口内无可用 → 放宽后仍可选（历史只有 2 天）
    recent = history(["A", "B", "C", "D", "E", "F"], days_back=1)
    result, widened = recommend.candidates(RECIPES, recent, TODAY, seed="s1")
    assert widened
    assert len(result) >= 1


def test_candidates_no_widen_without_history():
    result, widened = recommend.candidates(RECIPES, [], TODAY, seed="s1")
    assert not widened


def test_candidates_tag_filter():
    result, _ = recommend.candidates(RECIPES, [], TODAY, tags=["素"], seed="s1")
    assert all("素" in r["tags"] for r in result)
    result2, _ = recommend.candidates(
        RECIPES, [], TODAY, tags=["素", "快手"], seed="s1"
    )
    assert all({"素", "快手"} <= set(r["tags"]) for r in result2)


def test_candidates_empty_pool_returns_empty():
    result, widened = recommend.candidates([], [], TODAY, seed="s1")
    assert result == []
    assert not widened


def test_candidates_tag_no_match_returns_empty():
    result, widened = recommend.candidates(
        RECIPES, [], TODAY, tags=["汤"], seed="s1"
    )
    assert result == []
    assert not widened


# --- 周规划 ---


def test_week_plan_returns_five_weekdays_starting_next_monday():
    plan, _ = recommend.week_plan(RECIPES, [], TODAY, seed="w1")
    assert len(plan) == 5
    assert plan[0][0].isoformat() == "2026-08-17"  # 下周一
    assert [d.isoweekday() for d, _ in plan] == [1, 2, 3, 4, 5]


def test_week_plan_no_intra_batch_repeat():
    plan, _ = recommend.week_plan(RECIPES, [], TODAY, seed="w1")
    chosen = [r["name"] for _, r in plan]
    assert len(set(chosen)) == len(chosen)


def test_week_plan_excludes_recent_history():
    # 库充足（8 道），历史吃过的 2 道不出现在周计划里
    big = RECIPES + [
        {"name": "G", "ingredients": ["g"], "tags": ["荤", "快手"], "note": ""},
        {"name": "H", "ingredients": ["h"], "tags": ["素", "快手"], "note": ""},
    ]
    plan, relaxed = recommend.week_plan(big, history(["A", "B"]), TODAY, seed="w1")
    chosen = [r["name"] for _, r in plan]
    assert "A" not in chosen
    assert "B" not in chosen
    assert len(chosen) == 5
    assert not relaxed


def test_week_plan_relaxes_window_to_fill_week():
    # 库偏小（6 道、2 道刚吃过）：放宽历史去重后仍填满 5 天，批内不重复
    plan, relaxed = recommend.week_plan(RECIPES, history(["A", "B"]), TODAY, seed="w1")
    chosen = [r["name"] for _, r in plan]
    assert relaxed
    assert len(chosen) == 5
    assert len(set(chosen)) == 5


def test_week_plan_reproducible_with_seed():
    p1, _ = recommend.week_plan(RECIPES, [], TODAY, seed="fixed")
    p2, _ = recommend.week_plan(RECIPES, [], TODAY, seed="fixed")
    assert [r["name"] for _, r in p1] == [r["name"] for _, r in p2]


def test_week_plan_marks_unfillable_days():
    # 库只有 1 道：只能填 1 天，其余 4 天为 None，无需放宽（放宽也无效）
    plan, relaxed = recommend.week_plan([RECIPES[0]], [], TODAY, seed="w1")
    picked = [r["name"] for _, r in plan if r is not None]
    assert len(picked) == 1
    assert sum(1 for _, r in plan if r is None) == 4
    assert not relaxed
