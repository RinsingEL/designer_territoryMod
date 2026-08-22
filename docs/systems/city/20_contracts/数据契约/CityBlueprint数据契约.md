# CityBlueprint 数据契约

## 定位

本文冻结 D4 结构设计与 D6 后户外空间设计共用的单次城市决策边界。Java 不调用 LLM：程序先生成完整只读 `CityBlueprintContext`，AI/Codex 随后只提交一次完整 `CityBlueprint`。上下文准备不计入 AI 城市设计调用。

CityBlueprint 本身不生成结构或景观坐标。结构编译器消费 `groups[]/arrayCompositions[]/relations[]`；D6 锁定真实 footprint 后，户外编译器消费同一 Blueprint 的 `outdoorPlan`。坐标、旋转、模板 identity、collision、逐格 mask 与实际面积只能出现在程序编译产物中。

## 版本

| 对象 | schemaVersion |
| --- | --- |
| 上下文 | `city_blueprint_context.v0.10` |
| 引用目录 | `city_blueprint_reference_catalog.v0.8` |
| 目录快照 | `city_blueprint_catalog_snapshot.v0.10` |
| 蓝图 | `city_blueprint.v0.11` |
| 校验报告 | `city_blueprint_validation_report.v0.4` |
| 提交 trace | `city_blueprint_submission_trace.v0.4` |

## ArtifactRef

所有真值引用统一使用严格对象：

```json
{
  "path": "<runId>/city_test_runs/<citySeedId>/steps/d3/city_landform_review_package.json",
  "schemaVersion": "city_landform_review.v0.1",
  "contentHash": "sha256:<64 lowercase hex>"
}
```

`path` 是相对运行时 debug root 的冻结路径。提交时文件内容 hash 失配即 stale，不按文件名或修改时间猜兼容。

## CityBlueprintContext

必填字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `schemaVersion` | string | 固定 `city_blueprint_context.v0.10`。 |
| `contextId` | string | 对除 `preparedAt` 外的冻结上下文做 SHA-256。 |
| `runId` / `cityId` | string | 当前 run 与城市。 |
| `sourceD3Ref` | ArtifactRef | 当前 D3 review package。 |
| `catalogSnapshotRef` | ArtifactRef | 本次完整目录快照。 |
| `generationSeedSuggestion` | safe integer | 程序按 city + D3 hash + catalog hash 稳定派生，范围为 JavaScript safe integer。 |
| `decisionBoundary` | object | 明确 prepare 不计 AI 调用、最多一次提交、提交后不允许候选请求。 |
| `citySeed` | object | 当前 CitySeed 完整只读输入。 |
| `d3ReviewPackage` | object | D3 地形、patch、member cells、指标、邻接与 preview 引用。 |
| `catalogSnapshot` | object | `city_blueprint_catalog_snapshot.v0.10`；包含 `city_semantic_profile_catalog.v0.4` 结构画像、固定模板目录、Reference Catalog v0.8 及 D3 terrain field 引用。引用目录同时冻结 LandUse rule、Foundation Profile、Surface Recipe、Landscape Profile、ParcelStyle 与 Landscape Fill Profile 完整定义，D6 后不得重新解释为另一版配置。 |
| `preparedAt` | instant | 追踪字段，不进入 `contextId`。 |

D3 `status=partial`、未知 schema、城市 ID 不一致，以及 AI 候选首都未接受/审查 identity 过期时，不得准备上下文。

## Structure Terrain Modes

`terrainModes` 是 City 固定 placement topology 枚举数组，不属于 TerraSense 动态词表。值域严格为 `SURFACE | EMBEDDED | FLOATING`，导入时大小写归一为大写；正式画像必须非空，未知值或归一后重复值直接拒绝。旧 `terrainTerms` 是退役字段，导入器必须显式拒绝。

多值按 OR 解析。当前运行时只真正实现 `SURFACE`：只要数组含 `SURFACE`，D4 便解析并冻结 `resolvedTerrainMode=SURFACE`；只有 `EMBEDDED/FLOATING` 时明确返回 `CITY_STRUCTURE_TERRAIN_MODE_UNSUPPORTED`，不得伪装为已支持。

SURFACE 门禁只读取已有 `city_land_use_terrain_field.v0.1`，不触发扫描或 chunk 加载。transformed collision footprint 覆盖的每个 terrain-field cell 必须存在、`sampled=true` 且 `water=false`；`terrainPolicy=CONFORM|BALANCED|ASSERTIVE` 另分别把完整占地的最大坡度限制为 `6|12|18`、最大 `localRelief` 限制为 `8|12|18`、最大高程范围限制为 `6|12|18`。roughness、biome、landform 与 patch 平均坡度只参与评分或诊断。Context/Snapshot 只冻结 `terrainFieldRef` 的 schema 与内容 hash；文件变化、city/grid/step 不一致均 stale。

## Blueprint 引用目录

### Landscape v0.10

`outdoorPlan.landscapes[]` 使用严格判别结构：

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| `landscapeId` / `landscapeProfileRef` | string | 城市内唯一 ID；Profile 必须存在。 |
| `purpose` | enum | `FUNCTIONAL | COMPOSITIONAL | AMBIENT`。 |
| `originMode` | enum | `ATTACHED | FREE_STANDING`。 |
| `owner` | object/null | `ATTACHED` 必填，严格为 `{groupId,requiredStructureRef}`；必须指向该 Group 唯一 required 条目。`FREE_STANDING` 必须为 null。 |
| `placementDomain` | enum/null | `FREE_STANDING` 必填：`URBAN_RESIDUAL | FOUNDATION_EDGE | BETWEEN_GROUPS | ALONG_WATER`；`ATTACHED` 必须为 null。 |
| `instanceCount` | positive int | AI 精确提交；`ATTACHED` 固定为 1。 |
| `parcelCount` | positive int | AI 精确提交的每实例数量，必须落在 Profile `parcelCountMin..Max`。 |
| `required` | boolean | true 时所有实例完整满足，否则 D4/D6 hard fail；false 仅允许 `FREE_STANDING`，逐实例准入。 |
| `preferredPatchRefs` / `terrainPolicy` / `fillSelection` | existing | 自由选址偏好、地形策略和 Parcel 内填充方案。 |

`groups[].requiredStructureRefs[]` 在 v0.11 必须唯一。fill/connectivity 结构不允许作为 owner，也不从自身派生 Landscape。

`ParcelStyle` 严格字段为 `parcelCountMin`、`parcelCountMax`、`parcelAreaMinBlocks`、`parcelAreaMaxBlocks`、`minSharedBoundaryBlocks`。删除的 `coreParcelCount*`、`fillParcelCount*`、`branchFromExistingChance`、`gapMinBlocks`、`gapMaxBlocks` 均按未知旧字段拒绝。

### D4 景观容量预留

新增 `city_landscape_capacity_reservation_plan.v0.1`。根字段为 `schemaVersion/cityId/sourceBlueprintHash/sourceD4Hash/planHash/status/searchNodeCount/instances/failures`。每个 required instance 冻结：

- `landscapeId/landscapeInstanceId/profileRef/ownerGroupId/ownerRequiredStructureRef/ownerAnchorId`；
- `capacityCandidateId/directionVariant/topologyVariant/parcelCount/parcelAreaBlocks`；
- `reservationSpans[]` 和逐 Parcel `parcelReservations[]`；
- `parentParcelId/rootSource/sharedBoundaryProof` 连通证明；
- 失败时的候选原因，不生成部分成功 artifact。

景观容量格彼此互斥但允许四邻接。D4 容量预留和 D6 Parcel 实际扩张必须使用同一相邻高程连续性门禁：`CONFORM|BALANCED|ASSERTIVE` 的相邻 terrain-field cell 高程差上限分别为 `4|6|10`；种子与每一步生长都不得跨越该断崖门禁。联合搜索最多访问 100000 节点；穷尽为 `CITY_BLUEPRINT_REQUIRED_LANDSCAPE_LAYOUT_UNSATISFIED`，达到上限为 `CITY_BLUEPRINT_LANDSCAPE_SEARCH_LIMIT_EXHAUSTED`。

引用目录根对象所有数组必填且非空：

- `structureRefs[]`：`structureRef` 必须存在于冻结 TerraSense semantic profile；`templateCandidates[]` 的 `templateId + variantId` 必须存在于固定模板目录。
- `fillPools[]`：`poolRef` 与只引用上述 `structureRef` 的 `structureRefs[]`。
- `algorithmProfiles[]`：`algorithmProfileRef`；算法枚举为 `COMPACT | GRID | LINEAR | COURTYARD | ORGANIC_COMPACT | CENTER_SYMMETRIC`。仅 `CENTER_SYMMETRIC` 可选 `centerAxisStreetEnabled=true|false`，缺省为 false；其他算法携带该开关必须拒绝。
- `compositionProfiles[]`：`compositionProfileRef` 与 `mode=ROUND_ROBIN`；只控制模板组成顺序，不携带建筑数量上限。
- `styleProfiles[]`：`profileRef`。
- `roadProfiles[]`：`profileRef`、`hierarchy=SIMPLE|HIERARCHICAL`、`density=SPARSE|BALANCED|DENSE`。
- `surfaceDetailProfiles[]`：`profileRef`、`intensity=LOW|MEDIUM|HIGH`。
- `landUseRuleProfile`：完整严格 `city_land_use_rules.v0.1`；其 `ruleRef` 是 Foundation/Landscape Profile 的规则白名单。
- `surfaceRecipes[]`：冻结 `surfaceRecipeRef`、是否写地表、`UNIFORM|CONTOUR_BANDS`、全部方块材料、可选 `boundaryBlockId`；`UNIFORM` 可选携带 `cropBlockId/channelBankBlockId/channelWaterBlockId/channelBankOverlayBlockId`，供区域接力按 `materialRole` 取材，但仍不执行旧式固定条带分类；`CONTOUR_BANDS` 必须完整携带这些材料并另填正整数 `fieldBeforeBlocks/channelWidthBlocks/fieldAfterBlocks`。`autoConnectDefault` 只服务 legacy/debug，正式 v0.7 编译固定关闭。
- `foundationProfiles[]`：冻结 `foundationProfileRef`、LandUse rule、Surface recipe、`structureMarginBlocks`、`closeRadiusBlocks`、`maxJoinDistanceBlocks`；距离必须满足 `0 <= margin <= close <= join`。
- `landscapeProfiles[]`：冻结 `landscapeProfileRef`、`FARMLAND|COMMON_GREEN|WOODLAND|MEADOW|POND`、LandUse rule、Surface recipe、SMALL/MEDIUM/LARGE 基准面积、membership 和严格 `parcelStyle`。
- `landscapeFillProfiles[]`：冻结 `fillProfileRef`、显示名、视觉意图、唯一 `algorithm=SINGLE_SOURCE_REGION_RELAY`、`relayOrigin=PARENT_REGION_LOCAL_BOUNDARY`、兼容景观类型、`primaryRoleRef`、角色目录、内容白名单和非空接力示例。每个 `landscapeProfiles[]` 暴露的景观类型必须至少被一个 Fill Profile 覆盖，否则整个目录拒绝；服务不注入默认 Profile，调用方必须把完整目录传入 prepare，随后目录原样进入 Context 供 AI 选择。

每个 Fill Profile 的 `roles[]` 必填 `roleRef`、`materialRole=PRIMARY_CONTENT|BANK|WATER|GROUND`、非空 `allowedGrowthForms[]`、`defaultGrowthForm`、`minShare/maxShare/defaultShare`。生长偏置仅允许 `PATCH|CORRIDOR`，默认值必须位于本角色白名单。占比满足 `0 <= min <= default <= max <= 1`，全部 default 之和为 1；主角色必须为 `PRIMARY_CONTENT`。已删除 `layerSequence/repeatLayers`，不允许目录另藏距离层或固定形状。`allowedContentRefs[]` 是 AI 内容权重的唯一白名单。

`examples[]` 每项必填 `exampleId`、`description`、有序 `roleShares[]` 和 `contentWeights[]`。每个 role occurrence 必填 `roleRef/growthForm/targetShare`；同一角色允许重复出现，数组顺序就是区域接力顺序。全部 occurrence 占比和为 1，同角色 occurrence 的占比合计必须落入该角色范围，每个声明角色至少出现一次。内容只引用白名单。示例是正式目录数据，不能只存在于提示词或实现注释中。

`parcelStyle` 必填：

| 字段 | 约束 |
| --- | --- |
| `parcelCountMin/parcelCountMax` | 正整数且 min <= max；约束 AI 可提交的每实例精确 Parcel 数。 |
| `parcelAreaMinBlocks/parcelAreaMaxBlocks` | 正整数且 min <= max；单块面积范围。 |
| `minSharedBoundaryBlocks` | 正整数；每个非根 Parcel 与冻结父 Parcel 的最小四邻接共享边界格数。 |

所有 namespace 内引用唯一。案子 02 必须按这些冻结 ID 读取配置，不得把 Blueprint 字符串解释为自由算法或隐藏模板路径。

## CityBlueprint v0.11

根字段全部必填，未知字段拒绝：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `schemaVersion` | string | 固定 `city_blueprint.v0.11`；旧 Blueprint 不兼容且不迁移。 |
| `cityId` | string | 与 context / D3 一致。 |
| `sourceD3Ref` / `catalogSnapshotRef` | ArtifactRef | 与 context 逐字段一致。 |
| `generationSeed` | safe integer | `-9007199254740991..9007199254740991`；后续编译器唯一记录随机源。 |
| `designIntent` | object | `cityIdentity`、`theme`、非空 `functionalRoles[]`。 |
| `styleProfile` | object | 仅 `profileRef`。 |
| `groups[]` | Group[] | 至少一个。 |
| `arrayCompositions[]` | ArrayComposition[] | 可为空；父阵列按完整 Group 范围编排子阵列。 |
| `relations[]` | Relation[] | 可为空。 |
| `roadProfile` | object | 仅 `profileRef`。 |
| `surfaceDetailProfile` | object | 仅 `profileRef`。 |
| `outdoorPlan` | OutdoorPlan | 同一次提交中的完整户外设计意图。 |

Group 必填字段：

| 字段 | 值域 |
| --- | --- |
| `groupId` | 蓝图内唯一非空字符串。 |
| `groupKind` | v0.11 仍只接受 `STRUCTURE`；景观只能进入 `outdoorPlan.landscapes[]`。 |
| `preferredPatchRefs[]` | 非空当前 D3 `landformPatchId` 列表；多个 Group 可以共享。 |
| `preferredPatchZone` | `CENTER | NORTH | EAST | SOUTH | WEST`；核心在全部偏好 patch 精确 member-cell 并集内的起步方位。北=-Z、南=+Z、西=-X、东=+X；不表示世界坐标，也不约束连接阶段。 |
| `placementRelation` | 可选严格对象；使用 `BETWEEN_PATCHES | ALONG_PATCH_BOUNDARY | BETWEEN_GROUPS` 表达城市内部关系位置。 |
| `role` | 非空功能角色。 |
| `priority` | `CORE | STANDARD | PERIPHERAL`。 |
| `extentClass` | `SMALL | MEDIUM | LARGE`，表示空间范围而非建筑数量。 |
| `densityClass` | `SPARSE | BALANCED | DENSE`。 |
| `algorithmProfileRef` | 冻结算法引用。 |
| `terrainPolicy` | `CONFORM | BALANCED | ASSERTIVE`。 |
| `requiredStructureRefs[]` | 非空、组内唯一且全部在结构白名单；`groupId + requiredStructureRef` 唯一定位 Landscape owner。 |
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

`CENTER_SYMMETRIC` 是正式中心对称阵列。使用该算法的 Group 必须且只能提交一个 `requiredStructureRef`，该结构成为冻结中心主体；fill pool 中每次选择一个结构类型，并在中心两侧生成两个互为中心对称的候选。每一对必须使用同一模板候选，以两栋为一个原子批次同时通过地形、碰撞、范围和关系门禁；任一侧失败时程序旋转整对候选继续搜索，不得单侧提交或退化为普通 `GRID/COURTYARD`。中心主体之外的内部结构数因此只能按偶数增长。中心主体提交后，编译器必须先原子预留该 Group 的最低成形对数，再允许其他 Group 播种 required 核心，避免相邻核心抢占阵列轴线；每层依次使用两组正交轴线，下一层整体旋转 45 度。连接阶段不承担内部对称成形，继承该算法时只使用 `COURTYARD` 形态生成跨组连接批次。

### 关系位置

`placementRelation` 严格包含 `kind/patchRefs[]/groupRefs[]`，只决定 Group 首个阵列核心的位置，不提交坐标，也不替换该 Group 自身的算法、模板池或 `terrainPolicy`：

- `BETWEEN_PATCHES`：恰好两个不同 `patchRefs`，`groupRefs` 为空；以两 Patch 最近合法 member cell 中心的中点起步，候选域只包含这两个 Patch。
- `ALONG_PATCH_BOUNDARY`：恰好两个不同 `patchRefs`，`groupRefs` 为空；`patchRefs[0]` 是落地方，以其最接近 `patchRefs[1]` 的边界 member cell 起步，候选域只包含第一个 Patch。
- `BETWEEN_GROUPS`：`patchRefs` 为空，恰好两个不同 `groupRefs`，且不能引用自身；编译器先完成两个端点 Group 的 required 核心，再以两端实际 extent 中心的中点起步，候选域为当前 D3 城市规划边界。

显式关系位置无合法候选时直接失败，不得回退到普通 `preferredPatchRefs` 或整张 D3。没有 `placementRelation` 时仍按 `preferredPatchRefs + preferredPatchZone` 工作，并保留原有 terrain fallback。

### 父阵列

`arrayCompositions[]` 每项严格包含：

| 字段 | 约束 |
| --- | --- |
| `compositionId` | Blueprint 内唯一非空字符串。 |
| `algorithmProfileRef` | 冻结算法引用；只编排完整子 Group，不覆盖子 Group 自身算法。 |
| `centerGroupId` | 中心完整 Group；可按 Patch 关系定位，但不能使用 `BETWEEN_GROUPS`。 |
| `memberGroupIds[]` | 非空、组内唯一的完整子 Group。成员由父阵列给出起点，不能再声明 `placementRelation`。 |

一个 Group 最多属于一个父阵列。当前正式契约只允许一层 Group 级编排，不允许父阵列再次作为另一父阵列的成员。父阵列按 required/fill 模板 transformed footprint、最低成形数量、子算法、密度和区内街带推导 `plannedSpanBlocks`，预留互不相交且不越出 D3 城市边界的播种槽位；不得把 `extentClass` 最大跨度直接当作槽位边长。每个子槽中心必须命中该子 Group 自己的 `preferredPatchRefs[]`，子 Group 仍独立使用自身 `requiredStructureRefs/fillPoolRef/algorithmProfileRef/terrainPolicy`。父算法为 `CENTER_SYMMETRIC` 时，`memberGroupIds[]` 必须为偶数，相邻两项组成一对；程序可旋转轴线并交换这一对的两侧位置，使两个完整 Group 槽位既关于中心 Group 成对对称，也分别满足各自 Patch 限制。

Relation 必填 `fromGroupId`、`toGroupId`、`relationKind`、`strength`、`distancePreference`、`directionPreference`。`relationKind` 为 `HIERARCHY | ADJACENCY | CONNECTION | BUFFER | DISTANCE | DIRECTION`，`strength` 为 `HARD | SOFT`。只有 `DISTANCE` 可使用 `distancePreference=NEAR|FAR`，其他关系必须为 `NONE`；只有 `DIRECTION` 可使用 `directionPreference=NORTH|EAST|SOUTH|WEST`，其他关系必须为 `NONE`。`HIERARCHY` 按 `fromGroupId -> toGroupId` 表示父到子，必须无环；编译器据此做稳定拓扑排序，同批节点再按 priority 和 `groupId` 排序。

## OutdoorPlan

`outdoorPlan` 根字段严格为 `mode`、`envelopeProfile`、`foundationProfileRef`、`spatialGrounds[]` 和 `landscapes[]`，未知字段拒绝。

- `mode=GENERATE`：`foundationProfileRef` 必须命中冻结目录；每个 STRUCTURE Group 必须且只能有一项 spatial ground；D6 后自动编译基础地板与景观 Parcel。
- `mode=PRESERVE`：`foundationProfileRef` 必须为空，`spatialGrounds[]` 与 `landscapes[]` 必须为空。
- `envelopeProfile=COMPACT|BALANCED|LOOSE`：保留为城市总体紧凑度语义；正式几何参数以 Foundation Profile 冻结值为权威，不接受 Blueprint block 数。

`spatialGrounds[]` 每项字段：

| 字段 | 类型 / 值域 | 说明 |
| --- | --- | --- |
| `sourceGroupId` | string | 必须引用本 Blueprint 的 STRUCTURE Group；全表唯一。 |
| `sharedSpaceType` | `CIVIC_SQUARE|MARKET_STREET|RESIDENTIAL_COURT|FARMSTEAD|GENERAL_URBAN` | 组团共享空间的建筑学类型。 |
| `hierarchyLevel` | `PRIMARY|SECONDARY|LOCAL` | 建筑学层级；不生成道路或地表连接线。 |
| `membership` | `URBAN|LANDSCAPE` | 是否纳入城市主体 footprint 集；不选择铺地材质。 |

`landscapes[]` 每项字段：

| 字段 | 类型 / 值域 | 说明 |
| --- | --- | --- |
| `landscapeId` | string | 户外计划内唯一；不得与其他 landscape 重复。 |
| `landscapeProfileRef` | string | 冻结景观 profile，决定 rule、surface recipe、基准面积和 membership。 |
| `purpose` | `FUNCTIONAL|COMPOSITIONAL|AMBIENT` | 景观在城市构图中的意义。 |
| `originMode` | `ATTACHED|FREE_STANDING` | 严格判别字段。 |
| `owner` | object | 仅 ATTACHED 使用；严格为 `groupId/requiredStructureRef`，必须定位唯一 required 结构。 |
| `placementDomain` | `URBAN_RESIDUAL|FOUNDATION_EDGE|BETWEEN_GROUPS|ALONG_WATER` | 仅 FREE_STANDING 使用。 |
| `instanceCount` | positive integer | AI 提交的精确实例数；ATTACHED 固定为 1。 |
| `parcelCount` | positive integer | AI 提交的每实例精确 Parcel 数，必须落入 Profile 范围。 |
| `preferredPatchRefs[]` | string[] | 可为空；非空项必须命中冻结 D3 patch。 |
| `terrainPolicy` | `CONFORM|BALANCED|ASSERTIVE` | 景观地形适配档位。 |
| `required` | boolean | required 所有实例和 Parcel 必须完整满足；FREE_STANDING 当前必须 optional。 |
| `fillSelection` | object | 必填候选填充方案；AI 只提交目录引用、候选权重、有序接力区域的角色/生长偏置/目标占比和内容权重。 |

`fillSelection` 严格只含非空 `variants[]`。每个 variant 必填：

| 字段 | 约束 |
| --- | --- |
| `fillProfileRef` | 命中同一快照的 Landscape Fill Profile，且兼容当前 Landscape Type。 |
| `selectionWeight` | 正有限数；程序按 Parcel 稳定选择候选，不要求归一为 1。 |
| `roleShares[]` | 非空有序接力区域列表；每项为 `roleRef/growthForm/targetShare`。同一角色可重复；每个声明角色至少出现一次，全部 occurrence 占比和为 1，同角色合计占比落入 Profile 范围，且 `growthForm` 命中该角色白名单。 |
| `contentWeights[]` | 可为空；`contentRef` 唯一且命中 `allowedContentRefs`，`weight` 为正有限数。 |

AI 可直接参考目录示例后调整占比，例如：

```json
{
  "fillSelection": {
    "variants": [
      {
        "fillProfileRef": "fill:relay_irrigated_farmland",
        "selectionWeight": 3.0,
        "roleShares": [
          {"roleRef": "CULTIVATED", "growthForm": "PATCH", "targetShare": 0.46},
          {"roleRef": "BANK", "growthForm": "CORRIDOR", "targetShare": 0.09},
          {"roleRef": "WATER", "growthForm": "CORRIDOR", "targetShare": 0.08},
          {"roleRef": "BANK", "growthForm": "CORRIDOR", "targetShare": 0.09},
          {"roleRef": "CULTIVATED", "growthForm": "PATCH", "targetShare": 0.28}
        ],
        "contentWeights": [
          {"contentRef": "crop:wheat", "weight": 3.0},
          {"contentRef": "crop:carrot", "weight": 1.0}
        ]
      },
      {
        "fillProfileRef": "fill:relay_dry_farmland",
        "selectionWeight": 1.0,
        "roleShares": [
          {"roleRef": "CULTIVATED", "growthForm": "PATCH", "targetShare": 0.58},
          {"roleRef": "GROUND_BREAK", "growthForm": "CORRIDOR", "targetShare": 0.18},
          {"roleRef": "CULTIVATED", "growthForm": "PATCH", "targetShare": 0.24}
        ],
        "contentWeights": [{"contentRef": "crop:wheat", "weight": 1.0}]
      }
    ]
  }
}
```

`selectionWeight` 决定不同 Parcel 使用哪套方案；每个 occurrence 的 `targetShare` 决定该接力区域的目标面积，同角色合计决定该角色总体占比。AI 不提交固定层宽、坐标、mask 或方块 ID。程序严格按 `roleShares[]` 顺序执行逐格 frontier 扩张，并冻结每块区域的父子关系与实际面积。

required Landscape 在 D4 与 required 结构候选联合求解；数量严格等于 `instanceCount × parcelCount`，不得按 required/fill anchor 倍增、缩减或降级。程序只枚举容量方向、父子拓扑和主体候选位置，成功后原子提交，fill/connectivity 结构把全部预留 spans 当硬排除。FREE_STANDING optional 在 D6 后从剩余空间逐实例准入；成功实例同样必须达到精确 Parcel 数。固定 Blueprint、catalog、D3、D6 与 seed 必须完全复现。

`residualPolicy` 已删除。单一 Foundation domain 内部全部使用同一基础地板，Landscape Parcel 后写覆盖；不得按 SpatialGround 分配不同铺地，也不得保留原群系残余。显式自然、绿地和农田只能通过 `landscapes[]` 声明。

## 禁止字段

Blueprint 任意层级禁止：世界/block `x/y/z`、`blockX/Y/Z`、anchor、rotation、mirror、candidateId、直接 templateId/templateRef/nbtFile、`algorithm` 或 `algorithmName`。户外层另禁止 block ID、逐格 mask、固定形状、距离环、几何 fallback、裸面积、行动力和成本。它们属于程序输出，不属于 AI 决策。

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
CITY_BLUEPRINT_PLACEMENT_RELATION_INVALID
CITY_BLUEPRINT_ARRAY_COMPOSITION_ID_DUPLICATE
CITY_BLUEPRINT_ARRAY_COMPOSITION_INVALID
CITY_BLUEPRINT_ARRAY_COMPOSITION_GROUP_UNKNOWN
CITY_BLUEPRINT_ARRAY_COMPOSITION_GROUP_REUSED
CITY_BLUEPRINT_OUTDOOR_REFERENCE_INVALID
```

## 01 -> 02 审查门

案子 02 的冻结输入是：校验通过的 `city_blueprint.json`、同目录 `city_blueprint_catalog_snapshot.json`、Blueprint 中两份 ArtifactRef 和 `generationSeed`。编译器不得再次请求 AI 选择 candidate/slot/扩张方向，且最终必须输出现有标准 `structure_anchor_plan.json` / `structure_anchor_map.json`。

02 已接通：`city_run_workflow` 默认 `d4CandidateMode=blueprint`。所有 candidate/session/manual anchor 接口统一视为 `legacy/debug`，只有显式指定旧 mode 才执行，不属于新的正式 Blueprint 决策边界。

## CityGenerationCompileTrace v0.12

文件：`city_test_runs/<cityId>/steps/d4/city_generation_compile_trace.json`，`schemaVersion=city_generation_compile_trace.v0.12`。

根字段：`cityId`、`status=compiled|failed`、`reasonCode`、`generationSeed`、`selectionMode`、`aiCandidateSelectionCount=0`、`manualCandidateSelectionCount=0`、`sourceD3Ref`、`catalogSnapshotRef`、`districtCapacityPlan`、`connectivityPlan`、`arrayCompositionSlots[]`、`selections[]`、`groupResults[]`。`districtCapacityPlan` 是 D4 在建筑搜索前冻结的连通功能区容量预留，不能由调用方补写。

每个 selection 按执行顺序记录 `phase=required|fill|connectivity_growth`。全部 Group 的 required 先完成，随后各 Group 的 fill 完成内部成形，最后才允许出现 connectivity selection。同一 Group 的 required 先稳定排列画像带 `planning_role.anchor|key` 的结构，再保留 AI required 列表的原相对顺序；没有 anchor/key 时列表首项自然成为主建筑。required/fill 继续记录单结构候选、评分、envelope 与提交状态；connectivity selection 必须按完整阵列批次记录 `arrayId`、`plannerType`、`focusArrayId`、自动方向、`resolvedConnectionPlan`、语义参数、近圈搜索 trace、候选数、选中 candidate、批次 anchor IDs、连接前后 gap 与整批结构数。任一连接批次只有完整 cardinality、全部 terrain/collision 合法且确实缩短目标 gap 时才能原子提交，不得部分落地。

connectivity selection 另必填 `requestedBatchSize`、`terminalBatch`、`initialBodyGapBlocks`、`frontierGapCorrectionBlocks`；对应 `frontierSearchTrace[].rings[]` 记录 `correctedForBodyGap`。批量从解析后的配置规模按 `N..1` 确定性降级重试，失败尝试同样进入 trace；一组完整合法候选即可提交，零组才失败。`minCandidateCount` 不属于 Blueprint 或编译请求，旧字段必须以 `D4_ARRAY_LAYOUT_MIN_CANDIDATE_COUNT_REMOVED` 明确拒绝。

required、fill 和 connectivity batch 必须调用同一 Structure Terrain gate。门禁以 transformed collision footprint 为范围，对 `terrainModes` 做 OR 解析；当前 SURFACE 要求全部相交 D3 terrain-field cells 存在、已采样、非水并满足 Group `terrainPolicy` 的完整占地坡度、起伏和高程范围上限，不得只检查 anchor 点、首个 patch 或 dominant biome。候选生成必须逐点应用该门禁，不合法时继续搜索同一合法域。首个 required 先搜索 `preferredPatchRefs[]`；该域没有任何完整占地合法候选时，允许以 `patchSelectionScope=d3_terrain_fallback` 搜索同一 D3 review grid，并在后续 `claimedPatchRefs[]` 记录实际认领 patch。trace 至少记录 `structureRef`、`declaredTerrainModes`、`resolvedTerrainMode`、footprint、相交/已评估/拒绝格数、阈值、reasonCode 和有限失败样本；anchor 同样冻结 `resolvedTerrainMode`。`styleTerms` 不得出现在 gate、分数或候选排序依据中。

`selections[]` 的 committed 项与最终 `StructureAnchorPlan.anchors[]` 必填 `blueprintLayout`：`algorithm`、单调递增但可因非法留空而跳号的 `slotIndex`、`spacingBlocks`、`theoreticalAnchor`、`outwardGuided`、`densityParameters`、`preferredPatchZone`，首个核心另写精确 `coreSeedCell`，anchor 另冻结 `acceptedAnchor`。GRID、COURTYARD、LINEAR、CENTER_SYMMETRIC 使用全组最大 collision span 派生一次固定 pitch，锁世界轴或主入口显式轴，只能尝试精确 guide；不得追加 member-cell center、随机旋转或其他形状兜底，不合法槽位写 `skipped_illegal_slot/EXACT_SLOT_ILLEGAL_LEFT_EMPTY` 后留空。GRID 另写 `gridRow/gridColumn/gridPitchBlocks/worldAxisLocked=true`；COURTYARD 另写 `courtyardRing/courtyardRow/courtyardColumn/courtyardCenter/courtyardGateSide=SOUTH`，slot 0–4 必须构成北侧主建筑、东、东南、西、西南且中心空置；COMPACT 写 `compactLaneRank/compactLaneSide/compactLaneTarget`，建筑在允许旋转内朝弯巷；ORGANIC_COMPACT 只使用程序随机 guides，在功能区内保持 collision gap 1–3 blocks，不产正式道路。需要朝路的结构必须写 `frontageRotation/frontageEntranceId/frontageDirection/frontageAlignmentScore/frontageMinimumAlignmentScore/frontageTargetRef`；规则直路要求满分朝向，弯巷/院角接受最近合法四向且不得低于 0.7。

最终 `StructureAnchorPlan` 与 `StructureAnchorMap` 根级可写 `streetBands[]`，同一 Group 可含多个直段。每项 schema 为 `city_internal_street_band.v0.1`，必填 `streetBandId/roadNetworkId/roadKind/segmentIndex/groupId/geometryMode=STRAIGHT_AXIS_CLIPPED_BY_TERRAIN/widthBlocks/surfacePolicy=FOLLOW_TERRAIN_NO_LEVEL/hardSkeleton=true/axisX/axisZ/start/end/bounds/platformBounds/platformPolicy=LOCAL_HARD_SKELETON`。`roadKind` 至少支持 `GRID_MAIN_STREET|GRID_ROW_LANE|GRID_COLUMN_LANE|COURTYARD_RING_*|COURTYARD_GATE|LINEAR_STREET_BAND|COMPACT_ALLEY|CENTER_AXIS_NORTH|CENTER_AXIS_SOUTH`；GRID、COURTYARD、LINEAR、COMPACT 必须产相应网络，CENTER_SYMMETRIC 仅在 profile 开关启用时产轴街，ORGANIC_COMPACT 禁止产正式道路。每个直段进入 D4 预览、D6 和 Foundation；RoadWeaver 不消费该数组。

最终 plan/map/trace 根级必填 `arrayVisualQuality`，schema=`city_array_visual_quality.v0.1`，含 `passed/hardBlocks/groups[]`。门禁直接检查最终几何：GRID 理论格点误差不超过 1 block、固定 pitch 与街巷网连通；COURTYARD 中心空置、基础五槽完整、南门与环路连通；LINEAR 街带存在且连通；CENTER_SYMMETRIC 镜像证明成立且可选轴街结构完整；COMPACT 弯巷连通且门脸达标；ORGANIC_COMPACT 无正式路且 collision gap 1–3 blocks 的图连通。任一失败以 `CITY_BLUEPRINT_ARRAY_VISUAL_GEOMETRY_INVALID` 阻断 D4。

`CENTER_SYMMETRIC` 的 fill selection 另写 `requestedBatchSize=2`、`atomicPair=true` 与 `centerSymmetryProof`；两栋 anchor 的 `blueprintLayout` 必须共享 `symmetryPairId/symmetryPairIndex/symmetryCenter/visualCenter`，分别写 `symmetryPairMember=FIRST|OPPOSITE`。程序按模板变换后的 collision footprint 校正 anchor 对称中心；证明必须同时满足两端 anchor 关于校正中心成对，以及两栋实际 collision footprint 的几何中心关于中心主体的实际 collision footprint 中心成对。

`connectivityPlan` 必填 `topologyPolicy=EXPLICIT_RELATIONS_THEN_DETERMINISTIC_SHORTEST_FALLBACK`、`handoffThresholdPolicy=STRICT_BILATERAL_MINIMUM`、`edgeCount`、`fallbackEdgeCount` 与 `edges[]`。每条边必填 `fromGroupId`、`toGroupId`、`topologySource=EXPLICIT|FALLBACK`、`topologyReason`、`initialGapBlocks`、`finalGapBlocks`、`handoffGapBlocks`、`connectionStructureCount`、`connectionBatchCount`、`status`；fallback 原因固定为 `DETERMINISTIC_SHORTEST_COMPONENT_EDGE`。`handoffGapBlocks` 及 HARD 关系复验必须同源读取双方解析后的 `resolvedConnectionPlan.derivedLayoutParameters.landUseHandoffGapBlocks` 严格最小值，不得混用 Group required/fill 的内部 handoff。

`groupResults[]` 必填 `groupId`、`requestedExtentClass`、`densityClass`、`terrainPolicy`、`densityParameterization=ALGORITHM_SPECIFIC`、`layoutAlgorithm`、`placementMode`、`layoutParameters`、`resolvedConnectionPlan`、`spatialDemand`、`targetAreaBlocks`、`maxExtentSpanBlocks`、`maxIntraGroupGapBlocks`、`outwardGuidedPlacementCount`、`derivedMinimumStructureCount`、`internalStructureCount`、`minimumStructureCountReached`、`internalSpatialDemandBlocks`、`connectionStructureCount`、`connectionBatchCount`、`connectionSpatialDemandBlocks`、`connectionExpansionBlocks`、`extentExpandedForConnectivity`、`actualStructureCount`、`requiredStructureCount`、`builtCollisionAreaBlocks`、`actualSpatialDemandBlocks`、`estimatedCoverageRatio`、`preferredPatchRefs[]`、`claimedPatchRefs[]`、`structureCounts` 与 `stopReason`。`spatialDemand.source=TEMPLATE_ARRAY_DEMAND`，并冻结模板实际占地、最低成形数量、算法密度间距、区内街带面积、最低/目标/上限面积、`formationSpanBlocks/formationWidthBlocks/formationLengthBlocks` 和可选 `primaryAxisDirection`；LINEAR 另写与根数组同源的 `streetBandPlan`。CORE 保留 extent 设计目标，STANDARD/PERIPHERAL 允许目标面积按真实最低需求小于 extent 设计目标。`placementMode` 是程序依据 `layoutAlgorithm` 派生的空间落地分类，只允许 `CORE_ANCHORED | AXIS_ANCHORED | CLUSTER_BOUNDED | TERRAIN_FOLLOWING`，不属于 AI 输入。`layoutParameters.placementMode` 必须与其一致。关系定位 Group 另写 `placementRelation`；父阵列参与 Group 另写 `arrayCompositionSlot` 和 `formationBounds`。`resolvedConnectionPlan` 必须写出继承后的 pool、算法、planner、疏密及继承来源。`SPATIAL_BUDGET_REACHED` 是正常完成，`CONNECTED_SPACE_EXHAUSTED` 只表示达到最低成形量后未填满空间预算；未达到最低成形量必须 hard fail。连接阶段可越过 extent 软目标，但不得越过 D3 规划网格等硬边界。

`arrayCompositionSlots[]` 每项写 `groupId/compositionId/parentAlgorithm/centerGroupId/slotIndex/plannedSpanBlocks/spanSource/origin/placementOrigin/slotBounds`；`spanSource` 固定为 `TEMPLATE_ARRAY_DEMAND`，不得再把 `extentMaxSpan(SMALL|MEDIUM|LARGE)` 当作父阵列占位边长。`origin` 是父阵列用于碰撞、固定 pitch 和对称证明的槽中心；普通子组 `placementOrigin=origin`，LINEAR 则按 `primaryAxisDirection + formationLength/formationWidth` 把 `placementOrigin` 平移到槽外缘，使主建筑成为轴端且单向街带完整留在 `slotBounds` 内。中心对称成员另写 `pairIndex`，其对称性比较槽中心 `origin`，不比较 LINEAR 轴端。坐标均为程序编译结果，不是 Blueprint 输入。

`groupResults[]` 与 extent 中的每个 Group 还必须回写 `preferredPatchZone`，用于区分 AI 指定的内部方位与程序最终认领的 `claimedPatchRefs[]`。

## GroupExtentMap v0.10

文件：`city_test_runs/<cityId>/steps/d4/group_extent_map.json`，`schemaVersion=group_extent_map.v0.10`。根字段为 `cityId`、`generationSeed`、`connectivityPolicy=RELATION_GRAPH_ARRAY_GROWTH_THEN_LAND_USE`、`connectionSemantics=STRUCTURE_FRONTIER_FOR_LAND_USE`、`cityBoundaryPolicy=D3_REVIEW_GRID_HARD_BOUNDARY`、`districtBoundaryPolicy=PREALLOCATED_CONNECTED_CAPACITY_WITH_RELATION_AWARE_HARD_BUFFER`、`minimumDistrictSeparationBlocks=12`、`districtCapacityPlan`、`handoffThresholdPolicy=STRICT_BILATERAL_MINIMUM`、`structureGraphConnected`、`landUseConnected=false`、`landUseConnectionStatus=PENDING_LAND_USE_COMPILE`、`arrayCompositionSlots[]`、`connections[]`、`groups[]`。不得出现 `maxInterGroupGapBlocks` 或含糊的旧 `connected` 字段；调用方不得自行把结构拓扑解释成实体地表连通。

`connections[]` 与 compile trace 边字段同源，并增加 `landUseHandoffReady` 与 `connectionEdge{fromX,fromZ,toX,toZ}`；每个 Group 同时携带上述布局/空间/count/stop 字段、可选 `streetBandPlan`、`districtCapacity`、closed `collisionExtent{minX,minZ,maxX,maxZ}`、`districtEnvelope`、`districtEnvelopePolicy=PREALLOCATED_CAPACITY_PLUS_MARGIN|COLLISION_EXTENT_PLUS_MARGIN`、`districtEnvelopeMarginBlocks=4` 与 `districtBufferExemptGroupIds[]`。`districtCapacity` 必须写出 `status`、最低/目标/上限面积、`roadReserveAreaBlocks=0`、实际预留面积、预留格数和精确 `reservationSpans[]`；区内街带已计入 `spatialDemand.internalStreetAreaBlocks`，不得再为 RoadWeaver 追加固定预算。普通有界/地形跟随 Group 的 `status=RESERVED` 时，建筑候选只能落在这些连通预留格内；AXIS_ANCHORED required/fill 使用精确硬骨架 guides，不得为回到粗格而移动。`BETWEEN_GROUPS` Group 可写 `DEFERRED_BETWEEN_GROUPS`，待两端 Group 形成后定位。预览的 `districtEnvelope` 来源于预留格包络并外扩 4 格，不是 Blueprint 输入坐标；豁免列表只由已验证 Blueprint 关系确定，调用方不能补写。

根 `districtCapacityPlan` 的 `schemaVersion=city_district_capacity_plan.v0.1`，策略固定为 `PREALLOCATE_CONNECTED_CAPACITY_THEN_GROW_GROUPS`。每个 Group 预留项必须写出与 D4 `groupResults[]` 一致的 `placementMode`。程序以父阵列槽位或普通 Group 方位作为种子，从 D3 Patch 成员格逐格连通扩张；容量候选入口按 Group `CONFORM/BALANCED/ASSERTIVE` 使用与结构门禁同源的 6/12/18 坡度和 8/12/18 局部起伏上限。`slotBounds` 负责父阵列播种和组间编排，不把功能区或后续建筑裁成同尺寸矩形。普通有界/地形跟随 Group 的 required/fill 受 `districtCapacity.cells` 硬合法区约束；AXIS_ANCHORED 硬骨架使用连续精确 guides 和逐建筑 terrain gate，不得为回到预留粗格而移动 guide，成功后的 `streetBandPlan` 与实际 footprint 共同进入 Foundation。扩张先满足模板阵列最低面积，再达到目标面积；水体、缺失或未采样格不得进入候选域。核心规则型保持种子周围的紧凑骨架，轴线/廊道型按编排槽位长轴优先，有界簇团型限制局部扩张，地形跟随型提高坡度、起伏和粗糙度代价；不相关 Group 之间仍执行 12 格硬缓冲。整个域没有可用陆地时，容量项只能记录无可用地形并留给结构地形门禁给出具体诊断，不得把水体计入面积。存在可用陆地但容量不足时，必须以 `CITY_BLUEPRINT_GROUP_DISTRICT_CAPACITY_UNREACHABLE` 明确失败，不得把功能区缩成零占地或用固定几何补齐。

所有 required、fill 与 connectivity batch 的 transformed collision envelope 默认必须与其他 Group 保持至少 12 blocks 边缘距离；命中时以 `GROUP_DISTRICT_BUFFER_VIOLATED` 拒绝当前候选并继续搜索。这段留白用于道路、绿化、坡坎或其他街区边界。直接构图伙伴豁免该硬缓冲：同一 `arrayComposition` 的中心与成员、显式 `ADJACENCY` 两端、`HARD CONNECTION|HIERARCHY` 两端、`BETWEEN_GROUPS` Group 与其明确 `groupRefs`。关系任一端属于父阵列时，只向该父阵列的全部成员展开一次；豁免不再沿普通关系链传递，不得把整座城市合并为一个街区。豁免伙伴仍受 collision、各自 extent/阵列参数和 handoff 约束。LandUse 编译后仍必须以真实 block spans 验收道路与地表连续性。

所有 Group 的 required 核心先搜索各自 `preferredPatchRefs[]`；首选域完整占地不可承载时允许回退到同一 D3 `review.grid`，后续组建围绕实际认领核心继续，`preferredPatchRefs[]` 与 `claimedPatchRefs[]` 必须分别保留意图和结果。连接阶段同样可认领 D3 `review.grid` 内其他 patch/member cells。Group `terrainPolicy` 不按 patch 平均坡度裁剪，而是对每个 transformed collision footprint 的 terrain-field 事实执行硬门禁。

固定模板 worldgen 的 `templateDatumPolicy=generator_base_height_motion_blocking_no_leaves` 表示高度来源。StructureStart 以 locked actual footprint 为范围每 4 blocks 采样 generator base height（包含远端边界），取排序中位数作为全结构唯一 `templateDatumY`；不得只取 anchor 点。仅 `supportPolicy=full_footprint_support` 的模板在 Beardifier 密度阶段获得完整矩形占地承托：台面下最大 32 blocks、外侧 2 blocks 收肩；其他 support policy 不生成该台基。Foundation 外围硬质地表使用 7×7 外环中位数做有界填挖，填方上限 48 blocks、切方上限 12 blocks；局部窗口起伏本身不得再使 `delta=0` 的表面列被跳过。

`extentClass` 核心/fill 目标空间预算为 `4096 / 16384 / 36864 blocks²`，最大跨度为 `96 / 160 / 240 blocks`。程序另按 D3 `targetScale.scale` 与 `extentClass` 派生最低成形栋数：HAMLET=`2/3/4`、VILLAGE=`3/4/6`、TOWN=`3/6/9`、CITY=`4/8/12`（SMALL/MEDIUM/LARGE）；COURTYARD 最低值另强制不小于 5，CENTER_SYMMETRIC 则把偶数投影为不小于 3 的最近较小奇数。`spatialDemand` 另冻结 `maximumTemplateSpanBlocks`，规则阵列和父规则阵列用它统一 pitch；各模板 claimed area 先分别离散到 D3 cell 后再求和，GRID/COURTYARD/LINEAR/COMPACT 的内部道路面积必须计入需求。连接结构不代替最低成形。

若任一 Group 在连接前无法达到 `derivedMinimumStructureCount`，编译必须以 `CITY_BLUEPRINT_GROUP_MINIMUM_UNREACHABLE` 失败；不得进入 connectivity growth 后再用连接建筑补足数量。

编译成功后仍必须输出原有 `city_structure_anchor_plan.v0.2`、`city_structure_anchor_map.v0.2` 与结构预览。D4 总览和局部结构预览必须以独立颜色叠加每个 Group 的 `districtCapacity.reservationSpans[]`、`districtEnvelope`、`streetBandPlan` 和建筑 geometry；局部预览只画当前聚簇涉及的 Group。预览同时叠加 `landscapeCapacityReservationPlan.reservationSpans[]` 的精确格点面积，并以独立颜色和图例区分各 Landscape；不得只画外接矩形或只列文字数量。D5/D6 只消费这些标准产物，不读取 Blueprint、compile trace 或 extent map 建立特殊分支。
