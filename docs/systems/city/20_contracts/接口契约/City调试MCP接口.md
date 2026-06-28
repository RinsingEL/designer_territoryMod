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
| `city_plan_d4` | `POST /realm/city/plan_d4` | 提交 `StructureAnchorPlan`，生成结构 anchor / envelope。 |
| `city_plan_d5` | `POST /realm/city/plan_d5` | 生成 reservation mask、road access、build operation plan。 |
| `city_execute_d5` | `POST /realm/city/execute_d5` | 激活 mask registry 与 planned structure worldgen registry，不主动生成目标 chunk。 |
| `city_plan_d6` | `POST /realm/city/plan_d6` | planned_worldgen 校验，不要求 chunk loaded，不改世界。 |
| `city_execute_d7` | `POST /realm/city/execute_d7` | 保留入口名，正式路径只查询 worldgen ledger / chunk 状态。 |

## city_plan_d4

必填参数：

- `runId`
- `citySeedId`
- `terrasenseProfileSource`
- `structureAnchorPlan`

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

- 激活 server-root `geomantia_city_masks/active_reservation_mask_plan.json`。
- 同步激活 `active_planned_structure_registry.json`。
- hook 不可用 hard fail：`CITY_MASK_HOOK_UNAVAILABLE` / `CITY_WORLDGEN_STRUCTURE_HOOK_UNAVAILABLE`。
- active path 不执行 `build_operation_plan.json`，返回 skipped / deferred 的 `worldMutationReport`，避免提前生成目标 chunk。
- 响应包含 `activePlannedStructureCount`、`plannedStructureRegistryPath`、`worldgenPlacementMode=true`。

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
- `debugLateMaterialize=true`：显式开发模式，才允许旧 `StructureStart.placeInChunk` 路径；trace 标记 `lateMaterialization=true`，不作为验收通过。

返回 artifact：

- `placedStructureLedger`
- `structureMaterializationTrace`
- `inferredFunctionAreaMap`
- `placedStructurePreview`
- `qualityReport`
- `sourceStructureMaterializationPlan`

## 推荐调用流程

```text
city_plan_d3
city_plan_d4 { terrasenseProfileSource, structureAnchorPlan }
city_plan_d5
city_execute_d5 { confirmWorldMutation: true }
city_plan_d6
city_execute_d7 { executeStructurePlacement: false }
city_execute_d7 { executeStructurePlacement: true }
```

真实执行如果返回 `WAITING_FOR_WORLDGEN`，从目标 chunk 外侧靠近 / TP 触发 chunk 首次生成；生成后重复 `city_execute_d7 { executeStructurePlacement: true }` 查询 ledger。若返回 `STRUCTURE_CHUNK_ALREADY_GENERATED`，说明该 chunk 已错过生成期，正式路径不得补贴结构。
