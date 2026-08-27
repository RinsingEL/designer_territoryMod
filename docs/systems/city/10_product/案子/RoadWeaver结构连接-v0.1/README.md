# City 案子：RoadWeaver 结构连接 v0.1

## 状态

已完成 v0.1 optional adapter 接入。旧 v0.2 的自动长距 placement group 最小生成树已被《City城市基面与路网形态-v0.1》废止；适配器只能消费 Blueprint 另行确认的外部长距真实交通连接。

本案只定义生成期 RoadWeaver optional adapter。City 区内路、城市主路和城区桥梁由 D4/SurfacePrint 自己负责；RoadWeaver 不得根据 placement group、功能区关系或距离自行决定连接。缺 RoadWeaver 只跳过明确委托给它的外部长距道路，不影响 City 自有道路。

## 当前口径

- RoadWeaver 是可选长距依赖，不是 mandatory mod；只接收两端均为真实道路出口、且 Blueprint 已显式确认的外部长距连接，不生成 placement group 内道路，不做自动组间连线。
- 当前开发验收固定验证 Forge `2.3.0-1.20.1`；City 仍只经反射调用 API，升级后必须复核 `RoadNetworkApi.registerStructureEndpoint` 与 `ensureConnection` 签名。
- 开发运行标准启动不再加载 RTF / ReTerraForged，只启用结构包和 RoadWeaver：`.\gradlew.bat runClient -PgeomantiaDevUseStructurePacks=true -PgeomantiaDevUseRoadWeaver=true`。
- Java 端通过 `ModList` + 反射调用 `net.shiroha233.roadweaver.api.RoadNetworkApi`，避免缺 mod 时类加载崩溃。
- `city_execute_d5` 是 RoadWeaver 注册点，必须发生在目标 chunk 首次生成前。
- endpoint 和 MCP 新增 `roadProvider=auto|roadweaver|worldedit_debug|none`：
  - `auto`：RoadWeaver 存在则注册 RoadWeaver；缺失则跳过道路，记录 `status=skipped` / `reasonCode=ROADWEAVER_UNAVAILABLE` / `useWorldEditDebugFallback=false`。
  - `roadweaver`：RoadWeaver 缺失时 hard fail `ROADWEAVER_UNAVAILABLE`。
  - `worldedit_debug`：显式走 D7 WorldEdit 调试道路。
- `none`：禁用道路生成。
- 实机道路验收把 `run/config/roadweaver/roadweaver.json` 的 `roadAppearance.roadsEnabled=true`；同时固定 `spawnCabinEnabled=false`、`roadsideStructure.enabled=false`，避免 RoadWeaver 在道路附近额外生成小屋或 roadside 结构干扰 City 结构 / 道路验收。

## 当前流程

```text
D6 locked plan
  -> lockedActualFootprint / priority
  -> city_execute_d5
  -> roadweaver_connection_plan.json
  -> 读取 Blueprint 显式确认的外部长距道路意图
  -> 校验两端真实目的地、冻结入口和正式道路出口
  -> 未确认连接保持 connectionCount=0
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

当前只输出最小可用连接：

- `anchorId`
- `templateRef`
- `templateHash`
- `variant`
- `rotation`
- `mirror`
- `priority`
- `lockedActualFootprint` / `footprint`
- `roadEntrances[]`：模板局部入口经 rotation / mirror 变换后的世界入口，至少包含 `entranceId`、`worldPosition`、`direction`
- `placementGroupId`
- 显式道路意图标识、两端真实目的地与冻结道路出口；缺少任一项时不得形成连接
- `delegatedToCityMainRoad`：城区道路或桥梁已由 City 接管时为 true，此时 RoadWeaver `connectionCount=0`
- 每条连接的 `distanceBlocks`、两端 group / anchor / endpoint
- `generateImmediately=false`

后续可扩展：

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
- 没有显式道路意图时 `connectionCount=0`；不得再按 priority、anchorId、最近距离或最小生成树把功能区串链。

## 暂不处理

- 不实现 RoadWeaver 本体。
- 不保证 RoadWeaver 最终道路美术符合 City 设计风格。
- 不做 RoadWeaver non-mutating preview。
- 不处理 RoadWeaver 已加载 chunk 无法补路的问题；该限制由“D5 生成期注册”规避。
