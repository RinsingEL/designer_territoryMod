# CityBlueprint 数据契约

## 定位

本文冻结 D4 结构设计与 D6 后户外空间设计共用的城市决策边界。城市编译器不调用 LLM：程序先生成完整只读 `CityBlueprintContext`，AI 提交设计，宿主组装完整 canonical `CityBlueprint` revision。可操作的编译设计冲突允许同一 Context 下修订，最多五次；明确的搜索预算耗尽、程序安全上限、锚点终审故障属于程序阻塞，不增加设计失败预算。上下文准备和提交校验拒绝也不计入预算。

CityBlueprint 本身不生成结构或景观坐标。结构编译器消费 `groups[]/arrayCompositions[]/relations[]`；D6 锁定真实 footprint 后，户外编译器消费同一 Blueprint 的 `outdoorPlan`。坐标、旋转、模板 identity、collision、逐格 mask 与实际面积只能出现在程序编译产物中。

## 当前 schema

### D4 一次初版与整体性扩张协议（2026-09-17）

HTTP 共用 `/realm/city/submit_d4_blueprint`，路由注入 d4Tool。请求携带 contextId、workflowRevision；公开 MCP 另带 runId、citySeedId，Provider 由宿主绑定。存档主阶段为 OVERVIEW / DISTRICTS / INTEGRATION / COMPLETE。不公开局部修饰、重开、逐区评价和完成工具。

| 工具 | 职责及输入 |
| --- | --- |
| city_d4_overview | overview={citySettings,districts,districtDisposition?}；outdoorPlan 仅全城基础设置。预标记可选。 |
| city_d4_district | 当前区 districtDesign：groups、arrayCompositions、relations、foundationGroupIds、landscapes、局部 surfaceMaterials。有效落位后自动推进，只有本区建筑与景观全空返回 initialDistrictEmpty=true 并允许重做。 |
| city_d4_mark | 看初版总览后以 baseDraftHash、assessment、districtDisposition 确认全城标记；每个 districtId 恰好一次，independent 为布尔值。独立区还需 peripheralRole（BORDER_OUTPOST / PERIPHERAL_RESOURCE / SUBURBAN_INDUSTRY / OTHER_PERIPHERAL）与 reason，仅限职责本身适合独立的外围区。 |
| city_d4_integrate | baseDraftHash、assessment、targetDistrictId、protectedDistrictIds、expansionMode、integrationIntent、changes。只扩大一个非独立区。ADJUST_ARRAY 调整阵列参数/嵌套；OUTWARD_ARRAY 追加以 BETWEEN_GROUPS 指向本区及目标区的完整阵列。切换处理区须 previousExpansionComplete=true，说明上一处整体性已成立。 |
| city_d4_preview | baseDraftHash + overview=true 或 groupIds（1–3），按需补看图。 |
| city_d4_finalize | 当前 baseDraftHash、assessment、functionsPreserved=true，可附 autoAdvanceAfterD4；直接确认已预览的实际布局，不夹带新设计，不要求至少一次扩张。 |
| city_d4_materials / example / blocks / handbook | 按需选材、案例、方块与手册读取。 |

设计与扩张返回当前实际总览，后续标记、扩张或提交必须基于已展示的当前版本；不要求逐区评价。整体性由 AI 判断，允许隔河、道路和合理空隙，不设固定距离、边界接触或道路连通门槛。空间独立标记不修改交通连接意图。

changes 按 ID 合并；本轮扩张只接受 groups / arrayCompositions / relations / foundationGroupIds，不接受删除组、重做用途、素材或景观。已有组只能调整阵列参数；新增嵌套成员属于当前区。clearFields 只用于增加嵌套前清除独立 placementRelation。

宿主用上一草稿的真实建筑几何冻结其他区；保护名单禁止覆盖，未保护区允许替换冲突的完整建筑。新建筑通过地形和硬碰撞检查才执行替换，若会清空其他区则跳过该新建筑并记录 DISTRICT_WOULD_BE_EMPTIED。被替换建筑记录于 compiledLayout.displacedBuildings；下一次增量编译继续使用保留结果，不恢复被替换建筑。其他区景观保持既有范围并作为障碍。程序保底不代替 AI 对“功能主体仍成立”的判断。

FINAL 复用同一草稿保存的 host-only compiledResult，接受后交付现有 geometry commit 与后续 D5/D6 链；不重新排布已确认建筑。compiledResult 不进入 revisionEvidence 的模型载荷。D4 提示词位于 `config/geomantia/prompts/city/d4_v2/`，旧 city/ 自定义提示保留但不再用于新协议。

格式、参数、引用错误允许按具体反馈修正。正常地形裁减不触发局部美化重试；程序故障保留方案并归宿主处理。原有 CORE 唯一、作者素材、模板边界与实际安全校验继续有效，空间主次由功能与几何表达。

### 意图、计划阵列与逐栋结果（2026-09-13）

- `city_submit_d4_blueprint` 可先提交工具根级 `designIntent={groups:[{groupId,role,intent,preferredPatchRefs}]}`；该对象不是蓝图内部的城市主题 designIntent。再批量提交 `materialSelections=[{groupId,query?,structureRefs?,fillPoolRefs?}]` 搜索作者元数据或确认素材。两阶段与 cityBlueprint/blueprintPatch 分开调用，返回 `designInProgress=true`，不推进生成。会话按 contextId 保存，prepare 与后续草稿返回已确认意图和估算。
- Group 可填 `structureCount`：1–1024 的整数且不少于 required 引用数；省略采用已有规模、extent 和算法建议值。CENTER_SYMMETRIC 总数为奇数（一中心与若干同素材成对计划成员）。数量是计划输入，地形筛选不另设保留数量门槛。
- 同一 DRAFT 可提交一个完整嵌套组团及之前的设计。部分草稿暂不执行整城规模嵌套门槛，FINAL 执行既有 CITY 核心参与组合、LARGE_CITY 至少两个有效组合规则；没有新增面积或主体比例硬门槛。
- 编译先确定阵列位置、模板和完整矩形占地，再逐栋筛选。正常水域、山体、边界或碰撞导致成员跳过，不换模板、搜索替补槽位或搬动其余建筑。全空组保留记录。作者入口/不支持的地形能力及格式错误仍明确拒绝。
- `designReview` 同时记录 planned/retained 建筑、底层阵列及嵌套承载量；`skippedMembers` 记录槽位、plannedBounds、原始过滤原因。DRAFT 的 revisionEvidence.compiledDesignReview 内联报告，预览橙色虚框 S 对应跳过位置。程序可编译不代表 AI 已认可效果。
- 取消百分比面积补建筑和连接补建筑。fillPools 仅提供 AI 已计划槽位的素材；旧 expansionPolicy/connectionPlan 保留读取兼容，但不能再触发额外建筑。ADJACENCY 对完整阵列做整体相邻落位，CONNECTION 只请求道路。内部通路预留，主路在建筑筛选后路由；缺失端点或无法通行明确记录跳过，不伪装连通。
- 普通起伏沿用台面；超过现有 terrainPolicy 适配上限两倍的极端坡度、起伏或高差逐栋跳过。浅水坑还要求四周八个采样单元都是陆地、无显著岸壁高差且地貌非河湖海/峡谷，不将水深单独作为可铺平的依据。细地形仍依赖真实落地基础保护。


### D4 提交的几何接受边界（2026-09-07）

#### 设计优先硬门槛收敛（2026-09-07）

- 编译器推导的功能区formationBounds/formationSpan仅用于初始槽位、容量估计和布局引导，不是作者禁建边界。计划建筑仍不得越过真实cityPlanningBounds、实体碰撞和明确硬关系。
- COMPACT/ORGANIC_COMPACT等的最大建筑间距参与评分，不因超过推导最大gap而直接拒绝候选；显式道路所需的最小通行间隙与真实道路碰撞仍检查。默认功能区隔离距离不再作为硬门槛，明确BUFFER/DISTANCE关系仍由关系检查执行。
- 同一对功能区的相反HARD方向约束在submit前置返回 `CITY_BLUEPRINT_RELATION_CONTRADICTION`，同时指出当前与冲突关系字段。不会把可兼容的多轴方位或软偏好判为矛盾。
- 数学搜索槽位耗尽不是设计不成立的证明。保留程序故障分类和上一版accepted；不可伪造宽深修正建议。局部自然高差的工程承诺、作者水陆/拓扑限制及采样覆盖规则沿用下述边界；审美质量仍为warning，不冒充硬安全失败。
- 搜索检查点key升级以隔离旧硬门槛语义，不能复用旧求解结果假装新规则验证通过。

#### 局部失败反馈与未接受草稿（2026-09-07）

- 几何拒绝直接返回 `designFeedback`（`city_design_failure_feedback.v1`）：失败group/structure、精确group字段路径、候选过滤原因计数、至多8个失败坐标样本。中途失败后成功的槽位不当作最终失败；坐标样本非完整搜索空间证明。
- 正常地形/碰撞候选失败以逐栋缺口回传；只有作者能力缺失、异常和程序安全故障保留阻塞分类。不得将普通空阵列升级为程序阻塞。
- 数值校验中，景观parcelCount和景观角色占比范围/总和失败可携带 `issues[].constraint`：measurement、actual、minimumInclusive、maximumInclusive、instruction。比例总和容差仍为1e-6。建议只指向已有字段，不虚构院落宽深等尚未接入的字段。
- 未通过几何接受的canonical方案保存为 `city_blueprint_draft.json`（`city_blueprint_draft.v1`），并通过 `revisionEvidence` 内联回传。草稿不代表accepted、不进入worldgen。
- `blueprintPatch` 可选 `baseDraftHash` 作为拒绝草稿修订基准，与 `baseBlueprintHash` 严格二选一；两者都只允许EXACT_SHARES和replace操作。绑定当前Context、城市、草稿内容哈希以及保存草稿时的accepted版本，过期即拒绝。成功接受后使草稿失效。
- prepare 与恢复回传有效草稿和设计会话。DRAFT 支持逐组团推进，哈希补丁仍只支持替换；新增组使用保留其他组的完整蓝图。

- 新提交在发布 accepted 之前执行 D4 布局编译和 `compilationAcceptance`。仅 JSON/schema 合法不等于设计被接受。
- 成功后保存 `city_blueprint_geometry_commit.json`，schema 为 `city_blueprint_geometry_commit.v1`；内容包含 canonical `blueprintHash` 和完整 `CompilationResult`。接受 trace 增加 `designGeometryValidated=true` 与该文件的 `geometryCommitHash`。
- 正式 `city_compile_d4_blueprint` 校验 Context/D3/catalog/terrain/blueprint 和几何文件 hash 后复用冻结结果，不重新排建筑。几何文件损坏或缺失不得退回重新搜索。
- 几何拒绝写独立 rejection trace，不覆盖上一版已接受的蓝图/几何。异常或已识别的程序搜索故障标记 `failureOwner=program`，保留 `city_blueprint_blocked_proposal.json`，不要求 AI 重设计，也不调用可能执行旧 revision 的 post-D4 retry。
- 未带几何冻结标记的旧 accepted 存档仍走旧 D4 编译入口。
- **当前冻结范围仅是 D4 结构布局及该编译器输出，不宣称 D5/D6/D7 全部工程已完成预验。** 新场景阵列的正式 Blueprint 字段尚未接入；不得因 Java 几何核心存在便向 Agent 宣告这些算法已正式可用。

铺台面的功能区（`outdoorPlan.mode=GENERATE` 且列于 `foundationGroupIds`）将局部坡度/起伏作为台面实现要求，仍检查采样覆盖、水陆与作者拓扑类型。保留自然地面的功能区不自动获得这项工程承诺。已冻结台面的区块实现采用浅凹填土、深凹桥面、凸起切除，不再以填土深度阈值否决桥面。

| 对象 | schema |
| --- | --- |
| 上下文 | `city_blueprint_context` |
| 引用目录 | `city_blueprint_reference_catalog` |
| 目录快照 | `city_blueprint_catalog_snapshot` |
| 蓝图 | `city_blueprint` |
| 校验报告 | `city_blueprint_validation_report` |
| 提交 trace | `city_blueprint_submission_trace` |
| 编译失败预算 | `city_blueprint_failure_budget` |

## ArtifactRef

所有真值引用统一使用严格对象：

```json
{
  "path": "<runId>/city_test_runs/<citySeedId>/steps/d3/city_landform_review_package.json",
  "schema": "city_landform_review",
  "contentHash": "sha256:<64 lowercase hex>"
}
```

`path` 是相对运行时 debug root 的冻结路径。提交时文件内容 hash 失配即 stale，不按文件名或修改时间猜兼容。

## CityBlueprintContext

必填字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `schema` | string | 固定 `city_blueprint_context`。 |
| `contextId` | string | 对除 `preparedAt` 外的冻结上下文做 SHA-256。 |
| `runId` / `cityId` | string | 当前 run 与城市。 |
| `sourceD3Ref` | ArtifactRef | 当前 D3 review package。 |
| `catalogSnapshotRef` | ArtifactRef | 本次完整目录快照。 |
| `generationSeedSuggestion` | safe integer | 程序按 city + D3 hash + catalog hash 稳定派生，范围为 JavaScript safe integer。 |
| `decisionBoundary` | object | 明确 prepare 与提交校验拒绝不计失败、D4 编译失败上限为 5、编译失败后允许提交完整 revision；同时冻结 Agent 只能使用工具响应和明确返回 artifacts 的恢复边界。 |
| `designGuide` | object | 程序从实际可用引用目录生成的策划说明：作者语义权威、设计流程、起点边界、建筑阵列与功能区组合的不同职责、道路目的和修订边界。随 Context 冻结并进入 `contextId`，不是替代 AI 决策的默认设计。 |
| `citySeed` | object | 当前 CitySeed 完整只读输入。 |
| `d3ReviewPackage` | object | D3 地形、patch、member cells、指标、邻接与 preview 引用。 |
| `catalogSnapshot` | object | `city_blueprint_catalog_snapshot`；包含 `city_semantic_profile_catalog` 结构画像、固定模板目录、`city_blueprint_reference_catalog` 及 D3 terrain field 引用。引用目录同时冻结 LandUse rule、Foundation Profile、Surface Recipe、Landscape Profile、ParcelStyle、Landscape Fill Profile、建筑可选绿化标记与城市植物 palette，D6 后不得重新解释为另一份配置。 |
| `preparedAt` | instant | 追踪字段，不进入 `contextId`。 |

D3 `status=partial`、未知 schema、城市 ID 不一致，以及 AI 候选首都未接受/审查 identity 过期时，不得准备上下文。

## Structure Terrain Modes

`terrainModes` 是 City 固定 placement topology 枚举数组，不属于 TerraSense 动态词表。值域严格为 `SURFACE | EMBEDDED | FLOATING`，导入时大小写归一为大写；正式画像必须非空，未知值或归一后重复值直接拒绝。旧 `terrainTerms` 是退役字段，导入器必须显式拒绝。

多值按 OR 解析。当前运行时只真正实现 `SURFACE`：只要数组含 `SURFACE`，D4 便解析并冻结 `resolvedTerrainMode=SURFACE`；只有 `EMBEDDED/FLOATING` 时明确返回 `CITY_STRUCTURE_TERRAIN_MODE_UNSUPPORTED`，不得伪装为已支持。

SURFACE 门禁只读取已有 `city_land_use_terrain_field`，不触发扫描或 chunk 加载。transformed collision footprint 覆盖的每个 terrain-field cell 必须存在、`sampled=true` 且 `water=false`；`terrainPolicy=CONFORM|BALANCED|ASSERTIVE` 另分别把完整占地的最大坡度限制为 `6|12|18`、最大 `localRelief` 限制为 `8|12|18`、最大高程范围限制为 `6|12|18`。roughness、biome、landform 与 patch 平均坡度只参与评分或诊断。Context/Snapshot 只冻结 `terrainFieldRef` 的 schema 与内容 hash；文件变化、city/grid/step 不一致均 stale。

## Blueprint 引用目录

### 2026-09-06 编译可靠性与局部修订补充

- `automaticConnectionMaxDistanceBlocks` 保留旧目录兼容，不再触发连接补建筑。
- `fillPools[]` 可选 `maxCopiesPerStructurePerGroup`，非负整数，0/省略不限。计数包含同组已放下的 required/fill/connectivity/percentage 同种结构；限制只阻止继续填充，不删除或替换必需建筑。各自动填充阶段优先选择池内当前使用较少的合法结构，同次数按稳定游标选择，不按名称猜功能。
- 所有组的建筑量由计划阵列决定，核心与普通组都不再按目标面积追加建筑。景观仍按自身配置处理，本次不接管景观独立生长案。
- 局部修订沿用 `baseBlueprintHash + blueprintPatch`。编译器可复用成功的单阵列搜索检查点，键绑定冻结 context、当前布局状态、请求、占用及邻区避让依赖，输入变更即失效；最多保留 128 个、每个 1 MiB，损坏或不可用时正常计算。检查点不是成功城市/成功分区的整体快照，共享道路、景观和最终验收必须重新执行。独立统计在 `city_array_checkpoint_statistics.json`，不得让缓存命中改变正式布局或其 hash。
- 程序内部骨架道路在填充前对全部已放置建筑进行包含路缘的有限绕行，并以同样横截面预留占地。绕行失败保留程序错误，不跳过安全检查、不删除建筑。检查点只复用未改变的精确搜索输入，不承诺修改一个功能区后其他所有功能区完全不受共享依赖影响。

### Landscape v0.10

`outdoorPlan.landscapes[]` 使用严格判别结构：

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| `landscapeId` / `landscapeProfileRef` | string | 城市内唯一 ID；Profile 必须存在。 |
| `purpose` | enum | `FUNCTIONAL | COMPOSITIONAL | AMBIENT`。 |
| `originMode` | enum | `ATTACHED | FREE_STANDING`。 |
| `owner` | object/null | `ATTACHED` 必填 `{groupId}`，表示所属功能组；兼容可选 `requiredStructureRef` 作为初始位置参考，不依赖建筑落位。`FREE_STANDING` 必须为 null。 |
| `placementDomain` | enum/null | `FREE_STANDING` 必填：`URBAN_RESIDUAL | FOUNDATION_EDGE | BETWEEN_GROUPS | ALONG_WATER`；`ATTACHED` 必须为 null。 |
| `instanceCount` | positive int | AI 提交目标实例数；`ATTACHED` 固定为 1。 |
| `parcelCount` | positive int | AI 提交的每实例目标数量，必须落在 Profile `parcelCountMin..Max`；实际数量可被地形减少。 |
| `required` | boolean | true 表示功能区必须尝试提供此类景观；位置、形状、实际 Parcel 数与面积服从地形。完全无可用格时写警告并继续 D4/D6。false 仅允许 `FREE_STANDING`，逐实例准入。 |
| `preferredPatchRefs` / `terrainPolicy` / `fillSelection` | existing | 自由选址偏好、地形策略和 Parcel 内填充方案。 |

`groups[].requiredStructureRefs[]` 在 v0.12 必须唯一。景观归属功能组；各阶段建筑均可作为初始位置参考，不产生存续依赖。

`ParcelStyle` 严格字段为 `parcelCountMin`、`parcelCountMax`、`parcelAreaMinBlocks`、`parcelAreaMaxBlocks`、`minSharedBoundaryBlocks`。删除的 `coreParcelCount*`、`fillParcelCount*`、`branchFromExistingChance`、`gapMinBlocks`、`gapMaxBlocks` 均按未知旧字段拒绝。

### D4 景观容量预留

当前产物为 `city_landscape_capacity_reservation_plan`。根字段为 `schema/cityId/sourceBlueprintHash/sourceD4Hash/planHash/status/searchNodeCount/selectionPolicy/patchBoundaryPolicy/attachedOriginPolicy/layoutScore/instances/warnings/failures`。每个取得地形容量的 required instance 冻结：

- `landscapeId/landscapeInstanceId/profileRef/ownerGroupId/ownerRequiredStructureRef/ownerAnchorId`；
- `capacityCandidateId/directionVariant/topologyVariant/requestedParcelCount/parcelCount/parcelAreaBlocks/actualAreaBlocks/capacityStatus/ownerSeedDistanceBlocks`；
- `reservationSpans[]` 和逐 Parcel `parcelReservations[]`；
- `parentParcelId/rootSource/seed/targetAreaBlocks/actualAreaBlocks/sharedBoundaryProof` 来源与接力证明；
- `warnings[]` 逐实例记录 `REQUIRED_LANDSCAPE_NO_TERRAIN_FIT_WARNING` 或 `REQUIRED_LANDSCAPE_TERRAIN_REDUCED_WARNING`；地形缩减仍生成可消费 artifact。

景观只保留地形门禁与真实占用避让：未采样、水体、陡坡和断崖格不得进入容量；景观不得覆盖结构或其他已冻结景观。`preferredPatchRefs[]` 只作软偏好，不能裁断扩张；未提供 growth 时，`ATTACHED owner` 提供外向生长种子和方向；显式 growth 以指定点为准，不可用时报告零格，普通地块无需强制父子接力。容量格彼此互斥但允许四邻接；相邻高程连续性门禁继续按 `CONFORM|BALANCED|ASSERTIVE = 4|6|10`。目标面积不可满足时保留实际非零格并警告；完全零格也只警告，不得切换固定图形、预制 mask 或让整城 D4 失败。本轮取消组合回溯：按景观逐项选择并冻结，计算预算用尽也只报告未实现需求。显式 growth 使用粗 cell 生长，不扫描全域寻找替代起点。

引用目录根对象所有数组必填且非空：

- `structureRefs[]`：`structureRef` 必须存在于冻结 TerraSense semantic profile；`templateCandidates[]` 的 `templateId + variantId` 必须存在于固定模板目录。可选 `greenParcel` 严格为 `{pattern=FREEFORM|FIELD_GRID,density=LOW|MEDIUM|HIGH,groundBlockId,pathBlockId}`；缺少即该建筑不生成自带绿化，喷泉、广场等开放结构按此方式明确关闭。
- `fillPools[]`：`poolRef` 与只引用上述 `structureRef` 的 `structureRefs[]`。
- `algorithmProfiles[]`：`algorithmProfileRef`；算法枚举为 `COMPACT | GRID | LINEAR | COURTYARD | ORGANIC_COMPACT | CENTER_SYMMETRIC`。仅 `CENTER_SYMMETRIC` 可选 `centerAxisStreetEnabled=true|false`，缺省为 false；其他算法携带该开关必须拒绝。
- `compositionProfiles[]`：`compositionProfileRef` 与 `mode=ROUND_ROBIN`；只控制模板组成顺序，不携带建筑数量上限。
- `styleProfiles[]`：`profileRef`，可选非空 `plantPalette[]`；每项严格为 `{blockId,weight>0}` 且 blockId 不重复。Blueprint 选中的城市 style profile 是建筑绿化唯一植物集合；任一带 `greenParcel` 建筑存在而该城市 palette 为空时，户外编译 hard fail。
- `roadProfiles[]`：`profileRef`、`hierarchy=SIMPLE|HIERARCHICAL`、`density=SPARSE|BALANCED|DENSE`。
- `surfaceDetailProfiles[]`：`profileRef`、`intensity=LOW|MEDIUM|HIGH`。
- `landUseRuleProfile`：完整严格 `city_land_use_rules`；其 `ruleRef` 是 Foundation/Landscape Profile 的规则白名单。
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

## CityBlueprint

### 设计输入适配（不改变 canonical schema）

`city_submit_d4_blueprint` 接受 `cityBlueprint` 或 `blueprintPatch`，严格二选一。完整设计输入可以省略 `schema/cityId/sourceD3Ref/catalogSnapshotRef/generationSeed`；宿主从当前冻结 Context 补齐，显式身份/引用冲突仍走原验证拒绝。非 DISTANCE/DIRECTION 关系可省略对应 preference，宿主只补无歧义的 `NONE`，不替模型选择距离或方向。

默认 `proportionMode=EXACT_SHARES` 保持原占比语义及误差门槛。显式 `RELATIVE_WEIGHTS` 将所有 Group 的 targetAreaShare、各 Group 的 spaceComposition 三项、各 Landscape fillSelection.variants 的 roleShares.targetShare 分别按相对权重归一化。必须是有限非负数且每组总量非零；之后原有正值、角色范围、角色完整性和作者白名单继续验证，不能借归一化越过作者限制。

局部修订必带 `baseBlueprintHash`（accepted submissionTrace.cityBlueprintHash），`blueprintPatch` 为 1～128 条 `{op:"replace",path:<JSON Pointer>,value:<JSON value>}`。仅替换已有路径，可替换数组/对象整体；新增或删除成员需替换父数组/对象，或完整重提。禁止修订身份、来源引用和 generationSeed；不接受相对权重模式。宿主在同一提交锁内检查原文件及 accepted trace 的哈希/Context，组装完整 revision 并执行全部原校验。过期、未知路径、无效结果不得覆盖 accepted Blueprint，也不重置预算。

### 冻结 canonical 对象

多入口模板出现 `D4_ARRAY_LAYOUT_FRONTAGE_ENTRANCE_AMBIGUOUS` 时，即使外层归并为 `REQUIRED_STRUCTURE_NO_LEGAL_PLACEMENT`，也必须按真实 hardBlocks 归为配置/程序阻塞，不要求 AI 更换 required 结构、改 Patch 或猜主入口。该路由不新增主入口推断，不改变既有朝向规则，也不减写历史失败计数。

根字段全部必填，未知字段拒绝：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `schema` | string | 固定 `city_blueprint`；旧 `schemaVersion` Blueprint 不兼容且不迁移。 |
| `cityId` | string | 与 context / D3 一致。 |
| `sourceD3Ref` / `catalogSnapshotRef` | ArtifactRef | 与 context 逐字段一致。 |
| `generationSeed` | safe integer | `-9007199254740991..9007199254740991`；后续编译器唯一记录随机源。 |
| `designIntent` | object | `cityIdentity`、`theme`、非空 `functionalRoles[]`。 |
| `styleProfile` | object | 仅 `profileRef`。 |
| `groups[]` | Group[] | 至少一个。 |
| `arrayCompositions[]` | ArrayComposition[] | 可为空；父阵列按完整 Group 范围编排子阵列。 |
| `relations[]` | Relation[] | 单 Group 可为空；多 Group 城市中，任何 `allowRelationConnection=true` 的 Group 都必须至少出现在一条 relation 中。 |
| `roadProfile` | object | 仅 `profileRef`。 |
| `surfaceDetailProfile` | object | 仅 `profileRef`。 |
| `outdoorPlan` | OutdoorPlan | 同一次提交中的完整户外设计意图。 |

Group 必填字段：

| 字段 | 值域 |
| --- | --- |
| `groupId` | 蓝图内唯一非空字符串。 |
| `groupKind` | 只接受 `STRUCTURE`；景观只能进入 `outdoorPlan.landscapes[]`。 |
| `preferredPatchRefs[]` | 非空当前 D3 `landformPatchId` 列表；多个 Group 可以共享。 |
| `preferredPatchZone` | `CENTER | NORTH | EAST | SOUTH | WEST`；核心在全部偏好 patch 精确 member-cell 并集内的起步方位。北=-Z、南=+Z、西=-X、东=+X；不表示世界坐标，也不约束连接阶段。 |
| `placementRelation` | 可选严格对象；使用 `BETWEEN_PATCHES | ALONG_PATCH_BOUNDARY | BETWEEN_GROUPS` 表达城市内部关系位置。 |
| `role` | 非空功能角色。 |
| `priority` | `CORE | STANDARD | PERIPHERAL`。 |
| `targetAreaShare` | `0 < number <= 1`；所有 Group 之和必须为 `1.0`。全城只能有一个 `CORE`，其余 Group 之间按各自 priority 两两比较。 |
| `extentClass` | `SMALL | MEDIUM | LARGE`，表示空间范围而非建筑数量。 |
| `densityClass` | `SPARSE | BALANCED | DENSE`。 |
| `algorithmProfileRef` | 冻结算法引用。 |
| `terrainPolicy` | `CONFORM | BALANCED | ASSERTIVE`。 |
| `requiredStructureRefs[]` | 非空、组内唯一且全部在结构白名单；与 Landscape 归属分开；景观 owner.groupId 定位所属功能组。 |
| `fillPoolRef` / `fillPools` | 二选一：单池引用，或非空 `[{poolRef, weight}]`。池引用唯一、权重必须为有限正数。用于初始填充和外扩。 |
| `compositionProfileRef` | 冻结目录引用；composition 不限制数量。 |
| `spaceComposition` | 严格对象 `buildingShare/landscapeShare/openSpaceShare`；三者均为 `0..1` 且和为 `1.0`。 |
| `expansionPolicy` | 严格对象 `allowOutwardExpansion/allowRelationConnection/stopWhenTargetReached`；均为 boolean。 |
| `buildingGreeneryPolicy` | 严格对象 `{coverage,patternPreference,densityPreference}`。`coverage=NONE|SPARSE|BALANCED|LUSH`；`patternPreference=TEMPLATE_DEFAULT|FREEFORM|FIELD_GRID|MIXED`；`densityPreference=TEMPLATE_DEFAULT|LOW|MEDIUM|HIGH`。AI 只表达功能区整体意图，不提交逐栋坐标、mask、逐栋开关或方块材料。 |
| `connectionPlan` | 可选连接专用覆写；不填时继承本 Group 的 fill pool、算法和疏密。 |
| `attachedFeatures[]` | 当前版本必须为空；案子 04 才定义景观归属。 |

`connectionPlan` 只表达连接阵列语义，不表达结构永久类型，也不提交坐标：

| 字段 | 值域与继承 |
| --- | --- |
| `structurePoolRef` / `structurePools` | 可选，最多配置一种；连接单池或加权多池，均省略时继承功能区的全部填充池。 |
| `algorithmProfileRef` | 可选；连接阵列算法，不填继承 Group 的 `algorithmProfileRef`。 |
| `densityClass` | 可选 `SPARSE | BALANCED | DENSE`；不填继承 Group 疏密，并由程序换算实体间距与 handoff。 |
| `parameters.clusterShape` | `ORGANIC_COMPACT | GRID | COURTYARD | L_SHAPE | U_SHAPE`；只适用于解析为 `compound_cluster` 的算法。 |
| `parameters.sideMode` | `LEFT | RIGHT | BOTH`；只适用于解析为 `guide_line_dual_side` 的 LINEAR 算法。 |
| `parameters.stagger` | boolean；只适用于 `guide_line_dual_side`。 |
| `parameters.widthClass` | `NARROW | MEDIUM | WIDE`；只适用于 `guide_line_dual_side`，控制阵列宽度档位而非 block 宽度。 |

连接参数与解析后的 planner family 不匹配时返回 `CITY_BLUEPRINT_CONNECTION_PARAMETERS_INVALID`。AI 不提交 focus、外扩方向、block gap、候选数量、candidateId 或逐栋坐标；这些都由编译器按当前已提交阵列和目标 Group 自动派生。

`CENTER_SYMMETRIC` 计划一个 required 中心和同模板成对成员，先固定对称几何，再分别筛选各栋。单侧地形失败留下单侧缺口，不能旋转重试整对或替换算法填洞。

### 关系位置

`placementRelation` 严格包含 `kind/patchRefs[]/groupRefs[]`，只决定 Group 首个阵列核心的位置，不提交坐标，也不替换该 Group 自身的算法、模板池或 `terrainPolicy`：

- `BETWEEN_PATCHES`：恰好两个不同 `patchRefs`，`groupRefs` 为空；以两 Patch 最近合法 member cell 中心的中点起步，首个核心候选域只包含这两个 Patch。
- `ALONG_PATCH_BOUNDARY`：恰好两个不同 `patchRefs`，`groupRefs` 为空；`patchRefs[0]` 是落地方，以其最接近 `patchRefs[1]` 的边界 member cell 起步，首个核心候选域只包含第一个 Patch。
- `BETWEEN_GROUPS`：`patchRefs` 为空，恰好两个不同 `groupRefs`，且不能引用自身；编译器先完成两个端点 Group 的 required 核心，再以两端计划包围盒中心的中点起步，候选域为当前 D3 城市规划边界。

显式关系和 preferredPatchRefs/preferredPatchZone 确定计划位置；正常地形不适配只跳过对应建筑。后续计划槽位不随前项保留情况移动，不改投其他 Patch 补洞。

### 父阵列

`arrayCompositions[]` 每项严格包含：

| 字段 | 约束 |
| --- | --- |
| `compositionId` | Blueprint 内唯一非空字符串。 |
| `algorithmProfileRef` | 冻结算法引用；只编排完整子 Group，不覆盖子 Group 自身算法。 |
| `centerGroupId` | 中心完整 Group；可按 Patch 关系定位，但不能使用 `BETWEEN_GROUPS`。 |
| `memberGroupIds[]` | 非空、组内唯一的完整子 Group。成员由父阵列给出起点，不能再声明 `placementRelation`。 |

一个 Group 最多作为一个父组合的成员，同时可以作为另一个组合的中心继续组织子阵列；每个中心只定义一个组合，成员归属不得成环。组合本身不是额外建筑组，不重复计入底层阵列数量。程序先由内向外估算子树范围，再由外向内分配槽位，子 Group 保留自身素材、算法、街巷和入口。父阵列按 required/fill 模板 transformed footprint、最低成形数量、子算法、密度和区内街带推导范围，预留互不相交且不越出 D3 城市边界的播种槽位；不得把 `extentClass` 最大跨度直接当作槽位边长。每个独立选址沿用该 Group 的 `preferredPatchRefs[]`；嵌套子槽由父阵列的整体关系安排。父算法为 `CENTER_SYMMETRIC` 时，`memberGroupIds[]` 必须为偶数，相邻两项组成一对；仍保持完整 Group 槽位的成对对称。

2026-09-10 起，新 prepare 的 Context 增加 `scaleDesignTask`，在设计前说明五档任务。初始底层阵列建议：hamlet 1–2、village 2–4、town 4–7、city 8–12、large_city 12–18；范围是建议，不成为数量或面积拒绝阀门。CITY 要求主体实际嵌套，最低结构校验要求 CORE 参与非空组合；LARGE_CITY 还要求多个非空组合。该最低检查不等于美观验收，不能用一个很小的组合冒充完整主体。有效嵌套的更细数量阈值尚未定义。首都身份仍不自动升级为 LARGE_CITY。旧 frozen Context 缺少此任务时不追溯追加新规则。

`ALONG_PATCH_BOUNDARY` 沿实际相邻采样单元的共同边缘生成候选，第一 patch 为落位侧。COMPACT / ORGANIC_COMPACT 可沿边缘落建筑，非对称父组合可沿边缘放完整子阵列；CENTER_SYMMETRIC 保留自身对称语义。没有共同边缘时返回 `CITY_BLUEPRINT_PATCH_BOUNDARY_UNAVAILABLE`，不会回退普通点位；水域、碰撞和工程限制不放宽。不增加专用功能区枚举或逐侧接路配置。

Relation 必填 `fromGroupId`、`toGroupId`、`relationKind`、`strength`、`distancePreference`、`directionPreference`。`relationKind` 为 `HIERARCHY | ADJACENCY | CONNECTION | BUFFER | DISTANCE | DIRECTION`，`strength` 为 `HARD | SOFT`。只有 `DISTANCE` 可使用 `distancePreference=NEAR|FAR`，其他关系必须为 `NONE`；只有 `DIRECTION` 可使用 `directionPreference=NORTH|EAST|SOUTH|WEST`，其他关系必须为 `NONE`。`HIERARCHY` 按 `fromGroupId -> toGroupId` 表示功能父到子，其自身必须无环，但不参与几何编译排序。几何排序仅使用 BETWEEN_GROUPS 的参考组依赖和阵列组合中心到成员的落位依赖；嵌套尺寸仍先解算子阵列再组合父阵列。无依赖节点保持既有算法/priority/groupId 稳定顺序。两种图分别校验，不能混合制造假循环。

## OutdoorPlan

`outdoorPlan` 根字段严格为 `mode`、`envelopeProfile`、`foundationProfileRef`、`foundationGroupIds[]` 和 `landscapes[]`，未知字段拒绝。旧 spatialGrounds 及其空间类型、主次声明已删除，不翻译旧输入。

- `mode=GENERATE`：foundationProfileRef 命中冻结目录；foundationGroupIds 声明显式共同台地，引用存在且不重复，不要求全覆盖。列表用于落位时的地形工程适应判定；落位后的台面范围另包含满足下文条件的城区阵列。
- `mode=PRESERVE`：foundationProfileRef 为空，foundationGroupIds 和 landscapes 为空。
- `envelopeProfile=COMPACT|BALANCED|LOOSE`：保留总体紧凑度语义，正式几何参数仍由 Foundation Profile 决定。
- 台地凹坑处理、自然地形保护和选材能力保留；不新增替代主次枚举。
- AI 在功能区阶段提交台地对象与景观，宿主合并成 canonical OutdoorPlan；总览只配基础策略。

`landscapes[]` 每项字段：

| 字段 | 类型 / 值域 | 说明 |
| --- | --- | --- |
| `landscapeId` | string | 户外计划内唯一；不得与其他 landscape 重复。 |
| `landscapeProfileRef` | string | 冻结景观 profile，决定 rule、surface recipe、基准面积和 membership。 |
| `purpose` | `FUNCTIONAL|COMPOSITIONAL|AMBIENT` | 景观在城市构图中的意义。 |
| `originMode` | `ATTACHED|FREE_STANDING` | 严格判别字段。 |
| `owner` | object | 仅 ATTACHED 使用；填写 `groupId`，旧 `requiredStructureRef` 可选且仅作位置参考。 |
| `placementDomain` | `URBAN_RESIDUAL|FOUNDATION_EDGE|BETWEEN_GROUPS|ALONG_WATER` | 仅 FREE_STANDING 使用。 |
| `instanceCount` | positive integer | AI 提交的目标实例数；ATTACHED 固定为 1。 |
| `parcelCount` | positive integer | AI 提交的每实例目标 Parcel 数，必须落入 Profile 范围；实际结果服从地形。 |
| `preferredPatchRefs[]` | string[] | 可为空；非空项必须命中冻结 D3 patch。 |
| `terrainPolicy` | `CONFORM|BALANCED|ASSERTIVE` | 景观地形适配档位。 |
| `required` | boolean | required 必须尝试提供该景观功能；非零可用地按实际形状/面积冻结，零格写警告；FREE_STANDING 当前必须 optional。 |
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

required Landscape 在 required 建筑落位后，以 owner 为种子枚举近地与远端好地、方向和父子拓扑；景观不得为了满足规划完整性反向迫使建筑换位。程序优先保留更多非零实例与更多地形可用格，同面积时优先离 owner 更近且形态更好的方案。实际 `instanceCount/parcelCount/area` 可被地形减少，减少或零格都写 warning；景观在 fill 前冻结初始形状；fill/connectivity/percentage 建筑及道路可以占用景观，最终从原 spans 裁除，不迁移景观，不反向挤建筑。裁让记录初始与保留面积及 warning。FREE_STANDING optional 在 D6 后从剩余空间逐实例准入。固定 Blueprint、catalog、D3、D6 与 seed 必须完全复现。

`residualPolicy` 已删除。单一 Foundation domain 内部全部使用同一基础地板，Landscape Parcel 后写覆盖；不得按 SpatialGround 分配不同铺地，也不得保留原群系残余。显式自然、绿地和农田只能通过 `landscapes[]` 声明。

## 禁止字段

Blueprint 任意层级禁止：世界/block `x/y/z`、`blockX/Y/Z`、anchor、rotation、mirror、candidateId、直接 templateId/templateRef/nbtFile、`algorithm` 或 `algorithmName`。户外层另禁止 block ID、逐格 mask、固定形状、距离环、几何 fallback、裸面积、行动力和成本。它们属于程序输出，不属于 AI 决策。

## 校验与失败预算

- 同一 `contextId` 可以提交完整 Blueprint revision；字段、枚举、引用、关系或 stale 等提交校验拒绝均不增加 `failureCount`。
- 只有程序化 D4 编译或 D4 终审明确失败才原子增加 `failureCount`。第 1～4 次失败返回 `retryAllowed=true` 与 `nextAction=city_submit_d4_blueprint`；第 5 次失败后 `retryAllowed=false`，停止 Agent Loop 并请求人工处理。
- `city_blueprint_failure_budget.json` 以当前 `contextId` 为身份，必填 `failureCount/maximumFailureCount=5/remainingFailureCount/status/retryAllowed/failures[]`。程序阻塞后因作者目录修正而正式刷新 Context 时，旧文件随旧方案归档，原 failureCount/failures 不减写并迁移至新 contextId，previousContextId 标识来源；预算耗尽不能经此入口重置。旧 Blueprint 仅作设计参考，需完整提交到新 Context，旧哈希补丁仍拒绝。计数更新只锁定短 ledger 写入，不得把整个编译过程串行化，也不得引入“同一时间只允许一个 Blueprint 编译”的契约。
- `preferredPatchRefs[]` 必须非空并命中 D3；多个 Group 可以共享 patch；Group ID 唯一；relation 端点存在且不自指。多 Group 城市的 relation-enabled Group 缺少关系时，以 `CITY_BLUEPRINT_FUNCTION_AREA_RELATION_UNSPECIFIED` 在提交前拒绝。
- 所有 D3、catalog、structure、pool、algorithm、composition、style、road、surface 引用必须命中冻结快照。
- `GENERATE` 必须完整覆盖全部 STRUCTURE Group；户外 group、landscape、patch、rule、recipe、profile 和 reference Group 必须命中同一冻结上下文。
- 最新校验通过的 revision 原子发布为 active `city_blueprint.json`、validation report 与 submission trace。校验拒绝写独立 last-rejection report/trace，不得覆盖 active accepted artifacts。
- submission trace 记录 prepare 是否计数、D3/catalog refs、status 和 failure reasons；不再记录 `aiCityDesignSubmissionCount` 或 `attemptConsumed`，也不保存被拒 Blueprint payload。
- 编译失败恢复时，Agent 只能使用工具响应、`failureCount/retryAllowed/nextAction` 和工具明确返回的 artifacts。不得读取服务端源码、项目文档或未由工具返回的原始 run 文件寻找答案。

主要 reason code：

```text
CITY_BLUEPRINT_SCHEMA_UNSUPPORTED
CITY_BLUEPRINT_FORBIDDEN_PLACEMENT_FIELD
CITY_BLUEPRINT_CONTEXT_STALE
CITY_BLUEPRINT_D3_STALE
CITY_BLUEPRINT_CATALOG_STALE
CITY_BLUEPRINT_FAILURE_BUDGET_EXHAUSTED
CITY_BLUEPRINT_GROUP_KIND_UNSUPPORTED
CITY_BLUEPRINT_PREFERRED_PATCH_UNKNOWN
CITY_BLUEPRINT_RELATION_ENDPOINT_UNKNOWN
CITY_BLUEPRINT_FUNCTION_AREA_RELATION_UNSPECIFIED
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

案子 02 的冻结输入是：当前校验通过并原子发布的 active `city_blueprint.json`、同目录 `city_blueprint_catalog_snapshot.json`、Blueprint 中两份 ArtifactRef 和 `generationSeed`。编译器不得再次请求 AI 选择 candidate/slot/扩张方向，且最终必须输出现有标准 `structure_anchor_plan.json` / `structure_anchor_map.json`。

02 已接通：`city_run_workflow` 只有 CityBlueprint 主线，不接收模式选择字段。`d4CandidateMode` 已删除并显式拒绝；candidate/session/manual anchor 接口仅是各自独立的 legacy/debug 工具，不得通过正式 workflow 选择。

## CityGenerationCompileTrace

文件：`city_test_runs/<cityId>/steps/d4/city_generation_compile_trace.json`，`schema=city_generation_compile_trace`。

根字段：`cityId`、`status=compiled|failed`、`reasonCode`、`generationSeed`、`selectionMode`、`aiCandidateSelectionCount=0`、`manualCandidateSelectionCount=0`、`sourceD3Ref`、`catalogSnapshotRef`、`functionAreaFormationPlan`、`connectivityPlan`、`arrayCompositionSlots[]`、`selections[]`、`groupResults[]`、`cityMainRoadPlan`、`streetFirstNetworkTrace`、`residentialOverflowPlan`、`compilationAcceptance` 与 `dynamicAreaPlan`。`functionAreaFormationPlan` 只能由 D4 根据已提交建筑形成，调用方不能补写；其中 `preallocatedAreaCount` 必须为 `0`。

组合槽分配失败同样返回 `CompilationResult` 并落盘 trace，不直接抛出无恢复动作的异常。`failureSummary.phase=array_composition` 保存失败原因；非对称成员联合分配无解时另保存 `compositionId/searchVisited/searchLimitReached/members[]`，成员项记录 `groupId/formationSpanBlocks/candidateCount/legalCandidateCount/outsidePlanningBoundsCount/reservedOverlapCount/outsidePreferredPatchCount`。成员候选联合避让并允许回溯，不能因前一个成员的首次选择阻塞后一个成员。`CITY_BLUEPRINT_ARRAY_COMPOSITION_SEARCH_LIMIT_EXHAUSTED` 属于程序搜索预算失败，不得据此要求 AI 改设计；完整候选域内无法分配时返回具体槽位约束。COMPACT 正式计划采用沿蜿蜒引导线分簇的布局，簇内通常4–5栋、末簇按剩余数量收尾；位置按成员实际模板跨度错落安排，簇间留空，弯曲由种子确定，不依赖坡地。建筑落位、空间估算、父组合包络和内部道路共用冻结布局。道路引导线转为可落地的正交短段，再由既有入口接续与地形道路流程处理。初始根阵列以首栋对齐选址点，必要时整体平移进入规划边界；显式关系和实际边界引导仍优先，不移动单栋绕过失败。DENSE最小间距容纳既有道路横断面。不新增AI轮次、嵌套要求或落地硬门槛。

正式 Blueprint D4 的外部 `quality_report.json` 保存 `sourceAnchorMapHash`，绑定同次最终输出的 `structure_anchor_map.json` 原始 UTF-8 内容。workflow 复用除校验 accepted Blueprint/context/hash 外，还必须要求最终质量 `passed=true` 且该 hash 一致；缺失、失败、旧版无 hash 或漂移的报告必须重编译，不得把失败时遗留的 map 视为成功产物。

每个 selection 按执行顺序记录 `phase=required|fill|connectivity_growth`。全部 Group 的 required 先完成并尝试各自第一批 fill，随后才允许规划 Landscape 起点；Landscape 容量结果不得触发 required/fill 建筑换位。`roadProfile.hierarchy=SIMPLE` 才允许最后执行既有 connectivity structure growth；`HIERARCHICAL` 由父阵列城市主干路承担区际连接，必须不生成 `connectivity_growth` 建筑。required/fill 继续记录单结构候选、评分、envelope 与提交状态；SIMPLE 的 connectivity selection 仍按完整阵列批次记录并原子提交，不得部分落地。

connectivity selection 另必填 `requestedBatchSize`、`terminalBatch`、`initialBodyGapBlocks`、`frontierGapCorrectionBlocks`；对应 `frontierSearchTrace[].rings[]` 记录 `correctedForBodyGap`。批量从解析后的配置规模按 `N..1` 确定性降级重试，失败尝试同样进入 trace；一组完整合法候选即可提交，零组才失败。`minCandidateCount` 不属于 Blueprint 或编译请求，旧字段必须以 `D4_ARRAY_LAYOUT_MIN_CANDIDATE_COUNT_REMOVED` 明确拒绝。

required、fill 和 connectivity batch 必须调用同一 Structure Terrain gate。门禁以 transformed collision footprint 为范围，对 `terrainModes` 做 OR 解析；当前 SURFACE 要求全部相交 D3 terrain-field cells 存在、已采样、非水并满足 Group `terrainPolicy` 的完整占地坡度、起伏和高程范围上限，不得只检查 anchor 点、首个 patch 或 dominant biome。候选生成必须逐点应用该门禁，不合法时继续搜索同一合法域。首个 required 只搜索 `preferredPatchRefs[]`，不得用 `d3_terrain_fallback` 改认领同一 D3 review grid 的其他 Patch；该域没有任何完整占地合法候选时单栋留空。selection 必须写 `CITY_BLUEPRINT_SELECTED_PATCH_TERRAIN_UNFIT` 与具体 `terrainFailureReasonCounts`，Group 写入 `terrainPlacementFailures[]`，验收写入 `SELECTED_PATCH_TERRAIN_UNABLE_TO_SUPPORT_REQUIRED_STRUCTURE`；普通局部起伏允许提交时仍记录 `terrainAdaptationRequired=true` 与 `foundation_or_skip`，不得误升级为承载失败。trace 至少记录 `structureRef`、`declaredTerrainModes`、`resolvedTerrainMode`、footprint、相交/已评估/拒绝格数、阈值、reasonCode 和有限失败样本；anchor 同样冻结 `resolvedTerrainMode`。`styleTerms` 不得出现在 gate、分数或候选排序依据中。

`selections[]` 的 committed 项与最终 `StructureAnchorPlan.anchors[]` 必填 `blueprintLayout`：`algorithm`、单调递增但可因非法留空而跳号的 `slotIndex`、`spacingBlocks`、`theoreticalAnchor`、`outwardGuided`、`densityParameters`、`preferredPatchZone`，首个核心另写精确 `coreSeedCell`，anchor 另冻结 `acceptedAnchor`。COURTYARD、LINEAR、CENTER_SYMMETRIC 使用全组最大 collision span 派生一次固定 pitch；GRID 同尺寸成员保留统一 pitch，混合尺寸成员按计划清单冻结各行列最大模板跨度及档位间距，使大核心只扩大所在行列。全部锁世界轴或主入口显式轴，只能尝试精确 guide；不得追加 member-cell center、随机旋转或其他形状兜底，不合法槽位写 `skipped_illegal_slot/EXACT_SLOT_ILLEGAL_LEFT_EMPTY` 后留空。GRID 另写 `gridRow/gridColumn/gridPitchBlocks/worldAxisLocked=true`；混合尺寸另写 `gridSpacingMode=FOOTPRINT_TRACKS`、`gridTracks={origin,gapBlocks,rows[],columns[]}`，每条 track 记录 `index/offset/span`。此模式的 `gridPitchBlocks/spacingBlocks` 仅为兼容的最大跨度参考，实际位置以 tracks 和 theoreticalAnchor 为准；道路骨架及父组合包络共用同一冻结布局，质量摘要 `fixedPitch=false`。不引入新AI参数、调用轮次或落地门槛；COURTYARD 另写 `courtyardRing/courtyardRow/courtyardColumn/courtyardCenter/courtyardGateSide=SOUTH`，slot 0–4 必须构成北侧主建筑、东、东南、西、西南且中心空置；COMPACT 分簇模式写 `compactLayoutMode=MEANDERING_CLUSTERS/compactClusterIndex/compactRoadGuide/compactLaneTarget`，引导线是世界坐标有序点列；不写旧环层方向字段。建筑在允许旋转内朝主巷或合法入口方向的支巷，最终必须由实际道路接通；实际地块边界引导不携带不匹配的蜿蜒引导线；ORGANIC_COMPACT 只使用程序随机 guides，在功能区内保持 collision gap 1–3 blocks，不产正式道路。需要朝路的结构必须写 `frontageRotation/frontageEntranceId/frontageDirection/frontageAlignmentScore/frontageMinimumAlignmentScore/frontageTargetRef`；规则直路要求满分朝向，弯巷/院角接受最近合法四向且不得低于 0.7。

阵列纵深：COURTYARD保留首层七槽及原有前五槽顺序；后续第r层使用8r-1槽，逐层保留南侧中央入口，不再只复制七个远端位置。CENTER_SYMMETRIC首两对仍在正交方向，之后补齐本层侧面与角部成对槽位；第r层4r对，完成后才外扩，不沿四条射线无限拉长。精确对称、原有道路开关、碰撞和入口检查保持不变。LINEAR仍表示沿街双侧队列，ORGANIC_COMPACT仍为无正式道路的自然布局；不把所有算法强制改成密集网格。

每个最终 anchor 另必填 `buildingParcelPlan`，schema=`city_building_parcel_plan`。`planningStage=D4_BEFORE_ARRAY_COMMIT`、`collisionPolicy=RAW_NBT_FOOTPRINT`、`marginBlocks=0`；`preferredBounds`、`resolvedBounds` 与 `hardCollisionEnvelope` 使用同一原始 NBT 占地（旋转只交换宽深）。不得叠加旧 clearance、Foundation 边距、间距或面积倍率，不为建筑分配额外绿化外圈。`usableGreenCells=0`，旧绿化配置可兼容读取但不能增加建筑占地；D6 原样保留计划。道路、院落布局空间和台面自身铺装另行处理，不反向扩大建筑占地。选材容量的 `footprintBasis=RAW_NBT_WIDTH_DEPTH`、`assumedGapBlocks=0`，仅为不含道路景观的基础估计。

紧凑布局的内部道路无法绕行时，保留建筑并在 `streetWarnings` 返回 `CITY_INTERNAL_STREET_REROUTE_UNAVAILABLE` 及省略组内道路的说明，不伪装连通或扩张建筑占地。

每个候选生成或编译器二次门禁拒绝的位置必须写入对应 `selections[].attempts[].failedAttemptPositions[]`。每项至少包含 `templateId`、`anchorBlock{x,z}` 与 `reasonCode`；已经计算出几何时同时保存 `plannedFootprint/estimatedCollisionEnvelope/estimatedMaskEnvelope`。没有生成 raw point 的精确槽失败也必须以 `blueprintLayout.theoreticalAnchor` 留下位置，不能只保存原因计数。该数组是失败功能区局部预览的正式输入，不得因最终 quality 失败而丢弃。

最终 `city_structure_anchor_plan` 与 `city_structure_anchor_map` 根级必填 `streetBands[]`、`cityMainRoadPlan`、`streetFirstNetworkTrace` 与 `residentialOverflowPlan`。区内道路项 schema 为 `city_internal_street_band`，必填 `streetBandId/roadNetworkId/roadKind/segmentIndex/groupId/geometryMode=STRAIGHT_AXIS_CLIPPED_BY_TERRAIN/widthBlocks/surfacePolicy=FOLLOW_TERRAIN_STEP_GRADED/crossSectionProfile=STAIR_SLAB_STAIR/hardSkeleton/axisX/axisZ/start/end/bounds/platformBounds/platformPolicy=LOCAL_HARD_SKELETON`；先行骨架另写 `reservedBeforeFill=true/planningPhase=STREET_SKELETON_BEFORE_FILL`，最终保留段改写 `planningPhase=FINAL_NETWORK_AFTER_BUILDING_USE_REVIEW/usageReview/servedEntranceIds[]/junctionCount`。短巷写 `hardSkeleton=false/reservedBeforeFill=false/planningPhase=FINAL_INDIVIDUAL_ENTRANCE_FALLBACK`；绕障共享扩展写 `roadKind=SHARED_NETWORK_EXTENSION/planningPhase=FINAL_SHARED_NETWORK_REROUTE`。`widthBlocks` 是中间半砖路面宽，两侧台阶路缘各额外占 1 block。短巷必须先沿 transformed entrance 门向退出完整横断面净空，再以 block 级四邻域避开全城 actual footprint；最多 32 格短巷无合法解时，只能在同一 Group 的既有网络上生成确定性绕障共享扩展，不得跨 Group 或为 ORGANIC_COMPACT 隐式造路。CENTER_SYMMETRIC 仅在 profile 开关启用时产轴街。

`streetFirstNetworkTrace.schema=city_street_first_network_trace`，必填 `planningOrder=CORE_THEN_SHARED_SKELETON_THEN_FILL_THEN_USAGE_REVIEW`、`reservedSkeletonSegmentCount/retainedSkeletonSegmentCount/removedUnusedSegmentCount/networkExtensionSegmentCount/shortAlleySegmentCount`、`removedStreetBandIds[]` 与 `accessOutcomes[]`。每个入口结果写 `entranceId/groupId/status/reasonCode`；正常城市不得含 `UNRESOLVED`，极端地形无法接入时必须进入 acceptance warning，不能静默消失。

`cityMainRoadPlan.schema=city_main_road_plan`，必填 `cityId/roadProfileRef/hierarchy/density/planningOwner=BLUEPRINT_EXPLICIT_TRAFFIC_CONNECTIONS/sharedNetworkPolicy=ONE_NETWORK_SERVES_MULTIPLE_TRAFFIC_DEMANDS/geometryMode=TERRAIN_AWARE_AXIS_ALIGNED_90_DEGREE/surfacePolicy=FOLLOW_TERRAIN_STEP_GRADED/crossSectionProfile=STAIR_SLAB_STAIR/internalStreetMaxWidthBlocks/mainRoadWidthBlocks/status/reasonCode/connectionCount/segmentCount/sharedNetworkReuseBlocks/connections[]`。只有 `relations[].relationKind=CONNECTION` 表示需要修路的显式交通意图；`HIERARCHY/ADJACENCY/BUFFER/DISTANCE/DIRECTION`、父阵列成员关系和功能区空间关系都不得自动生成主路或桥。每条显式交通连接的两端必须解析到真实模板 `roadEntrances[]` 或已冻结区内街端点，不再使用 Group 边界伪 gateway；连接项写 `routingPolicy=SHARED_NETWORK_REUSE_BEFORE_NEW_CORRIDOR/sharedNetworkReuseBlocks`。路径先在 D3 terrain field 四邻域避崖、再在 block 级按完整路面和路缘宽度避开实际建筑 footprint；已冻结主路 cell 的代价低于新走廊，后续需求优先复用同一网络。没有显式交通连接时合法输出空计划，显式连接缺真实出口或无合法路径时记录明确失败。

主干路每个直段 schema 为 `city_main_road_band`，写入同一 `streetBands[]`；主路半砖面宽取不小于 7 的奇数，且严格大于本城最大区内道路半砖面宽，两侧路缘另各加 1 block。陆地主路进入 Foundation 整地和 SurfacePrint；确认通路跨水时由 City 生成 `roadKind=CITY_BRIDGE` 的直线或 L 形桥段，桥段不填水、不进入 Foundation，使用独立桥面、护栏与水中桥墩，并保持两岸正式道路出口。所有正式道路均写入 City 自有冻结几何，不向外部道路 Mod 委托。

模板入口位于 footprint 内部时，城市主路接驳只沿作者门向在 footprint 外侧生成；模板内部既有院落/通道由模板保留，不生成穿过模板的接驳面。接驳不得穿过所属建筑原始 NBT 占地，也不得豁免其他建筑；起点及全段路面、两侧路缘均需避让。该投影只确定外部接入位置，不证明模板内部一定存在可通行路径，不得据此伪造入口连通验收。

`residentialOverflowPlan.schema=city_residential_overflow_plan`。程序只使用同 Group 已提交的 `phase=fill + blueprintLayout.outwardGuided=true` 建筑；至少 3 栋且其区内正式道路与子区范围相交时，冻结一个 `RESIDENTIAL_OVERFLOW` 子区。每项写 `zoneId/parentGroupId/generationMode=OUTWARD_GUIDED_FILL_BUILDINGS/buildingCount/boundaryBounds/boundaryBlockId/anchorIds[]/streetBandIds[]`，并把 `residentialOverflowZoneId` 回写成员 layout。执行层沿矩形边界写墙，所有关联道路 bounds 自动形成门洞；不足数量或无道路时不伪造子区。

最终 plan/map/trace 根级必填 `arrayVisualQuality`，schema=`city_array_visual_quality`，含 `passed/safeToMaterialize/hardBlocks/warnings/roadStructureOverlapCount/groups[]`。六阵列视觉与局部流线缺口写入 warnings；`passed` 只有安全与视觉检查都通过才为 true。全部区内路、过渡段和城市主路连同两侧路缘不得重叠任何建筑实际 footprint（包括 connectivity_growth 建筑）；碰撞进入 hardBlocks 并令 `safeToMaterialize=false`，始终阻断落地。`arrayVisualGapRecorded=true` 仅表示缺口有记录，不能降级安全失败。编译器可返回 `status=compiled` 保留预览，但最终能否落地由分层验收决定。

plan/trace 根级 `compilationAcceptance` 必填 `acceptancePolicy=SAFETY_AND_REQUIRED_CONTENT_V1/passed/qualityFullySatisfied/previewCompiled/requiredRelationCount/requiredRelationsSatisfied/structureGraphConnected/allFunctionAreasFormed/allRequiredStructuresCommitted/allRequiredContentPresent/arrayVisualGeometryPassed/allStreetEntrancesConnected/hardBlocks[]/warnings[]`。`passed` 表示落地底线通过，不表示质量满分；`qualityFullySatisfied` 仅在没有硬失败和警告时为 true。`previewCompiled=true` 仅表示预览已形成，失败也必须保留 PNG。局部入口 `UNRESOLVED` 逐项写 `STREET_ENTRANCE_UNRESOLVED` warning，`allStreetEntrancesConnected` 仍为 false，不伪造道路连通。

资源身份、规划边界、建筑及道路碰撞、空功能区、必需关系和指定建筑内容仍是落地硬门槛。多个 Group 中，凡 `expansionPolicy.allowRelationConnection=true` 的 Group 必须显式参与 relation；孤立 Group 必须显式关闭该能力。REQUIRED 阶段候选被拒绝时回溯已选候选，不得因 `D4_ARRAY_COUNT_UNSATISFIED` 或地形不适合跳过必需项，寄望后续填充补齐。有限候选组合穷尽后及时返回 `CITY_BLUEPRINT_REQUIRED_STRUCTURE_NO_LEGAL_PLACEMENT` 及分组、建筑、过滤原因，停止后续道路/填充；搜索预算耗尽与作者 frontage 缺口仍归程序处理。最终 `missingRequiredContent[]/allRequiredContentPresent` 继续按同一 Group 中同一 structureRef 的所有实际提交数量复核，不足仍写 `REQUIRED_STRUCTURE_MISSING`，兼容旧产物的阶段缺口诊断，不允许按推测功能替换。

交通验收以 `cityMainRoadPlan.connections[]` 和具备实际街带的 `bridgeConnections[status=PLANNED_BY_CITY]` 为依据；不以 `allowOutwardExpansion` 作为修路前提。`CONNECTION` 的满足与组间交通连通由道路结果判定；ADJACENCY/HIERARCHY 的建筑扩张约束仍由 connectivityPlan 判定。无路、跳过连接或仅声明桥委托不能视为通路。`group_extent_map.structureGraphConnected` 仍仅描述结构扩张拓扑，不能替代交通验收。COMPACT 与 COURTYARD 的首个成员偏离阵列中心，提交首个成员后不得把阵列中心平移到该成员位置。

最终 `StructureAnchorMap.quality.metrics.compilationAcceptance` 原样保存结果；只合并安全与必需内容 hardBlocks，质量问题只合并 warnings，外层 `qualityFullySatisfied` 同时考虑 warnings 和 needsReview。MCP 决策展示中，已有正式 artifact 引用的 `structureAnchorPlan/structureAnchorMap/cityGenerationCompileTrace/groupExtentMap` 可替换为包含 artifactPath、状态、计数与验收结论的摘要；完整质量报告、警告、作者选择及磁盘产物不截断、不删除。展示超限阈值不因此提高。

`CENTER_SYMMETRIC` 的 fill selection 另写 `requestedBatchSize=2`、`atomicPair=true` 与 `centerSymmetryProof`；两栋 anchor 的 `blueprintLayout` 必须共享 `symmetryPairId/symmetryPairIndex/symmetryCenter/visualCenter`，分别写 `symmetryPairMember=FIRST|OPPOSITE`。程序按模板变换后的 collision footprint 校正 anchor 对称中心；证明必须同时满足两端 anchor 关于校正中心成对，以及两栋实际 collision footprint 的几何中心关于中心主体的实际 collision footprint 中心成对。

`connectivityPlan` 必填 `topologyPolicy=EXPLICIT_RELATIONS_ONLY_NO_UNRELATED_FALLBACK`、`handoffThresholdPolicy=STRICT_BILATERAL_MINIMUM`、`edgeCount`、`fallbackEdgeCount` 与 `edges[]`。只允许 Blueprint 显式 `CONNECTION/ADJACENCY/HIERARCHY` 关系；缺少关系时不自动补最短路，不得让无关 Group 相向扩张。允许关系连接却未参与任何 relation 的功能区必须在 `compilationAcceptance` 记录 `FUNCTION_AREA_RELATION_UNSPECIFIED`，不能把这种歧义蓝图的离散结果验收为城市。每条边必填 `fromGroupId`、`toGroupId`、`topologySource=EXPLICIT`、`topologyReason`、`initialGapBlocks`、`finalGapBlocks`、`handoffGapBlocks`、`connectionStructureCount`、`connectionBatchCount`、`status`，`fallbackEdgeCount` 固定为 `0`；显式关系任一端禁止外扩或连接时跳过该连接并记录策略结果。`handoffGapBlocks` 及 HARD 关系复验必须同源读取双方解析后的 `resolvedConnectionPlan.derivedLayoutParameters.landUseHandoffGapBlocks` 严格最小值，不得混用 Group required/fill 的内部 handoff。

`groupResults[]` 必填 `groupId`、`requestedExtentClass`、`densityClass`、`terrainPolicy`、`densityParameterization=ALGORITHM_SPECIFIC`、`layoutAlgorithm`、`placementMode`、`layoutParameters`、`resolvedConnectionPlan`、`spatialDemand`、`targetAreaBlocks`、`maxExtentSpanBlocks`、`maxIntraGroupGapBlocks`、`outwardGuidedPlacementCount`、`derivedMinimumStructureCount`、`internalStructureCount`、`minimumStructureCountReached`、`internalSpatialDemandBlocks`、`connectionStructureCount`、`connectionBatchCount`、`connectionSpatialDemandBlocks`、`connectionExpansionBlocks`、`extentExpandedForConnectivity`、`actualStructureCount`、`requiredStructureCount`、`requiredStructureCounts`、`missingRequiredStructures[]`、`allRequiredStructuresCommitted`、`builtCollisionAreaBlocks`、`actualSpatialDemandBlocks`、`estimatedCoverageRatio`、`preferredPatchRefs[]`、`claimedPatchRefs[]`、`structureCounts` 与 `stopReason`。`requiredStructureCounts` 只统计 REQUIRED 阶段提交，`missingRequiredStructures[]` 每项写 `structureRef/missingCount/reasonCode=CITY_BLUEPRINT_REQUIRED_STRUCTURE_MISSING`。`spatialDemand.source=TEMPLATE_ARRAY_DEMAND`，并冻结模板实际占地、最低成形数量、算法密度间距、区内街带面积、最低/目标/上限面积、`formationSpanBlocks/formationWidthBlocks/formationLengthBlocks` 和可选 `primaryAxisDirection`；LINEAR 另写与根数组同源的 `streetBandPlan`。CORE 保留 extent 设计目标，STANDARD/PERIPHERAL 允许目标面积按真实最低需求小于 extent 设计目标。`placementMode` 是程序依据 `layoutAlgorithm` 派生的空间落地分类，只允许 `CORE_ANCHORED | AXIS_ANCHORED | CLUSTER_BOUNDED | TERRAIN_FOLLOWING`，不属于 AI 输入。`layoutParameters.placementMode` 必须与其一致。关系定位 Group 另写 `placementRelation`；父阵列参与 Group 另写 `arrayCompositionSlot` 和 `formationBounds`。`resolvedConnectionPlan` 必须写出继承后的 pool、算法、planner、疏密及继承来源。`SPATIAL_BUDGET_REACHED` 是正常完成，`CONNECTED_SPACE_EXHAUSTED` 表示达到可用空间边界后未填满预算；普通坡度/起伏、冲突、容量或候选域耗尽时，必须以成员级跳过或 `*_GAP_RECORDED` 留档并继续 D4，不能把运行期缺口冒充输入 hard fail。连接阶段可越过 extent 软目标，但不得越过 D3 规划网格等硬边界。

`groupResults[]` 另必填 `terrainPlacementFailures[]`。无失败时为空数组；有失败时每项包含 `structureRef`、`reasonCode=CITY_BLUEPRINT_SELECTED_PATCH_TERRAIN_UNFIT`、`selectedPatchRefs[]` 与底层 `terrainFailureReasonCounts`，不得只保留泛化阵列数量缺口。

`arrayCompositionSlots[]` 每项写 `groupId/compositionId/parentAlgorithm/centerGroupId/slotIndex/plannedSpanBlocks/spanSource/origin/placementOrigin/slotBounds`；`spanSource` 固定为 `TEMPLATE_ARRAY_DEMAND`，不得再把 `extentMaxSpan(SMALL|MEDIUM|LARGE)` 当作父阵列占位边长。`origin` 是父阵列用于碰撞、固定 pitch 和对称证明的槽中心；普通子组 `placementOrigin=origin`，LINEAR 则按 `primaryAxisDirection + formationLength/formationWidth` 把 `placementOrigin` 平移到槽外缘，使主建筑成为轴端且单向街带完整留在 `slotBounds` 内。中心对称成员另写 `pairIndex`，其对称性比较槽中心 `origin`，不比较 LINEAR 轴端。坐标均为程序编译结果，不是 Blueprint 输入。

`groupResults[]` 与 extent 中的每个 Group 还必须回写 `preferredPatchZone`，用于区分 AI 指定的内部方位与程序最终认领的 `claimedPatchRefs[]`。

## Landscape owner 的跨阶段一致性

景观由 `owner.groupId` 对应功能组拥有，与单栋建筑存续解耦。新设计省略 `requiredStructureRef`；旧字段兼容为初始位置参考，不要求该模板成功落位。显式 `growth.seed` 优先；无显式起点时可参考同组建筑，全部建筑为空则从景观/所属组偏好地形中确定稳定起点。`ownerAnchorId/ownerFootprint` 仅保留位置参考来源，D6 不因建筑缺失、后续填充或位置变化重新绑定或拒绝已冻结景观。D6 仍校验蓝图与容量 hash、所属功能组、地块、种子和实例完整性；旧容量几何直接保留，不补写存档绕过 hash。运行期景观 source anchor IDs 为空，建筑与道路仍通过占地排除规则协调。

空间关系并未解耦：功能区 intent 说明景观服务对象、选址理由及可达方式，终审结合实际总览检查。农田牧场考虑生产通道/邻近聚落，林场考虑作业运输，公共花园融入公共步行空间。无需每块景观自动造路，不能把功能名称当作整体性证据。

## GroupExtentMap v0.11

文件：`city_test_runs/<cityId>/steps/d4/group_extent_map.json`，`schema=group_extent_map`。根字段为 `cityId`、`generationSeed`、`connectivityPolicy=RELATION_GRAPH_ARRAY_GROWTH_THEN_LAND_USE`、`connectionSemantics=STRUCTURE_FRONTIER_FOR_LAND_USE`、`cityBoundaryPolicy=D3_REVIEW_GRID_HARD_BOUNDARY`、`functionAreaPolicy=COMMITTED_BUILDINGS_THEN_RELATION_AND_PERCENTAGE_EXPANSION`、`functionAreaFormationPlan`、`handoffThresholdPolicy=STRICT_BILATERAL_MINIMUM`、`structureGraphConnected`、`landUseConnected=false`、`landUseConnectionStatus=PENDING_LAND_USE_COMPILE`、`arrayCompositionSlots[]`、`connections[]`、`groups[]`。不得出现 `maxInterGroupGapBlocks` 或含糊的旧 `connected` 字段；调用方不得自行把结构拓扑解释成实体地表连通。

`connections[]` 与 compile trace 边字段同源，并增加 `landUseHandoffReady` 与 `connectionEdge{fromX,fromZ,toX,toZ}`；每个 Group 同时携带上述布局/空间/count/stop 字段、可选 `streetBandPlan`、`functionArea`、closed `collisionExtent{minX,minZ,maxX,maxZ}`、`functionAreaEnvelope`、`functionAreaEnvelopePolicy=COMMITTED_CLAIM_EXTENT` 与 `groupSeparationExemptGroupIds[]`。`functionArea.schema=city_function_area`，必须写出 `status=EMPTY_NO_COMMITTED_CLAIM|FORMED_FROM_COMMITTED_CLAIMS`、`source=COMMITTED_STRUCTURE_AND_LANDSCAPE_CLAIMS`、初始/实际总面积、结构数、Landscape 面积、精确 `initialFormationSpans[]`、`formationSpans[]` 与 Landscape 子集 spans。结构 spans 只能来自成功提交的 collision envelope，Landscape spans 只能来自成功规划的实际 reservation spans；不能来自预画容量格、外接矩形或 extent 档位。

根 `functionAreaFormationPlan.schema=city_function_area_formation_plan`，策略固定为 `COMMIT_BUILDINGS_BEFORE_FORMING_FUNCTION_AREAS`，并写出 `formedBeforeDynamicTargetFreeze=true` 和各 Group 的 `functionArea`。父阵列 `slotBounds` 只负责递归阵列的组间编排与碰撞容量，不是功能区面积；普通 Group required/fill 不受任何预分配功能区裁切。显式 Patch 只约束首个核心起点，后续建筑阵列只受 GIS 预览硬边界、逐建筑 terrain gate、实际碰撞与明确阵列关系约束，并可连续跨越相邻 Patch 标签边界。第一批建筑提交后才冻结 `initialFormationSpans[]`，再处理连接与占比目标。按占比补面积时，建筑循环只能补到 `targetAreaBlocks × spaceComposition.buildingShare`，Landscape 只能补到对应 `landscapeShare`；不得先用建筑填满整个功能区目标后再额外叠加景观。

所有 required、fill 与 connectivity batch 的 transformed collision envelope 默认必须与其他 Group 保持至少 12 blocks 边缘距离；命中时以 `GROUP_DISTRICT_BUFFER_VIOLATED` 拒绝当前候选并继续搜索。这段留白用于道路、绿化、坡坎或其他街区边界。直接构图伙伴豁免该硬缓冲：同一 `arrayComposition` 的中心与成员、显式 `ADJACENCY` 两端、`HARD CONNECTION|HIERARCHY` 两端、`BETWEEN_GROUPS` Group 与其明确 `groupRefs`。关系任一端属于父阵列时，只向该父阵列的全部成员展开一次；豁免不再沿普通关系链传递，不得把整座城市合并为一个街区。豁免伙伴仍受 collision、各自阵列参数和 handoff 约束。LandUse 编译后仍必须以真实 block spans 验收道路与地表连续性。

所有 Group 的首个 required 核心只搜索各自 `preferredPatchRefs[]`；起点域完整占地不可承载时留空并记录原因，不得回退到同一 D3 `review.grid` 的其他 Patch。首个核心成功提交后，后续 required、fill 与连接围绕实际核心连续生长，可认领 D3 `review.grid` 内其他 patch/member cells；`preferredPatchRefs[]` 与 `claimedPatchRefs[]` 必须分别保留起点意图和实际生长结果。Group `terrainPolicy` 不按 patch 平均坡度裁剪，而是对每个 transformed collision footprint 的 terrain-field 事实执行硬门禁。

固定模板 worldgen 的 `templateDatumPolicy=generator_base_height_motion_blocking_no_leaves` 表示高度来源。StructureStart 以 locked actual footprint 为范围每 4 blocks 采样 generator base height（包含远端边界），取排序中位数作为全结构唯一 `templateDatumY`；不得只取 anchor 点。仅 `supportPolicy=full_footprint_support` 的模板在 Beardifier 密度阶段获得完整矩形占地承托：台面下最大 32 blocks、外侧 2 blocks 收肩；其他 support policy 不生成该台基。城区 Foundation 与陆地道路先在同一建设面内按邻域主高程分成相邻目标差不超过 1 格的平台组件，再把组件统一到主高程；填方上限 48、切方上限 12，平台边缘目标差至少 2 格时以 stone bricks 垂直收边。城区水列保持原样；Landscape 农田、林场、牧场不进入该整地掩码。结构台基只消化整地后剩余的建筑局部高差。

`extentClass` 只参与单组最低成形与模板阵列推导，不是全城面积上限，也不生成固定城市外接框。D4 初始放置、冲突处理和显式关系连接完成后，`dynamicAreaPlan.frozenAreaSource=ACTUAL_COMMITTED_OWNED_AND_CONNECTION_AREA`，并只冻结唯一 `CORE` 已实际提交的建筑与连接 claim 面积作为基准；district reservation、`spatialDemand.minimumAreaBlocks`、extent 和 bbox 都不是实际所属面积，不得用于抬高基准。以 `frozenCoreArea / targetAreaShare` 推导参考总面积，再按所有 Group 的 `targetAreaShare` 计算目标面积；冻结后基准不移动。若 CORE 没有任何成功 claim，则 `frozenHighestPriorityAreaBlocks/referenceCityAreaBlocks` 及各停止型 Group 的目标允许为 0，不得用 minimum 伪造城市面积。目标不得超过 D3/GIS 预览的实际审查范围；达到边界、无可用地形或无合法候选时记录面积缺口。

单栋建筑遇到水体、缺失/未采样地形或特别陡地形时，记录 `CITY_STRUCTURE_TERRAIN_UNFIT_SKIP_MEMBER` 并跳过该成员，继续其余阵列；普通坡度/起伏允许以 foundation/platform 适配。不得因单成员跳过使整座城市失败。连接结构只能满足显式关系，不能代替组内建筑最低意图。

编译成功后必须输出 `city_structure_anchor_plan`、`city_structure_anchor_map` 与结构预览。D4 总览和每个功能区局部结构预览必须用独立颜色、半透明填充和清晰边线叠加各 Group 的精确 `functionArea.formationSpans[]`；`functionAreaEnvelope` 只可作为辅助轮廓，不得替代实际范围。预览还必须画出全部区内 `streetBands[]`、棕色粗线城市主干路和建筑 geometry；局部预览只画当前 Group 及与其相接的主干路。预览同时叠加 `landscapeCapacityReservationPlan.reservationSpans[]` 的精确格点面积，并以独立颜色和图例区分各 Landscape；不得只画外接矩形或只列文字数量。D5/D6 只消费这些标准产物，不读取 Blueprint、compile trace 或 extent map 建立特殊分支。


## 2026-09-08 逐区设计与地形保护主线更新

本节记录当前逐区提交、按需台面与支撑契约。下一阶段规模与嵌套需求见 City意图驱动规模与嵌套设计-v0.1；尚未实施的新需求不代表本节接口已更新。

- `city_submit_d4_blueprint.submissionMode` 为 `DRAFT|FINAL`，默认 FINAL，仍需通过当前草稿复核检查。DRAFT 对当前已有功能区执行完整 canonical 校验与几何预览；可用 RELATIVE_WEIGHTS 为当前部分功能区归一化。新增功能区使用完整 cityBlueprint，局部修改仍使用 replace-only blueprintPatch。FINAL 才发布正式 Blueprint/geometry commit 并允许后续编译队列推进。
- DRAFT 成功返回 `ok=true, designInProgress=true, nextAction=city_submit_d4_blueprint`。`city_blueprint_draft.json.status=preview_valid` 保留可修订基底；正式拒绝草稿仍为 rejected。二者均带 baseDraftHash，不能作为世界生成输入。成功预览另存 `city_blueprint_last_valid_preview.json`；失败保留该底图，working_preview 标记本次已知失败采样位置或受影响建筑。没有有效底图时明确标识，不制造建筑。
- `revisionEvidence.compiledPreview` 指向宿主生成的 PNG；宿主下一轮附加该图供模型检查。较大的几何保存在草稿文件，不在每次反馈中重复展开。旧 baseDraftHash/baseBlueprintHash 返回 recovery 和当前有效 revisionEvidence，不要求模型猜测新的哈希。
- 格式错误使用独立 `city_submission_format_budget.json`，按 contextId 记录 failedAttempts/maximumAttempts=10/remainingAttempts/retryAllowed。到第十次停止自动格式纠错。它不扣除原五次设计编译失败预算；程序故障、失效上下文和草稿恢复不算格式失败。外层三轮无进度不得截断此格式纠错区间；设计进展以草稿身份变化为依据，不能把重复回传同一草稿算新进展。
- 最终 geometry acceptance 存在时，designFeedback 只提取当前 hardBlocks，关联精确 relations 路径及主路 skippedConnections，不把已解决的候选失败当作修改目标。必需建筑的有限候选失败若具备具体结构/位置证据，可进行相关局部设计修订；没有证据或达到搜索安全上限仍由程序处理。
- `arrayRoadInterfaces[]` 在 required 阵列街道形成后、填充扩张前冻结接入候选与保护范围。reserved 接入区用于碰撞保护，不等于已经铺设的道路。LINEAR/院门/轴线接口优先于个别建筑门口；COMPACT 通过巷道出口接入。主路先按接口等级和距离排序，失败后尝试其他可用接口组合；不移动建筑让路。
- Foundation 只来自需要城区铺地的 URBAN 成员及局部间隙闭合，不再求全城连通凸包。高度依据附近实际建筑与地形局部主高程量化为台阶；连通不再要求同一标高。PRESERVE 仍保留 D4 道路，LANDSCAPE 成员不生成统一城区地板。建筑底板下空洞由独立基础支撑保护。


## 多池与局部组合外扩（2026-09-08）

功能区的 `fillPools` 与引用目录中的 `fillPools` 不同：前者仅保存 `poolRef/weight`，后者定义池内容和单结构复用上限。旧 `fillPoolRef` 视为唯一候选池；序列化保留单池或多池形式，不同时输出两种。连接的 `structurePools` 使用相同权重格式。初始填充逐次选择池，比例外扩每个组合选择一次；种子、功能区、阶段、组合序号和池引用决定可复现的加权顺序。池内仍优先选择本组使用较少、未耗尽的结构，计数跨阶段累计。

比例外扩使用程序固定枚举顺序 `GRID → LINEAR → COURTYARD → COMPACT → ORGANIC_COMPACT`，按算法优先级尝试可放置的小组合；不由 AI 配置优先级，不重新排列已提交建筑。每个组合最多六栋，受限时尝试较小组合，院落至少五栋。城市既有正交阵列方向延续到新增组合；内部巷道及接续段与建筑一起检查，原子提交后立即加入后续扩张的道路保护范围。道路与建筑碰撞、门口无法接续、无法接到已有道路时，该候选不提交。缺少任何既有道路时允许第一个小组合建立自己的内部通路，最终整城道路仍按主线验收。

外扩 anchor 的 `blueprintLayout` 增加 `expansionUnitId`、`expansionAlgorithm`、`selectedPoolRef`；组合首栋携带 `expansionStreetBands`，最终道路进入标准 `streetBands`，等级 SECONDARY、窄巷横断面 SURFACE_ONLY。选择 trace 同步记录实际算法、池和整组提交的 anchor IDs。达到面积目标停止；无合法组合保留已提交结果并记录空间不足，不因新组合失败留下部分建筑。


## 2026-09-14 功能区初版、局部修饰与整城复核

设计指引由冻结 Context 的 `designGuide.designLoop` 提供：先根据地形、城市职能与素材池决定功能区意图，再按既有 `scaleDesignTask` 规划数量与嵌套。逐功能区初版和局部修饰后，检查整城总览，按需要显式添加有用途的相邻阵列、调整组合或保留留白。功能区可以由多个叶阵列组成，不新增构图枚举、面积门槛或强制修改次数。

- 工具侧 `designIntent.groups` 按 groupId 增量合并，不删除未在本次请求中出现的意图。相同意图保留选材和估算，修改该意图则重新选材。
- `city_submit_d4_blueprint.designReview` 与蓝图、补丁、选材或意图修改分开提交，不改变 canonical Blueprint。对象包含 `baseDraftHash`，以及 `groupIds`（1～3 个唯一当前叶组 ID）或 `overview=true`，可选 `assessment`。
- 先不带 assessment 请求当前局部图，响应 `requestedPreviews` 经共享展示层转换成模型实际收到的 PNG 图片。看图后再次提交同一目标及 assessment，记录空间意图是否落实、实际规模、组合关系与保留理由或修改计划。允许一个判断覆盖同一功能区的多个子阵列。程序记录模型判断，不宣称已经自动审美验收。
- 所有当前局部图已复核后，使用 overview 请求总览，再提交整城 assessment。修订使用 DRAFT；受影响的局部图内容变化使对应复核失效，未变局部保留。整城复核同时绑定草稿哈希与总览图内容，任意蓝图修订都需重新复核总览。模型未请求当前图片时不能直接登记 assessment。
- 复核状态持久化在当前城市 `city_design_review.json` 并绑定 contextId；prepare 与 DRAFT 回传 `designReviewWorkflow`，包括阶段、pendingGroupIds、既有判断和 readyForFinal，支持恢复。
- 正常取图、登记与等待复核返回 `ok=true, designInProgress=true`，不扣格式/设计失败预算，不发布正式产物、不推进生成队列。参数格式错误仍走原格式预算。
- 工具入口 FINAL 只接受与已完成局部及整城复核的有效草稿相同的 canonical 输入。未复核或 FINAL 携带新设计时，返回待复核流程和下一步操作。底层程序提交入口保留直接验证能力，游戏内 Agent/MCP 一律经过复核入口。


### 设计优先的复核判断（2026-09-14）

AI 应大胆使用当前素材、阵列参数、嵌套及显式向外阵列，依据地形实现设计意图。按功能区完成初版、看局部图并修饰，再继续下一功能区；最终依据总览调整区间关系。设计满意是目标，编译成功仅说明获得了可复核结果。

- 分档阵列数的 min/max 是初版建议，不是最终上限、验收目标或停止修饰的理由；有明确用途时可以超过建议范围。
- 局部复核对照原定意图检查共享空间、沿街连续性、距离、层次与实际保留规模。全部落位、各区非空、嵌套数量达标不能单独证明设计合格。
- 减数量、删建筑、移除嵌套后重新检查设计意图是否仍成立；受损时通过合适的位置、参数、素材或有用途的新增阵列补偿，不以降低请求来单纯追求保留率。允许有理由的删减，不强制补回相同数量。
- 总览检查各区是否形成整体。距离过远时可以调整已有组合或设计过渡；留白应有图上可核对的位置和用途，不能仅以“呼吸感”解释空洞。
- 纠错时保留无关工作，不代表禁止修改已成功落位但设计薄弱的区域。可以保留真正合适的布局，但 assessment 应给出具体空间依据；不强制修改次数。

以上为模型设计与验收指引，不增加字段、面积阈值、预算或程序美观判定，不解除地形、碰撞、素材与正式状态约束。


### 2026-09-14 落地道路占用、模板土基与台地边缘修正

- 最终道路 feature 的 X/Z 列拥有地面与上层作物/覆盖层的优先权，执行端再次排除同列景观和边界；台地通行路径及台阶列同样不种作物。该保护不替代前置道路排除掩码。
- 台地 accessPaths 不得覆盖现有道路 feature。冻结道路台阶保持既定高度和朝向，未冻结道路仍可通过现有台地台阶替换机制衔接。
- 新建固定模板 StructureStart 以原台面/地形 first-free 高度减去模板土基地面偏移作为 NBT 原点。偏移取 NBT 外缘土类方块各列最高层的 first-free 高度众数，同票取低层；不根据结构名称决定下沉，不把内部花盆作为地面。没有外缘土基证据时保留原点策略。偏移按模板实例缓存。已经冻结的 templateDatumY 保持不变，避免旧结构各区块错层。
- 台地边缘按相邻台面的实际目标高度判断，不因 areaId 不同而把同高区域当悬崖。平行经过边缘的 accessPath 不再整段清掉护栏，仅跨越高差的路径、台阶及正式入口保留开口；原有高差门槛、建筑占用排除及墙/绿化交替保留。


### 2026-09-14 功能层级与几何依赖分离

提交前分别校验功能层级自身及几何依赖图；成环返回 `CITY_BLUEPRINT_DEPENDENCY_CYCLE`，issues 指明实际循环的组名、组合或关系来源、JSON 字段路径和局部修订建议。走既有提交校验纠错，不标记宿主程序故障，不改变预算上限；原有效草稿保持。旧蓝图直接编译也返回同类结构化失败，避免循环异常被包装成宿主故障。

## 景观独立 cell 设计（2026-09-14）

`outdoorPlan.landscapes[].growth` 可选对象：`seed:{x,z}` 为预览内世界坐标，`targetCellCount` 为每实例总目标 cell 数（正整数），`allowedLandformTypes` 复制 terrain field 的 landformType 名称，空数组表示在原有可落地限制内不额外筛选。当前用于 required=true、ATTACHED、owner.groupId 的景观，instanceCount=1；支持按功能区归属且配套建筑未落下时仍从指定点设计。数量不由建筑面积比例推算，parcelCount 只组织内部地块。

cell 边长使用当前 terrain field.cellStepBlocks，不能假定等于 MC 区块。D4 按地形代价一次生长，边界在同一选中域内细化；输出 targetCellCount、actualCellCount、actualCellEquivalent、actualAreaBlocks、cellStepBlocks 和短缺警告。种不满或零格均为有效预览，不能回溯补满或越预览安全圈补量。已有未提供 growth 的方案保留输入兼容，但景观候选按顺序选择，不再组合回溯；内部内容比例允许近似。

## 可选材质覆盖与按需方块查询

`cityBlueprint.surfaceMaterials` 和独立 `blockMaterials` 查询见 [AI 材质与方块检索契约](CityAI材质与方块检索数据契约.md)。它们不改变阵列与景观布局参数。


## CONTIGUOUS 模板景观连片阵列（2026-09-18）

- Reference Catalog `algorithmProfiles[].algorithm` 新增 `CONTIGUOUS`。托管内容源在未配置该算法时加入 `algorithm:contiguous`；作者已有同算法引用时保留其引用。Context 冻结后按原 catalog hash 流转，旧 Context 不动态补字段。
- Group 使用现有 `algorithmProfileRef`、`requiredStructureRefs`、fill pool 和 `structureCount`；后者范围更新为 1–1024，仍不得少于 required 数量。填充仍遵守作者的 `maxCopiesPerStructurePerGroup`，0 表示无限制；提示词不能绕过作者限额。
- 按选定模板首个合法旋转后的真实宽深预编排，固定 seed 与成员前缀可复现。模板外框四邻边接触，禁止角接触替代连片；内部间距、随机抖动和街带宽度均为 0。以紧凑、有缓慢轮廓变化的形态选择外缘位置，不生成每块农田的城市式街网。
- 每个成员的 origin 和变换冻结后复用普通 template placement / `structure_start_beard_thin` 链路。地形或碰撞拒绝不移动其他成员；后续成员必须连接已有保留成员，根成员失败不能另生孤岛。报告 `CONTIGUOUS_ROOT_UNAVAILABLE` / `CONTIGUOUS_EDGE_CONTACT_REQUIRED`，仍采用原成员缺失反馈。
- 父 CONTIGUOUS 阵列按完整子阵列外框贴边组织，不拆平子成员。质量输出提供 `connectedComponents`、`retainedMemberCount` 与 `contactBasis=TEMPLATE_XZ_FOOTPRINT_EDGE`；分裂时报告 `CONTIGUOUS_DISCONNECTED_COMPONENTS`。
- 接触指标证明 X/Z 模板外框连片，不等于素材内部田埂或高程接缝已验收。天然 `outdoorPlan.landscapes` 行为保持原契约。
- AI 指引鼓励可用空间内数百块规模，禁止把高规模理解成高随机性；仍只选作者批准的功能素材。素材导入与语义审核仍走模板内容包流程，新增算法不会自动导入外部投影。

## 建筑地形异常占比（2026-09-18）

逐建筑 terrain gate 在原有浅封闭水坑豁免与普通坡度适配之外，增加异常面积预算。异常面积按 transformed collision footprint 与 terrain-field cell 的实际相交 block 面积求和，不按完整格数量估算；默认最大比例为 0.10（含边界）。面积比例适用于所有尺寸的建筑，不按模板名称判断巨构。

原本会拒绝的水格、超过 policy 两倍坡度/局部起伏的格，以及整体高差超过 policy 两倍高差阈值时偏离面积加权高程中位数超过一倍高差阈值的格，合并计为异常，不重复累计。缺失或未采样、无 terrainPolicy、水深未知或超过一倍高差阈值、坡度/起伏/相对中位数高差超过四倍对应阈值仍为硬拒绝。异常八邻接连通分量接触 footprint 的两条相对边时仍拒绝，防止低面积占比掩盖贯穿沟壑。原浅封闭水坑豁免保持不变，不计入新增异常预算。

其余异常比例不超过 10% 时允许进入基础适配，记录 CITY_STRUCTURE_LOCAL_TERRAIN_ANOMALY_TOLERATED / foundation_support_required；准入不等于真实 worldgen 已验收。超过比例仍返回原地形拒绝原因。trace 新增 anomalyAreaBlocks、footprintAreaBlocks、anomalyAreaRatio、maximumAnomalyAreaRatio、anomalyCellCount、referenceElevation、hardTerrainFailure、crossingAnomaly。通过时 rejectedCellCount 为 0，failureSamples 保留原始异常诊断，terrainAdaptations 标明适配要求。缺省 policy 的旧调用仍严格拒绝异常，不放宽采样与碰撞约束。此节细化上述单成员水体/陡地形拒绝口径，不改变景观容量门禁。

## 聚落组合与贴地地面增量（2026-09-21）

- 角色继续来自 StructureProfile：`planning_role.key/anchor` 为明确主体，`planning_role.fill` 为重复候选，`planning_role.structure` 为明确选用结构，`planning_role.self_contained` 表示已核对的完整组合。核心、明确选用和完整组合不会因旧填充池残留而再次随机填充；未知角色保持旧目录兼容。完整组合标记必须有素材证据，不能只凭名称推断。
- `designReview.groups[]` 增加 `core/retainedCompositionCount/selfContainedComposition/isolatedCore`；顶层 `isolatedCoreGroupIds` 记录未形成组合的核心。检查实际保留的同组及嵌套成员，不将计划数量当成落位结果。已标记的完整组合可单独成立。
- 总览存在孤立核心时禁止 FINAL；`REPAIR_CORE` 只修复当前有此缺口的功能区，允许调整 `requiredStructureRefs/fillPools` 与阵列参数，不能更改用途、选址或删除主体。独立外围区也可修复自身组合。其余视觉主次仍由 AI 看图判断，不能用随意增加一个配件冒充设计成立。
- `designReviewWorkflow.coreReworkCount` 对触发返工的不同草稿去重；单纯看图和评价不计数。五次返工仍未解决时 `coreReworkExhausted=true` 并停止请求人工检查；不放宽组合要求。
- `foundationGroupIds` 选择显式共同台地，不承担全部公共地表范围。GENERATE 模式下，已落位的 STRUCTURE 组若算法为 GRID / COURTYARD / CENTER_SYMMETRIC、密度非 SPARSE、地形策略非 CONFORM 且 landscapeShare=0，也整理共同台面。此补地不放宽 D4 落位条件。
- 共同台面包含组内短间隙与邻近城市道路的路肩；已接受建筑周边的粗采样 cliff 标签不再挖出台面空洞，水域、未采样区域与已预留景观仍受保护。不同高度通过台地衔接，不整平城墙内全部土地。
- Compact 村落未显式选择共同台地时保留簇间自然地面，只有靠近城区台面的道路局部接坡。接坡使用不可变地形采样和邻近冻结高程，不依赖区块施工顺序；入口已接入同层冻结道路时复用该道路，不重复要求台阶。

## 村庄道路外观配置（2026-09-24）

复用 `COMPACT_ALLEY` 作为村庄道路；同村庄组的入口短巷、入口接近段和延伸段使用相同外观。默认取消道路两侧连续砖阶，以泥土径、砂土、缠根泥土按6:3:1确定性混铺，接坡台阶独立保留。城区主路与桥梁保持原样。

配置文件为 `config/geomantia/city_land_use/village_roads.json`，服务器启动时只补缺失文件，不覆盖用户配置；下一次地表编译读取配置。内置默认位于实现仓 `src/main/resources/geomantia/default_config/city_land_use/village_roads.json`。

| 字段 | 作用 |
| --- | --- |
| enabled / roadKinds / seed | 外观开关、应用的道路类型（默认 COMPACT_ALLEY）、固定随机种子。 |
| surfacePalette[].blockId / weight | 混铺方块及正整数相对权重；按城市ID、坐标与seed固定选择。 |
| stairBlockId / baseBlockId | 坡道台阶与路基材质。 |
| decorationsEnabled / spacingBlocks / chance | 装饰开关、每侧候选间隔、候选放置概率；默认12格与0.55，两侧错开，并保持装饰间距。 |
| structureTreesEnabled | 村路沿线是否额外摆放原有大树结构，默认false，避免与小装饰叠加。 |
| edgeOffsetBlocks / endClearanceBlocks | 装饰离路面边界距离、路段端部留白；默认2格与2格。 |
| variants[].id / weight / blocks[] | 栅栏灯笼、杜鹃树叶、浆果丛等组合的ID、相对权重与方块列表。 |
| blocks[].along / outward / height / blockId | 沿道路、向路外、离实际地面高度的偏移与方块；上层方块要求同列下方有支撑。 |

宽度、走向仍由已有阵列道路几何参数确定，外观配置不移动道路。村路混铺配置优先于城市通用材质覆盖，最终方块、装饰和坡道材质冻结进 SurfacePrint 及其 hash；执行时不重新随机，也不读取新配置改写旧计划。关闭外观则使用原道路材质流程。

装饰避开建筑、其他道路、台面/景观和D5预留区；可用位置不足时减少，不强行挤入。执行时仅落在自然地表，可选装饰遇水体、占用或不适合植物存活的地面时跳过该列；栅栏与其上灯笼作为同列一起检查。叶块保持 persistent，浆果丛按原版生长。城区道路树及自然地形中的树木保留，村路自动大树由上述开关控制。
