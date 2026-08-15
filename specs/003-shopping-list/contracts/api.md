# 页面 API 契约：购物清单（shopping-list）

**日期**: 2026-08-15 | **规格**: [spec.md](../spec.md) | **数据模型**: [data-model.md](../data-model.md)

本文件定义 `recipe serve` 服务中购物清单相关 HTTP 端点。与 002 功能既有端点共享同一约定（仅监听 127.0.0.1、JSON 响应、`DataError` 转 HTTP 400、写操作串行化——本功能无写操作）。

## 通用约定

- **Base URL**: `http://127.0.0.1:<随机端口>/`
- **内容类型**: 请求与响应均为 `application/json; charset=utf-8`
- **错误语义**: 核心模块抛出的 `DataError` 统一转为 HTTP 400，响应体 `{ "ok": false, "error": "中文错误信息" }`
- **成功响应**: `{ "ok": true, "data": { ... } }`

## 端点

### GET `/api/shopping-list` — 购物清单

只读端点，实时聚合指定时间窗口内已安排菜的食材，返回与 CLI `recipe shopping-list` 完全一致的结果。

**查询参数**（均可选）：

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `days` | int | 7 | 聚合窗口天数（含今日）；等价 CLI `--days` |
| `merge` | bool | `true` | 是否去重合并同一食材；`false` 等价 CLI `--no-merge` |

**响应 data**:

```json
{
  "windowDays": 7,
  "items": [
    { "ingredient": "番茄", "sources": ["番茄牛腩", "番茄炒蛋"] },
    { "ingredient": "牛腩", "sources": ["番茄牛腩"] }
  ],
  "skippedRecipes": [],
  "empty": false
}
```

- `items` 已按 `ingredient` 排序（服务端排序，页面不做二次排序）。
- `skippedRecipes` 列出因不在食谱库或食材非法而被跳过的菜名；为空数组表示无跳过。
- `empty` 为 `true` 时 `items` 为空数组，页面展示空态提示（与 CLI 一致）。

**错误示例**:

```json
{ "ok": false, "error": "days 必须是正整数，当前为 0" }
```

**状态流转**: 纯只读，无状态变更；与页面「购物清单」区域加载 / 刷新动作对应。页面任一方修改数据（如新增今日确认）后刷新本端点即可获得最新清单。

## 与 CLI 的一致性

| CLI 参数 | API 参数 | 语义 |
|----------|----------|------|
| `--days N` | `days=N` | 窗口天数 |
| `--today` | `days=1` | 仅今日 |
| `--no-merge` | `merge=false` | 不合并重复食材 |
| 无 | — | 默认 7 天 + 合并去重 |
