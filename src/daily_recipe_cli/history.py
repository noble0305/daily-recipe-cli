"""历史记录：每日选择的写入、读取与「当日已确定」判断。

历史条目存菜名快照，删除食谱不影响已有历史。
"""

from __future__ import annotations

from daily_recipe_cli import storage


def load() -> list[dict]:
    """加载全部历史记录（按日期升序）。"""
    return sorted(storage.load_history(), key=lambda e: e["date"])


def decided_for_date(date: str) -> str | None:
    """返回指定日期已确定的菜名；未确定返回 None。"""
    for entry in storage.load_history():
        if entry["date"] == date:
            return entry["recipe"]
    return None


def add(date: str, recipe: str, source: str = "today") -> None:
    """写入一条历史；同日期已有记录时覆盖（支持 --force 语义）。"""
    entries = [e for e in storage.load_history() if e["date"] != date]
    entries.append({"date": date, "recipe": recipe, "source": source})
    storage.save_json(storage.history_path(), entries)
