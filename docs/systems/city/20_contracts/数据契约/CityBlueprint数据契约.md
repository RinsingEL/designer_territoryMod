# CityBlueprint 数据契约

## 定位

本文冻结案子 01 的 D4 单次城市决策边界。Java 不调用 LLM：程序先生成完整只读 `CityBlueprintContext`，AI/Codex 随后只提交一次完整 `CityBlueprint`。上下文准备不计入 AI 城市设计调用。

CityBlueprint 本身不生成结构坐标。案子 02 已接通程序化编译器，只能消费校验通过的 `city_blueprint.json` 和同一目录快照；坐标、旋转、模板 identity、collision 与 Group 范围只能出现在编译产物中。

## 版本

| 对象 | schemaVersion |
| --- | --- |
| 上下文 | `city_blueprint_context.v0.2` |
| 引用目录 | `city_blueprint_reference_catalog.v0.2` |
| 目录快照 | `city_blueprint_catalog_snapshot.v0.2` |
| 蓝图 | `city_blueprint.v0.4` |
| 校验报告 | `city_blueprint_validation_report.v0.2` |
| 提交 trace | `city_blueprint_submission_trace.v0.2` |

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
| `schemaVersion` | string | 固定 `city_blueprint_context.v0.2`。 |
| `contextId` | string | 对除 `preparedAt` 外的冻结上下文做 SHA-256。 |
| `runId` / `cityId` | string | 当前 run 与城市。 |
| `sourceD3Ref` | ArtifactRef | 当前 D3 review package。 |
| `catalogSnapshotRef` | ArtifactRef | 本次完整目录快照。 |
| `generationSeedSuggestion` | safe integer | 程序按 city + D3 hash + catalog hash 稳定派生，范围为 JavaScript safe integer。 |
| `decisionBoundary` | object | 明确 prepare 不计 AI 调用、最多一次提交、提交后不允许候选请求。 |
| `citySeed` | object | 当前 CitySeed 完整只读输入。 |
| `d3ReviewPackage` | object | D3 地形、patch、member cells、指标、邻接与 preview 引用。 |
| `catalogSnapshot` | object | TerraSense 结构画像、固定模板目录和 Blueprint 引用目录。 |
| `preparedAt` | instant | 追踪字段，不进入 `contextId`。 |

D3 `status=partial`、未知 schema、城市 ID 不一致，以及 AI 候选首都未接受/审查 identity 过期时，不得准备上下文。

## Blueprint 引用目录

引用目录根对象所有数组必填且非空：

- `structureRefs[]`：`structureRef` 必须存在于冻结 TerraSense semantic profile；`templateCandidates[]` 的 `templateId + variantId` 必须存在于固定模板目录。
- `fillPools[]`：`poolRef` 与只引用上述 `structureRef` 的 `structureRefs[]`。
- `algorithmProfiles[]`：`algorithmProfileRef`；算法枚举为 `COMPACT | GRID | LINEAR | COURTYARD | ORGANIC_COMPACT`。
- `compositionProfiles[]`：`compositionProfileRef` 与 `mode=ROUND_ROBIN`；只控制模板组成顺序，不携带建筑数量上限。
- `styleProfiles[]`：`profileRef`。
- `roadProfiles[]`：`profileRef`、`hierarchy=SIMPLE|HIERARCHICAL`、`density=SPARSE|BALANCED|DENSE`。
- `surfaceDetailProfiles[]`：`profileRef`、`intensity=LOW|MEDIUM|HIGH`。

所有 namespace 内引用唯一。案子 02 必须按这些冻结 ID 读取配置，不得把 Blueprint 字符串解释为自由算法或隐藏模板路径。

## CityBlueprint v0.4

根字段全部必填，未知字段拒绝：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `schemaVersion` | string | 固定 `city_blueprint.v0.4`；v0.3 缺少连接阵列意图，不兼容。 |
| `cityId` | string | 与 context / D3 一致。 |
| `sourceD3Ref` / `catalogSnapshotRef` | ArtifactRef | 与 context 逐字段一致。 |
| `generationSeed` | safe integer | `-9007199254740991..9007199254740991`；后续编译器唯一记录随机源。 |
| `designIntent` | object | `cityIdentity`、`theme`、非空 `functionalRoles[]`。 |
| `styleProfile` | object | 仅 `profileRef`。 |
| `groups[]` | Group[] | 至少一个。 |
| `relations[]` | Relation[] | 可为空。 |
| `roadProfile` | object | 仅 `profileRef`。 |
| `surfaceDetailProfile` | object | 仅 `profileRef`。 |

Group 必填字段：

| 字段 | 值域 |
| --- | --- |
| `groupId` | 蓝图内唯一非空字符串。 |
| `groupKind` | v0.3 只接受 `STRUCTURE`；`LANDSCAPE` 明确失败。 |
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

## 禁止字段

Blueprint 任意层级禁止：世界/block `x/y/z`、`blockX/Y/Z`、anchor、rotation、mirror、candidateId、直接 templateId/templateRef/nbtFile、`algorithm` 或 `algorithmName`。这些信息属于案子 02 的程序输出，不属于 AI 决策。

## 校验与一次提交

- 同一 `contextId` 最多消费一次 AI 城市设计提交。非法提交也会消费该 context 的一次预算；要重新设计必须产生不同输入身份的新 context。
- `preferredPatchRefs[]` 必须非空并命中 D3；多个 Group 可以共享 patch；Group ID 唯一；relation 端点存在且不自指。
- 所有 D3、catalog、structure、pool、algorithm、composition、style、road、surface 引用必须命中冻结快照。
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

## CityGenerationCompileTrace v0.6

文件：`city_d4_<cityId>/city_generation_compile_trace.json`，`schemaVersion=city_generation_compile_trace.v0.6`。

根字段：`cityId`、`status=compiled|failed`、`reasonCode`、`generationSeed`、`selectionMode`、`aiCandidateSelectionCount=0`、`manualCandidateSelectionCount=0`、`sourceD3Ref`、`catalogSnapshotRef`、`connectivityPlan`、`selections[]`、`groupResults[]`。

每个 selection 按执行顺序记录 `phase=required|connectivity_growth|fill`。required/fill 继续记录单结构候选、评分、envelope 与提交状态；connectivity selection 必须按完整阵列批次记录 `arrayId`、`plannerType`、`focusArrayId`、自动方向、`resolvedConnectionPlan`、语义参数、近圈搜索 trace、候选数、选中 candidate、批次 anchor IDs、连接前后 gap 与整批结构数。任一连接批次只有完整 cardinality、全部 terrain/collision 合法且确实缩短目标 gap 时才能原子提交，不得部分落地。

`selections[]` 的 committed 项与最终 `StructureAnchorPlan.anchors[]` 必填 `blueprintLayout`：`algorithm`、从 0 连续递增的 `slotIndex`、`spacingBlocks`、`outwardGuided`、`densityParameters`、`preferredPatchZone`，可选 `outwardTarget`；首个核心另写精确 `coreSeedCell`，anchor 另冻结 `acceptedAnchor`。该字段是程序 provenance，不是 AI 输入坐标。

`connectivityPlan` 必填 `topologyPolicy=EXPLICIT_RELATIONS_THEN_DETERMINISTIC_SHORTEST_FALLBACK`、`handoffThresholdPolicy=STRICT_BILATERAL_MINIMUM`、`edgeCount`、`fallbackEdgeCount` 与 `edges[]`。每条边必填 `fromGroupId`、`toGroupId`、`topologySource=EXPLICIT|FALLBACK`、`topologyReason`、`initialGapBlocks`、`finalGapBlocks`、`handoffGapBlocks`、`connectionStructureCount`、`connectionBatchCount`、`status`；fallback 原因固定为 `DETERMINISTIC_SHORTEST_COMPONENT_EDGE`。`handoffGapBlocks` 及 HARD 关系复验必须同源读取双方解析后的 `resolvedConnectionPlan.derivedLayoutParameters.landUseHandoffGapBlocks` 严格最小值，不得混用 Group required/fill 的内部 handoff。

`groupResults[]` 必填 `groupId`、`requestedExtentClass`、`densityClass`、`densityParameterization=ALGORITHM_SPECIFIC`、`layoutAlgorithm`、`layoutParameters`、`resolvedConnectionPlan`、`targetAreaBlocks`、`maxExtentSpanBlocks`、`maxIntraGroupGapBlocks`、`outwardGuidedPlacementCount`、`connectionStructureCount`、`connectionBatchCount`、`connectionSpatialDemandBlocks`、`connectionExpansionBlocks`、`extentExpandedForConnectivity`、`actualStructureCount`、`requiredStructureCount`、`builtCollisionAreaBlocks`、`actualSpatialDemandBlocks`、`estimatedCoverageRatio`、`preferredPatchRefs[]`、`claimedPatchRefs[]`、`structureCounts` 与 `stopReason`。`resolvedConnectionPlan` 必须写出继承后的 pool、算法、planner、疏密及继承来源。`SPATIAL_BUDGET_REACHED` 是正常完成，`CONNECTED_SPACE_EXHAUSTED` 是保留必要结构后的软停；连接阶段可越过 extent 软目标，但不得越过 D3 规划网格等硬边界。

`groupResults[]` 与 extent 中的每个 Group 还必须回写 `preferredPatchZone`，用于区分 AI 指定的内部方位与程序最终认领的 `claimedPatchRefs[]`。

## GroupExtentMap v0.6

文件：`city_d4_<cityId>/group_extent_map.json`，`schemaVersion=group_extent_map.v0.6`。根字段为 `cityId`、`generationSeed`、`connectivityPolicy=RELATION_GRAPH_ARRAY_GROWTH_THEN_LAND_USE`、`connectionSemantics=STRUCTURE_FRONTIER_FOR_LAND_USE`、`cityBoundaryPolicy=D3_REVIEW_GRID_HARD_BOUNDARY`、`handoffThresholdPolicy=STRICT_BILATERAL_MINIMUM`、`structureGraphConnected`、`landUseConnected=false`、`landUseConnectionStatus=PENDING_LAND_USE_COMPILE`、`connections[]`、`groups[]`。不得出现 `maxInterGroupGapBlocks` 或含糊的旧 `connected` 字段；调用方不得自行把结构拓扑解释成实体地表连通。

`connections[]` 与 compile trace 边字段同源，并增加 `landUseHandoffReady` 与 `connectionEdge{fromX,fromZ,toX,toZ}`；每个 Group 同时携带上述布局/空间/count/stop 字段和 closed `collisionExtent{minX,minZ,maxX,maxZ}`。所有 Group 的 required 核心必须先在各自 `preferredPatchRefs[]` 播种；连接阶段允许认领 D3 `review.grid` 内符合 terrain policy 的其他 patch/member cells，并在 `claimedPatchRefs[]` 中解释。Group 间初始距离不构成 D4 固定阈值；LandUse 编译后必须另以真实 block spans 验收连续性。LandUse 子系统自身的 64 格自动连接策略是独立契约，不属于本 D4 extent map。

`extentClass` 核心/fill 目标空间预算为 `4096 / 16384 / 36864 blocks²`，最大跨度为 `96 / 160 / 240 blocks`。`densityClass` 必须经当前布局算法参数化；基础 target/max/handoff gap 见案子 02，空间需求按模板 collision 与算法 gap/multiplier 计算。结构数是输出事实，不是输入约束。连接阶段绕过 extent 软目标，但仍受 D3 grid、collision、terrain policy、组内连续最大 gap 和内部 256 anchor 安全护栏约束；安全护栏命中必须 hard fail，不能作为正常规模停止原因。

编译成功后仍必须输出原有 `city_structure_anchor_plan.v0.2`、`city_structure_anchor_map.v0.2` 与结构预览。D5/D6 只消费这些标准产物，不读取 Blueprint、compile trace 或 extent map 建立特殊分支。
