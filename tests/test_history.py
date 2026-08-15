"""历史记录测试：写入/读取、当日已确定、同日期覆盖。"""

from __future__ import annotations

import pytest

from daily_recipe_cli import history, storage


@pytest.fixture()
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("RECIPE_CLI_DIR", str(tmp_path))
    return tmp_path


def test_decided_for_date_returns_none_when_empty(data_dir):
    assert history.decided_for_date("2026-08-15") is None


def test_add_then_decided(data_dir):
    history.add("2026-08-15", "番茄牛腩", source="today")
    assert history.decided_for_date("2026-08-15") == "番茄牛腩"
    assert storage.load_history()[0]["source"] == "today"


def test_add_replaces_same_date(data_dir):
    history.add("2026-08-15", "A", source="today")
    history.add("2026-08-15", "B", source="today")
    entries = storage.load_history()
    assert len(entries) == 1
    assert entries[0]["recipe"] == "B"


def test_add_keeps_multiple_dates_sorted_load(data_dir):
    history.add("2026-08-15", "A", source="today")
    history.add("2026-08-14", "B", source="week")
    entries = storage.load_history()
    assert len(entries) == 2
    assert {e["recipe"] for e in entries} == {"A", "B"}


def test_history_persists_across_reload(data_dir):
    history.add("2026-08-15", "A", source="today")
    assert history.decided_for_date("2026-08-15") == "A"
    # 再次读取仍是同一结果（落盘）
    assert history.decided_for_date("2026-08-15") == "A"
