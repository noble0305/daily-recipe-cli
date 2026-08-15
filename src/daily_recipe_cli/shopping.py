"""购物清单聚合逻辑：时间窗口过滤、食材去重合并、来源标注、排序。

纯计算、零 I/O：不触碰数据文件，由 CLI 与页面（server）分别装载数据后
调用。确定性：无随机源，同数据状态必然产出同一清单（constitution 原则 III）。
"""

from __future__ import annotations

from datetime import date, timedelta


def build_list(
    recipes: list[dict],
    history: list[dict],
    today: date,
    days: int = 7,
    merge: bool = True,
) -> dict:
    """聚合窗口内已安排菜的食材，返回购物清单视图。

    规则：
    - 窗口为 [today, today + (days - 1)] 闭区间，含 today 与窗口末日；
    - 以食谱 `ingredients` 原始字符串为键去重合并，标注来源菜；
    - merge=False 时同一食材每出现于一道菜就单独列一条；
    - 菜名不在食谱库或 `ingredients` 非法时跳过并记入 skippedRecipes；
    - 返回的 items 按食材名排序（UTF-8 字节序）。
    """
    start = today
    end = today + timedelta(days=days - 1)

    recipe_by_name = {r["name"]: r for r in recipes}

    # 收集窗口内菜名（保留出现顺序，同一菜去重——同日期多条记录也仅记一次）
    planned_names: list[str] = []
    seen: set[str] = set()
    for entry in history:
        entry_date = date.fromisoformat(entry["date"])
        if start <= entry_date <= end and entry["recipe"] not in seen:
            planned_names.append(entry["recipe"])
            seen.add(entry["recipe"])

    if not planned_names:
        return {"windowDays": days, "items": [], "skippedRecipes": [], "empty": True}

    items: list[dict] = []
    skipped: list[str] = []
    for name in planned_names:
        recipe = recipe_by_name.get(name)
        ingredients = recipe["ingredients"] if recipe else None
        if not recipe or not _valid_ingredients(ingredients):
            skipped.append(name)
            continue
        if merge:
            for ing in ingredients:
                item = next((i for i in items if i["ingredient"] == ing), None)
                if item is None:
                    items.append({"ingredient": ing, "sources": [name]})
                else:
                    item["sources"].append(name)
        else:
            for ing in ingredients:
                items.append({"ingredient": ing, "sources": [name]})

    items.sort(key=lambda i: i["ingredient"])
    return {
        "windowDays": days,
        "items": items,
        "skippedRecipes": skipped,
        "empty": False,
    }


def _valid_ingredients(ingredients: object) -> bool:
    return (
        isinstance(ingredients, list)
        and bool(ingredients)
        and all(isinstance(x, str) and x.strip() for x in ingredients)
    )
