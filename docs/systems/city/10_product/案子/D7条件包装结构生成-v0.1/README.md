# City D7 案子：剩余结构条件包装生成

## 定位

D7 只负责真实结构生成。

D7 不重新选择固定大小结构，不重新选择固定结构落点，不让 AI 解 jigsaw。它读取 D6 的固定落点计划和剩余比例预算，然后执行：

```text
PlannedFixedPlacementMap
  -> 完整放置 fixed_footprint
  -> 扣除占用
StructurePoolMap
  -> 程序生成 StartCandidateSet
  -> seeded weighted random 选择起点
  -> 按剩余可见面积比例生成 variable_area
  -> 条件包装 validator
  -> configured structure 执行（/place structure 等价入口）
  -> trace
```

## 输入与输出

| 方向 | 输入 / 输出 | 说明 |
| --- | --- | --- |
| 输入 | `PlannedFixedPlacementMap` | D6 选定并校验过的固定结构落点。 |
| 输入 | `StructurePoolMap` | D6 输出的非固定结构菜单、权重和目标可见面积占比。 |
| 输入 | `FunctionZoneMap` | 功能区边界和类型。 |
| 输入 | `BuildableAreaMap` | D5 可建区。 |
| 输入 | `RoadIntent` / `BoundaryIntent` | 道路、边界、水岸和保留区。 |
| 运行时产物 | `StartCandidateSet` | D7 程序为 `variable_area` 生成的候选起点集合。 |
| 输出 | `PlacedStructureMap` | 已放置结构和占用 footprint。 |
| 输出 | `StructureGenerationTrace` | 成功、失败、跳过和重试记录。 |

## 阶段边界

| D7 做 | D7 不做 |
| --- | --- |
| 优先完整放置 D6 选定的 `fixed_footprint`。 | 不为固定结构重新选点。 |
| 对固定结构做最终兜底 validator。 | 不裁切固定结构，不补半截，不收尾。 |
| 扣除固定结构占用后，按剩余面积生成 `variable_area`。 | 不让 AI 配 jigsaw 深度、半径或 piece budget。 |
| 程序生成剩余结构起点候选并 seeded weighted random 抽选。 | 不让 AI 选择剩余结构坐标，不在功能区内盲随机坐标。 |
| 用条件包装限制 configured structure 能否落下。 | 不把功能区边缘随机失败当主流程。 |
| D7 真实放置使用 `/place structure` 等价入口。 | 不把 NBT template 路径或 jigsaw pool ID 当作真实 `structureId`。 |
| 对可变 jigsaw 分支做停止、少生成或收尾。 | 不要求可变结构必须长满。 |
| 输出失败 trace。 | 不静默吞掉失败。 |

## 固定结构放置

固定结构来自 `PlannedFixedPlacementMap`。

硬规则：

- D7 必须先处理固定结构。
- 固定结构只能完整放置或失败。
- D7 不允许裁掉固定结构的一角。
- D7 不允许对固定结构做 jigsaw 分支停止 / 收尾。
- 固定结构失败后按 D6 的 `failurePolicy` 处理。

最终兜底 validator 只确认 D6 计划在真实生成上下文中仍可用：

| 条件 | 说明 |
| --- | --- |
| `FixedCandidateStillValid` | `landingCandidateId` 和结构画像仍匹配。 |
| `FootprintStillInsideZone` | footprint 仍在功能区可建范围内。 |
| `NoRoadOrReservedConflict` | 不压道路、hard reserved、边界缓冲。 |
| `NoAabbConflict` | 不与已放置结构冲突。 |
| `TerrainStillAcceptable` | 真实高度、水体和坡度未突破阈值。 |

如果固定结构失败：

| `failurePolicy` | 处理 |
| --- | --- |
| `block_city` | D7 失败，城市结构生成停止。 |
| `degrade` | 只允许使用 D6 已声明的 fallback 结构或让本轮 partial。 |
| `skip_with_warning` | 跳过并记录 warning。 |

## 剩余结构生成

固定结构处理后，D7 计算每个功能区的剩余可见面积：

```text
remainingVisibleArea = D5 buildable area
  - placed fixed_footprint visibleAreaCost
  - fixed clearance
  - runtime occupied footprint
```

`variable_area` 结构按 D6 的 `targetVisibleAreaRatio` 在剩余可见面积内生成。D7 负责把比例翻译成生成任务和重试预算。

首版口径：

| 项 | 规则 |
| --- | --- |
| 候选点来源 | 读取 `D7剩余结构起点候选-v0.1`，由程序生成 `StartCandidateSet`。 |
| 结构抽选 | 按 D6 `weight` 和目标占比。 |
| 生成上限 | 每个 zone 有面积上限、任务上限和失败上限。 |
| 失败处理 | 可变结构少生成可以接受，但必须进入 trace。 |
| 结束条件 | 达到目标面积、候选耗尽、失败上限或任务上限。 |

起点选择口径：

- D7 起点选择是纯程序过程。
- D7 不让 AI 看图选坐标，不让 AI 参与重试。
- 程序先从剩余可建 cell 生成 `StartCandidateSet`。
- 候选点先过硬过滤：功能区内、不压道路、不压固定结构、不压 runtime footprint、地形硬条件通过。
- 通过候选再按靠路、靠水、靠核心、间距、平坦度等软条件打分。
- 使用 `worldSeed + cityId + zonePatchId + taskId + structureId + attemptIndex` 做 seeded weighted random。
- 抽中后仍需通过 D7 validator。

## 条件包装

D7 使用条件包装结构执行剩余生成。包装层可以是自定义 `city_building_structure` 或等价实现，但 D7 真实放置的结构入口必须是 configured structure，也就是 `/place structure <structure_id>` 的等价入口。

首版真实验收只接受 `placementKind=minecraft_place_structure`。NBT template 路径和 jigsaw pool ID 可以作为 TerraSense 画像或 debug 来源，但不能作为 D7 真实 `structureId`。

每次尝试前必须过 validator：

| 条件 | 说明 |
| --- | --- |
| `ZoneTypeCondition` | 结构目标功能必须匹配 zone。 |
| `RemainingAreaCondition` | 不超过剩余可见面积预算。 |
| `BuildableAreaCondition` | 不压道路、边界、缓冲区和 fixed footprint。 |
| `WaterPolicyCondition` | 按结构功能判断是否允许贴水或压水。 |
| `SlopeReliefCondition` | 坡度和局部高差不能超阈值。 |
| `RoadAccessCondition` | 需要道路接入的结构必须靠近道路。 |
| `AabbOccupancyCondition` | 不与已放置结构冲突。 |

失败原因必须结构化：

```text
FIXED_FOOTPRINT_INVALID
FOOTPRINT_OUT_OF_ZONE
ROAD_RESERVED_CONFLICT
WATER_OVERLAP
SLOPE_TOO_HIGH
LOCAL_RELIEF_TOO_HIGH
NO_ROAD_CONNECTION
AABB_OCCUPIED
VARIABLE_AREA_BUDGET_EXCEEDED
JIGSAW_BRANCH_BLOCKED
JIGSAW_SOLVE_FAILED
RETRY_BUDGET_EXHAUSTED
```

## 可变 configured structure / 内部 jigsaw 规则

`variable_area` 可以缺一部分。这里的 jigsaw 指 configured structure 内部的 MC 结构解算，不是让 D7 直接接收 jigsaw pool ID，也不是让 AI 逐 piece 解算。max depth 类结构不要求完整长满。

piece / 分支规则：

| 情况 | 处理 |
| --- | --- |
| piece 在 allowed area 内 | 允许。 |
| piece 会压固定结构 / 道路 / hard reserved | 拒绝该分支。 |
| piece 越出功能区 | 停止该分支。 |
| 有 terminal / endcap | 可放收尾结构。 |
| 没有 terminal / endcap | 该分支少生成即可。 |
| 总面积超过目标比例 | 停止继续扩展。 |

收尾只适用于 `variable_area`。固定结构永远不走收尾 / 裁切。

## Trace

`StructureGenerationTrace` 至少记录：

| 字段 | 说明 |
| --- | --- |
| `fixedPlacements[]` | 固定结构完整放置结果。 |
| `variableAttempts[]` | 可变结构尝试、失败、跳过和重试。 |
| `remainingVisibleAreaByZone` | 每个功能区的剩余面积变化。 |
| `failureSummary` | 按 reasonCode 聚合。 |
| `debugRefs[]` | 调试图、日志或报告。 |

## 最小可玩闭环

1. 读取 D6 `PlannedFixedPlacementMap`。
2. 完整放置 1 个固定广场或市政核心结构。
3. 扣除固定结构占用。
4. 读取 D6 `StructurePoolMap` 中的 `variable_area` 选择和目标占比。
5. 在剩余可见面积内条件包装生成 2-4 个 configured structure；其内部 jigsaw 分支按规则停止 / 收尾 / 失败回写。
6. 输出 `placed_structure_map.json` 和 `structure_generation_trace.json`。

## 验收

| 检查 | 通过口径 |
| --- | --- |
| 固定结构不被裁切 | `fixed_footprint` 要么完整放置，要么失败。 |
| D7 不重选固定落点 | 所有固定结构都引用 D6 `landingCandidateId`。 |
| 剩余面积正确 | `variable_area` 预算基于扣除固定结构后的剩余可见面积。 |
| 可变结构可少生成 | jigsaw 分支越界可停止或收尾，不阻断整个城市。 |
| 无无限重试 | 每个 zone 和结构任务有明确重试上限。 |
| AI 不解 jigsaw | trace 中没有 AI 逐 piece 决策字段。 |
| 放置入口正确 | D7 真实 `structureId` 来自 `/place structure` configured structure registry。 |
