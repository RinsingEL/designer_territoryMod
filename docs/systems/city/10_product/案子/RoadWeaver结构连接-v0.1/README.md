# City 案子：RoadWeaver 结构连接 v0.1

## 状态

已完成 v0.1 接入并并入当前 City 主线。

本案把“结构之间的正式道路连接”从 D7 WorldEdit 调试后处理，迁移到生成期 RoadWeaver optional adapter。City 不强绑 RoadWeaver；缺少 RoadWeaver 且 `roadProvider=auto` 时跳过道路并写明 `ROADWEAVER_UNAVAILABLE`，不再自动铺 WorldEdit debug fallback。旧 debug 道路只允许通过 `roadProvider=worldedit_debug` 显式启用。

## 当前口径

- RoadWeaver 是可选依赖，不是 mandatory mod。
- 开发运行标准启动不再加载 RTF / ReTerraForged，只启用结构包和 RoadWeaver：`.\gradlew.bat runClient -PgeomantiaDevUseStructurePacks=true -PgeomantiaDevUseRoadWeaver=true`。
- Java 端通过 `ModList` + 反射调用 `net.shiroha233.roadweaver.api.RoadNetworkApi`，避免缺 mod 时类加载崩溃。
- `city_execute_d5` 是 RoadWeaver 注册点，必须发生在目标 chunk 首次生成前。
- endpoint 和 MCP 新增 `roadProvider=auto|roadweaver|worldedit_debug|none`：
  - `auto`：RoadWeaver 存在则注册 RoadWeaver；缺失则跳过道路，记录 `status=skipped` / `reasonCode=ROADWEAVER_UNAVAILABLE` / `useWorldEditDebugFallback=false`。
  - `roadweaver`：RoadWeaver 缺失时 hard fail `ROADWEAVER_UNAVAILABLE`。
  - `worldedit_debug`：显式走 D7 WorldEdit 调试道路。
  - `none`：禁用道路生成。

## 当前流程

```text
D6 locked plan
  -> lockedActualFootprint / priority
  -> city_execute_d5
  -> roadweaver_connection_plan.json
  -> RoadNetworkApi.registerStructureEndpoint(...)
  -> RoadNetworkApi.ensureConnection(..., generateImmediately=false)
  -> chunk 首次生成时由 RoadWeaver 自己生成道路
  -> city_execute_d7 只查询 ledger，不覆盖 RoadWeaver 结果
```

## 当前 artifacts

`city_execute_d5` 新增：

- `roadweaver_connection_plan.json`
- `roadweaver_registration_report.json`
- `road_provider_state.json`

`road_provider_state.json` 至少说明：

- `roadProvider`
- `roadWeaverRegistered`
- `useWorldEditDebugFallback`
- `roadWeaverAvailable`
- `reasonCode`

## City 输出给 RoadWeaver 的信息

v0.1 只输出最小可用连接：

- `anchorId`
- `structureId`
- `priority`
- `lockedActualFootprint`
- `roadPoint`
- connection chain
- `generateImmediately=false`

后续可扩展：

- entrance candidates
- roadAccessIntent
- D3 坡度 / 水岸 / 禁行区域
- actual footprint avoidance
- bridge / shore policy
- road style palette

## 验收

- 缺 RoadWeaver 时 `roadProvider=auto` 不崩溃、不生成旧 debug 道路，state / trace 标记 `skipped`、`ROADWEAVER_UNAVAILABLE` 和 `useWorldEditDebugFallback=false`。
- 缺 RoadWeaver 时 `roadProvider=roadweaver` hard fail `ROADWEAVER_UNAVAILABLE`。
- 只有显式 `roadProvider=worldedit_debug` 时，D7 才允许生成旧 WorldEdit 调试道路。
- RoadWeaver 注册发生在 `city_execute_d5`，早于目标 chunk 首次生成。
- RoadWeaver 模式下 D7 不再默认生成 WorldEdit road operation。
- `roadweaver_connection_plan.json` 能解释哪些结构被连接、连接顺序和端点。

## 暂不处理

- 不实现 RoadWeaver 本体。
- 不保证 RoadWeaver 最终道路美术符合 City 设计风格。
- 不做 RoadWeaver non-mutating preview。
- 不处理 RoadWeaver 已加载 chunk 无法补路的问题；该限制由“D5 生成期注册”规避。

## 后续方向

- 从结构 profile 中读取入口候选，而不是只用 bbox 外侧点。
- 把 D3 坡度、水岸、桥梁意图交给 RoadWeaver 或 adapter。
- 道路 style / palette 与后续 City 结构风格化换皮联动。
