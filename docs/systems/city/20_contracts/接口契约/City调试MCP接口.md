# City 调试 MCP 接口契约

## 版本

v0.2 — City D3-D6 结构落地驱动主线。

Java HTTP：`127.0.0.1:5000`
Node MCP：`country_designer_mcp`
环境变量：`GEOMANTIA_MC_API_URL`，默认 `http://127.0.0.1:5000`

## 工具总览

| MCP 工具 | HTTP 端点 | 当前语义 |
| --- | --- | --- |
| `city_plan_d2` | `POST /realm/city/plan_d2` | 构建 CitySiteContext。 |
| `city_plan_d3` | `POST /realm/city/plan_d3` | 构建 CityLandformReviewPackage 和 D3 review PNG。 |
| `city_profile_structure_envelopes` | `POST /realm/city/profile_structure_envelopes` | 对顶层 configured structure 做非写世界 bbox 采样，输出 validSamples、bboxGroups、generationConfigHash、P95/P99/maxObserved facts。 |
| `city_plan_d4_candidates` | `POST /realm/city/plan_d4_candidates` | 提交 `DesignSlotPlan`，按 D3 patch / 关系意图生成少量 anchor 候选点和预览。 |
| `city_select_d4_candidates` | `POST /realm/city/select_d4_candidates` | 提交 `AnchorSelectionPlan`，把候选选择转换为标准 `StructureAnchorPlan` 并生成 D4 anchor artifact。 |
| `city_plan_d4` | `POST /realm/city/plan_d4` | 直接提交 `StructureAnchorPlan`，生成结构 anchor / envelope；保留为调试入口。 |
| `city_plan_d5` | `POST /realm/city/plan_d5` | 生成 reservation mask、road access、build operation plan。 |
| `city_execute_d5` | `POST /realm/city/execute_d5` | 激活 mask registry 与 planned structure worldgen registry，不主动生成目标 chunk。 |
| `city_plan_d6` | `POST /realm/city/plan_d6` | planned_worldgen 校验，不要求 chunk loaded，不改世界。 |
| `city_execute_d7` | `POST /realm/city/execute_d7` | 保留入口名，正式路径只查询 worldgen ledger / chunk 状态。 |

## city_profile_structure_envelopes

必填参数：

- `runId`
- `citySeedId`
- `terrasenseProfileSource`
- `structureIds`

可选：

- `sampleCount`，默认 256。
- `dimensionId`
- `playerName`

语义：

- 只采样 `/place structure <id>` 可触发的顶层 configured structure。
- 不写世界，不生成正式 ledger。
- 输出 `structure_envelope_facts.json`，供 D4 推导 `collisionEnvelope` / `maskEnvelope`。
- facts 同时包含 `validSamples[]`、`bboxGroups[]`、`generationConfigHash`。
- 固定 / 近固定结构使用 dominant `bboxGroups[]` 或 anchor 指定的 `envelopeGroupKey`。
- 非固定结构继续使用固定生成配置下的 P95 / P99 / maxObserved。

返回 artifact：

- `structureEnvelopeFacts`
- `structureEnvelopeProfilePreview`
- `qualityReport`

## city_plan_d4

必填参数：

- `runId`
- `citySeedId`
- `terrasenseProfileSource`
- `structureAnchorPlan`

可选：

- `structureEnvelopeFactsSource`，形如 `{ "factsPath": "..." }`；未传时读取当前 run/city 默认产物。
- anchor 可选 `envelopeGroupKey` 指定 profiling bbox group。
- anchor 可选 `smallClearanceBlocks` 指定固定结构 bbox group 小间距，默认 4。

`terrasenseProfileSource` 支持：

- `sourceType=structure_profile_jsonl` + `profilePath`
- `sourceType=debug_catalog` + `debugCatalogPath`

旧 `patchGroupPlan`、`functionType`、`functionTag`、`function_candidates` 等字段必须失败：`LEGACY_CITY_FUNCTION_ZONE_FLOW_REMOVED`。

返回 artifact：

- `structureAnchorPlan`
- `structureAnchorMap`
- `structureProfileCatalog`
- `structureAnchorPreview`
- `qualityReport`
- `sourceD3Package`

`structureAnchorMap.anchors[]` 会输出 `envelopeMode`、`selectedEnvelopeGroupKey`、`smallClearanceBlocks`、`collisionEnvelope`、`maskEnvelope`、`safetyEnvelope`。其中 `fixed_bbox_group` 表示固定 / 近固定结构走紧 bbox；`fixed_depth_statistics` 表示非固定结构走 P95/P99。

## city_plan_d4_candidates / city_select_d4_candidates

`city_plan_d4_candidates` 必填参数：

- `runId`
- `citySeedId`
- `terrasenseProfileSource`
- `designSlotPlan`

可选：

- `structureEnvelopeFactsSource`，形如 `{ "factsPath": "..." }`；未传时读取当前 run/city 默认产物。

语义：

- `slotId` / `displayRole` 只表示本次设计槽位，不是 City 全局功能枚举。
- `candidatePatchRefs` 是候选搜索依据，不是硬边界；结构真实 hard gate 仍由 D6 actual footprint 决定。
- slot 可使用 `structureId` 表示单一顶层 configured structure，也可使用 `structureIds[]` 表示多个备选结构。
- 每个 slot 默认输出最多 5 个候选，候选包含 `candidateKind`、`anchorBlock`、`estimatedCollisionEnvelope`、`estimatedMaskEnvelope`、`scoreBreakdown`、`placementReason`、`risks`。
- `candidateId` 在同一 slot 内稳定且唯一，用于 `city_select_d4_candidates` 精确回选。
- `distanceBand` 首版固定为 `near=32-96`、`medium=96-224`、`far=>224` blocks；`targetAnchorId` 只引用已选 anchor，`targetSlotId` 只作为软提示。

返回 artifact：

- `designSlotPlan`
- `anchorCandidateSet`
- `anchorCandidatePreview`
- `qualityReport`
- `sourceD3Package`
- `sourceStructureEnvelopeFacts`

`city_select_d4_candidates` 必填参数：

- `runId`
- `citySeedId`
- `terrasenseProfileSource`
- `anchorSelectionPlan`

可选：

- `anchorCandidateSetSource`，形如 `{ "candidateSetPath": "..." }`；未传时读取当前 run/city 默认候选产物。
- `structureEnvelopeFactsSource`，同 `city_plan_d4`。

语义：

- 读取 `anchor_candidate_set.json`，把 `selectedCandidates[]` 转换为标准 `StructureAnchorPlan`。
- 转换后立即复用 `city_plan_d4` 的硬校验与 artifact 输出；后续 D5/D6/D7 不需要知道候选层存在。
- 旧 `patchGroupPlan`、`functionType`、`functionTag`、`function_candidates` 等字段同样必须失败：`LEGACY_CITY_FUNCTION_ZONE_FLOW_REMOVED`。

## city_plan_d5 / city_execute_d5

`city_plan_d5` 无 AI payload，只读取 D3/D4 artifact。

返回 artifact：

- `reservationMaskPlan`
- `roadAccessPlan`
- `buildOperationPlan`
- `reservationMaskPreview`
- `qualityReport`
- `sourceStructureAnchorMap`

`city_execute_d5` required：

- `runId`
- `citySeedId`
- `confirmWorldMutation=true`

执行语义：

- 必须已存在 D6 locked `structure_materialization_plan.json`；未跑 D6 或 locked plan 不完整时 hard fail。
- 激活 server-root `geomantia_city_masks/active_reservation_mask_plan.json`。
- 同步激活 `active_planned_structure_registry.json`，registry 写入 `expectedStartSignature`、`lockedActualFootprint`、`lockedCollisionEnvelope`。
- hook 不可用 hard fail：`CITY_MASK_HOOK_UNAVAILABLE` / `CITY_WORLDGEN_STRUCTURE_HOOK_UNAVAILABLE`。
- active path 不执行 `build_operation_plan.json`，返回 skipped / deferred 的 `worldMutationReport`，避免提前生成目标 chunk。
- 响应包含 `activePlannedStructureCount`、`plannedStructureRegistryPath`、`worldgenPlacementMode=true`、`requiresLockedMaterializationPlan=true`、`roadPlanningStage=d7_after_worldgen_ledger`。

## city_plan_d6

必填参数：

- `runId`
- `citySeedId`

可选：

- `dimensionId`
- `playerName`

不得传旧 `terrasenseProfileSource`、`structureChoicePlan`、`fixedPlacementSelectionPlan`、`plannedFixedPlacementMap`、`structurePoolMap`。

返回 artifact：

- `structureMaterializationPlan`
- `placedStructureLedger`
- `structureMaterializationTrace`
- `inferredFunctionAreaMap`
- `structureMaterializationPreview`
- `qualityReport`

未生成 chunk 时 response 为 `status=planned_worldgen` / `reasonCode=WAITING_FOR_WORLDGEN`；这不是结构失败。

chunk 已经生成到 `FEATURES` 或之后且没有 ledger 时，返回 `STRUCTURE_CHUNK_ALREADY_GENERATED`，不得继续走 active placement。

D6 会做 non-mutating probe-and-lock，输出 `locked=true`、`lockedActualFootprint`、`lockedBBoxGroupKey`、`lockedCollisionEnvelope`、`expectedStartSignature`。若 actual group 与 D4 selected/dominant group 不一致，但 facts 中存在该 group 且最终防撞通过，D6 锁定实际 group，不再直接失败。

D6 trace 会记录 `actualFootprint`、`actualLocalBounds`、`actualBBoxGroupKey`、`lockedCollisionEnvelope`、`envelopeMode`、`selectedEnvelopeGroupKey`，用于解释 fixed bbox group 是否匹配本次实际生成形态。默认 `collisionClearanceBlocks=4`。

## city_execute_d7

必填参数：

- `runId`
- `citySeedId`

可选：

- `executeStructurePlacement`，默认 false。
- `debugLateMaterialize`，默认 false，仅开发诊断可用。
- `dimensionId`
- `playerName`

语义：

- `executeStructurePlacement=false`：只查看 worldgen ledger / 当前 chunk 状态。
- `executeStructurePlacement=true`：正式路径仍只查看 worldgen ledger / 当前 chunk 状态，不 late paste。
- 当所有 planned structures 都有 ledger 时，D7 基于 ledger 真实 `actualFootprint` 生成道路 / 边界后处理；道路避障使用 `actualFootprint + roadAvoidanceMarginBlocks`，默认 3。
- `debugLateMaterialize=true`：显式开发模式，才允许旧 `StructureStart.placeInChunk` 路径；trace 标记 `lateMaterialization=true`，不作为验收通过。

返回 artifact：

- `placedStructureLedger`
- `structureMaterializationTrace`
- `inferredFunctionAreaMap`
- `placedStructurePreview`
- `qualityReport`
- `sourceStructureMaterializationPlan`

响应 / report 增加：

- `roadPostprocessSource=worldgen_ledger_actual_footprint`
- `roadAvoidanceMarginBlocks`
- `roadBlockedByStructureCount`
- `boundarySource=actual_footprint_union`

## 推荐调用流程

```text
city_plan_d3
city_profile_structure_envelopes { terrasenseProfileSource, structureIds }
city_plan_d4_candidates { terrasenseProfileSource, designSlotPlan }
city_select_d4_candidates { terrasenseProfileSource, anchorSelectionPlan }
city_plan_d5
city_plan_d6
city_execute_d5 { confirmWorldMutation: true }
city_execute_d7 { executeStructurePlacement: false }
city_execute_d7 { executeStructurePlacement: true }
```

真实执行如果返回 `WAITING_FOR_WORLDGEN`，从目标 chunk 外侧靠近 / TP 触发 chunk 首次生成；生成后重复 `city_execute_d7 { executeStructurePlacement: true }` 查询 ledger。若返回 `STRUCTURE_CHUNK_ALREADY_GENERATED`，说明该 chunk 已错过生成期，正式路径不得补贴结构。
