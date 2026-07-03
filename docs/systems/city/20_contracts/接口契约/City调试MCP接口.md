# City 调试 MCP 接口契约

## 版本

v0.3 — City D3-D6 结构落地驱动主线 + 快速验收 workflow。

Java HTTP：`127.0.0.1:5000`
Node MCP：`country_designer_mcp`
环境变量：`GEOMANTIA_MC_API_URL`，默认 `http://127.0.0.1:5000`

## 工具总览

| MCP 工具 | HTTP 端点 | 当前语义 |
| --- | --- | --- |
| `city_plan_d2` | `POST /realm/city/plan_d2` | 构建 CitySiteContext。 |
| `city_plan_d3` | `POST /realm/city/plan_d3` | 构建 CityLandformReviewPackage 和 D3 review PNG。 |
| `city_profile_structure_envelopes` | `POST /realm/city/profile_structure_envelopes` | 对顶层 configured structure 做非写世界 bbox 采样，输出 validSamples、bboxGroups、generationConfigHash、P95/P99/maxObserved facts。 |
| `city_create_d4_candidate_session` | `POST /realm/city/create_d4_candidate_session` | D4 v2 推荐入口：创建逐 slot 候选 session，开始记录设计耗时。 |
| `city_plan_d4_next_candidates` | `POST /realm/city/plan_d4_next_candidates` | D4 v2：只为当前未选择 slot 生成候选，避开已冻结 occupied envelope。 |
| `city_select_d4_candidate` | `POST /realm/city/select_d4_candidate` | D4 v2：选择当前 slot 的一个 candidate，冻结占用并进入下一个 slot。 |
| `city_finalize_d4_candidate_session` | `POST /realm/city/finalize_d4_candidate_session` | D4 v2：所有 slot 选完后生成标准 D4 `StructureAnchorPlan` / `StructureAnchorMap`。 |
| `city_plan_d4_candidates` | `POST /realm/city/plan_d4_candidates` | v0.1 debug batch 入口：一次性生成全部 slot 候选，`planningMode=all_slots_tentative_order_debug`。 |
| `city_select_d4_candidates` | `POST /realm/city/select_d4_candidates` | v0.1 debug batch 选择入口。推荐使用 D4 v2 session。 |
| `city_plan_d4` | `POST /realm/city/plan_d4` | 直接提交 `StructureAnchorPlan`，生成结构 anchor / envelope；保留为调试入口。 |
| `city_plan_d5` | `POST /realm/city/plan_d5` | 生成 reservation mask、road access、build operation plan。 |
| `city_execute_d5` | `POST /realm/city/execute_d5` | 激活 mask registry、planned structure worldgen registry，并按 `roadProvider` 注册 RoadWeaver 连接计划。 |
| `city_plan_d6` | `POST /realm/city/plan_d6` | planned_worldgen 校验，不要求 chunk loaded，不改世界。 |
| `city_execute_d7` | `POST /realm/city/execute_d7` | 保留入口名，正式路径只查询 worldgen ledger / chunk 状态。 |
| `city_plan_city_walls` | `POST /realm/city/plan_city_walls` | 读取 D7 ledger、D5 wall reservation 和 actual road mask，生成城墙 plan、preview 和 NBT 模板；v3 可生成结构种子城市外环 hull + 道路聚类裁门；`wallDesignPolicy=v3.2/v3.3` 增加天然边界、道路趋势 / 近路投影开门和独立 gatehouse；`wallVersion=v4` 生成 actualFootprint 优先、D5 cityDomain cell 轻量贴形的陆侧墙图。 |
| `city_execute_city_walls` | `POST /realm/city/execute_city_walls` | 按城墙 plan 使用 vanilla setBlock 后端放置临时石墙 / 塔楼 / gatehouse；v3/v4 可开启 debug scan 输出缺口原因，v4 按 `wallUnits[]` 和 `nodeConnectorUnits[]` 执行。 |
| `city_run_workflow` | `POST /realm/city/run_workflow` | 调试 / 验收快跑器：串联 D3 -> profiling -> D4 v2 session -> D5 -> D6 -> execute_d5 -> execute_d7，可选 plan/execute 城墙；记录每步时间戳、耗时、失败原因，遇到确认或等待 worldgen 时暂停。 |

## city_run_workflow

这是 City 真实验收提速入口，不替代单步调试接口。它按当前 active path 调用现有 endpoint handler，并写出 `city_workflow_report.json`。

必填参数：

- `runId`
- `citySeedId`

首次完整运行通常还需要：

- `terrasenseProfileSource`
- `designSlotPlan`
- `structureIds[]`

常用可选参数：

- `skipExisting`，默认 `true`。已有 artifact 时跳过对应步骤，用于等待 chunk worldgen 后复跑。
- `sampleCount`，默认 256。
- `patchScanPaddingBlocks`，默认 128；首次 D3 会按 city bounds + padding 覆盖多个 GIS region，把结构 bbox 和 v4 城墙 breathing room 需要的外侧 patch context 一并写入 D3 package。D4 候选仍受原 city grid 约束，padding 不是新的城市核心可选域。
- `confirmWorldMutation`，默认 `false`。未传时 workflow 在 execute_d5 前返回 `waiting_for_confirmation`。
- `roadProvider=auto|roadweaver|worldedit_debug|none`。
- `planWalls` / `executeWalls`，默认 `false`。
- `wallVersion`、`wallTerrainPolicy`、`wallDesignPolicy` 及对应城墙参数，会透传给 D5 / CityWalls；`wallVersion=v4` 时额外可传 `wallUnitLengthBlocks`、`waterRunMinUnits`、`waterRetreatMaxCells`、`structureWallBreathingRoomBlocks`、`heightDatumClampBlocks`、`localMedianWindowUnits`。
- `debugScan`，执行城墙时默认 `true`。
- `dimensionId` / `playerName`。

语义：

- workflow 会顺序执行：`city_plan_d3` -> `city_profile_structure_envelopes` -> D4 v2 session 自动选择最高分候选 -> `city_plan_d5` -> `city_plan_d6` -> `city_execute_d5` -> `city_execute_d7`。
- D3 step 会刷新覆盖 `grid.blockBounds + patchScanPaddingBlocks` 的所有 GIS region；不得只刷新城市中心所在单个 region。
- 若 `confirmWorldMutation=false`，返回 `status=waiting_for_confirmation`，不激活 mask / planned registry。
- 若 D7 返回 `WAITING_FOR_WORLDGEN`，workflow 返回 `status=waiting_for_worldgen`。玩家或 debug command 加载目标 chunk 后，用相同请求复跑；已存在 artifact 会被跳过。
- `planWalls=true` 时 ledger 完整后继续调用 `city_plan_city_walls`。
- `executeWalls=true` 时继续调用 `city_execute_city_walls`；成功完成后 HTTP controller 才请求保存世界。
- 每个 step 都记录 `startedAt`、`endedAt`、`durationMs`、`status`、`reasonCode`、`artifacts`。
- `skipExisting=true` 复跑城墙时，workflow 必须校验已有 `city_wall_plan.json` 的 `wallVersion` / `wallDesignPolicy` / `wallTerrainPolicy` 与请求匹配；不匹配时不得跳过旧 plan。

返回 artifact：

- `city_workflow_<citySeedId>/city_workflow_report.json`

质量口径：

- workflow 报告只用于提速和留痕；任何结构越界、重叠、worldgen ledger 不完整、墙体缺口等最终判断仍以各阶段 artifact / trace 为准。
- 不允许 workflow 在正式路径绕过 `city_execute_d5` / `city_execute_d7` 的 worldgen-time placement 规则；不得回退 late paste。

## city_plan_d3

必填参数：

- `runId`
- `citySeedId`

可选参数：

- `cellStepBlocks`，未传时从 run manifest 恢复。
- `patchScanPaddingBlocks`，默认 128。
- `dimensionId`
- `playerName`

语义：

- D3 的 `grid` 仍表示城市核心规划域，D4 候选不得因为 padding 扩大而离开该 grid。
- `patchScanPaddingBlocks` 只扩大 patch 上下文：实现必须刷新覆盖 `grid.blockBounds + padding` 的所有 GIS region，并把这些 region 的 `LandformPatch` / `memberCells` 合并进同一个 `CityLandformReviewPackage`。
- 目的：当 AI 选择靠近城市核心边界的 patch 时，D6 `actualFootprint`、D5/D7 reservation 和 v4 城墙 `structureWallBreathingRoomBlocks` 仍有已扫描 patch 背景，不允许墙体静默长到未知 patch 外。
- D3 package 必须写出 `patchScanPaddingBlocks`、`patchContextBounds`、`refreshedRegions[]`，用于判断 patch coverage 是否足够。

## city_plan_city_walls v4

`wallVersion=v4` 为当前 City Walls 新测试路径。

新增 / 关键参数：

- `wallUnitLengthBlocks`：默认 16，墙图基础 unit 长度，和 step 对齐。
- `waterRunMinUnits`：默认 3，连续多少个 unit 命中水体后判定为湖 / 海并尝试陆侧退避。
- `waterRetreatMaxCells`：默认 4，水体退避最多尝试多少个 unit 步长。
- `structureWallBreathingRoomBlocks`：默认 32，以 D7 `actualFootprint` union 为核心外扩生成墙圈。
- `heightDatumClampBlocks`：默认 6，`targetY` 相对全局 `cityWallDatumY` 的夹取范围。
- `localMedianWindowUnits`：默认 3，局部高度 median 采样窗口。

输出要求：

- `schemaVersion=city_wall_plan.v0.4`
- `wallBoundaryMode=actual_footprint_land_ring`
- `wallContourMode=terrain_adaptive_domain_guided_land_ring`
- `terrainContourEvents[]`：记录 unit 因 D5 `cityDomainMask` 外缘 guide 而发生的有限偏移，以及为连接偏移 unit 插入的短 `terrain_contour_link`。
- `wallNodes[]`：节点类型包括 `corner_tower`、`beacon_tower`、`gatehouse`、`terrace_node`、`natural_boundary_endpoint`。
- `wallUnits[]`：16 格左右的短墙 unit；普通墙不得依赖执行层再任意切成长短不一的重叠片。
- `nodeConnectorUnits[]`：墙体到塔 / 门楼 / terrace 的连接单元，输出 `connectorStatus=connected|stepped|blocked|skipped`。
- `cityWallDatumY`：整圈候选墙线的 trimmed median 高度基准。
- `wallGraphValidation`：记录水体退避、mask skip、height break、闭环候选和断点。

v4 行为口径：

- 边界必须包住 D7 `actualFootprint`，不得被 D3 source patch 锁死。
- 规划层先用 `actualFootprint + structureWallBreathingRoomBlocks` 生成保守外圈，再读取 D5 `cityDomainMask[]` 中的 `maskType=city_domain_cell` 外缘作为地形 / 城市域 guide；每个 unit 只允许小幅偏移，且必须仍在 `knownPatchBounds` 内、不能压结构 footprint 或水体。相邻 unit 偏移后用 `terrain_contour_link` 连接，避免预览继续呈现纯四边形。
- D5 `seedPatches[]` 若带 `memberCells[]`，v4 水体判定必须优先按真实成员 cell 判断，不能把大型 water patch 的 envelope 当作整片硬水体；`shore` 不应直接等同于普通墙禁止落点。
- 连续水体 run 达阈值时优先退回陆地侧；退避失败时输出天然水体边界 gap，而不是把普通墙落入湖 / 海。
- `actualRoadMask` 只用于真实道路开门；复跑或实机验收时不得把本系统已放置的石砖 / 圆石 / 安山岩等城墙或结构材料反扫成道路并造成大面积 `ROAD_MASK_GATEHOUSE_OPENING`。
- 相邻节点高差 `<=2` 走普通平墙，`3..6` 走 `stepped_wall_unit` 或 `stair_link`，`>6` 插入 `terrace_node`；仍无法缓解时在 validation 中输出明确 reason。
- 执行层按 `wallUnits[]` / `nodeConnectorUnits[]` 放置，并在地形采样时忽略本系统已经放置的墙 / 塔 / 门楼材料，避免重复执行叠高。

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

## city_create_d4_candidate_session / city_plan_d4_next_candidates / city_select_d4_candidate / city_finalize_d4_candidate_session

D4 v2 推荐使用顺序候选 session：

```text
city_create_d4_candidate_session
city_plan_d4_next_candidates
city_select_d4_candidate
... repeat until all slots selected ...
city_finalize_d4_candidate_session
```

`city_create_d4_candidate_session` 必填参数：

- `runId`
- `citySeedId`
- `terrasenseProfileSource`
- `designSlotPlan`

可选：

- `sessionId`
- `structureEnvelopeFactsSource`

`city_plan_d4_next_candidates` 必填参数：

- `runId`
- `citySeedId`

语义：

- 每次只返回当前 `currentSlotId` 的候选。
- 候选基于 session 中已经冻结的 `selectedAnchors[]` / `occupiedEnvelopes[]` 重新生成。
- 返回 `slot_candidate_set.json`、`anchor_candidate_preview.png`、`d4_candidate_session_trace.json`。
- `anchor_candidate_preview.png` 必须叠加 D3 patch member-cell 底图；已冻结 anchor 用 `S1/S2...` 标注，当前 slot 候选用 `C1/C2...` 标注，候选完整 id / score / role 放入右侧 legend，避免把同一 slot 的多个候选重叠误读为最终落地重叠。

`city_select_d4_candidate` 必填参数：

- `runId`
- `citySeedId`
- `slotId`
- `candidateId`

可选：

- `sessionId`
- `anchorId`
- `selectionReason`
- `quickPreflight`

语义：

- `slotId` 必须等于当前 session `currentSlotId`，否则返回 `D4_SLOT_ORDER_VIOLATION`。
- 选择成功后优先冻结 `estimatedSafetyEnvelope` 作为 `occupiedEnvelopes[].blockBounds`，缺失时回退 `estimatedCollisionEnvelope`；后续 slot 候选必须避开该冻结 envelope。
- 本轮 `quickPreflight` 只记录请求，返回 `quickPreflightStatus=deferred_to_d6`；MC actual bbox 仍由 D6 负责。
- 每次 selection 会累计 `agentThinkTimeMs`。

`city_finalize_d4_candidate_session` 必填参数：

- `runId`
- `citySeedId`
- `terrasenseProfileSource`

可选：

- `sessionId`
- `structureEnvelopeFactsSource`

语义：

- 必须所有 placementOrder slot 都已选择，否则返回 `D4_SESSION_NOT_FINALIZABLE`。
- finalize 会把 session `selectedAnchors[]` 转换为标准 `StructureAnchorPlan`，并调用现有 D4 hard validation。
- 输出 `structure_anchor_plan.json`、`structure_anchor_map.json`、`structure_anchor_preview.png`、`d4_design_time_report.json`。
- `structure_anchor_preview.png` 同样必须叠加 D3 patch 底图，用于复核最终 anchor 与 patch / 水岸 / 山脊 / 崖壁等地形关系。

新增 artifacts：

- `d4_candidate_session.json`
- `slot_candidate_set.json`
- `d4_candidate_session_trace.json`
- `d4_design_time_report.json`

`d4_design_time_report.json` 至少包含：

- `totalWallClockMs`
- `toolRuntimeMs`
- `agentThinkTimeMs`
- `stepTimings[]`
- `failureReasons`

## city_plan_d4_candidates / city_select_d4_candidates

`city_plan_d4_candidates` 必填参数：

- `runId`
- `citySeedId`
- `terrasenseProfileSource`
- `designSlotPlan`

可选：

- `structureEnvelopeFactsSource`，形如 `{ "factsPath": "..." }`；未传时读取当前 run/city 默认产物。

语义：

- 这是 v0.1 debug batch path；active 推荐路径是 D4 v2 session。
- 返回 `planningMode=all_slots_tentative_order_debug`。
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
- `wallReservationPlan`
- `roadAccessPlan`
- `buildOperationPlan`
- `reservationMaskPreview`
- `wallReservationPreview`
- `qualityReport`
- `sourceStructureAnchorMap`

可选参数：

- `wallVersion=v3|v2|v1_debug`，默认 `v2`；`v3` 生成结构种子 patch region hull，`v2` 生成 D3 patch 贴边 wall reservation，`v1_debug` 保留旧矩形调试墙。
- `wallMarginBlocks`，默认 24。
- `segmentLengthBlocks`，默认 15。
- `wallCorridorHalfWidthBlocks`，默认 4。
- `wallBreathingRoomBlocks`，v3 默认 24。
- `patchExpansionMaxRounds`，v3 默认 4。
- `concavityOpeningMaxBlocks`，v3 默认 64。
- `concavityDepthRatioMin`，v3 默认 0.6。

`city_execute_d5` required：

- `runId`
- `citySeedId`
- `confirmWorldMutation=true`

可选：

- `roadProvider=auto|roadweaver|worldedit_debug|none`，默认 `auto`。

执行语义：

- 必须已存在 D6 locked `structure_materialization_plan.json`；未跑 D6 或 locked plan 不完整时 hard fail。
- 激活 server-root `geomantia_city_masks/active_reservation_mask_plan.json`。
- 同步激活 `active_planned_structure_registry.json`，registry 写入 `expectedStartSignature`、`lockedActualFootprint`、`lockedCollisionEnvelope`。
- hook 不可用 hard fail：`CITY_MASK_HOOK_UNAVAILABLE` / `CITY_WORLDGEN_STRUCTURE_HOOK_UNAVAILABLE`。
- active path 不执行 `build_operation_plan.json`，返回 skipped / deferred 的 `worldMutationReport`，避免提前生成目标 chunk。
- RoadWeaver 存在且 `roadProvider=auto|roadweaver` 时，D5 生成 `roadweaver_connection_plan.json` 并反射调用 `RoadNetworkApi.registerStructureEndpoint` / `ensureConnection(..., generateImmediately=false)`。
- RoadWeaver 缺失且 `roadProvider=roadweaver` 时 hard fail `ROADWEAVER_UNAVAILABLE`。
- RoadWeaver 缺失且 `roadProvider=auto` 时保留 D7 WorldEdit debug fallback，并写入 `road_provider_state.json`。
- 响应包含 `activePlannedStructureCount`、`plannedStructureRegistryPath`、`worldgenPlacementMode=true`、`requiresLockedMaterializationPlan=true`、`roadPlanningStage=d7_after_worldgen_ledger`、`roadProvider`、`roadWeaverAvailable`。

返回 artifact 增加：

- `roadWeaverConnectionPlan`
- `roadWeaverRegistrationReport`
- `roadProviderState`

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
- 当所有 planned structures 都有 ledger 时，若 RoadWeaver 已注册，D7 不再覆盖 RoadWeaver 道路；若显式 `worldedit_debug` 或 `auto` fallback，D7 基于 ledger 真实 `actualFootprint` 生成调试道路 / 边界后处理，避障使用 `actualFootprint + roadAvoidanceMarginBlocks`，默认 3。
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
- `roadProviderState`
- `terrainAdaptationReport`

## city_plan_city_walls / city_execute_city_walls

`city_plan_city_walls` 必填参数：

- `runId`
- `citySeedId`

可选：

- `wallVersion=v3|v2|v1_debug`，默认 `v2`。
- `wallBoundaryMode=structure_seeded_patch_region_hull`，v3 兼容字段。
- `wallMarginBlocks`，默认 24。
- `segmentLengthBlocks`，默认 15。
- `gateWidthBlocks`，默认 9。
- `roadScanMarginBlocks`，默认 8。
- `roadProtectionMarginBlocks`，默认 2。
- `maxFoundationDepthBlocks`，默认 8。
- `maxSegmentHeightDeltaBlocks`，默认 7。
- `gateClusterRadiusBlocks`，v3 默认 24。
- `terrainFitUnitLengthBlocks`，v3 默认 5。
- `wallTerrainPolicy=v3|v3.1`，v3 城墙执行层地形策略，默认 `v3`。
- `wallDesignPolicy=v3|v3.2|v3.3`，v3 城墙规划层设计策略，默认 `v3`；`v3.2` 启用天然边界、道路趋势开门、独立 gatehouse 和可用塔节点；`v3.3` 增加近路投影开门。
- `minGateSpacingBlocks`，v3.2 / v3.3 城门最小间距，默认 48。
- `minGateRoadLengthBlocks`，v3.2 / v3.3 道路趋势最小长度，默认 24。
- `roadProjectionMaxDistanceBlocks`，v3.3 近路投影开门最大距离，默认 32。
- `naturalWaterBoundaryMinAreaBlocks`，v3.2 / v3.3 大片水体天然边界最小 patch 面积，默认 4096。
- `flatMaxDeltaBlocks`，v3.1 默认 7。
- `steppedMaxDeltaBlocks`，v3.1 默认 16。
- `mountainProbeDistanceBlocks`，v3.1 默认 6。
- `naturalBoundaryMinDeltaBlocks`，v3.1 默认 17。
- `embeddedSlopeTower`，v3.1 默认 true。

语义：

- 默认 `wallVersion=v2`，读取 D5 `wall_reservation_plan.json`、D7 `placed_structure_ledger.json` 和世界实际方块。
- `wallVersion=v3` 读取 v3 wall reservation 的 `cityDomainMask` / `outerWallRing`，对 actual road mask 进行 road component 分类，内部路不裁门，外部入城路按 cluster 裁门。
- `wallTerrainPolicy=v3.1` 不改变 v3 外环边界，只改变执行层地形策略：8-16 高差生成阶梯墙，高差更大时尝试嵌坡或标记天然峭壁边界。
- `wallDesignPolicy=v3.2` 不改变 v3 外环边界或 v3.1 地形策略，只改变规划层设计语义：大片水体 / shore / cliff 可生成 `natural_boundary` 段并跳过连续墙；外部道路必须满足趋势和长度才生成 `gatehouse`；贴墙 / 擦边 / 碎路进入 `roadTrendSkippedIntersections[]`；城门按 `minGateSpacingBlocks` 合并。
- `wallDesignPolicy=v3.3` 继承 v3.2；外部道路未真正穿墙但靠近墙体、距离不超过 `roadProjectionMaxDistanceBlocks` 且能投影到墙段时，生成 `WALL_GATE_FROM_ROAD_PROJECTION` gatehouse；内部道路仍不裁门，touch-only 碎路仍跳过。
- v2 扫描 wall corridor 附近 actual road mask，按 road-wall intersection 生成 `generatedGates[]`，墙段不得覆盖真实道路。
- `wallVersion=v1_debug` 才使用 v0.1 的 `actualFootprint` union 外扩矩形城墙。
- 输出 `actual_road_mask.json`、`city_wall_plan.json`、`city_wall_preview.png` 和 `city_wall_templates/*.nbt`。
- v3 / v3.1 的 `wallSegments[]` 必须带 `wallAxis=X|Z`，作为执行层拆 unit、生成阶梯切片、判断墙体厚度和嵌坡方向的唯一主轴来源。
- v3.2 的 `wallSegments[]` 允许出现 `segmentType=gatehouse` 和 `segmentType=natural_boundary`；`gatehouse` 使用 `gatehouse_9` / `gatehouse_13`，`natural_boundary` 使用 `natural_water_boundary` / `natural_cliff_boundary` 空模板作为 artifact 标记，不放连续墙。
- v3.3 的 `city_wall_plan.json` 额外包含 `projectedRoadGateCandidates[]`、`roadProjectionSkippedIntersections[]` 和 `roadProjectionMaxDistanceBlocks`；没有直接门或投影门时，fallback 原因为 `NO_VALID_GATE_CANDIDATE_AFTER_FILTER`。

返回 artifact：

- `cityWallPlan`
- `actualRoadMask`
- `cityWallPreview`
- `cityWallTemplateDirectory`
- `sourcePlacedStructureLedger`

`city_execute_city_walls` 必填参数：

- `runId`
- `citySeedId`
- `confirmWorldMutation=true`

可选：

- `dimensionId`
- `playerName`
- `debugScan`，v3 调试开关，默认 false。
- `debugScanStepBlocks`，默认 1。

语义：

- 使用 `city_wall_plan.json` 放置临时石砖城墙、可用塔节点、gate gap 或 v3.2 独立 gatehouse。
- 后端为 `vanilla_setblock`，不依赖 WorldEdit。
- 默认 v2 硬保护 `actualRoadMask`、gate gap 和 structure `actualFootprint`，不覆盖 RoadWeaver 道路或建筑。
- v3 按 `wallAxis` 和 `terrainFitUnitLengthBlocks` 把墙段拆成小 unit，按 unit/column 采样地形，输出 `placementUnitResults[]` 与 `terrainFitMode`，避免因局部高差整段消失；执行层不得用拆碎后的 unit 长宽反推朝向。
- `wallTerrainPolicy` 从 `city_wall_plan.json.terrainFitPolicy.policyVersion` 读取；`v3.1` report 额外输出 `terrainPolicyVersion`、`terrainDeltaBand`、`stepSlices[]`、`mountainProbe` 和 debug sample 的 `policyDecision`。
- `segmentType=natural_boundary` 必须跳过连续墙并在 gap debug 中说明 `NATURAL_WATER_BOUNDARY` / `NATURAL_CLIFF_BOUNDARY`；`segmentType=gatehouse` 必须清出完整门洞并放置石木混合门楼。
- `debugScan=true` 时输出 `wall_terrain_debug_scan.json`、`wall_mask_conflict_report.json`、`wall_gap_debug_report.json`，用于手工 TP 复核缺口原因。

返回 artifact：

- `cityWallPlan`
- `cityWallPlacementReport`
- `wallTerrainDebugScan`
- `wallMaskConflictReport`
- `wallGapDebugReport`

## 推荐调用流程

```text
city_plan_d3
city_profile_structure_envelopes { terrasenseProfileSource, structureIds }
city_plan_d4_candidates { terrasenseProfileSource, designSlotPlan }
city_select_d4_candidates { terrasenseProfileSource, anchorSelectionPlan }
city_plan_d5
city_plan_d6
city_execute_d5 { confirmWorldMutation: true, roadProvider: "auto" }
city_execute_d7 { executeStructurePlacement: false }
city_execute_d7 { executeStructurePlacement: true }
city_plan_city_walls
city_execute_city_walls { confirmWorldMutation: true }
```

真实执行如果返回 `WAITING_FOR_WORLDGEN`，从目标 chunk 外侧靠近 / TP 触发 chunk 首次生成；生成后重复 `city_execute_d7 { executeStructurePlacement: true }` 查询 ledger。若返回 `STRUCTURE_CHUNK_ALREADY_GENERATED`，说明该 chunk 已错过生成期，正式路径不得补贴结构。
