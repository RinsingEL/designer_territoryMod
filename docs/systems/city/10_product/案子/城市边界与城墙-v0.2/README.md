# City 案子：城市边界与城墙 v0.2

## 状态

已完成实现并进入当前 City 城墙默认口径。v0.1 的 `actualFootprint` 外扩矩形墙只保留为 `wallVersion=v1_debug` 对照路径。

v0.2 的核心修正是把城墙拆成两个时序层：

```text
早期 wall reservation mask
  -> 负责占地、禁植被、禁自然结构
晚期 wall materialization
  -> 基于真实 RoadWeaver 道路裁门、放墙、放塔、做地形贴合
```

也就是说，城墙位置要尽早进入 mask，避免树、草和自然结构抢占；但城门不能在 RoadWeaver 道路真实生成前写死，必须等实际道路出来后再决定。v0.2 默认边界算法是 **D3 patch 贴边墙带**：沿结构 source patch / 邻接岸线、山脊、坡地、崖壁 patch 的外缘抽取多段 corridor，而不是生成一个长方形。

## 问题背景

v0.1 已完成：

- D7 ledger 完整后，根据真实 `actualFootprint` union 外扩生成临时矩形墙。
- 输出 `city_wall_plan.json`、`city_wall_preview.png`、`city_wall_templates/*.nbt`。
- 使用 `vanilla_setblock` 放置临时石墙 / 塔楼。

但真实测试暴露出两个关键问题：

- 城墙会覆盖 RoadWeaver 已生成道路，因为 v0.1 只按 footprint 外扩矩形放墙，不读取真实路面。
- 如果完全等 RoadWeaver 道路生成后才规划城墙，会错过生成期植被抑制时机，导致墙带仍可能被树、草或自然结构占用。

因此 v0.2 不应简单改成“城墙晚规划”，而应改成“墙带早规划，城门晚裁剪，墙体最后落地”。

## 目标流程

```text
D3 patch 真值 + D4 source patches + D6 locked structure plan
  -> 生成 D3 patch 贴边 wall reservation corridor
  -> city_plan_d5 把 wall corridor 合入 reservation mask
  -> city_execute_d5 激活 noVegetation / noVanillaStructure mask
  -> RoadWeaver 在 chunk 首次生成时生成真实道路
  -> city_execute_d7 收集 structure ledger / road provider state
  -> city_plan_city_walls_v2 扫描 actual road mask，与 wall corridor 求交
  -> 生成 gate / tower / wall final plan
  -> city_execute_city_walls_v2 放置墙体并做基础地形贴合
```

## Key Changes

### 1. Wall Reservation Mask 前置

在 D5 之前或 D5 阶段增加 `wallReservationPlan`：

- 输入 D3 `city_landform_review_package.json`、D4 anchor 的 `sourcePatchIds`、D6 locked `actualFootprint` / `lockedCollisionEnvelope`。
- 默认从结构 source patch 与邻接边界 patch 抽取 patch union 外缘，生成非矩形、多段 `wallCorridorMask`。
- 输出墙带中心线、墙带厚度、塔楼候选点、潜在 gate candidate 区域。
- `wallCorridorMask` 必须合入：
  - `noVegetationMask`
  - `vegetationLimitedMask`
  - `noVanillaStructureMask`

注意：这一阶段只预留墙带，不放墙，不决定最终城门。若 D3 patch 信息不足，`wallVersion=v2` 应报告 `WALL_PATCH_BOUNDARY_UNAVAILABLE`；调试时可显式传 `wallVersion=v1_debug` 使用 v0.1 矩形墙。

### 2. Road Mask 后置扫描

RoadWeaver 真实道路生成后，`city_plan_city_walls` 需要读取世界中的实际道路方块，而不是只读取 RoadWeaver connection plan。

扫描范围默认是：

- `wallCorridorMask` 外扩若干格。
- 城市结构 union 到墙带之间的道路连接区域。

输出 `actualRoadMask`：

- road block positions / compact rectangles。
- road width estimate。
- road-wall intersections。
- road near-wall segments。

道路识别首版可以基于 block whitelist：

- dirt path
- gravel
- cobblestone
- stone / andesite / packed mud 等 RoadWeaver 常见道路材料

后续可改成 RoadWeaver API 或 tag 驱动。

### 3. 城门由 road-wall intersection 生成

墙线与 `actualRoadMask` 求交后：

- 道路正交穿墙：生成 `gate_gap_7/9/11`。
- 道路较宽：按 road width 自动扩大 gate。
- 道路斜穿墙：把交点附近多个 wall segment 合并成一个门洞。
- 道路贴墙平行：不直接开门，标记为 `WALL_ROAD_TOO_CLOSE`，优先外推墙线或跳过该段。

每个 gate 输出：

- `gateId`
- `sourceRoadMaskId`
- `gateCenter`
- `gateWidthBlocks`
- `gateOrientation`
- `flankingTowerIds`
- `reasonCode=ROAD_WALL_INTERSECTION`

### 4. 墙体最终放置时保护道路

`city_execute_city_walls` 执行时必须把道路当成硬保护区：

- 不覆盖 `actualRoadMask`。
- 不覆盖 gate gap。
- 不覆盖 placed structure `actualFootprint`。
- 如果墙体模板与道路发生冲突，优先：
  1. 裁成 gate。
  2. 外推墙段。
  3. 跳过墙段并报告。

新增 reason code：

```text
WALL_GATE_FROM_ROAD
WALL_ROAD_PROTECTED
WALL_ROAD_TOO_CLOSE_SKIP
WALL_SEGMENT_SHIFTED_FOR_ROAD
```

### 5. 基础地形贴合

v0.2 不追求完整城墙地形系统，但需要比 v0.1 更像“落地”：

- 低洼处向下补 foundation，直到接触实体地面或达到最大深度。
- 小起伏允许墙基随地形阶梯。
- 山体 / 斜坡相交时允许墙体嵌入山体，不强行清空整座山。
- 单段高差过大时仍可跳过，但报告要区分：
  - `WALL_TERRAIN_TOO_STEEP`
  - `WALL_FOUNDATION_TOO_DEEP`
  - `WALL_EMBEDDED_IN_SLOPE`

默认参数：

```text
wallCorridorHalfWidthBlocks = 4
gateWidthBlocks = 9
roadProtectionMarginBlocks = 2
maxFoundationDepthBlocks = 8
maxSegmentHeightDeltaBlocks = 7
```

## Artifacts

新增或升级：

- `wall_reservation_plan.json`
- `wall_reservation_preview.png`
- `actual_road_mask.json`
- `city_wall_plan.json`
- `city_wall_preview.png`
- `city_wall_placement_report.json`

`wall_reservation_plan.json` 至少包含：

- `schemaVersion=city_wall_reservation_plan.v0.2`
- `boundarySource=d3_patch_member_cell_outer_boundary` 或 `v1_debug_anchor_rectangle`
- `wallCorridorMask[]`
- `wallCenterline[]`
- `towerCandidatePoints[]`
- `gateCandidateZones[]`
- `maskContribution`

`city_wall_plan.json` 升级为：

- `schemaVersion=city_wall_plan.v0.2`
- `wallPlanningMode=reservation_then_road_gate_cut`
- `wallReservationSource`
- `roadMaskSource=actual_world_blocks`
- `wallRoadIntersections[]`
- `generatedGates[]`
- `wallSegments[]`
- `roadProtectionMarginBlocks`
- `terrainFitPolicy`

## 接口口径

首版可复用现有入口名，避免 MCP 大面积改动：

- `city_plan_d5`：合入 wall reservation mask。
- `city_plan_city_walls`：升级为 v2 plan，读取 D7 ledger + actual road mask。
- `city_execute_city_walls`：执行 v2 plan。

可选参数：

```json
{
  "wallVersion": "v2",
  "wallCorridorHalfWidthBlocks": 4,
  "wallMarginBlocks": 24,
  "segmentLengthBlocks": 15,
  "gateWidthBlocks": 9,
  "roadProtectionMarginBlocks": 2,
  "maxFoundationDepthBlocks": 8,
  "maxSegmentHeightDeltaBlocks": 7
}
```

如果 `wallVersion` 缺省，当前开发期可以默认 v2；若需要保留 v0.1 对照，可允许 `wallVersion=v1_debug`。

## 验收标准

- D5 mask 中能看到 wall corridor 进入 noVegetation / noVanillaStructure。
- RoadWeaver 道路生成后，`actual_road_mask.json` 能识别真实路面。
- 城墙与道路相交处生成 gate，而不是覆盖道路。
- 城墙执行不会覆盖 `actualRoadMask`。
- gate 两侧有塔楼或至少有明确门洞边界。
- 墙段不压结构 `actualFootprint`。
- 墙带来自 D3 patch 外缘，预览图中应明显不是单纯矩形外框；除非显式 `wallVersion=v1_debug`。
- 低洼处有 foundation，轻微坡地能贴合。
- 陡坡 / 山体段的跳过或嵌入原因写入 report。
- preview 同时显示：
  - structure footprint
  - wall corridor
  - actual road mask
  - generated gates
  - skipped / shifted wall segments

## Test Plan

自动测试：

- D5：wall corridor 合入 reservation mask。
- planner：road mask 与 wall segment 求交后生成 gate。
- planner：平行贴墙道路触发 `WALL_ROAD_TOO_CLOSE_SKIP` 或外推。
- executor：wall placement 不覆盖 road mask。
- executor：foundation 能向下补齐，超过深度时报告 `WALL_FOUNDATION_TOO_DEEP`。
- preview：能渲染 road mask / gate / wall corridor。

真实测试：

```text
D3
-> envelope profiling
-> D4 candidates / selection
-> D6 probe-and-lock
-> D5 reservation with D3 patch wall corridor
-> execute_d5 注册结构 + RoadWeaver + mask
-> 玩家加载新区块
-> D7 ledger
-> plan city walls v2
-> execute city walls v2
```

验收时重点观察：

- RoadWeaver 路穿墙处是否变成城门。
- 城墙是否仍砍断道路。
- 城墙带是否有树穿墙。
- 墙体遇到山坡 / 凹陷时是否比 v0.1 更自然。

## 暂不处理

- 不做最终美术级城门楼。
- 不做完整曲线城墙算法；首版 patch 贴边可用 memberCells / patch bounds 抽外缘。
- 不做护城河。
- 不做城墙巡逻 AI / 防御玩法。
- 不接 RoadWeaver 内部图数据，只先扫描世界真实道路方块。

## 后续方向

- 城门模板升级为完整门楼。
- 根据 D3 山脊 / 水岸 / 崖壁继续优化非矩形边界的转角、平滑和视觉节奏。
- 城墙风格与 City 结构风格化换皮联动。
- 用 RoadWeaver 或第三方道路 API 直接取得道路 graph，而不是扫描方块。
- 增加城墙破损、木栅栏、码头防波堤、农田篱笆等边界类型。
