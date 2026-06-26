# City D7 案子：剩余结构起点候选生成

## 定位

本案子只解决 D7 中 `variable_area` 剩余结构的起始点怎么选。

D6 已经确定固定大小结构的落点。D7 先完整放置 `PlannedFixedPlacementMap` 中的固定结构，然后在剩余可见面积中生成 configured structure。若这些结构内部由 MC jigsaw 规则展开，D7 只做边界 validator 和失败 trace，不直接接收 jigsaw pool ID。

这些剩余结构的起点选择必须是纯程序过程，不让 AI 介入。

## 核心口径

```text
BuildableAreaMap
  - D6 fixed_footprint footprint / clearance
  - runtime occupied footprint
  -> StartCandidateSet
  -> hard filter
  -> soft score
  -> seeded weighted random
  -> validator
  -> retry budget
  -> trace
```

允许随机，但只能在程序生成并过滤过的候选集合中随机。不得在功能区内盲随机 block 坐标。

## 输入与输出

| 方向 | 输入 / 输出 | 说明 |
| --- | --- | --- |
| 输入 | `FunctionZoneMap` | 功能区边界、类型和 cell 形状。 |
| 输入 | `BuildableAreaMap` | D5 扣除道路、边界、缓冲区和小模板后的可建区。 |
| 输入 | `PlannedFixedPlacementMap` | D6 已选固定结构落点；D7 必须先扣除。 |
| 输入 | `StructurePoolMap` | D6 输出的 `variable_area` 结构菜单、权重和目标占比。 |
| 输入 | `RoadIntent` / `BoundaryIntent` | 道路接入、边界、水岸和保留区。 |
| 输出 | `StartCandidateSet` | 每个 zone / structure task 的程序候选起点。 |
| 输出 | `StartSelectionTrace` | 候选过滤、评分、抽选、失败和重试记录。 |

## AI 边界

| AI 可做 | AI 不可做 |
| --- | --- |
| D6 选择 `variable_area` 结构。 | D7 不让 AI 选择剩余结构坐标。 |
| D6 配置目标可见面积占比。 | D7 不让 AI 逐个结构选起点。 |
| D6 给风格、密度、靠路 / 靠水等偏好。 | D7 不让 AI 参与失败重试。 |
| 未来可 review scoring 规则。 | D7 不让 AI 解 jigsaw piece。 |

D7 只能把 D6 的偏好翻译成程序评分项。

## StartCandidateSet

`StartCandidateSet` 是 D7 runtime 产物，不是 AI 草案。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `schemaVersion` | string | `city_start_candidate_set.v0.1`。 |
| `cityId` | string | 城市 ID。 |
| `zonePatchId` | string | 功能区 ID。 |
| `taskId` | string | D7 生成任务 ID。 |
| `structureId` | string | 目标 configured structure ID，必须可被 `/place structure` 等价入口识别。 |
| `seedKey` | string | seeded random 使用的稳定 key。 |
| `candidates[]` | object[] | 候选起点。 |

`candidates[]`：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `startCandidateId` | string | 稳定候选 ID。 |
| `anchorBlock` | object | 候选起点 block。 |
| `rotation` | string | 候选朝向。 |
| `candidateFootprint` | object | configured structure 的估算 footprint；若内部 jigsaw 展开，则记录起始 footprint / assembly 画像来源。 |
| `requiredPlacementBounds` | object | D7 为本候选推导的保守放置影响范围，用于等待 chunk 覆盖；首版来自 `candidateFootprint` 和 `expectedAreaRange`。 |
| `requiredChunkRange` | object | `requiredPlacementBounds` 覆盖的 chunk 范围。 |
| `hardPassed` | bool | 是否通过硬过滤。 |
| `score` | number | 综合软评分。 |
| `scoreBreakdown` | object | 各评分项。 |
| `riskFlags[]` | string[] | 风险标记。 |

## 候选生成

候选来源按功能区剩余可建 cell 生成。

基础流程：

1. 取 `BuildableAreaMap.buildableCells`。
2. 扣除 D6 固定结构 footprint / clearance。
3. 扣除 D7 已放置结构的 runtime footprint。
4. 按结构 footprint / 起始 piece footprint 做网格采样。
5. 为每个候选生成允许朝向。
6. 输出候选 ID、位置、朝向和估算 footprint。

D7 v2 默认对同一 D6 `variableSelections[]` 只选 1 个主 start。面积目标未满足时不自动追加 start，而是在 bounded dry-run 样本报告中输出 `feasibility=HAMLET/PARTIAL`、score、termination / rejection 统计。多 start 仅作为显式 satellite 策略；开启后，后续 start 必须把旧 ledger 和本轮已放置的 `variable_area` footprint 作为 runtime occupied 扣除，已使用的 `startCandidateId` 应标记为不可再次选择，避免重复放置或重叠。

首版可用规则：

| 项 | 规则 |
| --- | --- |
| 采样步长 | 可按结构尺寸、功能区大小和性能预算决定。 |
| 候选数量上限 | 每个 task 必须有上限，避免大区无限候选。 |
| 空候选处理 | 写 trace，减少该结构目标面积或跳过任务。 |
| 稳定性 | 同一 world seed、cityId、zonePatchId、structureId 下候选顺序可复现。 |

## 硬过滤

硬过滤失败的候选不能进入随机池。

| 条件 | 说明 |
| --- | --- |
| `InsideZone` | footprint 必须在目标功能区允许区域内。 |
| `BuildableArea` | 不压道路、边界缓冲、小模板和 hard reserved cell。 |
| `NoFixedConflict` | 不压 D6 固定结构 footprint / clearance。 |
| `NoRuntimeConflict` | 不压 D7 已放置结构。 |
| `TerrainAllowed` | 高差、坡度、水体策略不突破硬阈值。 |
| `StructureBudget` | 不超过该 zone 的剩余可见面积预算。 |

## 软评分

软评分只影响抽选概率，不直接保证最终成功。

首版评分项：

| 评分项 | 倾向 |
| --- | --- |
| `roadAccessScore` | 需要临路的结构靠近道路更高。 |
| `plazaEdgeScore` | 市场、公共建筑靠近广场 / 核心边缘更高。 |
| `waterAffinityScore` | 港口、鱼市、码头类靠水更高。 |
| `interiorScore` | 普通建筑不要太贴功能区边缘。 |
| `spacingScore` | 避免与已有结构过密或过远。 |
| `terrainComfortScore` | 更平整、更少修整的位置更高。 |
| `stylePreferenceScore` | 来自 D6 的靠路、靠水、密度等偏好。 |
| `expansionScore` | 起点周围局部窗口内可建 cell 比例越高越高，避免把主 start 选到一出门就被道路 / 边界 / reserved 区堵住的位置。 |
| `corridorScore` | 起点四向连续可建走廊越长越高，用于给 jigsaw 后续分支保留展开空间。 |
| `reservedPenalty` | 周边 reserved cell 比例越高、距离 reserved 越近扣分越重，降低贴角落 / 贴红区候选的采样优先级。 |

D6 可以提供偏好，但 D7 的打分和抽选由程序执行。

当前 D7 v2 的 `scoreBreakdown` 至少应记录 `interiorScore`、`expansionScore`、`corridorScore`、`reservedPenalty`、`localBuildableRatio`、`localReservedRatio`、`nearestReservedDistanceCells`、`corridorReachCells` 和 `buildableFit`。这些字段是 trace 解释起点为什么没有选在某个角落、为什么更偏向开阔区域的依据；它们只影响候选排序和 dry-run 样本入口，不替代 piece 级 validator。

## 抽选规则

抽选使用 seeded weighted random。

`seedKey` 建议包含：

```text
worldSeed + cityId + zonePatchId + taskId + structureId + attemptIndex
```

规则：

- 只从 hard passed 的候选中抽选。
- 权重来自 `score`，可对高分候选做 top-K 截断。
- 同一输入下结果可复现。
- 失败后按候选顺序或重新带 `attemptIndex` 抽下一个候选。
- 每个 task 和每个 zone 必须有 retry budget。

## Chunk 加载等待

D7 起点候选只决定结构起点，不代表结构可以立即写进世界。真实放置前，D7 必须检查候选对应的 `requiredChunkRange` 是否已加载：

| 情况 | 处理 |
| --- | --- |
| chunk 覆盖达标 | 进入真实 configured structure 放置入口。 |
| chunk 未覆盖 | 本次 attempt 写 `status=waiting`，`reasonCode=STRUCTURE_CHUNK_NOT_LOADED` 或 `WAITING_CHUNKS`，不消耗 AI 重试，不当作结构失败。 |
| 后续再次执行 | 复用同一输入和 seed，重新检查 chunk 覆盖；已真实放置的结构通过 ledger 跳过。 |

玩家 TP 和预加载 mod 只是 chunk 覆盖的来源；D7 不依赖特定预加载 mod API。

## Validator 与 Trace

抽中的候选还要经过 D7 结构 validator。

失败时必须记录：

| 字段 | 说明 |
| --- | --- |
| `taskId` | 生成任务。 |
| `startCandidateId` | 候选 ID。 |
| `structureId` | 结构 ID。 |
| `anchorBlock` | 候选起点。 |
| `rotation` | 候选朝向。 |
| `scoreBreakdown` | 抽中时评分。 |
| `validatorResult` | 失败原因。 |
| `retryIndex` | 第几次尝试。 |
| `requiredChunkRange` | 本次尝试需要的 chunk 覆盖范围。 |

常见失败原因：

```text
NO_START_CANDIDATE
START_CANDIDATE_FILTERED_OUT
START_FOOTPRINT_OUT_OF_ZONE
START_ROAD_RESERVED_CONFLICT
START_FIXED_CONFLICT
START_RUNTIME_OCCUPIED
START_TERRAIN_REJECTED
START_BUDGET_EXCEEDED
START_RETRY_BUDGET_EXHAUSTED
```

## 非目标

- 不让 AI 选择剩余结构坐标。
- 不让 D7 在功能区内盲随机 block 坐标。
- 不在本案子决定固定大小结构落点；固定结构落点由 D6 负责。
- 不在本案子解 jigsaw piece；这里只选 configured structure 起始点。
- 不保证 `variable_area` 必须长满；少生成可以接受，但必须 trace。

## 验收

| 检查 | 通过口径 |
| --- | --- |
| 纯程序 | D7 trace 中没有 AI 起点选择字段。 |
| 不盲随机 | 抽选前必须存在 `StartCandidateSet`。 |
| 可复现 | 同一 seed 和输入下候选与抽选结果稳定。 |
| 不压固定结构 | 候选不得压 D6 fixed footprint / clearance。 |
| 不贴死角 | 在存在更开阔 hard-passed 候选时，贴 reserved corridor / 边界且局部可建比例低的候选不应成为 top sample candidate。 |
| 有重试上限 | task / zone 都有 retry budget。 |
| 有失败 trace | 空候选、过滤失败、validator 失败都可追踪。 |
