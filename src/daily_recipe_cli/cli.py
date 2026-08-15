"""命令行入口：argparse 子命令注册与分发（薄层，不含业务逻辑）。

命令：today / week / add / list / remove / history
所有 DataError 在 main 统一转为中文错误输出并返回非零退出码。
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta

from daily_recipe_cli import history, recipes as recipes_mod, recommend, storage
from daily_recipe_cli.storage import DataError

_WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="recipe",
        description="每日带饭食谱推荐命令行工具",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_today = sub.add_parser("today", help="推荐今天的候选菜，或确认某个候选")
    p_today.add_argument("choice", nargs="?", type=int, metavar="序号", help="确认第几个候选（如 1）")
    p_today.add_argument("--tags", nargs="+", metavar="标签", help="按标签过滤（可多个，须同时满足）")
    p_today.add_argument("--count", type=int, default=3, metavar="N", help="候选数量（默认 3）")
    p_today.add_argument("--days", type=int, default=7, metavar="N", help="去重窗口天数（默认 7）")
    p_today.add_argument("--seed", metavar="S", help="随机种子（默认按当天日期）")
    p_today.add_argument("--force", action="store_true", help="今日已确定时强行重新推荐")

    p_week = sub.add_parser("week", help="规划未来 5 个工作日的带饭菜单")
    p_week.add_argument("--tags", nargs="+", metavar="标签", help="按标签过滤（可多个）")
    p_week.add_argument("--days", type=int, default=7, metavar="N", help="去重窗口天数（默认 7）")
    p_week.add_argument("--seed", metavar="S", help="随机种子")
    p_week.add_argument("--yes", action="store_true", help="跳过确认，直接写入历史")

    p_list = sub.add_parser("list", help="查看食谱库")
    p_list.add_argument("--tags", nargs="+", metavar="标签", help="按标签过滤")

    p_add = sub.add_parser("add", help="添加食谱")
    p_add.add_argument("name", metavar="菜名", help="菜名")
    p_add.add_argument("--ingredients", nargs="+", required=True, metavar="食材", help="主要食材")
    p_add.add_argument("--tags", nargs="+", required=True, metavar="标签", help="标签（如 荤 快手）")
    p_add.add_argument("--note", default="", metavar="做法", help="一句话做法")

    p_remove = sub.add_parser("remove", help="删除食谱（不影响历史记录）")
    p_remove.add_argument("name", metavar="菜名", help="要删除的菜名")

    p_history = sub.add_parser("history", help="查看吃过的历史")
    p_history.add_argument("--days", type=int, default=30, metavar="N", help="显示最近 N 天（默认 30）")

    return parser


def _cmd_today(args: argparse.Namespace) -> int:
    today = date.today().isoformat()
    decided = history.decided_for_date(today)
    if decided and not args.force:
        print(f"今日已确定：{decided}（如需更换请使用 recipe today --force）")
        return 0

    cands, widened = recommend.candidates(
        storage.load_recipes(),
        storage.load_history(),
        date.today(),
        tags=args.tags,
        days=args.days,
        count=args.count,
        seed=args.seed,
    )

    if args.choice is not None:
        if args.choice < 1 or args.choice > len(cands):
            print(f"无效选择：当前有 {len(cands)} 个候选，没有第 {args.choice} 个", file=sys.stderr)
            return 1
        chosen = cands[args.choice - 1]
        history.add(today, chosen["name"], source="today")
        print(f"已确定今天带饭：{chosen['name']}")
        return 0

    if not cands:
        total = len(storage.load_recipes())
        if total == 0:
            print("食谱库为空：请先使用 recipe add 添加菜谱")
        elif args.tags:
            print(
                f"可选菜不足：当前过滤条件下没有可用菜"
                f"（全库共 {total} 道，可减少 --tags 或 recipe add 添加新菜）"
            )
        else:
            print(
                "可选菜不足：近期吃过的菜较多，已无可选新菜"
                "（可 recipe add 添加新菜，或 --days 缩短去重窗口）"
            )
        return 0

    hint = "（已放宽去重窗口，近期吃过的菜也可能出现）" if widened else ""
    print(f"今日候选（避开最近 {args.days} 天已选）{hint}：")
    for i, r in enumerate(cands, 1):
        _print_recipe(i, r)
    print("确认：recipe today 1（选中第 1 个）")
    return 0


def _cmd_week(args: argparse.Namespace) -> int:
    today = date.today()
    plan, relaxed = recommend.week_plan(
        storage.load_recipes(),
        storage.load_history(),
        today,
        tags=args.tags,
        days=args.days,
        seed=args.seed,
    )
    hint = "（已放宽去重窗口）" if relaxed else ""
    print(f"下周带饭计划（5 个工作日）{hint}：")
    for i, (d, r) in enumerate(plan):
        label = _WEEKDAY_NAMES[i]
        if r is None:
            print(f"  {d} {label}：无可用菜")
        else:
            print(f"  {d} {label}：{r['name']}")

    filled = [(d, r) for d, r in plan if r is not None]
    if not filled:
        print("食谱库为空或过滤条件下无可用菜，无法生成计划。")
        return 0
    if not args.yes:
        try:
            answer = input("确认写入历史？[y/N] ").strip().lower()
        except EOFError:
            answer = ""
        if answer not in ("y", "yes"):
            print("已取消，未写入历史。")
            return 0
    for d, r in filled:
        history.add(d.isoformat(), r["name"], source="week")
    print(f"已写入 {len(filled)} 天的计划到历史。")
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    filtered = recipes_mod.filter_by_tags(storage.load_recipes(), args.tags or [])
    for r in filtered:
        print(
            f"{r['name']} [{'、'.join(r['tags'])}]：{'、'.join(r['ingredients'])}"
            + (f"；{r['note']}" if r.get("note") else "")
        )
    print(f"共 {len(filtered)} 道" + ("（已按标签过滤）" if args.tags else ""))
    return 0


def _cmd_add(args: argparse.Namespace) -> int:
    recipes_mod.add(args.name, args.ingredients, args.tags, args.note)
    print(f"已添加食谱：{args.name.strip()}")
    return 0


def _cmd_remove(args: argparse.Namespace) -> int:
    target = recipes_mod.remove(args.name)
    if target is None:
        print(f"未找到食谱：{args.name}", file=sys.stderr)
        return 1
    print(f"已删除食谱：{target['name']}（历史记录不受影响）")
    return 0


def _cmd_history(args: argparse.Namespace) -> int:
    entries = storage.load_history()
    cutoff = date.today() - timedelta(days=args.days)
    shown = sorted(
        (e for e in entries if date.fromisoformat(e["date"]) >= cutoff),
        key=lambda e: e["date"],
    )
    if not shown:
        print("暂无历史记录")
        return 0
    for e in shown:
        suffix = "（周计划）" if e["source"] == "week" else ""
        print(f"{e['date']}：{e['recipe']}{suffix}")
    return 0


def _print_recipe(index: int, r: dict) -> None:
    print(f"{index}. {r['name']} [{'、'.join(r['tags'])}]")
    print(f"   食材：{'、'.join(r['ingredients'])}" + (f"；做法：{r['note']}" if r.get("note") else ""))


_HANDLERS = {
    "today": _cmd_today,
    "week": _cmd_week,
    "list": _cmd_list,
    "add": _cmd_add,
    "remove": _cmd_remove,
    "history": _cmd_history,
}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return _HANDLERS[args.command](args)
    except DataError as e:
        print(f"错误：{e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
