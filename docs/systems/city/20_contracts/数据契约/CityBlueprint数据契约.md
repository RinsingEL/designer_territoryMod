# CityBlueprint 数据契约

## 定位

本文冻结 D4 结构设计与 D6 后户外空间设计共用的单次城市决策边界。Java 不调用 LLM：程序先生成完整只读 `CityBlueprintContext`，AI/Codex 随后只提交一次完整 `CityBlueprint`。上下文准备不计入 AI 城市设计调用。

CityBlueprint 本身不生成结构或景观坐标。结构编译器只消费 `groups[]/relations[]`；D6 锁定真实 footprint 后，户外编译器消费同一 Blueprint 的 `outdoorPlan`。坐标、旋转、模板 identity、collision、逐格 mask 与实际面积只能出现在程序编译产物中。

## 版本

| 对象 | schemaVersion |
| --- | --- |
| 上下文 | `city_blueprint_context.v0.5` |
| 引用目录 | `city_blueprint_reference_catalog.v0.3` |
| 目录快照 | `city_blueprint_catalog_snapshot.v0.6` |
| 蓝图 | `city_blueprint.v0.6` |
| 校验报告 | `city_blueprint_validation_report.v0.3` |
| 提交 trace | `city_blueprint_submission_trace.v0.3` |

## ArtifactRef

所有真值引用统一使用严格对象：

```json
{
  "path": "run/city_d3_city/city_landform_review_package.json",
  "schemaVersion": "city_landform_review.v0.1",
  "contentHash": "sha256:<64 lowercase hex>"
}
```

`path` 是相对运行时 debug root 的冻结路径。提交时文件内容 hash 失配即 stale，不按文件名或修改时间猜兼容。

## CityBlueprintContext

必填字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `schemaVersion` | string | 固定 `city_blueprint_context.v0.5`。 |
| `contextId` | string | 对除 `preparedAt` 外的冻结上下文做 SHA-256。 |
| `runId` / `cityId` | string | 当前 run 与城市。 |
| `sourceD3Ref` | ArtifactRef | 当前 D3 review package。 |
| `catalogSnapshotRef` | ArtifactRef | 本次完整目录快照。 |
| `generationSeedSuggestion` | safe integer | 程序按 city + D3 hash + catalog hash 稳定派生，范围为 JavaScript safe integer。 |
| `decisionBoundary` | object | 明确 prepare 不计 AI 调用、最多一次提交、提交后不允许候选请求。 |
| `citySeed` | object | 当前 CitySeed 完整只读输入。 |
| `d3ReviewPackage` | object | D3 地形、patch、member cells、指标、邻接与 preview 引用。 |
| `catalogSnapshot` | object | `city_blueprint_catalog_snapshot.v0.6`；包含 `city_semantic_profile_catalog.v0.4` 结构画像、固定模板目录、Blueprint v0.3 引用目录及 D3 terrain field 引用。引用目录同时冻结 LandUse rule、Surface recipe 和 Landscape profile 完整定义，D6 后不得重新解释为另一版配置。 |
| `preparedAt` | instant | 追踪字段，不进入 `contextId`。 |

D3 `status=partial`、未知 schema、城市 ID 不一致，以及 AI 候选首都未接受/审查 identity 过期时，不得准备上下文。

## Structure Terrain Modes

`terrainModes` 是 City 固定 placement topology 枚举数组，不属于 TerraSense 动态词表。值域严格为 `SURFACE | EMBEDDED | FLOATING`，导入时大小写归一为大写；正式画像必须非空，未知值或归一后重复值直接拒绝。旧 `terrainTerms` 是退役字段，导入器必须显式拒绝。

多值按 OR 解析。当前运行时只真正实现 `SURFACE`：只要数组含 `SURFACE`，D4 便解析并冻结 `resolvedTerrainMode=SURFACE`；只有 `EMBEDDED/FLOATING` 时明确返回 `CITY_STRUCTURE_TERRAIN_MODE_UNSUPPORTED`，不得伪装为已支持。

SURFACE 门禁只读取已有 `city_land_use_terrain_field.v0.1`，不触发扫描或 chunk 加载。transformed collision footprint 覆盖的每个 terrain-field cell 必须存在、`sampled=true` 且 `water=false`。坡度、`localRelief`、roughness、biome 与 landform 不做结构硬拒绝；它们仍可参与既有地形适配评分或诊断。Context/Snapshot 只冻结 `terrainFieldRef` 的 schema 与内容 hash；文件变化、city/grid/step 不一致均 stale。

## Blueprint 引用目录

引用目录根对象所有数组必填且非空：

- `structureRefs[]`：`structureRef` 必须存在于冻结 TerraSense semantic profile；`templateCandidates[]` 的 `templateId + variantId` 必须存在于固定模板目录。
- `fillPools[]`：`poolRef` 与只引用上述 `structureRef` 的 `structureRefs[]`。
- `algorithmProfiles[]`：`algorithmProfileRef`；算法枚举为 `COMPACT | GRID | LINEAR | COURTYARD | ORGANIC_COMPACT`。
- `compositionProfiles[]`：`compositionProfileRef` 与 `mode=ROUND_ROBIN`；只控制模板组成顺序，不携带建筑数量上限。
- `styleProfiles[]`：`profileRef`。
- `roadProfiles[]`：`profileRef`、`hierarchy=SIMPLE|HIERARCHICAL`、`density=SPARSE|BALANCED|DENSE`。
- `surfaceDetailProfiles[]`：`profileRef`、`intensity=LOW|MEDIUM|HIGH`。
- `landUseRuleProfile`：完整严格 `city_land_use_rules.v0.1`；其 `ruleRef` 是 SpatialGround 的唯一规则白名单。
- `surfaceRecipes[]`：冻结 `surfaceRecipeRef`、是否写地表、默认自动连接、`UNIFORM|CONTOUR_BANDS` 和算法所需全部方块材料；Blueprint 只引用 recipe ID，不提交 block ID。
- `landscapeProfiles[]`：冻结 `landscapeProfileRef`、`FARMLAND|COMMON_GREEN|WOODLAND|MEADOW|POND`、LandUse rule、Surface recipe、SMALL/MEDIUM/LARGE 基准面积和 `URBAN|LANDSCAPE` membership。

所有 namespace 内引用唯一。案子 02 必须按这些冻结 ID 读取配置，不得把 Blueprint 字符串解释为自由算法或隐藏模板路径。

## CityBlueprint v0.6

根字段全部必填，未知字段拒绝：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `schemaVersion` | string | 固定 `city_blueprint.v0.6`；v0.5 的逐建筑地表与 residual policy 不兼容。 |
| `cityId` | string | 与 context / D3 一致。 |
| `sourceD3Ref` / `catalogSnapshotRef` | ArtifactRef | 与 context 逐字段一致。 |
| `generationSeed` | safe integer | `-9007199254740991..9007199254740991`；后续编译器唯一记录随机源。 |
| `designIntent` | object | `cityIdentity`、`theme`、非空 `functionalRoles[]`。 |
| `styleProfile` | object | 仅 `profileRef`。 |
| `groups[]` | Group[] | 至少一个。 |
| `relations[]` | Relation[] | 可为空。 |
| `roadProfile` | object | 仅 `profileRef`。 |
| `surfaceDetailProfile` | object | 仅 `profileRef`。 |
| `outdoorPlan` | OutdoorPlan | 同一次提交中的完整户外设计意图。 |

Group 必填字段：

| 字段 | 值域 |
| --- | --- |
| `groupId` | 蓝图内唯一非空字符串。 |
| `groupKind` | v0.6 仍只接受 `STRUCTURE`；景观只能进入 `outdoorPlan.landscapes[]`。 |
| `preferredPatchRefs[]` | 非空当前 D3 `landformPatchId` 列表；多个 Group 可以共享。 |
| `preferredPatchZone` | `CENTER | NORTH | EAST | SOUTH | WEST`；核心在全部偏好 patch 精确 member-cell 并集内的起步方位。北=-Z、南=+Z、西=-X、东=+X；不表示世界坐标，也不约束连接阶段。 |
| `role` | 非空功能角色。 |
| `priority` | `CORE | STANDARD | PERIPHERAL`。 |
| `extentClass` | `SMALL | MEDIUM | LARGE`，表示空间范围而非建筑数量。 |
| `densityClass` | `SPARSE | BALANCED | DENSE`。 |
| `algorithmProfileRef` | 冻结算法引用。 |
| `terrainPolicy` | `CONFORM | BALANCED | ASSERTIVE`。 |
| `requiredStructureRefs[]` | 非空且全部在结构白名单。 |
| `fillPoolRef` / `compositionProfileRef` | 冻结目录引用；composition 不限制数量。 |
| `connectionPlan` | 可选连接专用覆写；不填时继承本 Group 的 fill pool、算法和疏密。 |
| `attachedFeatures[]` | 当前版本必须为空；案子 04 才定义景观归属。 |

`connectionPlan` 只表达连接阵列语义，不表达结构永久类型，也不提交坐标：

| 字段 | 值域与继承 |
| --- | --- |
| `structurePoolRef` | 可选；连接阶段使用的结构池，不填继承 `fillPoolRef`，允许与 fill pool 相同。 |
| `algorithmProfileRef` | 可选；连接阵列算法，不填继承 Group 的 `algorithmProfileRef`。 |
| `densityClass` | 可选 `SPARSE | BALANCED | DENSE`；不填继承 Group 疏密，并由程序换算实体间距与 handoff。 |
| `parameters.clusterShape` | `ORGANIC_COMPACT | GRID | COURTYARD | L_SHAPE | U_SHAPE`；只适用于解析为 `compound_cluster` 的算法。 |
| `parameters.sideMode` | `LEFT | RIGHT | BOTH`；只适用于解析为 `guide_line_dual_side` 的 LINEAR 算法。 |
| `parameters.stagger` | boolean；只适用于 `guide_line_dual_side`。 |
| `parameters.widthClass` | `NARROW | MEDIUM | WIDE`；只适用于 `guide_line_dual_side`，控制阵列宽度档位而非 block 宽度。 |

连接参数与解析后的 planner family 不匹配时返回 `CITY_BLUEPRINT_CONNECTION_PARAMETERS_INVALID`。AI 不提交 focus、外扩方向、block gap、候选数量、candidateId 或逐栋坐标；这些都由编译器按当前已提交阵列和目标 Group 自动派生。

Relation 必填 `fromGroupId`、`toGroupId`、`relationKind`、`strength`、`distancePreference`、`directionPreference`。`relationKind` 为 `HIERARCHY | ADJACENCY | CONNECTION | BUFFER | DISTANCE | DIRECTION`，`strength` 为 `HARD | SOFT`。只有 `DISTANCE` 可使用 `distancePreference=NEAR|FAR`，其他关系必须为 `NONE`；只有 `DIRECTION` 可使用 `directionPreference=NORTH|EAST|SOUTH|WEST`，其他关系必须为 `NONE`。`HIERARCHY` 按 `fromGroupId -> toGroupId` 表示父到子，必须无环；编译器据此做稳定拓扑排序，同批节点再按 priority 和 `groupId` 排序。

## OutdoorPlan

`outdoorPlan` 根字段严格为 `mode`、`envelopeProfile`、`spatialGrounds[]` 和 `landscapes[]`，未知字段拒绝。

- `mode=GENERATE`：每个 STRUCTURE Group 必须且只能有一项 spatial ground；D6 后自动编译城市空间织体。
- `mode=PRESERVE`：`spatialGrounds[]` 与 `landscapes[]` 必须为空。
- `envelopeProfile=COMPACT|BALANCED|LOOSE`：只选择冻结的城市包络形态档位，程序映射为固定形态学半径，不接受 block 数。

`spatialGrounds[]` 每项字段：

| 字段 | 类型 / 值域 | 说明 |
| --- | --- | --- |
| `sourceGroupId` | string | 必须引用本 Blueprint 的 STRUCTURE Group；全表唯一。 |
| `landUseRuleRef` | string | 冻结 LandUse rule 引用。 |
| `surfaceRecipeRef` | string | 冻结 Surface recipe 引用。 |
| `sharedSpaceType` | `CIVIC_SQUARE|MARKET_STREET|RESIDENTIAL_COURT|FARMSTEAD|GENERAL_URBAN` | 组团共享空间的建筑学类型。 |
| `hierarchyLevel` | `PRIMARY|SECONDARY|LOCAL` | 城市主脉、次级连接和本地空间的层级。 |
| `membership` | `URBAN|LANDSCAPE` | 是否参与城市包络；农业等外围地表必须使用 LANDSCAPE。 |

`landscapes[]` 每项字段：

| 字段 | 类型 / 值域 | 说明 |
| --- | --- | --- |
| `landscapeId` | string | 户外计划内唯一；不得与其他 landscape 重复。 |
| `landscapeProfileRef` | string | 冻结景观 profile，决定 rule、surface recipe、基准面积和 membership。 |
| `attachedGroupIds[]` | string[] | 可为空；非空项引用 STRUCTURE Group，D6 后提供 footprint / entrance seed。 |
| `preferredPatchRefs[]` | string[] | 可为空；非空项必须命中冻结 D3 patch。attached 与 patch 至少一者非空。 |
| `extentClass` | `SMALL|MEDIUM|LARGE` | 从 profile 选择基准面积。 |
| `intensity` | `LOW|MEDIUM|HIGH` | 程序化面积/内容强度档位，不是裸比例。 |
| `continuity` | `CONTINUOUS|MULTI_PARCEL|PATCHY` | seed 与连通组件策略。 |
| `growthRelation` | `AROUND_SOURCE|AWAY_FROM_REFERENCE|TOWARD_WATER|ALONG_WATER` | 选择程序白名单生长关系。 |
| `referenceGroupIds[]` | string[] | `AWAY_FROM_REFERENCE` 的参考 Group；其他模式按 validator 规则限制。 |
| `terrainPolicy` | `CONFORM|BALANCED|ASSERTIVE` | 景观地形适配档位。 |
| `required` | boolean | 无合法 seed / 容量明显不足时是否 hard fail。 |

农田 landscape 的多个 attached 建筑只贡献 seed，始终共享一份 landscape 总预算；不得回到“每栋建筑各贡献完整农田面积”的线性叠加。`CONTINUOUS` 编译为 1 个 parcel growth region，`MULTI_PARCEL` 最多 2 个，`PATCHY` 最多 4 个；各 region 的 `min/preferred/max` 由同一总预算确定性拆分，求和必须与 landscape 总预算严格相等。

`residualPolicy` 已删除。城市包络内部的剩余单元必须由程序并入最近的 SpatialGround，不能由 AI 或旧面积上限选择原群系回退。显式自然、绿地和农田只能通过 `landscapes[]` 声明。

## 禁止字段

Blueprint 任意层级禁止：世界/block `x/y/z`、`blockX/Y/Z`、anchor、rotation、mirror、candidateId、直接 templateId/templateRef/nbtFile、`algorithm` 或 `algorithmName`。户外层另禁止 block ID、逐格 mask、裸面积、行动力和成本。它们属于程序输出，不属于 AI 决策。

## 校验与一次提交

- 同一 `contextId` 最多消费一次 AI 城市设计提交。非法提交也会消费该 context 的一次预算；要重新设计必须产生不同输入身份的新 context。
- `preferredPatchRefs[]` 必须非空并命中 D3；多个 Group 可以共享 patch；Group ID 唯一；relation 端点存在且不自指。
- 所有 D3、catalog、structure、pool、algorithm、composition、style、road、surface 引用必须命中冻结快照。
- `GENERATE` 必须完整覆盖全部 STRUCTURE Group；户外 group、landscape、patch、rule、recipe、profile 和 reference Group 必须命中同一冻结上下文。
- 校验失败写 validation report 与 trace，但不得覆盖最后一次有效 `city_blueprint.json`。
- trace 记录 `aiCityDesignSubmissionCount`、prepare 是否计数、D3/catalog refs、status 和 failure reasons；不保存被拒 Blueprint payload。

主要 reason code：

```text
CITY_BLUEPRINT_SCHEMA_UNSUPPORTED
CITY_BLUEPRINT_FORBIDDEN_PLACEMENT_FIELD
CITY_BLUEPRINT_CONTEXT_STALE
CITY_BLUEPRINT_D3_STALE
CITY_BLUEPRINT_CATALOG_STALE
CITY_BLUEPRINT_AI_SUBMISSION_ALREADY_CONSUMED
CITY_BLUEPRINT_GROUP_KIND_UNSUPPORTED
CITY_BLUEPRINT_PREFERRED_PATCH_UNKNOWN
CITY_BLUEPRINT_RELATION_ENDPOINT_UNKNOWN
CITY_BLUEPRINT_STRUCTURE_REF_UNKNOWN
CITY_BLUEPRINT_FILL_POOL_UNKNOWN
CITY_BLUEPRINT_ALGORITHM_PROFILE_UNKNOWN
CITY_BLUEPRINT_CONNECTION_PARAMETERS_INVALID
CITY_BLUEPRINT_COMPOSITION_PROFILE_UNKNOWN
CITY_BLUEPRINT_STYLE_PROFILE_UNKNOWN
CITY_BLUEPRINT_ROAD_PROFILE_UNKNOWN
CITY_BLUEPRINT_SURFACE_DETAIL_PROFILE_UNKNOWN
CITY_BLUEPRINT_ATTACHED_FEATURE_UNSUPPORTED
```

## 01 -> 02 审查门

案子 02 的冻结输入是：校验通过的 `city_blueprint.json`、同目录 `city_blueprint_catalog_snapshot.json`、Blueprint 中两份 ArtifactRef 和 `generationSeed`。编译器不得再次请求 AI 选择 candidate/slot/扩张方向，且最终必须输出现有标准 `structure_anchor_plan.json` / `structure_anchor_map.json`。

02 已接通：`city_run_workflow` 默认 `d4CandidateMode=blueprint`。所有 candidate/session/manual anchor 接口统一视为 `legacy/debug`，只有显式指定旧 mode 才执行，不属于新的正式 Blueprint 决策边界。

## CityGenerationCompileTrace v0.9

文件：`city_d4_<cityId>/city_generation_compile_trace.json`，`schemaVersion=city_generation_compile_trace.v0.9`。

根字段：`cityId`、`status=compiled|failed`、`reasonCode`、`generationSeed`、`selectionMode`、`aiCandidateSelectionCount=0`、`manualCandidateSelectionCount=0`、`sourceD3Ref`、`catalogSnapshotRef`、`connectivityPlan`、`selections[]`、`groupResults[]`。

每个 selection 按执行顺序记录 `phase=required|fill|connectivity_growth`。全部 Group 的 required 先完成，随后各 Group 的 fill 完成内部成形，最后才允许出现 connectivity selection。required/fill 继续记录单结构候选、评分、envelope 与提交状态；connectivity selection 必须按完整阵列批次记录 `arrayId`、`plannerType`、`focusArrayId`、自动方向、`resolvedConnectionPlan`、语义参数、近圈搜索 trace、候选数、选中 candidate、批次 anchor IDs、连接前后 gap 与整批结构数。任一连接批次只有完整 cardinality、全部 terrain/collision 合法且确实缩短目标 gap 时才能原子提交，不得部分落地。

connectivity selection 另必填 `requestedBatchSize`、`terminalBatch`、`initialBodyGapBlocks`、`frontierGapCorrectionBlocks`；对应 `frontierSearchTrace[].rings[]` 记录 `correctedForBodyGap`。批量从解析后的配置规模按 `N..1` 确定性降级重试，失败尝试同样进入 trace；一组完整合法候选即可提交，零组才失败。`minCandidateCount` 不属于 Blueprint 或编译请求，旧字段必须以 `D4_ARRAY_LAYOUT_MIN_CANDIDATE_COUNT_REMOVED` 明确拒绝。

required、fill 和 connectivity batch 必须调用同一 Structure Terrain gate。门禁以 transformed collision footprint 为范围，对 `terrainModes` 做 OR 解析；当前 SURFACE 要求全部相交 D3 terrain-field cells 存在、已采样且非水，不得只检查 anchor 点、首个 patch 或 dominant biome。trace 至少记录 `structureRef`、`declaredTerrainModes`、`resolvedTerrainMode`、footprint、相交/已评估/拒绝格数、reasonCode 和有限失败样本；anchor 同样冻结 `resolvedTerrainMode`。`styleTerms` 不得出现在 gate、分数或候选排序依据中。

`selections[]` 的 committed 项与最终 `StructureAnchorPlan.anchors[]` 必填 `blueprintLayout`：`algorithm`、从 0 连续递增的 `slotIndex`、`spacingBlocks`、`outwardGuided`、`densityParameters`、`preferredPatchZone`，可选 `outwardTarget`；首个核心另写精确 `coreSeedCell`，anchor 另冻结 `acceptedAnchor`。该字段是程序 provenance，不是 AI 输入坐标。

`connectivityPlan` 必填 `topologyPolicy=EXPLICIT_RELATIONS_THEN_DETERMINISTIC_SHORTEST_FALLBACK`、`handoffThresholdPolicy=STRICT_BILATERAL_MINIMUM`、`edgeCount`、`fallbackEdgeCount` 与 `edges[]`。每条边必填 `fromGroupId`、`toGroupId`、`topologySource=EXPLICIT|FALLBACK`、`topologyReason`、`initialGapBlocks`、`finalGapBlocks`、`handoffGapBlocks`、`connectionStructureCount`、`connectionBatchCount`、`status`；fallback 原因固定为 `DETERMINISTIC_SHORTEST_COMPONENT_EDGE`。`handoffGapBlocks` 及 HARD 关系复验必须同源读取双方解析后的 `resolvedConnectionPlan.derivedLayoutParameters.landUseHandoffGapBlocks` 严格最小值，不得混用 Group required/fill 的内部 handoff。

`groupResults[]` 必填 `groupId`、`requestedExtentClass`、`densityClass`、`densityParameterization=ALGORITHM_SPECIFIC`、`layoutAlgorithm`、`layoutParameters`、`resolvedConnectionPlan`、`targetAreaBlocks`、`maxExtentSpanBlocks`、`maxIntraGroupGapBlocks`、`outwardGuidedPlacementCount`、`derivedMinimumStructureCount`、`internalStructureCount`、`minimumStructureCountReached`、`internalSpatialDemandBlocks`、`connectionStructureCount`、`connectionBatchCount`、`connectionSpatialDemandBlocks`、`connectionExpansionBlocks`、`extentExpandedForConnectivity`、`actualStructureCount`、`requiredStructureCount`、`builtCollisionAreaBlocks`、`actualSpatialDemandBlocks`、`estimatedCoverageRatio`、`preferredPatchRefs[]`、`claimedPatchRefs[]`、`structureCounts` 与 `stopReason`。`resolvedConnectionPlan` 必须写出继承后的 pool、算法、planner、疏密及继承来源。`SPATIAL_BUDGET_REACHED` 是正常完成，`CONNECTED_SPACE_EXHAUSTED` 只表示达到最低成形量后未填满空间预算；未达到最低成形量必须 hard fail。连接阶段可越过 extent 软目标，但不得越过 D3 规划网格等硬边界。

`groupResults[]` 与 extent 中的每个 Group 还必须回写 `preferredPatchZone`，用于区分 AI 指定的内部方位与程序最终认领的 `claimedPatchRefs[]`。

## GroupExtentMap v0.7

文件：`city_d4_<cityId>/group_extent_map.json`，`schemaVersion=group_extent_map.v0.7`。根字段为 `cityId`、`generationSeed`、`connectivityPolicy=RELATION_GRAPH_ARRAY_GROWTH_THEN_LAND_USE`、`connectionSemantics=STRUCTURE_FRONTIER_FOR_LAND_USE`、`cityBoundaryPolicy=D3_REVIEW_GRID_HARD_BOUNDARY`、`handoffThresholdPolicy=STRICT_BILATERAL_MINIMUM`、`structureGraphConnected`、`landUseConnected=false`、`landUseConnectionStatus=PENDING_LAND_USE_COMPILE`、`connections[]`、`groups[]`。不得出现 `maxInterGroupGapBlocks` 或含糊的旧 `connected` 字段；调用方不得自行把结构拓扑解释成实体地表连通。

`connections[]` 与 compile trace 边字段同源，并增加 `landUseHandoffReady` 与 `connectionEdge{fromX,fromZ,toX,toZ}`；每个 Group 同时携带上述布局/空间/count/stop 字段和 closed `collisionExtent{minX,minZ,maxX,maxZ}`。所有 Group 的 required 核心必须先在各自 `preferredPatchRefs[]` 播种；连接阶段允许认领 D3 `review.grid` 内其他 patch/member cells，并在 `claimedPatchRefs[]` 中解释。Group `terrainPolicy` 只形成排序偏好与 trace，不按 patch 平均坡度硬裁剪。Group 间初始距离不构成 D4 固定阈值；LandUse 编译后必须另以真实 block spans 验收连续性。

`extentClass` 核心/fill 目标空间预算为 `4096 / 16384 / 36864 blocks²`，最大跨度为 `96 / 160 / 240 blocks`。程序另按 D3 `targetScale.scale` 与 `extentClass` 派生最低成形栋数：HAMLET=`2/3/4`、VILLAGE=`3/4/6`、TOWN=`3/6/9`、CITY=`4/8/12`（SMALL/MEDIUM/LARGE）。它不是 Blueprint 输入数量；最终结构数仍是模板 collision、疏密、算法和空间预算共同形成的输出事实。连接结构只计入 `actualStructureCount/actualSpatialDemandBlocks` 与 connection 专用字段，不计入 `internalStructureCount/internalSpatialDemandBlocks` 或最低成形判定。连接阶段绕过 extent 软目标，但仍受 D3 grid、collision、结构 terrain mode gate、组内连续最大 gap 和内部 256 anchor 安全护栏约束；安全护栏命中必须 hard fail，不能作为正常规模停止原因。

若任一 Group 在连接前无法达到 `derivedMinimumStructureCount`，编译必须以 `CITY_BLUEPRINT_GROUP_MINIMUM_UNREACHABLE` 失败；不得进入 connectivity growth 后再用连接建筑补足数量。

编译成功后仍必须输出原有 `city_structure_anchor_plan.v0.2`、`city_structure_anchor_map.v0.2` 与结构预览。D5/D6 只消费这些标准产物，不读取 Blueprint、compile trace 或 extent map 建立特殊分支。
