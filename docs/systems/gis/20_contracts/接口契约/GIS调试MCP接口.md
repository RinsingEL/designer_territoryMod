# GIS 调试 MCP 接口契约

本文定义 GIS v1 基线的本地调试与验收接口。该接口服务于 agent 自动验收、现场复现和开发调试，不属于 G8 消费者查询接入，也不承诺生产级远程 API 兼容性。

## 边界

- Java 侧暴露本机 HTTP 接口，默认监听 `127.0.0.1:5000`。
- Node 侧 `country_designer_mcp` 通过 MCP 工具调用 HTTP 接口。
- 产物继续写入实现仓库运行目录下的 `run/gis_debug/<runId>/`。
- 接口返回调试统计和产物位置，不提供 City、Roads、Realm、Structure 的正式消费者查询。
- 轻量接口可用于测试复现；长期 SavedData、二进制持久层和生产级权限模型不在本契约范围。

## 环境变量

| 名称 | 默认值 | 说明 |
| --- | --- | --- |
| `GEOMANTIA_MC_API_URL` | `http://127.0.0.1:5000` | MCP 工具优先读取的 Java HTTP 根地址。 |
| `MC_API_URL` | `http://127.0.0.1:5000` | legacy 兼容环境变量，优先级低于 `GEOMANTIA_MC_API_URL`。 |

Java 侧端口可用 JVM system property `geomantia.apiPort` 覆盖。

## HTTP 接口

### `GET /gis/status`

读取本地 GIS 调试接口状态。

返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `ok` | boolean | 接口是否可用。 |
| `modId` | string | 固定为 `geomantia`。 |
| `api` | string | 固定为 `geomantia-gis-debug`。 |
| `serverDirectory` | string | 当前 MC server 运行目录。 |
| `debugRoot` | string | GIS 调试产物根目录。 |
| `players` | array | 在线玩家名、维度和方块坐标。 |

### `POST /gis/refresh`

执行一次真实 Minecraft 世界 GIS 半径刷新。未提供中心点时使用 `playerName` 指定玩家或首个在线玩家位置；无在线玩家时必须显式提供 `centerBlockX` 与 `centerBlockZ`。

请求字段：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `radiusChunks` | number | 否 | `8` | 刷新半径，范围 `1..64`。 |
| `sampleMode` | string | 否 | `prior` | `prior`、`observedIfLoaded`、`verifySurface`。 |
| `centerBlockX` | number | 条件 | - | 中心方块 X，需与 `centerBlockZ` 同时出现。 |
| `centerBlockZ` | number | 条件 | - | 中心方块 Z，需与 `centerBlockX` 同时出现。 |
| `dimensionId` | string | 否 | 玩家维度或主世界 | 例如 `minecraft:overworld`。 |
| `playerName` | string | 否 | 首个在线玩家 | 指定取中心和维度的玩家。 |

返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `ok` | boolean | `status == completed` 时为 true。 |
| `runId` | string | 刷新任务 ID。 |
| `status` | string | RefreshJob 状态契约名。 |
| `sampleMode` | string | 实际采样模式。 |
| `dimensionId` | string | 实际维度。 |
| `centerBlockX` / `centerBlockZ` | number | 实际中心点。 |
| `radiusChunks` | number | 实际刷新半径。 |
| `completedCells` / `totalCells` | number | 刷新进度统计。 |
| `runDirectory` | string | 绝对产物目录。 |
| `dirtyRegions` | array | 被标记脏区的 Region ID。 |
| `region` | object | Region ID、坐标、尺寸和状态摘要。 |
| `cellCounts` | object | AtlasCell 状态计数。 |
| `landformCounts` | object | 地貌类型计数。 |
| `patchCounts` | object | Patch 总量与最大 Patch cell 数。 |
| `artifacts` | object | `progress.png`、`progress_manifest.json`、`preview/preview_manifest.json` 相对路径。 |

### `POST /gis/test_run`

运行 GIS 合成验收用例。

请求字段：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `caseId` | string | 否 | `mixed` | `plain`、`mountain`、`water`、`mixed`。 |

返回字段沿用 `test_report.json`，并额外返回：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `ok` | boolean | 等同于 `passed`。 |
| `runDirectory` | string | 绝对产物目录。 |

## MCP 工具

| 工具 | HTTP 映射 | 说明 |
| --- | --- | --- |
| `gis_status` | `GET /gis/status` | 查询本地接口、debugRoot 和在线玩家。 |
| `gis_refresh` | `POST /gis/refresh` | 执行真实世界半径刷新。 |
| `gis_test_run` | `POST /gis/test_run` | 执行合成验收用例。 |

工具返回内容为格式化 JSON 文本，错误时返回 MCP `isError=true` 与 `Error: <message>`。

## 验收口径

- `gis_status` 能在 MC server 启动后返回 `ok=true`。
- `gis_test_run {"caseId":"mixed"}` 能返回 `ok=true`、`passed=true` 和 `runDirectory`。
- `gis_refresh {"radiusChunks":8,"sampleMode":"prior"}` 在有在线玩家时能返回 `ok=true`，并在 runDirectory 中生成 progress 与 preview manifest。
- 无在线玩家时，`gis_refresh` 必须显式传入 `centerBlockX` 与 `centerBlockZ`。
