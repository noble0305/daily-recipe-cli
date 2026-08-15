"""购物清单聚合逻辑测试：窗口过滤、去重合并、来源标注、排序、跳过、确定性。"""

from __future__ import annotations

from datetime import date, timedelta

from daily_recipe_cli import shopping

TODAY = date(2026, 8, 15)  # 周六

RECIPES = [
    {"name": "番茄牛腩", "ingredients": ["牛腩", "番茄", "洋葱", "土豆"], "tags": ["荤", "费时"], "note": ""},
    {"name": "番茄炒蛋", "ingredients": ["番茄", "鸡蛋"], "tags": ["素", "快手"], "note": ""},
    {"name": "日式咖喱鸡", "ingredients": ["鸡腿肉", "土豆", "胡萝卜"], "tags": ["荤", "快手"], "note": ""},
    {"name": "凉拌黄瓜", "ingredients": ["黄瓜"], "tags": ["素", "快手"], "note": ""},
]


def history_at(entries: list[tuple[str, str]]) -> list[dict]:
    """构造历史：[(days_from_today, 菜名), ...]，source 固定 today。"""
    return [
        {"date": (TODAY + timedelta(days=offset)).isoformat(), "recipe": name, "source": "today"}
        for offset, name in entries
    ]


def test_empty_window_returns_empty():
    result = shopping.build_list(RECIPES, [], TODAY)
    assert result["items"] == []
    assert result["skippedRecipes"] == []
    assert result["empty"] is True
    assert result["windowDays"] == 7


def test_aggregates_today_and_window():
    # 今日番茄牛腩 + 后天番茄炒蛋
    hist = history_at([(0, "番茄牛腩"), (2, "番茄炒蛋")])
    result = shopping.build_list(RECIPES, hist, TODAY)
    items = {i["ingredient"]: i["sources"] for i in result["items"]}
    assert set(items) == {"牛腩", "番茄", "洋葱", "土豆", "鸡蛋"}
    assert items["番茄"] == ["番茄牛腩", "番茄炒蛋"]  # 跨菜合并 + 来源标注
    assert result["empty"] is False


def test_items_sorted_by_ingredient():
    hist = history_at([(0, "凉拌黄瓜"), (0, "番茄牛腩")])
    result = shopping.build_list(RECIPES, hist, TODAY)
    names = [i["ingredient"] for i in result["items"]]
    assert names == sorted(names)


def test_window_excludes_outside_entries():
    # 第 8 天（窗口末日为第 6 天）的菜不在聚合范围内
    hist = history_at([(0, "番茄牛腩"), (7, "日式咖喱鸡")])
    result = shopping.build_list(RECIPES, hist, TODAY, days=7)
    items = [i["ingredient"] for i in result["items"]]
    assert "鸡腿肉" not in items  # 第 7 天超出 7 天窗口（含今日为第 0..6）
    assert "牛腩" in items


def test_window_days_custom():
    hist = history_at([(0, "番茄牛腩"), (2, "番茄炒蛋")])
    result = shopping.build_list(RECIPES, hist, TODAY, days=1)
    items = [i["ingredient"] for i in result["items"]]
    assert "鸡蛋" not in items  # 第 2 天不在 1 天窗口内
    assert "牛腩" in items


def test_today_only_is_window_one():
    hist = history_at([(0, "番茄牛腩"), (1, "番茄炒蛋")])
    result = shopping.build_list(RECIPES, hist, TODAY, days=1)
    items = [i["ingredient"] for i in result["items"]]
    assert "鸡蛋" not in items
    assert "牛腩" in items


def test_no_merge_lists_sources_separately():
    hist = history_at([(0, "番茄牛腩"), (0, "番茄炒蛋")])
    result = shopping.build_list(RECIPES, hist, TODAY, merge=False)
    # 番茄出现两次（各来源一条），其余食材一次
    toms = [i for i in result["items"] if i["ingredient"] == "番茄"]
    assert len(toms) == 2
    assert [i["sources"] for i in toms] == [["番茄牛腩"], ["番茄炒蛋"]]


def test_merge_true_default_combines():
    hist = history_at([(0, "番茄牛腩"), (0, "番茄炒蛋")])
    result = shopping.build_list(RECIPES, hist, TODAY)
    toms = [i for i in result["items"] if i["ingredient"] == "番茄"]
    assert len(toms) == 1
    assert toms[0]["sources"] == ["番茄牛腩", "番茄炒蛋"]


def test_skips_recipe_not_in_library():
    hist = history_at([(0, "番茄牛腩"), (1, "不存在的菜")])
    result = shopping.build_list(RECIPES, hist, TODAY)
    items = [i["ingredient"] for i in result["items"]]
    assert "牛腩" in items
    assert result["skippedRecipes"] == ["不存在的菜"]


def test_skips_recipe_with_bad_ingredients():
    hist = history_at([(0, "番茄牛腩"), (1, "番茄炒蛋")])
    broken = [
        {"name": "番茄炒蛋", "ingredients": "番茄", "tags": ["素"], "note": ""},  # 非法：非列表
    ]
    result = shopping.build_list(RECIPES + broken, hist, TODAY)
    items = [i["ingredient"] for i in result["items"]]
    assert "牛腩" in items
    assert result["skippedRecipes"] == ["番茄炒蛋"]


def test_duplicate_history_date_keeps_latest_source_order():
    # 同一日期两条记录（正常不会发生，但聚合应稳健：两菜都纳入）
    hist = history_at([(0, "番茄牛腩"), (0, "番茄炒蛋")])
    result = shopping.build_list(RECIPES, hist, TODAY)
    items = {i["ingredient"]: i["sources"] for i in result["items"]}
    assert items["番茄"] == ["番茄牛腩", "番茄炒蛋"]


def test_deterministic_same_input():
    hist = history_at([(0, "番茄牛腩"), (2, "番茄炒蛋")])
    r1 = shopping.build_list(RECIPES, hist, TODAY)
    r2 = shopping.build_list(RECIPES, hist, TODAY)
    assert r1 == r2


def test_week_source_records_included():
    # week 来源的记录同样纳入聚合（未来周计划）
    hist = history_at([(0, "番茄牛腩")])
    hist.append(
        {"date": (TODAY + timedelta(days=3)).isoformat(), "recipe": "日式咖喱鸡", "source": "week"}
    )
    result = shopping.build_list(RECIPES, hist, TODAY)
    items = {i["ingredient"]: i["sources"] for i in result["items"]}
    assert "鸡腿肉" in items
    assert items["土豆"] == ["番茄牛腩", "日式咖喱鸡"]


def test_window_end_is_today_plus_days_minus_one():
    # 窗口末日 = TODAY + (days-1) = 第 6 天；第 6 天的菜应纳入
    hist = history_at([(6, "凉拌黄瓜")])
    result = shopping.build_list(RECIPES, hist, TODAY, days=7)
    items = [i["ingredient"] for i in result["items"]]
    assert items == ["黄瓜"]
