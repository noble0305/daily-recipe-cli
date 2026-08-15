# 页面 API 契约：recipe-web-ui

**日期**: 2026-08-15 | **规格**: [spec.md](../spec.md) | **数据模型**: [data-model.md](../data-model.md)

本文件定义 `recipe serve` 一次性本地服务对外暴露的 HTTP API。所有端点仅监听 `127.0.0.1` 回环地址，完全离线。

## 通用约定

- **Base URL**: `http://127.0.0.1:<随机端口>/`（端口由服务启动时随机分配）
- **内容类型**: 请求与响应均为 `application/json; charset=utf-8`（`/` 首页除外，为 HTML）
- **错误语义**: 核心模块抛出的 `DataError` 统一转为 HTTP 400，响应体：
  ```json
  { "ok": false, "error": "中文错误信息（含字段/位置）" }
  ```
- **成功响应**: `{ "ok": true, "data": { ... } }`
- **写并发**: 服务端用 `threading.Lock` 串行化写操作；写入沿用原子语义（先 `.tmp` 再 `os.replace()`）

## 端点

### GET `/` — 页面入口

返回单页 HTML（渲染层，零业务逻辑）。页面加载后调用 `GET /api/state` 渲染初始状态。

### GET `/api/state` — 聚合状态

**响应 data**:

```json
{
  "today": {
    "decided": false,
    "decidedRecipe": null,
    "candidates": null,
    "reason": null
  },
  "recipes": [ { "name": "番茄牛腩", "ingredients": ["牛腩", "番茄"], "tags": ["荤"], "note": "..." } ],
  "historyDays": 30
}
```

- `today.candidates` 仅在页面点击「今日推荐」后由 `POST /api/today` 填充，state 中为 null。
- `recipes` 为完整食谱库（页面端做标签筛选渲染）。

### POST `/api/today` — 今日推荐 / 确认 / 重推

**请求 data**:

```json
{ "action": "recommend", "tags": ["荤"], "days": 7, "count": 3, "seed": null }
```

| action | 必填 | 可选 | 行为 |
|---|---|---|---|
| `recommend` | — | `tags` / `days` / `count` / `seed` | 生成候选，等价 CLI `recipe today --tags ... --days ... --count ... --seed ...`；今日已确定时返回提示与 `forceAvailable: true` |
| `confirm` | `choice`（int，候选序号从 1 开始） | — | 确认选择，写历史（source=`today`）；越界返回 400 中文错误 |
| `force` | — | `tags` / `days` / `count` / `seed` | 今日已确定时强行重推（覆盖当日旧记录），等价 `--force` |

**推荐响应 data**: `{ "candidates": [Recipe], "reason": "避开最近 7 天", "forceAvailable": false }`
**确认响应 data**: `{ "decided": true, "decidedRecipe": "番茄牛腩" }`

### POST `/api/week` — 周计划预览 / 写入

**请求 data**:

```json
{ "action": "preview", "tags": ["荤"], "days": 7, "seed": null }
```

| action | 必填 | 可选 | 行为 |
|---|---|---|---|
| `preview` | — | `tags` / `days` / `seed` | 生成预览（不写入），等价 CLI `recipe week` 的确认前阶段 |
| `confirm` | — | — | 写入 5 天菜单到历史（source=`week`），等价确认；候选不足时 400 中文错误且不写入 |

**预览响应 data**: `{ "days": [{ "date": "2026-08-17", "recipe": "番茄牛腩" }], "conflictCount": 0 }`
**写入响应 data**: `{ "ok": true, "written": 5 }`

### POST `/api/add` — 添加食谱

**请求 data**: `{ "name": "番茄牛腩", "ingredients": ["牛腩", "番茄"], "tags": ["荤"], "note": "..." }`

**响应 data**: `{ "recipe": { ...新建的食谱 } }`；重名时 400「已存在」中文错误。

### POST `/api/remove` — 删除食谱

**请求 data**: `{ "name": "番茄牛腩" }`

**响应 data**: `{ "removed": "番茄牛腩" }`；不存在时 400 中文错误；不影响历史记录。

### GET `/api/history?days=N` — 历史查询

**参数**: `days`（默认 30，正整数）

**响应 data**:

```json
{ "records": [ { "date": "2026-08-15", "recipe": "番茄牛腩", "source": "today" } ], "rangeDays": 30 }
```

按日期倒序；`source` 标注来源（`today` 单日推荐 / `week` 周计划）。

### POST `/api/bye` — 用完即停

**请求 data**: `{}`

**行为**: 服务端收到后关闭 HTTP 服务并退出进程（页面 `pagehide` / `navigator.sendBeacon` 触发）。另设 10 分钟空闲超时兜底 + 终端 Ctrl+C。

**响应 data**: `{ "bye": true }`（尽力返回，进程随即退出）

## 错误示例

```json
// GET /api/state 时数据文件损坏
HTTP 400
{ "ok": false, "error": "食谱库格式错误：第 2 条缺少有效的「菜名」" }

// 确认越界序号
HTTP 400
{ "ok": false, "error": "序号无效：请输入 1 到 3 之间的数字" }
```

## 安全与边界

- 仅监听 `127.0.0.1`，不绑定局域网地址；不提供任何跨域头（同源页面访问）。
- 服务进程随用随起、用完即停；无数据离开本机。
- 页面渲染层不含业务逻辑；所有校验/推荐/写回均经服务端核心模块。
